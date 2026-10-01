"""Narration audio.

Three tiers, chosen at call time:

1. Sarvam AI   — used when SARVAM_API_KEY is set. Best multilingual quality.
2. Google TTS  — keyless fallback. Real, intelligible speech, which matters
                 because slide durations are derived from the audio length.
3. Silence     — only if the network is unavailable, so the pipeline still
                 produces a correctly-timed video rather than failing.

Every tier emits 22.05 kHz mono PCM WAV so downstream duration measurement is
consistent regardless of source.
"""

import base64
import re
import subprocess
from pathlib import Path
from typing import Dict

import requests

from config import Config

SAMPLE_RATE = 22050

# Google TTS rejects requests beyond roughly 200 characters, so long
# narration is split on sentence boundaries and stitched back together.
CHUNK_LIMIT = 180

GOOGLE_LANGS = {
    "english": "en",
    "hindi": "hi",
    "kannada": "kn",
    "telugu": "te",
    "tamil": "ta",
    "bengali": "bn",
    "gujarati": "gu",
    "malayalam": "ml",
    "marathi": "mr",
    "odia": "or",
    "punjabi": "pa",
    "french": "fr",
    "german": "de",
    "spanish": "es",
    "japanese": "ja",
}

SARVAM_LANG_CODES = {
    "english": "en-IN",
    "hindi": "hi-IN",
    "kannada": "kn-IN",
    "telugu": "te-IN",
    "tamil": "ta-IN",
    "bengali": "bn-IN",
    "gujarati": "gu-IN",
    "malayalam": "ml-IN",
    "marathi": "mr-IN",
    "odia": "or-IN",
    "punjabi": "pa-IN",
}


class VoiceGenerator:
    """Render narration text to an audio file on disk."""

    def __init__(self):
        self.sarvam_key = Config.SARVAM_API_KEY
        self.sarvam_url = Config.SARVAM_TTS_URL
        self.session = requests.Session()

    # -- helpers --------------------------------------------------------
    @staticmethod
    def _safe(topic: str) -> str:
        return topic[:30].replace(" ", "_").replace(":", "").replace("/", "_")

    @staticmethod
    def _split(text: str, limit: int = CHUNK_LIMIT) -> list[str]:
        """Split narration into chunks that respect sentence boundaries."""
        text = text.strip()
        if len(text) <= limit:
            return [text]

        sentences = re.split(r"(?<=[.!?])\s+", text)
        chunks, current = [], ""
        for sentence in sentences:
            if len(sentence) > limit:
                # A single oversized sentence: fall back to word packing.
                if current:
                    chunks.append(current.strip())
                    current = ""
                words = sentence.split()
                buffer = ""
                for word in words:
                    if len(buffer) + len(word) + 1 > limit:
                        chunks.append(buffer.strip())
                        buffer = word
                    else:
                        buffer = f"{buffer} {word}".strip()
                if buffer:
                    current = buffer
                continue

            if len(current) + len(sentence) + 1 > limit:
                chunks.append(current.strip())
                current = sentence
            else:
                current = f"{current} {sentence}".strip()

        if current:
            chunks.append(current.strip())
        return [c for c in chunks if c]

    @staticmethod
    def _to_wav(source: Path, destination: Path) -> str:
        """Normalise any input audio to mono 22.05 kHz PCM WAV via ffmpeg."""
        subprocess.run(
            [
                "ffmpeg", "-y", "-loglevel", "error",
                "-i", str(source),
                "-ac", "1", "-ar", str(SAMPLE_RATE),
                "-c:a", "pcm_s16le",
                str(destination),
            ],
            check=True,
        )
        return str(destination)

    @staticmethod
    def _silence(destination: Path, seconds: float = 4.0) -> str:
        subprocess.run(
            [
                "ffmpeg", "-y", "-loglevel", "error",
                "-f", "lavfi", "-i", f"anullsrc=r={SAMPLE_RATE}:cl=mono",
                "-t", f"{max(1.0, seconds):.2f}",
                "-c:a", "pcm_s16le", str(destination),
            ],
            check=True,
        )
        return str(destination)

    # -- providers ------------------------------------------------------
    def _sarvam(self, text: str, language: str) -> bytes:
        speaker = Config.SARVAM_SPEAKER_MAP.get(language.lower(), "anushka")
        response = self.session.post(
            self.sarvam_url,
            headers={
                "Content-Type": "application/json",
                "API-Subscription-Key": self.sarvam_key,
            },
            json={
                "inputs": [text[:500]],
                "target_language_code": SARVAM_LANG_CODES.get(
                    language.lower(), "en-IN"
                ),
                "speaker": speaker,
                "pitch": 0,
                "pace": 1.0,
                "loudness": 1.5,
                "speech_sample_rate": SAMPLE_RATE,
                "enable_preprocessing": True,
                "model": Config.SARVAM_MODEL,
            },
            timeout=60,
        )
        response.raise_for_status()
        audios = response.json().get("audios") or []
        if not audios:
            raise RuntimeError("Sarvam returned no audio")
        return base64.b64decode(audios[0])

    def _google(self, text: str, language: str) -> bytes:
        lang = GOOGLE_LANGS.get(language.lower(), "en")
        response = self.session.get(
            "https://translate.google.com/translate_tts",
            params={
                "ie": "UTF-8",
                "q": text,
                "tl": lang,
                "client": "tw-ob",
                "ttsspeed": "1",
            },
            timeout=60,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        response.raise_for_status()
        if not response.content:
            raise RuntimeError("Google TTS returned an empty body")
        return response.content

    # -- public API -----------------------------------------------------
    def generate_voice_for_slide(
        self,
        narration_text: str,
        slide_number: int,
        topic: str,
        language: str = "english",
    ) -> str:
        """Render one slide's narration to a WAV file and return its path."""
        text = (narration_text or "").strip()
        if not text:
            text = "This slide continues the discussion."

        destination = Config.AUDIO_DIR / f"{self._safe(topic)}_slide_{slide_number}.wav"
        raw_chunks = []

        if self.sarvam_key:
            try:
                raw_chunks.append(self._sarvam(text, language))
            except Exception as exc:  # noqa: BLE001 - fall through to demo tier
                print(f"  Sarvam failed ({exc}); using fallback TTS")
        else:
            for chunk in self._split(text):
                raw_chunks.append(self._google(chunk, language))

        if not raw_chunks:
            return self._silence(destination, self._approx_seconds(text))

        # Stitch the raw chunks, then normalise to the canonical WAV format.
        suffix = ".mp3" if not self.sarvam_key else ".wav"
        merged = Config.AUDIO_DIR / f".tmp_{destination.stem}{suffix}"
        try:
            with open(merged, "wb") as handle:
                handle.write(b"".join(raw_chunks))
            return self._to_wav(merged, destination)
        except Exception as exc:  # noqa: BLE001
            print(f"  Audio conversion failed ({exc}); using silence")
            return self._silence(destination, self._approx_seconds(text))
        finally:
            merged.unlink(missing_ok=True)

    @staticmethod
    def _approx_seconds(text: str) -> float:
        return max(3.0, len(text.split()) / 2.5)

    @staticmethod
    def duration_of(path: str) -> float:
        """Measure an audio file with ffprobe — no extra decode cost."""
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        return float(result.stdout.strip())

    def combine_slide_audios(self, slide_audio_paths: Dict[int, str], topic: str) -> str:
        """Concatenate the per-slide tracks into one narration file."""
        from moviepy import AudioFileClip, concatenate_audioclips

        clips = [
            AudioFileClip(slide_audio_paths[n])
            for n in sorted(slide_audio_paths)
            if Path(slide_audio_paths[n]).exists()
        ]
        if not clips:
            raise RuntimeError("No audio clips available to combine")

        output_path = Config.AUDIO_DIR / f"{self._safe(topic)}_complete.wav"
        combined = concatenate_audioclips(clips)
        combined.write_audiofile(str(output_path), codec="pcm_s16le", logger=None)
        combined.close()
        for clip in clips:
            clip.close()

        print(f"Combined {len(clips)} clips -> {output_path}")
        return str(output_path)

    def generate_complete_audio(
        self, script_data: Dict, language: str = "english"
    ) -> str:
        """Render every slide's narration and return the combined track."""
        per_slide = {}
        for slide_script in script_data["slide_scripts"]:
            number = slide_script["slide_number"]
            per_slide[number] = self.generate_voice_for_slide(
                slide_script["narration_text"],
                number,
                script_data.get("topic", "narration"),
                language,
            )
        return self.combine_slide_audios(per_slide, script_data.get("topic", "narration"))