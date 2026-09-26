"""Adapter for the independent slide-generator v0.5 illustration renderer."""
from __future__ import annotations

import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image, ImageDraw

from .slide_v05_visuals import _draw_scene


ENVIRONMENT_KEYWORDS = {
    "water": ("바다", "호수", "강", "물결", "배", "항구", "해변"),
    "forest": ("숲", "나무", "정원", "들판", "꽃", "새가", "새들", "산책"),
    "home": ("집", "방", "마을", "도시", "거리", "문", "창문"),
    "mountain": ("산", "언덕", "길", "여행", "오르", "계곡"),
    "sky": ("하늘", "별", "달", "밤", "새벽", "빛", "구름"),
}


def classify_environment(text: str) -> str:
    scores = {name: sum(text.count(word) for word in words) for name, words in ENVIRONMENT_KEYWORDS.items()}
    winner = max(scores, key=scores.get)
    return winner if scores[winner] else "meadow"


class IllustratedSceneImageProvider:
    version = "0.5.0"

    def render(self, narration: str, style: str, width: int, height: int, output: Path) -> dict[str, str]:
        if style not in {"cute_character", "fantasy_anime"}:
            raise ValueError("unsupported illustrated scene style")
        if (width, height) not in {(1280, 720), (720, 1280), (1920, 1080), (1080, 1920)}:
            raise ValueError("unsupported illustrated scene dimensions")
        source_size = (1280, 720) if width > height else (720, 1280)
        source_style = "cute-character" if style == "cute_character" else "fantasy-anime"
        environment = classify_environment(narration)
        seed = hashlib.sha256(f"{source_style}\0{narration}".encode("utf-8")).digest()
        output.parent.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(dir=output.parent) as temporary:
            source = Path(temporary) / "source.png"
            _draw_scene(source, *source_size, source_style, environment, narration, seed)
            with Image.open(source) as image:
                if environment == "water":
                    cx = source_size[0] * (.34 if seed[2] % 2 else .64)
                    width_source, height_source = source_size
                    rim = height_source * .82
                    half = width_source * .16
                    draw = ImageDraw.Draw(image)
                    draw.polygon([(cx - half, rim), (cx + half, rim),
                                  (cx + half * .72, height_source * .94),
                                  (cx - half * .72, height_source * .94)], fill="#6e4939")
                    draw.line((cx - half, rim, cx + half, rim), fill="#d5af77",
                              width=max(4, width_source // 250))
                if image.size != (width, height):
                    image = image.resize((width, height), Image.Resampling.LANCZOS)
                image.save(output, "PNG", optimize=True)
        return {"environment": environment, "style": style, "provider_version": self.version,
                "source_dimensions": f"{source_size[0]}x{source_size[1]}"}
