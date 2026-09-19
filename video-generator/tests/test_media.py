from pathlib import Path

from PIL import Image

from app.config import Settings
from app.media import validate_image


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
