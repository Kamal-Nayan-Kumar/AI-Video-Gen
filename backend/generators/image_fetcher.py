"""Slide imagery.

With an Unsplash key this fetches a real photograph. Without one it generates
a deterministic abstract plate from the keyword — a soft duotone gradient with
a geometric motif. The generated plate is deliberately abstract rather than a
fake "photo" so nothing misleading appears in a demo.
"""

import colorsys
import hashlib
import io
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFilter

from config import Config

WIDTH, HEIGHT = 1280, 800


class ImageFetcher:
    """Obtain one image per slide."""

    def __init__(self):
        self.api_key = Config.UNSPLASH_ACCESS_KEY
        self.base_url = "https://api.unsplash.com/search/photos"
        self.session = requests.Session()

    @staticmethod
    def _safe(topic: str) -> str:
        return topic[:30].replace(" ", "_").replace(":", "").replace("/", "_")

    def fetch_image(self, keyword: str, slide_number: int, topic: str) -> str:
        """Return the path of a usable image, or "" if none could be produced."""
        destination = (
            Config.IMAGES_DIR / f"{self._safe(topic)}_slide_{slide_number}.jpg"
        )

        if self.api_key:
            try:
                if self._fetch_unsplash(keyword, destination):
                    return str(destination)
            except Exception as exc:  # noqa: BLE001
                print(f"  Unsplash failed ({exc}); generating a plate instead")

        return self._generate_plate(keyword or topic, destination)

    # -- real photos ----------------------------------------------------
    def _fetch_unsplash(self, keyword: str, destination: Path) -> bool:
        response = self.session.get(
            self.base_url,
            params={"query": keyword, "per_page": 1, "client_id": self.api_key},
            timeout=30,
        )
        response.raise_for_status()
        results = response.json().get("results") or []
        if not results:
            return False

        image_response = self.session.get(results[0]["urls"]["regular"], timeout=30)
        image_response.raise_for_status()

        # Re-encode so every slide image shares one resolution and format.
        source = Image.open(io.BytesIO(image_response.content)).convert("RGB")
        source = source.resize((WIDTH, HEIGHT), Image.LANCZOS)
        source.save(destination, "JPEG", quality=88)
        return True

    # -- generated plates -----------------------------------------------
    @staticmethod
    def _generate_plate(keyword: str, destination: Path) -> str:
        """Render a deterministic abstract plate for a keyword."""
        seed = hashlib.sha256(keyword.encode("utf-8")).digest()
        hue = (seed[0] / 255.0 + 0.58) % 1.0
        base = colorsys.hls_to_rgb(hue, 0.16, 0.16)
        accent = colorsys.hls_to_rgb((hue + 0.10) % 1.0, 0.62, 0.66)

        base_rgb = tuple(int(c * 255) for c in base)
        accent_rgb = tuple(int(c * 255) for c in accent)
        highlight = tuple(int(c * 255) for c in colorsys.hls_to_rgb(hue, 0.90, 0.72))

        # Diagonal gradient background.
        plate = Image.new("RGB", (WIDTH, HEIGHT))
        draw = ImageDraw.Draw(plate)
        for y in range(HEIGHT):
            t = y / HEIGHT
            draw.line(
                [(0, y), (WIDTH, y)],
                fill=tuple(int(c + (255 - c) * t * 0.10) for c in base_rgb),
            )

        # Concentric arcs, offset so the composition is not dead-centre.
        glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow)
        cx = int(WIDTH * (0.62 + (seed[1] / 255.0 - 0.5) * 0.12))
        cy = int(HEIGHT * (0.46 + (seed[2] / 255.0 - 0.5) * 0.12))
        for i in range(7):
            radius = 110 + i * 78
            glow_draw.ellipse(
                [cx - radius, cy - radius, cx + radius, cy + radius],
                outline=accent_rgb + (70 - i * 7,),
                width=3,
            )

        # A soft key light behind the arcs gives the plate some depth.
        halo = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        ImageDraw.Draw(halo).ellipse(
            [cx - 430, cy - 430, cx + 430, cy + 430],
            fill=accent_rgb + (46,),
        )
        halo = halo.filter(ImageFilter.GaussianBlur(90))
        glow = Image.alpha_composite(halo, glow)

        # Small bright core to anchor the focal point.
        ImageDraw.Draw(glow).ellipse(
            [cx - 7, cy - 7, cx + 7, cy + 7], fill=highlight + (210,)
        )

        plate = Image.alpha_composite(plate.convert("RGBA"), glow).convert("RGB")

        # A single thin rule for structure.
        draw = ImageDraw.Draw(plate)
        draw.line(
            [(int(WIDTH * 0.08), int(HEIGHT * 0.88)),
             (int(WIDTH * 0.52), int(HEIGHT * 0.88))],
            fill=accent_rgb,
            width=6,
        )

        plate.save(destination, "JPEG", quality=90)
        return str(destination)