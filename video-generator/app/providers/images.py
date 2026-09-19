from __future__ import annotations

import base64
import hashlib
import io
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

import httpx
from PIL import Image, ImageDraw, ImageFilter, ImageOps

from ..config import Settings
from ..tracking import Tracker


class ImageSubject(Protocol):
    id: str
    image_prompt: str


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def validate_reference_count(reference_paths: list[Path], *, allow_override: bool = False) -> None:
    count = len(reference_paths)
    if count > 16:
        raise ValueError("image provider reference hard limit is 16")
    if count > 8 and not allow_override:
        raise ValueError("image provider default reference limit is 8")


def _mock_image(scene: ImageSubject, path: Path, width: int, height: int) -> None:
    seed = int(hashlib.sha256(scene.image_prompt.encode("utf-8")).hexdigest()[:16], 16)
    rng = random.Random(seed)
    top = tuple(rng.randint(18, 70) for _ in range(3))
    bottom = tuple(rng.randint(80, 175) for _ in range(3))
    image = Image.new("RGB", (width, height), top)
    draw = ImageDraw.Draw(image, "RGBA")
    for y in range(height):
        ratio = y / max(1, height - 1)
        color = tuple(round(top[i] * (1 - ratio) + bottom[i] * ratio) for i in range(3))
        draw.line((0, y, width, y), fill=(*color, 255))
    for _ in range(8):
        radius = rng.randint(height // 12, height // 3)
        x = rng.randint(-radius, width + radius)
        y = rng.randint(-radius, height + radius)
        color = (rng.randint(120, 255), rng.randint(80, 220), rng.randint(30, 160), rng.randint(25, 85))
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)
    image = image.filter(ImageFilter.GaussianBlur(radius=max(8, height // 70)))
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, "PNG", optimize=True)


async def _oauth_image(
    prompt: str,
    system_prompt: str,
    settings: Settings,
    reference_paths: list[Path] | None = None,
    quality: str = "medium",
    input_fidelity: str | None = None,
    model: str | None = None,
) -> tuple[bytes, dict[str, Any], str | None]:
    reference_paths = reference_paths or []
    validate_reference_count(reference_paths)
    full_prompt = f"{system_prompt}\n\n{prompt}"
    payload = {
        "model": model or settings.image_generation_model,
        "prompt": full_prompt,
        "quality": quality,
        "size": "1536x1024",
    }
    if reference_paths and input_fidelity:
        payload["input_fidelity"] = input_fidelity
    async with httpx.AsyncClient(timeout=httpx.Timeout(300, connect=10)) as client:
        if not reference_paths:
            response = await client.post(
                f"{settings.subscription_base_url}/v1/images/generations",
                headers={"Content-Type": "application/json"},
                json=payload,
            )
        else:
            streams = [path.open("rb") for path in reference_paths]
            try:
                field = "image" if len(reference_paths) == 1 else "image[]"
                response = await client.post(
                    f"{settings.subscription_base_url}/v1/images/edits",
                    data=payload,
                    files=[(field, (path.name, stream, "image/png")) for path, stream in zip(reference_paths, streams)],
                )
            finally:
                for stream in streams:
                    stream.close()
    if response.status_code >= 400:
        raise RuntimeError(f"image OAuth proxy returned {response.status_code}: {response.text[:1000]}")
    result = response.json()
    item = (result.get("data") or [{}])[0]
    encoded = item.get("b64_json")
    if not encoded:
        raise RuntimeError("image OAuth proxy completed without b64_json")
    usage = {
        "image": result.get("usage") or {},
        "image_model": model or settings.image_generation_model,
        "quality": result.get("quality") or quality,
        "size": result.get("size") or "1536x1024",
        "request_kind": "edit" if reference_paths else "generation",
        "reference_images": [path.name for path in reference_paths],
        "input_fidelity": input_fidelity,
        "provider_request_id": response.headers.get("x-request-id") or result.get("id"),
    }
    return base64.b64decode(encoded), usage, item.get("revised_prompt")


async def generate_image(
    scene: ImageSubject,
    path: Path,
    system_prompt: str,
    settings: Settings,
    tracker: Tracker,
    reference_paths: list[Path] | None = None,
    *,
    stage: str = "image_generation",
    quality: str = "medium",
    input_fidelity: str | None = None,
    record_usage: bool = True,
    model: str | None = None,
) -> dict[str, Any]:
    started_at = _now()
    started = time.perf_counter()
    raw_usage: dict[str, Any] = {}
    if settings.image_provider == "mock":
        _mock_image(scene, path, settings.width, settings.height)
        provider = "mock"
    elif settings.image_provider == "oauth":
        content, raw_usage, revised_prompt = await _oauth_image(
            scene.image_prompt,
            system_prompt,
            settings,
            reference_paths,
            quality,
            input_fidelity,
            model,
        )
        with Image.open(io.BytesIO(content)) as source:
            source_size = {"width": source.width, "height": source.height}
            image = ImageOps.fit(source.convert("RGB"), (settings.width, settings.height), Image.Resampling.LANCZOS)
            image.save(path, "PNG", optimize=True)
        raw_usage = {
            **raw_usage,
            "revised_prompt": revised_prompt,
            "source_dimensions": source_size,
            "normalized_dimensions": {"width": settings.width, "height": settings.height},
        }
        provider = "chatgpt_oauth"
    else:
        raise RuntimeError(f"unsupported IMAGE_PROVIDER: {settings.image_provider}")
    finished_at = _now()
    if provider == "mock":
        raw_usage = {
            "image": {}, "image_model": "mock-image-v1", "quality": quality,
            "size": f"{settings.width}x{settings.height}", "request_kind": "generation",
            "reference_images": [path.name for path in reference_paths or []],
        }
    if record_usage and provider == "mock":
        tracker.add_usage(
            provider=provider,
            model="mock-image-v1",
            stage=stage,
            scene_id=scene.id,
            images_generated=1,
            started_at=started_at,
            finished_at=finished_at,
            duration_ms=round((time.perf_counter() - started) * 1000),
            raw_usage={},
        )
    elif record_usage:
        image_usage = raw_usage.get("image") or {}
        tracker.add_usage(
            provider="chatgpt_oauth_image",
            model=raw_usage.get("image_model") or model or settings.image_generation_model,
            stage=stage,
            scene_id=scene.id,
            input_tokens=int(image_usage.get("input_tokens") or image_usage.get("text_input_tokens") or 0),
            cached_input_tokens=int(
                image_usage.get("cached_input_tokens")
                or (image_usage.get("input_tokens_details") or {}).get("cached_tokens")
                or 0
            ),
            output_tokens=int(image_usage.get("output_tokens") or image_usage.get("image_output_tokens") or 0),
            images_generated=1,
            started_at=started_at,
            finished_at=finished_at,
            duration_ms=round((time.perf_counter() - started) * 1000),
            raw_usage=raw_usage,
        )
    return raw_usage
