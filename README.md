# AI Video Presentation Generator

Turns a topic into a narrated, illustrated video deck: outline, narration,
slides, animations and a final MP4.

---

## Quick start

```bash
git clone https://github.com/Kamal-Nayan-Kumar/AI-Video-Gen.git
cd AI-Video-Gen
./setup.sh
```

`setup.sh` creates the Python environment, installs both halves, and checks
that ffmpeg and a usable sans-serif font are present. Then run the two
servers in separate terminals:

```bash
# Terminal 1 — API
cd backend && .venv/bin/python app.py
```

```bash
# Terminal 2 — UI
cd frontend && npm run dev
```

Open **http://localhost:5173**.

No API keys are needed. With an empty `backend/.env` the app runs in **demo
mode**, where content, narration and imagery are produced locally, so the
whole pipeline can be demonstrated offline. Drop a key into `.env` (see
`backend/.env.example`) and that stage switches to the real provider
automatically — nothing else changes.

### Generating takes a minute

Encoding a 1920×1080 deck is CPU-bound. A five-slide deck typically takes
40–90 seconds depending on the machine. The progress rail updates live
throughout.

---

## Requirements

| Dependency | Why | Install (Arch / Debian) |
|---|---|---|
| Python 3.12 | Manim and MoviePy wheels | `uv` or `python3.12` |
| Node 18+ | Vite frontend | `npm` |
| ffmpeg | muxing audio, probing durations | `sudo pacman -S ffmpeg` |
| cairo + pango | Manim text rendering | `sudo pacman -S cairo pango` |
| A sans-serif font | slide text | `sudo pacman -S liberation-fonts` |

LaTeX is **not** required: the scenes avoid `MathTex`/`Tex` and use Pango for
text. If Gemini generates a scene that needs LaTeX, it is rejected and a local
template is used instead.

---

## How it works

```
topic
  │
  ├─ content_generator  →  outline (title, body, per-slide visual decision)
  ├─ script_generator   →  narration, one passage per slide
  ├─ voice_generator    →  one audio file per slide; real durations measured
  │                        script timestamps are rewritten from the audio
  ├─ slide_renderer     →  1920×1080 slide images (text / text+image / panel)
  ├─ video_renderer     →  Manim scenes rendered to MP4 (optional)
  └─ video_composer     →  slides + narration → final MP4
```

`POST /api/generate` returns a job id immediately. Progress streams from
`GET /api/progress/{job_id}` as server-sent events, and the finished payload
is fetched from `GET /api/job/{job_id}`.

Work runs on a worker thread rather than the event loop, so the progress
stream stays responsive for the duration of the job.

---

## API

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | status plus which providers are live |
| `POST` | `/api/generate` | queue a job, returns `{job_id}` |
| `GET` | `/api/progress/{job_id}` | SSE progress stream |
| `GET` | `/api/job/{job_id}` | finished payload |
| `GET` | `/api/video/{filename}` | stream the MP4 (supports range requests) |

```bash
curl -X POST localhost:8000/api/generate \
  -H 'Content-Type: application/json' \
  -d '{"topic":"How a refrigerator works","num_slides":5,"language":"english","tone":"formal"}'
```

---

## Modes

`GET /health` reports which stages use a real provider:

```json
{
  "status": "ok",
  "capabilities": {
    "mode": "live", "content": true, "provider": "groq",
    "voice": true, "images": true
  }
}
```

| Stage | Live provider | Fallback |
|---|---|---|
| Outline & script | Groq (or Gemini) | deterministic local outline |
| Narration | Sarvam AI | Google Translate TTS |
| Imagery | Unsplash | generated abstract plate |
| Animation | Groq scene code (or Gemini) | three local Manim templates |

Set `DEMO_MODE=1` to force demo behaviour even when keys are present.

**Provider notes**

- `GROQ_API_KEY` is preferred over `GEMINI_API_KEY`. Both work; the outline,
  script and animation generators call whichever is set through one interface
  (`generators/llm_client.py`).
- Sarvam retired `bulbul:v2` and its speakers. Use `bulbul:v3` with a speaker
  from `Config.SARVAM_SPEAKER_MAP` (`simran` for English, `ritu` for Hindi).
- Unsplash returns a real photograph, not a diagram. The script generator is
  told this explicitly so it does not narrate a photo as "the diagram shows".

---

## Layout

```
backend/
  app.py                  FastAPI app, job registry, SSE
  config.py               paths, keys, font resolution, mode detection
  generators/
    llm_client.py         one JSON/code interface over Groq and Gemini
    content_generator.py  outline
    script_generator.py   narration
    voice_generator.py    Sarvam / TTS fallback
    image_fetcher.py      Unsplash / generated plate
    manim_generator.py    animation scene code
  utils/                  slide renderer, video renderer, composer
  outputs/                generated at runtime (gitignored)
frontend/
  src/App.jsx             layout and view switching
  src/components/         Composer, ProgressPanel, Player, ModeBadge
  src/hooks/              useJobProgress (SSE), useCapabilities
  src/utils/api.js        typed backend client
```

The Vite dev server proxies `/api` and `/health` to port 8000 so the browser
sees a single origin — necessary for `EventSource`, which cannot set headers.