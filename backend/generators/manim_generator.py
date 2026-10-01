"""Manim animation code generation.

Uses Gemini to write a scene when a key is available, otherwise composes a
safe scene locally from a small set of templates. The templates deliberately
stick to core Mobjects and avoid `MathTex`/`Tex`, which would require a LaTeX
installation that is not present on most machines.
"""

import re
from typing import Dict

from config import Config
from generators.llm_client import LLMClient

class ManimGenerator:
    """Produce a renderable Manim scene for a slide."""

    def __init__(self):
        self.llm = LLMClient()

    @staticmethod
    def sanitize_filename(text: str, max_length: int = 20) -> str:
        text = text[:max_length]
        for char in ' :/"\\?!*<>|':
            text = text.replace(char, "_" if char in " /\\" else "")
        return text.strip("_") or "scene"

    @staticmethod
    def _quote(text: str) -> str:
        """Escape a string for safe embedding in generated Python source."""
        return str(text).replace("\\", "\\\\").replace('"', '\\"')

    def _build_prompt(self, slide: Dict, duration: float) -> str:
        guidelines = LLMClient.guide_text()

        return f"""Generate Manim Community v0.18 animation code.

Title: {slide['title']}
Requested animation: {slide.get('animation_description', '')}
Duration: {duration:.1f}s

RULES:
{guidelines}

Constraints:
- Only core Mobjects. Do NOT use MathTex or Tex (no LaTeX available).
- Keep total runtime close to {duration:.1f}s.
- Class name must be `SlideAnimation`.

OUTPUT: Python code only, no markdown fence, no commentary."""

    # -- local templates -------------------------------------------------
    def _template_scene(self, title: str, duration: float, variant: int) -> str:
        """Compose a scene without a model.

        `duration` is clamped so the scene cannot run away: each template has a
        fixed shape plus a wait proportional to the requested length.
        """
        title = self._quote(title)
        hold = max(0.5, round(duration - 3.0, 2))
        # Without an explicit family, Pango falls back to a serif face.
        font = self._font_kwarg()
        variants = [
            # Expanding rings.
            f"""
class SlideAnimation(Scene):
    def construct(self):
        title = Text("{title}", font_size=44, color=WHITE)
        title.to_edge(UP, buff=0.7)
        self.play(FadeIn(title, shift=UP * 0.3), run_time=0.8)

        center = UP * 0.6
        rings = VGroup()
        for i in range(4):
            ring = Circle(radius=0.55 + i * 0.42, color=BLUE_D, stroke_opacity=0.85)
            ring.move_to(center)
            rings.add(ring)

        self.play(LaggedStart(*[Create(r) for r in rings], lag_ratio=0.18),
                  run_time=1.6)
        self.wait({hold})
        self.play(FadeOut(rings), FadeOut(title), run_time=0.6)
""",
            # Bars that grow to represent magnitude.
            f"""
class SlideAnimation(Scene):
    def construct(self):
        title = Text("{title}", font_size=44, color=WHITE)
        title.to_edge(UP, buff=0.7)
        self.play(FadeIn(title), run_time=0.7)

        axes = Axes(
            x_range=[0, 5, 1], y_range=[0, 4, 1],
            x_length=6.4, y_length=3.4,
            axis_config={{"color": GREY_B, "stroke_opacity": 0.5,
                         "include_tip": False}},
        ).shift(DOWN * 0.5)

        bars = VGroup()
        heights = [1.1, 2.3, 1.6, 3.1, 2.0]
        for i, h in enumerate(heights):
            bar = Rectangle(
                width=0.55, height=h,
                fill_color=BLUE_E, fill_opacity=0.9, stroke_width=0,
            ).move_to(axes.c2p(i + 0.6, h / 2), aligned_edge=ORIGIN)
            bars.add(bar)

        self.play(Create(axes), run_time=0.9)
        self.play(LaggedStart(*[GrowFromEdge(b, DOWN) for b in bars],
                              lag_ratio=0.16), run_time=1.6)
        self.wait({hold})
        self.play(FadeOut(VGroup(axes, bars)), FadeOut(title), run_time=0.6)
""",
            # Nodes on a graph connected in sequence.
            f"""
class SlideAnimation(Scene):
    def construct(self):
        title = Text("{title}", font_size=44, color=WHITE)
        title.to_edge(UP, buff=0.7)
        self.play(FadeIn(title, shift=DOWN * 0.25), run_time=0.7)

        points = [
            LEFT * 4.6 + UP * 0.6,
            LEFT * 1.5 + UP * 1.9,
            RIGHT * 1.5 + UP * 0.2,
            RIGHT * 4.6 + DOWN * 1.0,
        ]
        nodes = VGroup(*[Dot(p, radius=0.16, color=TEAL) for p in points])
        edges = VGroup(*[Line(points[i], points[i + 1], color=GREY_B)
                         for i in range(len(points) - 1)])

        self.play(LaggedStart(*[GrowFromCenter(n) for n in nodes],
                              lag_ratio=0.2), run_time=1.3)
        self.play(LaggedStart(*[Create(e) for e in edges], lag_ratio=0.25),
                  run_time=1.4)
        pulse = SurroundingRectangle(nodes[1], color=YELLOW, buff=0.45)
        self.play(Create(pulse), run_time=0.6)
        self.wait({hold})
        self.play(FadeOut(VGroup(nodes, edges, pulse)), FadeOut(title),
                  run_time=0.6)
""",
        ]
        body = variants[variant % len(variants)].strip("\n")
        # Text renders via Pango, so the font is passed by family name.
        body = body.replace("font_size=44", f"font_size=44{font}")
        return "from manim import *\n\n" + body

    @staticmethod
    def _font_kwarg() -> str:
        """Font family keyword for generated Text calls, or empty."""
        family = Config.FONT_FAMILY
        return f', font="{family}"' if family else ""

    def generate_animation_code(self, slide_data: Dict, duration: float) -> str:
        title = slide_data.get("title", "Animation")

        if not self.llm.available:
            variant = int(hashlib_seed(title))
            return self._template_scene(title, duration, variant)

        try:
            code = self.llm.generate_code(self._build_prompt(slide_data, duration))
            code = code.strip()
            fence = re.search(r"```(?:python)?\s*(.*?)```", code, re.DOTALL)
            if fence:
                code = fence.group(1).strip()

            for marker in ("from manim import", "class SlideAnimation",
                           "def construct(self):"):
                if marker not in code:
                    raise ValueError(f"generated scene is missing: {marker}")

            # MathTex would fail at render time without a LaTeX install.
            if "MathTex" in code or re.search(r"\bTex\(", code):
                raise ValueError("generated scene requires LaTeX")

            return code
        except Exception as exc:  # noqa: BLE001
            print(f"  Animation code generation failed ({exc}); using template")
            return self._template_scene(title, duration, int(hashlib_seed(title)))

    def save_animation_code(
        self, code: str, slide_number: int, topic: str
    ) -> str:
        path = (
            Config.MANIM_CODE_DIR
            / f"{self.sanitize_filename(topic)}_slide_{slide_number}.py"
        )
        path.write_text(code, encoding="utf-8")
        return str(path)


def hashlib_seed(text: str) -> int:
    """Small stable integer for template selection."""
    return int.from_bytes(text.encode("utf-8")[:4].ljust(4, b"\0"), "big") % 3