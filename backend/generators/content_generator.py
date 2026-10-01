"""Slide content generation.

In `live` mode the outline comes from Gemini. In `demo` mode no model is
available, so we derive a structured outline locally: a title slide, an
overview, several concept slides built from the topic and its own key terms,
and a closing summary. The shape of the data is identical either way, so the
rest of the pipeline is unaware of which one ran.
"""

import json
import re
from typing import Dict

from config import Config
from generators.llm_client import LLMClient


def _keywords(topic: str) -> list[str]:
    """Split a topic into candidate sub-topics.

    "Photosynthesis in plants: how leaves make food" -> ["photosynthesis",
    "how leaves make food"]. Commas, colons and conjunctions all act as
    separators, which gives us a natural slide structure for free.
    """
    cleaned = re.sub(r"\s+", " ", topic).strip()
    parts = re.split(r"[,:/]| - |\band\b|\bof\b|\bin\b", cleaned, flags=re.IGNORECASE)
    parts = [p.strip(" ?.!") for p in parts if len(p.strip()) > 2]
    return parts or [cleaned or "the topic"]


class ContentGenerator:
    """Produce the structured slide outline for a topic."""

    def __init__(self):
        self.llm = LLMClient()

    # -- prompt ---------------------------------------------------------
    @staticmethod
    def _build_prompt(topic: str, num_slides: int) -> str:
        return f"""Generate educational presentation content about: "{topic}"

Create {num_slides} slides.

RULES:
- Slide 1 must be an introductory title slide.
- Exactly one of needs_image / needs_animation may be true per slide.
- Keep 70-80% of slides text-only (both flags false).
- Use images for concrete subjects: people, places, objects.
- Use animations sparingly, only for motion or geometric concepts.
- content_text must be 2-4 concise sentences.
- duration is an estimated speaking length in seconds (5-10).

Return JSON:
{{
  "topic": "...",
  "total_slides": {num_slides},
  "slides": [
    {{
      "slide_number": 1,
      "title": "...",
      "content_text": "...",
      "needs_image": false,
      "image_keyword": "",
      "needs_animation": false,
      "animation_description": "",
      "duration": 6.0
    }}
  ]
}}"""

    # -- demo fallback ---------------------------------------------------
    @staticmethod
    def _demo_content(topic: str, num_slides: int) -> Dict:
        """Build a deterministic, well-formed outline without a model."""
        parts = _keywords(topic)
        subject = parts[0]
        slides = []

        def add(title: str, body: str, **kw):
            slides.append(
                {
                    "slide_number": len(slides) + 1,
                    "title": title,
                    "content_text": body,
                    "needs_image": kw.get("needs_image", False),
                    "image_keyword": kw.get("image_keyword", ""),
                    "needs_animation": kw.get("needs_animation", False),
                    "animation_description": kw.get("animation_description", ""),
                    "duration": kw.get("duration", 7.0),
                }
            )

        add(
            subject[:1].upper() + subject[1:],
            f"A short introduction to {topic}. This deck walks through the key "
            f"ideas, why they matter, and how they fit together.",
            needs_image=True,
            image_keyword=subject,
            duration=6.0,
        )

        # Body slides drawn from the topic's own sub-phrases where possible,
        # padded with generic framing so any topic yields a full deck.
        focus = parts[1:] or [f"the core idea behind {subject}"]
        fillers = [
            ("How it works", "Breaking the process into its distinct stages and "
             "looking at what happens at each one."),
            ("Why it matters", "The practical significance, and the situations "
             "where understanding this changes the outcome."),
            ("Common misconceptions", "A few points that are often stated "
             "incorrectly, and what the evidence actually supports."),
            ("Key terms", "The vocabulary you need to follow the rest of the "
             "discussion without further explanation."),
            ("In practice", "A worked example that grounds the idea in "
             "something concrete and familiar."),
            ("Limitations", "Where this idea stops applying, and what is still "
             "open to debate."),
            ("Looking ahead", "How this connects to the surrounding field and "
             "where research is heading."),
        ]

        for i in range(num_slides - 2):
            if i < len(focus):
                piece = focus[i]
                add(
                    piece[:1].upper() + piece[1:],
                    f"A closer look at {piece}. This section covers what it "
                    f"involves, and the reasoning behind the common approach.",
                    duration=7.0,
                )
            else:
                title, body = fillers[(i - len(focus)) % len(fillers)]
                add(title, f"{body} For {topic}, this is where the detail "
                    "matters most.", duration=6.0)

        add(
            "Summary",
            f"The key points of {topic}, gathered into one place. Each idea "
            f"covered maps back to a specific stage or principle discussed above.",
            duration=6.0,
        )

        return {"topic": topic, "total_slides": len(slides), "slides": slides}

    # -- normalisation ---------------------------------------------------
    @staticmethod
    def _normalise(data: Dict, topic: str) -> Dict:
        """Repair a model response so downstream code can rely on its shape."""
        if not isinstance(data, dict) or not isinstance(data.get("slides"), list):
            raise ValueError("Model response did not contain a slides list")
        if not data["slides"]:
            raise ValueError("Model returned an empty slide list")

        data.setdefault("topic", topic)
        data["total_slides"] = len(data["slides"])

        for i, slide in enumerate(data["slides"], start=1):
            slide["slide_number"] = i
            slide.setdefault("title", f"Slide {i}")
            slide.setdefault("content_text", "")
            slide.setdefault("needs_image", False)
            slide.setdefault("image_keyword", "")
            slide.setdefault("needs_animation", False)
            slide.setdefault("animation_description", "")
            try:
                slide["duration"] = float(slide.get("duration") or 6.0)
            except (TypeError, ValueError):
                slide["duration"] = 6.0

            # A slide is either animated or illustrated, never both. The
            # animation wins, because it was the more deliberate request.
            if slide["needs_animation"] and slide["needs_image"]:
                slide["needs_image"] = False
                slide["image_keyword"] = ""
            if slide["needs_image"] and not slide["image_keyword"]:
                slide["needs_image"] = False
            if slide["needs_animation"] and not slide["animation_description"]:
                slide["needs_animation"] = False

        return data

    # -- entry point -----------------------------------------------------
    def generate_content(self, topic: str, num_slides: int = 5) -> Dict:
        num_slides = max(3, min(int(num_slides), 12))

        if not self.llm.available:
            data = self._demo_content(topic, num_slides)
        else:
            data = self._normalise(
                self.llm.generate_json(self._build_prompt(topic, num_slides)), topic
            )

        # Persist using the same naming scheme the API layer expects.
        safe = topic[:30].replace(" ", "_").replace(":", "").replace("/", "_")
        with open(Config.SLIDES_DIR / f"{safe}_content.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        slides = data["slides"]
        print(
            "Content breakdown: "
            f"text={sum(1 for s in slides if not s['needs_image'] and not s['needs_animation'])} "
            f"image={sum(1 for s in slides if s['needs_image'])} "
            f"animation={sum(1 for s in slides if s['needs_animation'])}"
        )
        return data