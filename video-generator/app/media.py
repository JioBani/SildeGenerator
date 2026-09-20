from __future__ import annotations

import asyncio
import json
import math
import os
import re
from pathlib import Path
from typing import Any

from PIL import Image, ImageFilter, ImageStat

from .config import Settings


def audio_speed_filter(speed: float) -> str:
    if not .75 <= speed <= 1.5:
        raise ValueError("narration speed must be between 0.75 and 1.5")
    return f"atempo={speed:.2f}"


async def apply_audio_speed(path: Path, speed: float) -> None:
    if abs(speed - 1) < .001:
        return
    output = path.with_name(f"{path.stem}.retimed{path.suffix}")
    process = await asyncio.create_subprocess_exec(
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(path),
        "-filter:a", audio_speed_filter(speed), "-ar", "44100", "-ac", "1",
        "-c:a", "libmp3lame", "-b:a", "128k", str(output),
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await process.communicate()
    if process.returncode:
        output.unlink(missing_ok=True)
        raise RuntimeError(stderr.decode("utf-8", errors="replace")[-1500:])
    os.replace(output, path)


async def probe(path: Path) -> dict[str, Any]:
    process = await asyncio.create_subprocess_exec("ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await process.communicate()
    if process.returncode: raise RuntimeError(stderr.decode("utf-8", errors="replace")[-1500:])
    return json.loads(stdout)


async def validate_audio(path: Path) -> dict[str, Any]:
    info = await probe(path); stream = next((item for item in info.get("streams", []) if item.get("codec_type") == "audio"), None)
    if not stream: raise ValueError(f"audio stream is missing: {path.name}")
    duration = float((info.get("format") or {}).get("duration") or stream.get("duration") or 0)
    if duration <= 0 or path.stat().st_size <= 0: raise ValueError(f"audio artifact is empty: {path.name}")
    process = await asyncio.create_subprocess_exec("ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "volumedetect", "-f", "null", "-", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    _, stderr = await process.communicate()
    if process.returncode: raise RuntimeError(stderr.decode("utf-8", errors="replace")[-1500:])
    report = stderr.decode("utf-8", errors="replace")
    def volume(name: str) -> float | None:
        match = re.search(rf"{name}:\s*(-?(?:inf|\d+(?:\.\d+)?)) dB", report)
        return None if not match or match.group(1) == "-inf" else float(match.group(1))
    mean_volume, max_volume = volume("mean_volume"), volume("max_volume")
    return {"duration_seconds": duration, "codec": stream.get("codec_name"), "sample_rate": int(stream.get("sample_rate") or 0), "channels": int(stream.get("channels") or 0), "bytes": path.stat().st_size, "mean_volume_db": mean_volume, "max_volume_db": max_volume, "silence_detected": max_volume is None or max_volume <= -55, "clipping_detected": max_volume is not None and max_volume >= -0.1}


def validate_image(path: Path, settings: Settings) -> dict[str, Any]:
    with Image.open(path) as image: image.verify()
    with Image.open(path) as image:
        rgb = image.convert("RGB")
        if rgb.size != (settings.width, settings.height): raise ValueError(f"unexpected image size {rgb.size}: {path.name}")
        sample = rgb.resize((64, 36), Image.Resampling.LANCZOS); grayscale = sample.convert("L"); pixels = list(grayscale.getdata()); variance = sum(ImageStat.Stat(sample).var)
        if variance < 1: raise ValueError(f"image is visually empty: {path.name}")
        histogram = grayscale.histogram(); entropy = -sum((count / len(pixels)) * math.log2(count / len(pixels)) for count in histogram if count); brightness = sum(pixels) / len(pixels); shadow_clip = sum(1 for value in pixels if value <= 5) / len(pixels); highlight_clip = sum(1 for value in pixels if value >= 250) / len(pixels); edges = grayscale.filter(ImageFilter.FIND_EDGES); sharpness = ImageStat.Stat(edges).var[0]; hash_sample = grayscale.resize((8, 8), Image.Resampling.LANCZOS); hash_pixels = list(hash_sample.getdata()); hash_mean = sum(hash_pixels) / len(hash_pixels); perceptual_hash = f"{sum((1 << index) for index, value in enumerate(hash_pixels) if value >= hash_mean):016x}"
        return {"width": rgb.width, "height": rgb.height, "variance": round(variance, 3), "entropy": round(entropy, 4), "mean_brightness": round(brightness, 3), "shadow_clip_ratio": round(shadow_clip, 6), "highlight_clip_ratio": round(highlight_clip, 6), "sharpness": round(sharpness, 3), "perceptual_hash": perceptual_hash}


async def validate_video(path: Path, settings: Settings) -> dict[str, Any]:
    info = await probe(path); streams = info.get("streams") or []; video = next((stream for stream in streams if stream.get("codec_type") == "video"), None); audio = next((stream for stream in streams if stream.get("codec_type") == "audio"), None)
    if not video or not audio: raise ValueError("rendered video must contain one video and one audio stream")
    if int(video.get("width", 0)) != settings.width or int(video.get("height", 0)) != settings.height: raise ValueError("rendered video has unexpected dimensions")
    rate = str(video.get("avg_frame_rate") or video.get("r_frame_rate") or "0/1").split("/"); actual_fps = float(rate[0]) / max(1.0, float(rate[1]))
    if abs(actual_fps - settings.fps) > 0.05: raise ValueError(f"rendered video has unexpected fps {actual_fps:.3f}")
    duration = float((info.get("format") or {}).get("duration") or 0)
    if duration <= 0: raise ValueError("rendered video duration is invalid")
    return {"duration_seconds": duration, "video_codec": video.get("codec_name"), "audio_codec": audio.get("codec_name"), "width": int(video["width"]), "height": int(video["height"]), "fps": actual_fps}
