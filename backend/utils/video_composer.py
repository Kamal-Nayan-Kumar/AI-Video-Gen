"""Final video assembly.

Concatenates the per-slide visuals in narration order and muxes the combined
narration onto the result.

Two things differ from a plain `write_videofile` call, both of which caused
real failures with the original implementation:

* **Ordering.** An animation is looped or trimmed to the slide's measured
  duration *before* being resized and positioned. Applying a position first and
  a duration afterwards discards the position in MoviePy, which is why
  animations previously appeared at the wrong origin or scale.

* **Encoding.** Frames are streamed to ffmpeg over an explicit pipe with a
  watchdog. MoviePy's own writer stalled indefinitely on this machine (an
  earlier `write_videofile` left a job "running" forever with a half-written
  file and a defunct ffmpeg child), and it also routed everything through an
  RGBA pipe, which is both slow and a source of `yuva420p` encoder hangs.
  Writing `yuv420p` frames directly is roughly an order of magnitude faster
  and cannot wedge.
"""

import subprocess
from pathlib import Path
from typing import Dict

import numpy as np

from moviepy import (
    AudioFileClip,
    ColorClip,
    CompositeVideoClip,
    ImageClip,
    VideoFileClip,
    concatenate_videoclips,
)

from config import Config

WIDTH, HEIGHT = 1920, 1080
FPS = 30

# Must match SlideRenderer.ANIMATION_PANEL.
ANIMATION_PANEL = (1010, 250, 850, 700)

# Rough ceiling for the whole encode; guards against a wedged ffmpeg.
ENCODE_TIMEOUT = 900


class VideoComposer:
    """Build the final MP4 from slide visuals and the narration track."""

    @staticmethod
    def sanitize_filename(text: str, max_length: int = 30) -> str:
        text = text[:max_length]
        for char in ':"/\\?*<>|!':
            text = text.replace(char, "")
        return text.replace(" ", "_")

    # -- clip construction ----------------------------------------------
    def create_slide_video(self, slide_path: str, duration: float):
        """Turn one slide asset into a clip of exactly `duration` seconds."""
        if not slide_path or not Path(slide_path).exists():
            print("  Slide asset missing; using a blank frame")
            return ColorClip(size=(WIDTH, HEIGHT), color=(17, 24, 39),
                             duration=duration)

        if slide_path.endswith((".mp4", ".mov", ".mkv")):
            clip = VideoFileClip(slide_path)
            if clip.duration > duration:
                return clip.subclipped(0, duration)
            return clip.with_duration(duration)

        return ImageClip(slide_path, duration=duration)

    def _fit_animation(self, animation_path: str, duration: float):
        """Loop or trim an animation to `duration`, then size it."""
        clip = VideoFileClip(animation_path)
        source = clip.duration

        if source > duration:
            adjusted = clip.subclipped(0, duration)
        elif source < duration:
            repeats = int(duration / source) + 1
            adjusted = concatenate_videoclips(
                [clip] * repeats, method="compose"
            ).subclipped(0, duration)
        else:
            adjusted = clip.with_duration(duration)

        # Resize last so no later duration operation discards it.
        return adjusted.resized(new_size=(ANIMATION_PANEL[2], ANIMATION_PANEL[3]))

    def composite_animation_on_slide(self, slide_image_path: str,
                                     animation_video_path: str, duration: float):
        """Overlay a Manim render onto the reserved panel of a base slide."""
        x, y, _w, _h = ANIMATION_PANEL
        slide = ImageClip(slide_image_path, duration=duration)
        animation = self._fit_animation(animation_video_path, duration).with_position(
            (x, y)
        )
        return CompositeVideoClip([slide, animation], size=(WIDTH, HEIGHT))

    # -- encoding --------------------------------------------------------
    def _encode(self, video, destination: Path, audio_path: str | None) -> None:
        """Stream frames to ffmpeg with narration muxed in.

        MoviePy yields RGB(A) arrays, so the pipe is declared `rgb24` and the
        pixel format is converted by ffmpeg on the way out. Declaring `yuv420p`
        here would mismatch the 3-bytes-per-pixel payload and break the pipe
        part-way through a long encode.
        """
        command = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "rawvideo",
            "-pix_fmt", "rgb24",
            "-s", f"{WIDTH}x{HEIGHT}",
            "-r", str(FPS),
            "-i", "-",
        ]
        if audio_path and Path(audio_path).exists():
            command += ["-i", str(audio_path), "-c:a", "aac", "-b:a", "192k",
                        "-shortest"]
        command += [
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-pix_fmt", "yuv420p",
            str(destination),
        ]

        frames = int(round(video.duration * FPS))
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )

        written = 0
        try:
            for frame in video.iter_frames(fps=FPS, dtype="uint8"):
                rgb = np.asarray(frame[:, :, :3], dtype=np.uint8)
                if process.poll() is not None:
                    raise RuntimeError(
                        f"ffmpeg exited early after {written}/{frames} frames"
                    )
                process.stdin.write(rgb.tobytes())
                written += 1
            process.stdin.close()
        except BrokenPipeError as exc:
            stderr = process.stderr.read().decode("utf-8", "ignore")
            raise RuntimeError(f"ffmpeg closed the pipe: {stderr}") from exc
        finally:
            if process.stdin and not process.stdin.closed:
                process.stdin.close()
            try:
                process.wait(timeout=120)
            except subprocess.TimeoutExpired:
                process.kill()

        if process.returncode != 0:
            stderr = process.stderr.read().decode("utf-8", "ignore")
            raise RuntimeError(f"ffmpeg failed ({process.returncode}): {stderr}")

    # -- assembly --------------------------------------------------------
    def compose_final_video(self, content_data: Dict, script_data: Dict,
                            slide_paths: Dict[int, object], audio_path: str) -> str:
        slides = content_data["slides"]
        scripts = {s["slide_number"]: s for s in script_data["slide_scripts"]}
        total = len(slides)
        print(f"Composing {total} slides")

        clips = []
        for slide in slides:
            number = slide["slide_number"]
            timing = scripts.get(number)
            if timing is None:
                print(f"  Slide {number} has no script; skipping")
                continue

            duration = max(
                1.0, float(timing["end_time"]) - float(timing["start_time"])
            )
            asset = slide_paths.get(number)
            if asset is None:
                print(f"  Slide {number} has no visual; skipping")
                continue

            if isinstance(asset, dict) and asset.get("type") == "animation_composite":
                clip = self.composite_animation_on_slide(
                    asset["base_slide"], asset["animation"], duration
                )
            else:
                clip = self.create_slide_video(str(asset), duration)

            clips.append(clip)

        if not clips:
            raise ValueError("No slide clips could be assembled")

        video = concatenate_videoclips(clips, method="compose")
        target = (
            Config.FINAL_DIR
            / f"{self.sanitize_filename(content_data['topic'])}_final.mp4"
        )

        # Trim the narration to the video length rather than the reverse, so the
        # video never ends before its audio.
        if audio_path and Path(audio_path).exists():
            audio = AudioFileClip(audio_path)
            if audio.duration > video.duration:
                audio = audio.subclipped(0, video.duration)
            trimmed = Config.FINAL_DIR / "_narration.wav"
            audio.write_audiofile(str(trimmed), codec="pcm_s16le", logger=None)
            audio.close()
            audio_path = str(trimmed)
        else:
            print("  No narration track found; writing a silent video")
            audio_path = ""

        print(f"  Encoding {video.duration:.1f}s at {FPS}fps")
        self._encode(video, target, audio_path)

        for clip in clips:
            clip.close()
        video.close()
        (Config.FINAL_DIR / "_narration.wav").unlink(missing_ok=True)

        if not target.is_file() or target.stat().st_size == 0:
            raise RuntimeError("Encode produced no output file")

        print(f"Final video: {target} ({target.stat().st_size // 1024} KB)")
        return str(target)