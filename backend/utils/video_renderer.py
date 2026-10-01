"""Manim scene rendering.

The previous version shelled out to a `manim` executable on PATH and then
searched for the output in a guessed `media/videos/...` directory. Both are
fragile: inside a virtualenv the binary only exists as `python -m manim`, and
the output directory depends on `--media_dir` and the resolution folder that
Manim picks for the chosen quality.

This version runs the interpreter that is actually executing the app and reads
the output path back from Manim's own JSON log, so nothing is guessed.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from config import Config

RENDER_TIMEOUT = 420  # seconds


class VideoRenderer:
    """Render a Manim scene file to an MP4."""

    def __init__(self):
        self.quality = Config.MANIM_QUALITY
        self.fps = Config.MANIM_FPS

    def render_manim_animation(
        self, code_path: str, output_name: str | None = None
    ) -> str:
        code_path = Path(code_path).resolve()
        if not code_path.is_file():
            raise FileNotFoundError(f"Manim scene not found: {code_path}")

        output_name = output_name or code_path.stem
        destination = Config.VIDEOS_DIR / f"{output_name}.mp4"
        destination.parent.mkdir(parents=True, exist_ok=True)

        # Render inside a scratch directory so Manim's `media/` tree never
        # accumulates next to the generated source files.
        with tempfile.TemporaryDirectory(prefix="manim_render_") as scratch:
            scene_copy = Path(scratch) / "scene.py"
            scene_copy.write_text(code_path.read_text(encoding="utf-8"),
                                  encoding="utf-8")
            log_dir = Path(scratch) / "logs"

            command = [
                sys.executable, "-m", "manim",
                "render",
                str(scene_copy),
                "SlideAnimation",
                f"-q{self.quality}",
                f"--fps={self.fps}",
                "--format=mp4",
                "--media_dir", str(Path(scratch) / "media"),
                "--log_dir", str(log_dir),
                "--log_to_file",
                "--verbosity", "info",
            ]

            try:
                result = subprocess.run(
                    command,
                    cwd=scratch,
                    capture_output=True,
                    text=True,
                    timeout=RENDER_TIMEOUT,
                )
            except subprocess.TimeoutExpired:
                raise RuntimeError(
                    f"Manim render exceeded {RENDER_TIMEOUT}s and was stopped"
                ) from None

            if result.returncode != 0:
                tail = "\n".join((result.stderr or result.stdout).splitlines()[-12:])
                raise RuntimeError(f"Manim render failed:\n{tail}")

            produced = self._locate_output(log_dir, Path(scratch) / "media")
            if produced is None:
                raise FileNotFoundError(
                    "Manim reported success but no video file was found"
                )

            destination.write_bytes(produced.read_bytes())

        print(f"Rendered animation -> {destination}")
        return str(destination)

    @staticmethod
    def _locate_output(log_dir: Path, media_dir: Path) -> Path | None:
        """Resolve the rendered file, preferring Manim's own log entry."""
        if log_dir.is_dir():
            for line in (
                entry.read_text(encoding="utf-8", errors="ignore")
                for entry in sorted(log_dir.rglob("*.log"))
            ):
                for candidate in line.splitlines():
                    candidate = candidate.strip()
                    if not candidate.endswith((".mp4", ".mov")):
                        continue
                    try:
                        payload = json.loads(candidate)
                    except json.JSONDecodeError:
                        continue
                    for value in payload.values():
                        path = Path(str(value))
                        if path.suffix == ".mp4" and path.is_file():
                            return path

        # Fall back to a search of the media tree, largest file first so a
        # stray thumbnail can never be mistaken for the render.
        return next(
            iter(sorted(media_dir.rglob("*.mp4"), key=lambda p: -p.stat().st_size)),
            None,
        )