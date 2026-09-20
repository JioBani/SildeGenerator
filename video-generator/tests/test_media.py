import asyncio
import shutil
import subprocess
from pathlib import Path

import pytest
from PIL import Image

from app.config import Settings
from app.media import apply_audio_speed, audio_speed_filter, probe, validate_image


def test_audio_speed_filter_uses_bounded_job_multiplier() -> None:
    assert audio_speed_filter(.75) == "atempo=0.75"
    assert audio_speed_filter(1) == "atempo=1.00"
    assert audio_speed_filter(1.5) == "atempo=1.50"


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg is provided by the runner image")
def test_apply_audio_speed_changes_the_persisted_audio_duration(tmp_path: Path) -> None:
    path = tmp_path / "voice.mp3"
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=3",
        "-c:a", "libmp3lame", "-b:a", "128k", str(path),
    ], check=True)
    asyncio.run(apply_audio_speed(path, 1.5))
    info = asyncio.run(probe(path))
    duration = float(info["format"]["duration"])
    assert 1.9 <= duration <= 2.1


def test_validate_image_reports_deterministic_quality_signals(tmp_path: Path) -> None:
    path = tmp_path / "gradient.png"
    image = Image.new("RGB", (1920, 1080))
    for x in range(image.width):
        value = round(255 * x / (image.width - 1))
        for y in range(image.height):
            image.putpixel((x, y), (value, (value + y) % 256, 255 - value))
    image.save(path)

    metrics = validate_image(path, Settings())

    assert metrics["width"] == 1920
    assert metrics["height"] == 1080
    assert metrics["entropy"] > 5
    assert 0 < metrics["mean_brightness"] < 255
    assert metrics["sharpness"] >= 0
    assert len(metrics["perceptual_hash"]) == 16


def test_validate_image_rejects_empty_image(tmp_path: Path) -> None:
    path = tmp_path / "empty.png"
    Image.new("RGB", (1920, 1080), "white").save(path)

    try:
        validate_image(path, Settings())
    except ValueError as error:
        assert "visually empty" in str(error)
    else:
        raise AssertionError("empty image should fail validation")
