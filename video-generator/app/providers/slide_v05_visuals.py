from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFilter, ImageOps


STYLE_ANCHORS = {
    "cute-character": {
        "name": "따뜻한 캐릭터 이야기",
        "character": "short dark-brown hair, mustard cardigan, cream shirt, teal satchel",
        "palette": ((251, 218, 151), (247, 154, 111), (86, 132, 120), (73, 65, 82)),
    },
    "fantasy-anime": {
        "name": "판타지 애니메이션",
        "character": "shoulder-length black hair, indigo cloak, silver crescent clasp, leather journal",
        "palette": ((32, 54, 101), (72, 78, 153), (64, 196, 214), (232, 188, 92)),
    },
}

ENVIRONMENT_KEYWORDS = {
    "water": ("바다", "호수", "강", "물결", "배", "항구", "해변"),
    "forest": ("숲", "나무", "정원", "들판", "꽃", "새", "산책"),
    "home": ("집", "방", "마을", "도시", "거리", "문", "창문"),
    "mountain": ("산", "언덕", "길", "여행", "오르", "계곡"),
    "sky": ("하늘", "별", "달", "밤", "새벽", "빛", "구름"),
}


def classify_environment(text: str) -> str:
    scores = {name: sum(text.count(word) for word in words) for name, words in ENVIRONMENT_KEYWORDS.items()}
    winner = max(scores, key=scores.get)
    return winner if scores[winner] else "meadow"


def visual_prompt(text: str, style: str, environment: str) -> str:
    anchor = STYLE_ANCHORS[style]
    cleaned = " ".join(text.split())[:180]
    return (
        f"{anchor['name']} style; consistent protagonist ({anchor['character']}); "
        f"{environment} environment; scene meaning: {cleaned}; no text or watermark"
    )


def create_scene_images(
    scenes: list[dict[str, Any]],
    style: str,
    aspect_ratio: str,
    output_dir: Path,
) -> list[dict[str, Any]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    width, height = ((1280, 720) if aspect_ratio == "16:9" else (720, 1280))
    results: list[dict[str, Any]] = []
    for scene in scenes:
        text = str(scene.get("text", ""))
        environment = classify_environment(text)
        digest = hashlib.sha256(f"{style}\0{text}".encode("utf-8")).digest()
        path = output_dir / f"scene-{int(scene.get('index', len(results) + 1)):03d}.png"
        _draw_scene(path, width, height, style, environment, text, digest)
        results.append(
            {
                "index": int(scene.get("index", len(results) + 1)),
                "path": str(path),
                "duration_seconds": float(scene.get("duration_seconds", 1.0)),
                "environment": environment,
                "prompt": visual_prompt(text, style, environment),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    return results


def write_scene_manifest(images: list[dict[str, Any]], manifest: Path) -> Path:
    if not images:
        raise ValueError("장면 이미지가 없습니다.")
    lines = ["ffconcat version 1.0"]
    for item in images:
        safe_path = Path(item["path"]).resolve().as_posix().replace("'", "'\\''")
        lines.extend([f"file '{safe_path}'", f"duration {max(0.04, float(item['duration_seconds'])):.6f}"])
    last_path = Path(images[-1]["path"]).resolve().as_posix().replace("'", "'\\''")
    lines.append(f"file '{last_path}'")
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return manifest


def _draw_scene(path: Path, width: int, height: int, style: str, environment: str, text: str, seed: bytes) -> None:
    anchor = STYLE_ANCHORS[style]
    warm = style == "cute-character"
    night = style == "fantasy-anime" or any(word in text for word in ("밤", "별", "달", "어둠"))
    sky_top = (28, 43, 87) if night else (111, 181, 225)
    sky_bottom = (119, 112, 181) if night else (255, 214, 157)
    gradient = Image.linear_gradient("L").resize((width, height))
    image = ImageOps.colorize(gradient, sky_top, sky_bottom).convert("RGB")
    draw = ImageDraw.Draw(image, "RGBA")
    horizon = int(height * (0.55 if width > height else 0.46))
    _draw_sky(draw, width, height, horizon, night, seed)
    _draw_background(draw, width, height, horizon, environment, warm, seed)
    _draw_character(draw, width, height, horizon, style, seed)
    _draw_atmosphere(draw, width, height, night, warm, seed)
    image = image.filter(ImageFilter.GaussianBlur(radius=0.35))
    image.save(path, "PNG", optimize=True)


def _draw_sky(draw: ImageDraw.ImageDraw, width: int, height: int, horizon: int, night: bool, seed: bytes) -> None:
    orb_x = int(width * (0.76 if seed[0] % 2 else 0.22))
    orb_y = int(height * 0.19)
    radius = max(22, int(min(width, height) * 0.045))
    color = (237, 244, 255, 235) if night else (255, 239, 172, 235)
    for scale, alpha in ((2.4, 25), (1.7, 45), (1.0, 235)):
        r = int(radius * scale)
        draw.ellipse((orb_x - r, orb_y - r, orb_x + r, orb_y + r), fill=(*color[:3], alpha))
    cloud_color = (230, 236, 255, 45) if night else (255, 249, 232, 100)
    for index in range(4):
        x = int(width * (0.08 + 0.22 * index) + seed[index + 1] % max(1, width // 10))
        y = int(height * (0.14 + 0.07 * (index % 2)))
        w = int(width * (0.10 + (seed[index + 5] % 30) / 300))
        draw.ellipse((x, y, x + w, y + w * 0.34), fill=cloud_color)
    if night:
        for index in range(46):
            x = (seed[index % len(seed)] * (index + 17) * 13) % width
            y = (seed[(index + 7) % len(seed)] * (index + 5) * 7) % max(1, horizon)
            r = 1 + index % 2
            draw.ellipse((x - r, y - r, x + r, y + r), fill=(205, 238, 255, 130 + index % 90))


def _draw_background(draw: ImageDraw.ImageDraw, width: int, height: int, horizon: int, environment: str, warm: bool, seed: bytes) -> None:
    mountain_far = (53, 75, 110, 155) if not warm else (104, 122, 113, 135)
    mountain_near = (44, 66, 92, 220) if not warm else (77, 112, 86, 210)
    draw.polygon([(0, horizon), (width * 0.18, horizon * 0.54), (width * 0.34, horizon), (width * 0.55, horizon * 0.47), (width * 0.78, horizon), (width, horizon * 0.63), (width, height), (0, height)], fill=mountain_far)
    draw.polygon([(0, horizon * 1.04), (width * 0.28, horizon * 0.68), (width * 0.48, horizon * 1.03), (width * 0.73, horizon * 0.72), (width, horizon), (width, height), (0, height)], fill=mountain_near)
    if environment == "water":
        draw.rectangle((0, horizon, width, height), fill=(39, 115, 153, 230) if warm else (29, 74, 130, 235))
        for index in range(18):
            y = horizon + int((height - horizon) * (index + 1) / 20)
            inset = (seed[index % len(seed)] % max(2, width // 8))
            draw.arc((inset, y, width - inset, y + 30), 190, 350, fill=(205, 239, 244, 85), width=max(2, width // 400))
        draw.polygon([(width * 0.45, horizon * 1.03), (width * 0.58, horizon * 1.03), (width * 0.55, horizon * 1.10), (width * 0.48, horizon * 1.10)], fill=(80, 56, 43, 230))
    else:
        ground = (99, 151, 84, 255) if warm else (47, 80, 91, 255)
        draw.rectangle((0, horizon, width, height), fill=ground)
        path_color = (225, 191, 140, 220) if warm else (126, 126, 145, 185)
        draw.polygon([(width * 0.46, height), (width * 0.58, height), (width * 0.53, horizon), (width * 0.50, horizon)], fill=path_color)
    if environment in {"forest", "meadow", "mountain"}:
        for index in range(8):
            x = int(width * (0.05 + index * 0.13))
            base = int(horizon + (height - horizon) * (0.18 + (seed[index] % 30) / 100))
            size = int(min(width, height) * (0.06 + (seed[index + 8] % 30) / 500))
            draw.rectangle((x - size * 0.08, base - size * 0.4, x + size * 0.08, base), fill=(74, 54, 41, 220))
            foliage = (55, 114, 72, 240) if warm else (29, 75, 78, 245)
            draw.ellipse((x - size, base - size * 1.35, x + size, base - size * 0.15), fill=foliage)
    if environment == "home":
        house_x = int(width * 0.68)
        house_y = int(horizon * 0.79)
        house_w = int(width * 0.18)
        house_h = int(height * 0.17)
        draw.rectangle((house_x, house_y, house_x + house_w, house_y + house_h), fill=(232, 203, 163, 245))
        draw.polygon([(house_x - house_w * 0.08, house_y), (house_x + house_w * 0.5, house_y - house_h * 0.55), (house_x + house_w * 1.08, house_y)], fill=(111, 59, 52, 245))
        draw.rectangle((house_x + house_w * 0.42, house_y + house_h * 0.42, house_x + house_w * 0.62, house_y + house_h), fill=(83, 65, 64, 230))
    if environment == "sky":
        for index in range(3):
            x = width * (0.66 + index * 0.09)
            y = horizon * (0.47 + index * 0.08)
            draw.polygon([(x, y), (x + width * 0.06, y - height * 0.04), (x + width * 0.11, y), (x + width * 0.075, y + height * 0.07), (x + width * 0.025, y + height * 0.065)], fill=(55, 66, 105, 180))


def _draw_character(draw: ImageDraw.ImageDraw, width: int, height: int, horizon: int, style: str, seed: bytes) -> None:
    scale = min(width, height)
    cx = int(width * (0.34 if seed[2] % 2 else 0.64))
    base = int(height * 0.89)
    body_h = int(scale * 0.28)
    head_r = int(scale * 0.060)
    skin = (238, 183, 144, 255)
    hair = (59, 37, 34, 255) if style == "cute-character" else (20, 24, 37, 255)
    if style == "cute-character":
        draw.rounded_rectangle((cx - body_h * 0.32, base - body_h, cx + body_h * 0.32, base), radius=int(scale * 0.04), fill=(210, 143, 39, 255))
        draw.polygon([(cx - body_h * 0.16, base - body_h * 0.86), (cx + body_h * 0.15, base - body_h * 0.86), (cx + body_h * 0.08, base - body_h * 0.35), (cx - body_h * 0.08, base - body_h * 0.35)], fill=(247, 236, 207, 255))
        draw.line((cx + body_h * 0.25, base - body_h * 0.87, cx - body_h * 0.18, base - body_h * 0.12), fill=(45, 91, 91, 255), width=max(4, int(scale * 0.014)))
        draw.rounded_rectangle((cx - body_h * 0.40, base - body_h * 0.42, cx - body_h * 0.10, base - body_h * 0.10), radius=10, fill=(55, 101, 97, 255))
    else:
        draw.polygon([(cx, base - body_h * 1.02), (cx - body_h * 0.55, base), (cx + body_h * 0.58, base)], fill=(39, 44, 92, 255))
        draw.polygon([(cx - body_h * 0.18, base - body_h * 0.80), (cx + body_h * 0.18, base - body_h * 0.80), (cx + body_h * 0.12, base - body_h * 0.12), (cx - body_h * 0.12, base - body_h * 0.12)], fill=(31, 34, 44, 255))
        clasp_r = max(4, int(scale * 0.012))
        draw.ellipse((cx - clasp_r, base - body_h * 0.82 - clasp_r, cx + clasp_r, base - body_h * 0.82 + clasp_r), outline=(207, 210, 218, 255), width=max(2, clasp_r // 3))
        draw.rounded_rectangle((cx + body_h * 0.03, base - body_h * 0.52, cx + body_h * 0.25, base - body_h * 0.22), radius=5, fill=(76, 48, 37, 255), outline=(190, 145, 81, 210), width=2)
    head_y = int(base - body_h * 1.12)
    draw.ellipse((cx - head_r * 1.05, head_y - head_r * 1.18, cx + head_r * 1.05, head_y + head_r * 1.18), fill=hair)
    draw.ellipse((cx - head_r * 0.75, head_y - head_r * 0.70, cx + head_r * 0.75, head_y + head_r * 0.88), fill=skin)
    eye_y = head_y - int(head_r * 0.05)
    for eye_x in (cx - int(head_r * 0.28), cx + int(head_r * 0.28)):
        eye_r = max(2, head_r // 12)
        draw.ellipse((eye_x - eye_r, eye_y - eye_r, eye_x + eye_r, eye_y + eye_r), fill=(42, 35, 36, 255))
    draw.arc((cx - head_r * 0.30, head_y + head_r * 0.10, cx + head_r * 0.30, head_y + head_r * 0.50), 10, 170, fill=(129, 69, 63, 220), width=max(2, head_r // 15))


def _draw_atmosphere(draw: ImageDraw.ImageDraw, width: int, height: int, night: bool, warm: bool, seed: bytes) -> None:
    for index in range(28):
        x = (seed[index % len(seed)] * (index + 3) * 19) % width
        y = int(height * 0.40 + (seed[(index + 11) % len(seed)] * (index + 9) * 11) % max(1, int(height * 0.55)))
        radius = 2 + index % 5
        color = (255, 221, 117, 80) if warm else (103, 225, 245, 75)
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)
    vignette = max(30, int(min(width, height) * 0.12))
    for step in range(8):
        alpha = int(8 + step * 3)
        inset = int(step * vignette / 8)
        draw.rectangle((inset, inset, width - inset, height - inset), outline=(8, 13, 28, alpha), width=max(1, vignette // 8))
