"""Central configuration.

Two modes are supported:

  live  — every provider has a real API key in backend/.env
  demo  — no keys required; content, narration and imagery are produced
          locally so the full pipeline can be demonstrated offline.

`Config.mode` is derived from which keys are present, so adding a key to .env
flips that single stage to the live provider without touching any call site.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")


def _font_candidates(*names: str) -> list[str]:
    """Resolve font filenames across common system font directories.

    The original code hardcoded Windows and macOS paths and only checked for a
    Debian-style `/usr/share/fonts/truetype` layout, which does not exist on
    Arch-based systems. Rather than enumerate every OS path we scan the usual
    font roots for the first filename that is present.
    """
    roots = [
        Path("/usr/share/fonts"),
        Path("/usr/local/share/fonts"),
        Path.home() / ".fonts",
        Path("/Library/Fonts"),
        Path("C:/Windows/Fonts"),
    ]
    found = []
    for name in names:
        for root in roots:
            if not root.exists():
                continue
            # Direct hit (flat font dir, e.g. macOS or Windows).
            direct = root / name
            if direct.is_file():
                found.append(str(direct))
                break
            # Recursive hit (Debian/Arch nested layout).
            try:
                match = next(root.rglob(name), None)
            except (OSError, PermissionError):
                match = None
            if match is not None:
                found.append(str(match))
                break
    return found


# Manim renders text through Pango, which matches on a family name rather
# than a file path, so map the resolved font files to their family names.
_FAMILY_BY_FILE = {
    "Inter-Regular.ttf": "Inter",
    "Inter-Bold.ttf": "Inter",
    "DejaVuSans.ttf": "DejaVu Sans",
    "DejaVuSans-Bold.ttf": "DejaVu Sans",
    "LiberationSans-Regular.ttf": "Liberation Sans",
    "LiberationSans-Bold.ttf": "Liberation Sans",
    "Arial.ttf": "Arial",
    "Arial Bold.ttf": "Arial",
    "arialbd.ttf": "Arial",
    "Helvetica.ttc": "Helvetica",
}


def _font_family(*font_files) -> str | None:
    """Family name for the first recognised font file, if any."""
    for path in font_files:
        if not path:
            continue
        for filename, family in _FAMILY_BY_FILE.items():
            if path.endswith(filename):
                return family
    return None


class Config:
    # --- API keys (optional; absence enables demo mode) -------------------
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
    SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "").strip()
    UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY", "").strip()

    # --- Paths -----------------------------------------------------------
    BASE_DIR = BASE_DIR
    OUTPUT_DIR = BASE_DIR / "outputs"
    SCRIPTS_DIR = OUTPUT_DIR / "scripts"
    SLIDES_DIR = OUTPUT_DIR / "slides"
    MANIM_CODE_DIR = OUTPUT_DIR / "manim_code"
    VIDEOS_DIR = OUTPUT_DIR / "videos"
    AUDIO_DIR = OUTPUT_DIR / "audio"
    FINAL_DIR = OUTPUT_DIR / "final"
    IMAGES_DIR = OUTPUT_DIR / "images"

    for _dir in (
        SCRIPTS_DIR,
        SLIDES_DIR,
        MANIM_CODE_DIR,
        VIDEOS_DIR,
        AUDIO_DIR,
        FINAL_DIR,
        IMAGES_DIR,
    ):
        _dir.mkdir(parents=True, exist_ok=True)

    # --- Models ----------------------------------------------------------
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # --- Manim -----------------------------------------------------------
    MANIM_QUALITY = os.getenv("MANIM_QUALITY", "m")  # l=low, m=medium, h=high
    MANIM_FPS = int(os.getenv("MANIM_FPS", "30"))

    # --- Sarvam AI TTS ---------------------------------------------------
    SARVAM_TTS_URL = os.getenv(
        "SARVAM_TTS_URL", "https://api.sarvam.ai/text-to-speech"
    )
    # bulbul:v2 and its speakers were retired; v3 uses a different set.
    SARVAM_MODEL = os.getenv("SARVAM_MODEL", "bulbul:v3")

    SARVAM_SPEAKER_MAP = {
        "english": "simran",
        "hindi": "ritu",
        "kannada": "kavya",
        "telugu": "vijay",
        "tamil": "kavitha",
        "bengali": "ishita",
        "gujarati": "dhruva",
        "malayalam": "manak",
        "marathi": "soham",
        "odia": "subhashree",
        "punjabi": "rupali",
    }

    # --- Fonts -----------------------------------------------------------
    # Liberation Sans is metric-compatible with Arial and present on most
    # Linux systems, so it is a safe portable fallback.
    _sans_regular = _font_candidates(
        "Inter-Regular.ttf", "DejaVuSans.ttf", "LiberationSans-Regular.ttf"
    )
    _sans_bold = _font_candidates(
        "Inter-Bold.ttf",
        "DejaVuSans-Bold.ttf",
        "LiberationSans-Bold.ttf",
        "Arial Bold.ttf",
        "arialbd.ttf",
    )

    TITLE_FONT = _sans_bold[0] if _sans_bold else None
    CONTENT_FONT = _sans_regular[0] if _sans_regular else None

    # Manim renders text through Pango, which matches on family name rather
    # than a file path, so derive the family from whichever file resolved.
    FONT_FAMILY = _font_family(TITLE_FONT, CONTENT_FONT)

    # --- Server ----------------------------------------------------------
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))

    # --- Demo mode -------------------------------------------------------
    # Force with DEMO_MODE=1 / DEMO_MODE=0 to override auto-detection.
    _demo_flag = os.getenv("DEMO_MODE", "").strip().lower()
    if _demo_flag in {"1", "true", "yes"}:
        MODE = "demo"
    elif _demo_flag in {"0", "false", "no"}:
        MODE = "live"
    else:
        MODE = "live" if (GROQ_API_KEY or GEMINI_API_KEY) else "demo"

    @classmethod
    def capability(cls) -> dict:
        """Which stages run against a real provider."""
        return {
            "mode": cls.MODE,
            "content": bool(cls.GROQ_API_KEY or cls.GEMINI_API_KEY),
            "provider": "groq" if cls.GROQ_API_KEY else ("gemini" if cls.GEMINI_API_KEY else "local"),
            "voice": bool(cls.SARVAM_API_KEY),
            "images": bool(cls.UNSPLASH_ACCESS_KEY),
        }