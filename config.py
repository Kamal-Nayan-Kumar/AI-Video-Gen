import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Keys
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    
    # Paths
    BASE_DIR = Path(__file__).parent
    OUTPUT_DIR = BASE_DIR / "outputs"
    SCRIPTS_DIR = OUTPUT_DIR / "scripts"
    MANIM_CODE_DIR = OUTPUT_DIR / "manim_code"
    VIDEOS_DIR = OUTPUT_DIR / "videos"
    AUDIO_DIR = OUTPUT_DIR / "audio"
    FINAL_DIR = OUTPUT_DIR / "final"
    
    # Create directories
    for dir_path in [SCRIPTS_DIR, MANIM_CODE_DIR, VIDEOS_DIR, AUDIO_DIR, FINAL_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # Models
    GEMINI_MODEL = "gemini-2.5-flash"
    
    # Manim settings
    MANIM_QUALITY = "m"  # l=low, m=medium, h=high
    MANIM_FPS = 30
    
    # Language voice mapping for ElevenLabs
    VOICE_MAP = {
        "english": "21m00Tcm4TlvDq8ikWAM",  # Rachel voice
        "hindi": "21m00Tcm4TlvDq8ikWAM",
        "kannada": "21m00Tcm4TlvDq8ikWAM",
        "telugu": "21m00Tcm4TlvDq8ikWAM"
    }
