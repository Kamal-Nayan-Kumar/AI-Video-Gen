#!/usr/bin/env bash
# One-shot local setup. Creates the Python environment, installs the frontend
# packages and verifies that the two system dependencies (ffmpeg, and a
# sans-serif font for PIL) are actually available.
set -euo pipefail

cd "$(dirname "$0")"

info() { printf '\033[36m==>\033[0m %s\n' "$1"; }
warn() { printf '\033[33m warn\033[0m %s\n' "$1"; }
fail() { printf '\033[31merror\033[0m %s\n' "$1"; exit 1; }

# --- system dependencies -----------------------------------------------------
info "Checking system dependencies"
command -v ffmpeg >/dev/null || fail "ffmpeg not found. Install it first (e.g. 'sudo pacman -S ffmpeg' or 'sudo apt install ffmpeg')."
info "ffmpeg: $(ffmpeg -version | head -1 | cut -d' ' -f1-3)"

# Manim renders text through Pango, which needs at least one real font.
if fc-list >/dev/null 2>&1 && [ -n "$(fc-list 2>/dev/null | head -1)" ]; then
  info "Fonts: $(fc-list | wc -l) available"
else
  warn "No system fonts found. Slides will fall back to a bitmap font."
fi

# --- backend -----------------------------------------------------------------
info "Creating the Python environment"
if [ ! -d backend/.venv ]; then
  # 3.12 is the newest release Manim and MoviePy both build against cleanly.
  if command -v uv >/dev/null; then
    uv venv --python 3.12 backend/.venv
  else
    python3.12 -m venv backend/.venv 2>/dev/null || python3 -m venv backend/.venv
  fi
fi

info "Installing backend dependencies"
if command -v uv >/dev/null; then
  uv pip install --python backend/.venv/bin/python -r backend/requirements.txt
else
  backend/.venv/bin/python -m pip install --upgrade pip -q
  backend/.venv/bin/python -m pip install -r backend/requirements.txt
fi

# Manim ships an ffmpeg binary it prefers; allow it to use the system one too.
if command -v uv >/dev/null; then
  uv pip install --python backend/.venv/bin/python imageio-ffmpeg -q || true
fi

# --- frontend ----------------------------------------------------------------
info "Installing frontend dependencies"
(cd frontend && npm install)

cat <<'EOF'

Setup complete.

  Terminal 1:  cd backend && .venv/bin/python app.py
  Terminal 2:  cd frontend && npm run dev

Then open http://localhost:5173
EOF