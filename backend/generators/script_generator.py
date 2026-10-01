"""Narration script generation.

Mirrors ContentGenerator: Gemini when a key is present, a locally composed
narration when not. Timestamps here are only estimates — `app.py` overwrites
them with the true durations of the rendered audio.
"""

import json
import re
from typing import Dict

from config import Config
from generators.llm_client import LLMClient

TONE_INSTRUCTIONS = {
    "formal": "Use precise, formal academic language.",
    "casual": "Use relaxed, conversational language a friend would use.",
    "storytelling": "Use a narrative style that builds through examples.",
    "enthusiastic": "Use energetic language that conveys genuine interest.",
}


class ScriptGenerator:
    """Write one narration passage per slide."""

    def __init__(self):
        self.llm = LLMClient()

    @staticmethod
    def _build_prompt(content_data: Dict, language: str, tone: str) -> str:
        outline = "\n".join(
            f"Slide {s['slide_number']}: {s['title']}\n"
            f"  Content: {s['content_text']}\n"
            f"  Duration: {s['duration']}s\n"
            f"  Animation: {s.get('animation_description') or 'none'}\n"
            f"  Image: {s.get('image_keyword') or 'none'}"
            for s in content_data["slides"]
        )
        return f"""Write voice-over narration for each slide of this presentation.

Topic: {content_data['topic']}
Language: {language}
Tone: {tone} — {TONE_INSTRUCTIONS.get(tone, TONE_INSTRUCTIONS['formal'])}

{outline}

RULES:
- Write natural spoken prose at roughly 150 words per minute.
- Slides with an animation must describe what the viewer is watching
  ("As you can see...", "Watch as...", "Notice how...").
- Slides with an image: the `Image` line holds the search keyword used to find
  a real photograph. Refer to it as "this image" or "this photo" and describe
  the subject. Never call it a diagram, schematic or chart, and never claim it
  labels or annotates specific parts — you cannot see the image, so do not
  invent what it depicts.
- Text-only slides explain the concept directly, with no visual references.
- Timestamps are estimates; they get replaced by real audio durations.

Return JSON:
{{
  "topic": "...",
  "language": "{language}",
  "total_duration": 0.0,
  "slide_scripts": [
    {{"slide_number": 1, "start_time": 0.0, "end_time": 6.0,
      "narration_text": "..."}}
  ]
}}"""

    @staticmethod
    def _estimate_duration(text: str) -> float:
        """Rough spoken length, used only until real audio is measured."""
        words = len(text.split())
        return max(3.0, round(words / 2.5, 1))  # 150 wpm

    # Narration for a demo deck should stay tight: roughly six seconds a
    # slide. These word budgets keep a five-slide deck near half a minute
    # instead of padding out to a minute and a half.
    OPEN_BUDGET = 16
    BODY_BUDGET = 26
    CLOSE_BUDGET = 22

    @classmethod
    def _trim(cls, text: str, budget: int) -> str:
        """Clamp narration to a word budget on a sentence boundary."""
        words = text.split()
        if len(words) <= budget:
            return text
        kept = " ".join(words[:budget])
        # Prefer ending on a full sentence where one fits inside the budget.
        for stop in range(len(kept), max(0, len(kept) - 14), -1):
            if kept[stop - 1] in ".!?":
                return kept[:stop]
        return kept.rstrip(",;:") + "."

    def _demo_scripts(self, content_data: Dict, language: str, tone: str) -> Dict:
        """Compose narration from the slide text itself."""
        speakers = {
            "english": "Welcome back",
            "hindi": "Namaskar",
            "kannada": "Namaskara",
            "telugu": "Namaskaram",
        }
        opener = speakers.get(language, speakers["english"])

        scripts = []
        cursor = 0.0
        slides = content_data["slides"]
        for i, slide in enumerate(slides):
            if i == 0:
                text = self._trim(
                    f"{opener}. In this video we look at "
                    f"{content_data['topic']}. {slide['content_text']}",
                    self.OPEN_BUDGET,
                )
            elif i == len(slides) - 1:
                text = self._trim(
                    f"{slide['content_text']} Thanks for watching.",
                    self.CLOSE_BUDGET,
                )
            elif slide.get("needs_animation"):
                text = self._trim(
                    f"As you can see on screen, the diagram illustrates this "
                    f"point. {slide['content_text']}",
                    self.BODY_BUDGET,
                )
            elif slide.get("needs_image"):
                text = self._trim(
                    f"Looking at this image, the idea becomes concrete. "
                    f"{slide['content_text']}",
                    self.BODY_BUDGET,
                )
            else:
                text = self._trim(slide["content_text"], self.BODY_BUDGET)

            duration = self._estimate_duration(text)
            scripts.append(
                {
                    "slide_number": slide["slide_number"],
                    "start_time": round(cursor, 2),
                    "end_time": round(cursor + duration, 2),
                    "narration_text": text,
                }
            )
            cursor += duration

        return {
            "topic": content_data["topic"],
            "language": language,
            "total_duration": round(cursor, 2),
            "slide_scripts": scripts,
        }

    def generate_scripts(
        self, content_data: Dict, language: str = "english", tone: str = "formal"
    ) -> Dict:
        if not self.llm.available:
            data = self._demo_scripts(content_data, language, tone)
        else:
            data = self.llm.generate_json(
                self._build_prompt(content_data, language, tone)
            )

        # Guarantee one narration per slide, in order.
        expected = [s["slide_number"] for s in content_data["slides"]]
        by_number = {
            s.get("slide_number"): s for s in data.get("slide_scripts", [])
        }
        ordered = []
        cursor = 0.0
        for number in expected:
            entry = by_number.get(number)
            if entry is None:
                slide = content_data["slides"][expected.index(number)]
                entry = {
                    "slide_number": number,
                    "narration_text": slide.get("content_text", ""),
                }
            text = entry.get("narration_text") or ""
            duration = self._estimate_duration(text)
            ordered.append(
                {
                    "slide_number": number,
                    "start_time": round(cursor, 2),
                    "end_time": round(cursor + duration, 2),
                    "narration_text": text,
                }
            )
            cursor += duration

        data["slide_scripts"] = ordered
        data["total_duration"] = round(cursor, 2)
        data.setdefault("topic", content_data["topic"])
        data.setdefault("language", language)

        safe = data["topic"][:30].replace(" ", "_").replace(":", "").replace("/", "_")
        with open(Config.SCRIPTS_DIR / f"{safe}_script.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return data