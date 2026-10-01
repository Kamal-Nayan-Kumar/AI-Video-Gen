"""FastAPI application.

The important structural change here is concurrency. The original
`/api/generate` was an `async def` that performed long blocking work —
network calls, Manim subprocesses, MoviePy encodes — directly on the event
loop. That blocked the loop for the entire generation, so the SSE progress
endpoint could never respond while a job was running, and the progress UI was
effectively dead.

Generations now run as background jobs on a worker thread. Each job owns an
asyncio queue that the worker pushes updates into; the SSE endpoint drains that
queue. This keeps the progress stream genuinely live and means several jobs can
be tracked at once.
"""

import asyncio
import json
import os
import queue
import threading
import traceback
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from config import Config

app = FastAPI(
    title="AI Video Presentation Generator",
    version="2.0.0",
    description="Turns a topic into a narrated, illustrated video deck.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Job registry
# ---------------------------------------------------------------------------
class Job:
    """One generation run, with a thread-safe event buffer for the UI."""

    def __init__(self, job_id: str, topic: str):
        self.id = job_id
        self.topic = topic
        self.state = "queued"
        self.progress = 0
        self.message = "Queued"
        self.result: dict | None = None
        self.error: str | None = None
        self.done = threading.Event()
        self.events: queue.Queue = queue.Queue()

    def emit(self, state: str, progress: int, message: str) -> None:
        self.state = state
        self.progress = progress
        self.message = message
        self.events.put(
            {
                "job_id": self.id,
                "status": state,
                "progress": progress,
                "message": message,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
            }
        )
        stamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{stamp}] {progress:>3}%  {message}")


jobs: dict[str, Job] = {}


class GenerateRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=200)
    num_slides: int = Field(5, ge=3, le=12)
    language: str = "english"
    tone: str = "formal"


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------
def run_pipeline(job: Job, request: GenerateRequest) -> None:
    """Execute the full generation. Runs on a worker thread."""
    # Imported here so the module loads fast and import errors surface at
    # request time with a useful message rather than at startup.
    from generators.content_generator import ContentGenerator
    from generators.image_fetcher import ImageFetcher
    from generators.manim_generator import ManimGenerator
    from generators.script_generator import ScriptGenerator
    from generators.voice_generator import VoiceGenerator
    from utils.slide_renderer import SlideRenderer
    from utils.video_composer import VideoComposer
    from utils.video_renderer import VideoRenderer

    topic = request.topic
    total = max(3, min(int(request.num_slides), 12))

    try:
        job.emit("running", 3, "Drafting the slide outline")

        content_data = ContentGenerator().generate_content(topic, total)
        slides = content_data["slides"]
        actual_total = len(slides)

        job.emit("running", 15, "Writing the narration script")

        script_data = ScriptGenerator().generate_scripts(
            content_data, request.language, request.tone
        )

        job.emit("running", 24, f"Synthesising narration for {actual_total} slides")

        voice = VoiceGenerator()
        audio_paths: dict[int, str] = {}
        durations: dict[int, float] = {}

        for index, slide_script in enumerate(script_data["slide_scripts"], start=1):
            number = slide_script["slide_number"]
            job.emit(
                "running",
                24 + int(18 * index / len(script_data["slide_scripts"])),
                f"Synthesising narration for slide {index}/{actual_total}",
            )
            try:
                path = voice.generate_voice_for_slide(
                    slide_script["narration_text"],
                    number,
                    topic,
                    request.language,
                )
                audio_paths[number] = path
                durations[number] = voice.duration_of(path)
            except Exception as exc:  # noqa: BLE001
                # One failed slide must not sink the whole video.
                print(f"  Narration failed for slide {number}: {exc}")

        # Retime the script against the audio we actually produced.
        cursor = 0.0
        for slide_script in script_data["slide_scripts"]:
            number = slide_script["slide_number"]
            length = durations.get(
                number,
                max(3.0, float(slide_script["end_time"]) - float(slide_script["start_time"])),
            )
            slide_script["start_time"] = round(cursor, 2)
            slide_script["end_time"] = round(cursor + length, 2)
            cursor += length
        script_data["total_duration"] = round(cursor, 2)

        if not audio_paths:
            raise RuntimeError("Narration could not be generated for any slide")

        job.emit("running", 44, "Joining the narration track")
        audio_path = voice.combine_slide_audios(audio_paths, topic)

        # --- visuals ---------------------------------------------------
        job.emit("running", 50, "Laying out slides")

        renderer = SlideRenderer()
        manim_gen = ManimGenerator()
        image_fetcher = ImageFetcher()
        video_renderer = VideoRenderer()

        visuals: dict[int, object] = {}
        counts = {"text": 0, "image": 0, "animation": 0}

        for index, slide in enumerate(slides, start=1):
            number = slide["slide_number"]
            share = 40 / actual_total
            job.emit(
                "running",
                50 + int(share * index),
                f"Laying out slide {index}/{actual_total}",
            )

            wants_animation = bool(slide.get("needs_animation"))
            wants_image = bool(slide.get("needs_image"))

            # Animation wins if the model asked for both.
            if wants_animation:
                base = renderer.create_slide_with_animation_placeholder(
                    slide["title"],
                    slide["content_text"],
                    number,
                    topic,
                    actual_total,
                )
                try:
                    code = manim_gen.generate_animation_code(
                        slide, slide.get("duration", 6.0)
                    )
                    code_path = manim_gen.save_animation_code(code, number, topic)
                    animation = video_renderer.render_manim_animation(
                        code_path, f"{manim_gen.sanitize_filename(topic)}_slide_{number}"
                    )
                    visuals[number] = {
                        "type": "animation_composite",
                        "base_slide": base,
                        "animation": animation,
                    }
                    counts["animation"] += 1
                    continue
                except Exception as exc:  # noqa: BLE001
                    print(f"  Animation failed on slide {number}: {exc}")
                    visuals[number] = base
                    counts["text"] += 1
                    continue

            if wants_image and slide.get("image_keyword"):
                try:
                    picture = image_fetcher.fetch_image(
                        slide["image_keyword"], number, topic
                    )
                    visuals[number] = renderer.create_slide_with_image(
                        slide["title"],
                        slide["content_text"],
                        picture,
                        number,
                        topic,
                        actual_total,
                    )
                    counts["image"] += 1
                    continue
                except Exception as exc:  # noqa: BLE001
                    print(f"  Image failed on slide {number}: {exc}")

            visuals[number] = renderer.create_text_slide(
                slide["title"], slide["content_text"], number, topic, actual_total
            )
            counts["text"] += 1

        print(f"  Visual breakdown: {counts}")

        job.emit("running", 92, "Encoding the final video")

        final_path = VideoComposer().compose_final_video(
            content_data, script_data, visuals, audio_path
        )

        job.result = {
            "video_filename": Path(final_path).name,
            "content_data": content_data,
            "script_data": script_data,
            "counts": counts,
            "total_duration": script_data["total_duration"],
        }
        job.emit("completed", 100, "Ready to play")

    except Exception as exc:  # noqa: BLE001
        job.error = str(exc)
        job.emit("error", job.progress, f"Failed: {exc}")
        traceback.print_exc()
    finally:
        job.done.set()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/health")
async def health() -> dict:
    """Liveness plus the capability matrix, so the UI can show what is live."""
    return {
        "status": "ok",
        "capabilities": Config.capability(),
        "jobs": len(jobs),
    }


@app.post("/api/generate")
async def generate(request: GenerateRequest) -> dict:
    """Queue a generation and return a job id immediately."""
    job_id = uuid.uuid4().hex[:12]
    job = Job(job_id, request.topic)
    jobs[job_id] = job

    # Daemon thread: the worker is CPU/IO bound and must not block the loop.
    threading.Thread(
        target=run_pipeline, args=(job, request), daemon=True, name=f"job-{job_id}"
    ).start()

    return {"job_id": job_id, "status": "queued"}


@app.get("/api/progress/{job_id}")
async def progress(job_id: str, request: Request) -> StreamingResponse:
    """Server-sent events describing a job's progress."""
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Unknown job id")

    async def stream():
        loop = asyncio.get_running_loop()
        yield f": stream open\n\n"

        while True:
            if await request.is_disconnected():
                break

            # Drain everything queued so far without blocking the event loop.
            while not job.events.empty():
                try:
                    event = job.events.get_nowait()
                except queue.Empty:
                    break
                yield f"data: {json.dumps(event)}\n\n"

            if job.done.is_set():
                # Flush the terminal state, then close cleanly.
                while not job.events.empty():
                    try:
                        event = job.events.get_nowait()
                    except queue.Empty:
                        break
                    yield f"data: {json.dumps(event)}\n\n"
                summary = {
                    "job_id": job.id,
                    "status": job.state,
                    "progress": job.progress,
                    "message": job.message,
                    "done": True,
                    "error": job.error,
                }
                yield f"data: {json.dumps(summary)}\n\n"
                break

            # Wait on the queue rather than polling it.
            try:
                event = await loop.run_in_executor(
                    None, lambda: job.events.get(timeout=0.25)
                )
                yield f"data: {json.dumps(event)}\n\n"
            except queue.Empty:
                continue  # Re-check the loop conditions.

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/job/{job_id}")
async def job_result(job_id: str) -> dict:
    """Fetch a finished job's payload."""
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Unknown job id")
    if not job.done.is_set():
        raise HTTPException(status_code=409, detail="Job is still running")
    if job.error:
        raise HTTPException(status_code=500, detail=job.error)
    return job.result or {}


@app.get("/api/video/{filename}")
async def get_video(request: Request, filename: str):
    """Stream a finished video, honouring HTTP range requests."""
    # Reject any path traversal attempt outright.
    name = Path(filename).name
    if name != filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    video_path = Config.FINAL_DIR / name
    if not video_path.is_file():
        raise HTTPException(status_code=404, detail=f"Video not found: {name}")

    file_size = video_path.stat().st_size
    range_header = request.headers.get("range")

    headers = {
        "accept-ranges": "bytes",
        "content-length": str(file_size),
        "access-control-expose-headers": "content-length, content-range, accept-ranges",
    }
    start, end, status = 0, file_size - 1, 200

    if range_header and range_header.startswith("bytes="):
        try:
            raw = range_header.removeprefix("bytes=").split("-")
            start = int(raw[0]) if raw[0] else 0
            end = int(raw[1]) if len(raw) > 1 and raw[1] else file_size - 1
        except ValueError:
            raise HTTPException(status_code=416, detail="Malformed range") from None
        if start > end or start >= file_size:
            raise HTTPException(status_code=416, detail="Range out of bounds")
        end = min(end, file_size - 1)
        headers["content-range"] = f"bytes {start}-{end}/{file_size}"
        headers["content-length"] = str(end - start + 1)
        status = 206

    def body():
        with open(video_path, "rb") as handle:
            handle.seek(start)
            remaining = end - start + 1
            while remaining > 0:
                chunk = handle.read(min(1024 * 512, remaining))
                if not chunk:
                    break
                remaining -= len(chunk)
                yield chunk

    return StreamingResponse(
        body(), media_type="video/mp4", headers=headers, status_code=status
    )


@app.get("/api/content/{job_id}")
async def get_content(job_id: str) -> dict:
    job = jobs.get(job_id)
    if job and job.result:
        return job.result["content_data"]
    raise HTTPException(status_code=404, detail="Content not available")


@app.get("/api/script/{job_id}")
async def get_script(job_id: str) -> dict:
    job = jobs.get(job_id)
    if job and job.result:
        return job.result["script_data"]
    raise HTTPException(status_code=404, detail="Script not available")


if __name__ == "__main__":
    import uvicorn

    print(f"Starting in {Config.MODE} mode — capabilities: {Config.capability()}")
    uvicorn.run(app, host=Config.HOST, port=Config.PORT)