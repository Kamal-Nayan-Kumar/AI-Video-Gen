"""Slide image rendering.

Draws 1920x1080 slides with PIL: a text-only layout, a text-plus-image
layout, and a text-plus-animation-panel layout used when a Manim animation is
composited over a slide.

Fonts come from `config.Config`, which resolves them across Windows, macOS and
the various Linux distributions. The previous implementation only looked for a
Debian-style `/usr/share/fonts/truetype` layout and silently fell back to
PIL's bitmap default, which renders tiny unreadable text.
"""

import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from config import Config

WIDTH, HEIGHT = 1920, 1080

# Panel geometry for the animation composite layout.
ANIMATION_PANEL = (1010, 250, 850, 700)


def _load(path: str | None, size: int) -> ImageFont.FreeTypeFont:
    """Load a TrueType font at a size, degrading to PIL's default."""
    if path:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return ImageFont.load_default()


class SlideRenderer:
    """Render slides as full-resolution PNG images."""

    def __init__(self):
        self.width = WIDTH
        self.height = HEIGHT
        self.bg_color = (255, 255, 255)
        self.title_color = (17, 24, 39)
        self.text_color = (55, 65, 81)
        self.muted_color = (107, 114, 128)
        self.accent_color = (37, 99, 235)

        self.margin = 130
        self.title_size = 76
        self.body_size = 44

    # -- helpers --------------------------------------------------------
    @staticmethod
    def sanitize_filename(text: str, max_length: int = 30) -> str:
        text = text[:max_length]
        for char in '<>:"/\\|?*!':
            text = text.replace(char, "")
        return text.replace(" ", "_")

    @staticmethod
    def clean_markdown(text: str) -> str:
        """Strip inline markdown emphasis and collapse whitespace."""
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", text or "")
        text = re.sub(r"\*(.+?)\*", r"\1", text)
        text = re.sub(r"__(.+?)__", r"\1", text)
        text = re.sub(r"[^A-Za-z0-9 ]_(.+?)_[^A-Za-z0-9]", r"\1", text)
        return re.sub(r"\s+", " ", text).strip()

    def fonts(self) -> tuple:
        """Title, body and small fonts, sized once per call site."""
        return (
            _load(Config.TITLE_FONT, self.title_size),
            _load(Config.CONTENT_FONT, self.body_size),
            _load(Config.CONTENT_FONT, 28),
        )

    @staticmethod
    def wrap(text: str, font, max_width: int, draw) -> list[str]:
        """Greedy word wrap measured against real glyph metrics."""
        words = text.split()
        lines: list[str] = []
        current: list[str] = []

        for word in words:
            candidate = " ".join(current + [word])
            try:
                width = draw.textlength(candidate, font=font)
            except AttributeError:
                bbox = draw.textbbox((0, 0), candidate, font=font)
                width = bbox[2] - bbox[0]

            if width <= max_width or not current:
                current.append(word)
            else:
                lines.append(" ".join(current))
                current = [word]

        if current:
            lines.append(" ".join(current))
        return lines or [""]

    @staticmethod
    def _cover(image: Image.Image, width: int, height: int) -> Image.Image:
        """Scale and centre-crop to fill the target box exactly."""
        ratio = image.width / image.height
        target = width / height
        if ratio > target:
            new_size = (int(height * ratio), height)
        else:
            new_size = (width, int(width / ratio))

        resized = image.resize(new_size, Image.LANCZOS)
        left = (resized.width - width) // 2
        top = (resized.height - height) // 2
        return resized.crop((left, top, left + width, top + height))

    # -- shared chrome --------------------------------------------------
    def _draw_header(self, draw, title_font, small_font, title: str,
                     slide_number: int, total: int = 0) -> int:
        """Accent rule, title and footer. Returns the y below the title."""
        draw.rectangle([0, 0, self.width, 14], fill=self.accent_color)

        title_lines = self.wrap(title, title_font, self.width - 2 * self.margin, draw)
        # Shrink rather than clip if the title is unexpectedly long.
        while len(title_lines) > 3 and self.title_size > 44:
            self.title_size -= 6
            title_font = _load(Config.TITLE_FONT, self.title_size)
            title_lines = self.wrap(title, title_font, self.width - 2 * self.margin, draw)

        y = 110
        for line in title_lines:
            draw.text((self.margin, y), line, font=title_font, fill=self.title_color)
            y += int(self.title_size * 1.18)

        # Short accent rule under the title.
        draw.rectangle([self.margin, y + 18, self.margin + 120, y + 26],
                       fill=self.accent_color)

        try:
            number = int(slide_number)
        except (TypeError, ValueError):
            number = 0
        try:
            count = int(total) if total else 0
        except (TypeError, ValueError):
            count = 0

        label = f"{number:02d}" + (f" / {count:02d}" if count else "")
        draw.text((self.width - self.margin - draw.textlength(label, font=small_font),
                   self.height - 84), label, font=small_font, fill=self.muted_color)

        return y + 70

    def _draw_body(self, draw, body_font, text: str, top: int, max_lines: int,
                   left: int | None = None, width: int | None = None) -> None:
        """Paragraph text, clipped to `max_lines` so a slide never overflows."""
        left = self.margin if left is None else left
        width = (self.width - self.margin - left) if width is None else width

        y = top
        floor = self.height - 200
        drawn = 0

        for paragraph in (text or "").split("\n"):
            lines = self.wrap(paragraph.strip(), body_font, width, draw)
            for line in lines:
                # Stop at the line budget or the bottom edge, so long
                # narration never spills off the slide.
                if drawn >= max_lines or y + self.body_size > floor:
                    return
                draw.text((left, y), line, font=body_font, fill=self.text_color)
                y += int(self.body_size * 1.5)
                drawn += 1
            y += int(self.body_size * 0.5)

    # -- layouts --------------------------------------------------------
    def create_text_slide(self, title: str, content: str, slide_number: int,
                          topic: str, total_slides: int = 0) -> str:
        image = Image.new("RGB", (self.width, self.height), self.bg_color)
        draw = ImageDraw.Draw(image)
        title_font, body_font, small_font = self.fonts()

        below = self._draw_header(draw, title_font, small_font, title,
                                  slide_number, total_slides)
        self._draw_body(draw, body_font, content, below, max_lines=6)

        draw.text((self.margin, self.height - 84), self.clean_markdown(topic)[:70],
                  font=small_font, fill=self.muted_color)

        return self._save(image, topic, slide_number, "text")

    def create_slide_with_image(self, title: str, content: str, image_path: str,
                                slide_number: int, topic: str,
                                total_slides: int = 0) -> str:
        image = Image.new("RGB", (self.width, self.height), self.bg_color)
        draw = ImageDraw.Draw(image)
        title_font, body_font, small_font = self.fonts()

        below = self._draw_header(draw, title_font, small_font, title,
                                  slide_number, total_slides)

        # Image occupies the right half; text reflows into the left column.
        panel_x = self.width // 2 + 20
        panel_w = self.width - self.margin - panel_x
        panel_h = self.height - below - 200

        try:
            photo = Image.open(image_path).convert("RGB")
            draw.rectangle([panel_x - 1, below - 1, panel_x + panel_w + 1,
                            below + panel_h + 1], outline=(229, 231, 235), width=2)
            image.paste(self._cover(photo, panel_w, panel_h), (panel_x, below))
        except Exception as exc:  # noqa: BLE001
            print(f"  Could not place slide image ({exc}); drawing text only")
            self._draw_body(draw, body_font, content, below, max_lines=6)
            return self._save(image, topic, slide_number, "image")

        self._draw_body(draw, body_font, content, below, max_lines=7,
                        left=self.margin, width=self.width // 2 - self.margin - 40)

        return self._save(image, topic, slide_number, "image")

    def create_slide_with_animation_placeholder(self, title: str, content: str,
                                                slide_number: int, topic: str,
                                                total_slides: int = 0) -> str:
        """Base slide for an animation composite.

        The panel is filled with a flat tint; `video_composer` later scales the
        Manim render to exactly these bounds.
        """
        image = Image.new("RGB", (self.width, self.height), self.bg_color)
        draw = ImageDraw.Draw(image)
        title_font, body_font, small_font = self.fonts()

        below = self._draw_header(draw, title_font, small_font, title,
                                  slide_number, total_slides)

        px, py, pw, ph = ANIMATION_PANEL
        draw.rounded_rectangle([px, py, px + pw, py + ph], radius=18,
                               fill=(248, 250, 252), outline=(226, 232, 240),
                               width=2)
        label = "animation"
        lw = draw.textlength(label, font=small_font)
        draw.text((px + (pw - lw) / 2, py + (ph - 20) / 2), label,
                  font=small_font, fill=(156, 163, 175))

        self._draw_body(draw, body_font, content, below, max_lines=8,
                        left=self.margin, width=px - self.margin - 40)

        return self._save(image, topic, slide_number, "animation")

    # -- output ---------------------------------------------------------
    def _save(self, image: Image.Image, topic: str, slide_number: int,
              kind: str) -> str:
        name = f"{self.sanitize_filename(topic)}_slide_{slide_number}_{kind}.png"
        path = Config.SLIDES_DIR / name
        image.save(path, "PNG")
        return str(path)