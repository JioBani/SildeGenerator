"""Narration-safe background music for the opt-in slide v0.5 path."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from .engine.process_runner import ProcessRunner


PRESETS = {
    "warm-story": (220.00, 277.18, 329.63),
    "quiet-reflection": (174.61, 220.00, 261.63),
    "fantasy-night": (146.83, 220.00, 293.66),
}


def verified_upload(selection: dict[str, Any], data_dir: Path) -> Path:
    path = Path(selection["path"]).resolve()
    root = (data_dir / "music-uploads").resolve()
    if root not in path.parents or not path.is_file() or path.stat().st_size > 10 * 1024 * 1024:
        raise ValueError("Uploaded music is outside the managed store or missing")
    if hashlib.sha256(path.read_bytes()).hexdigest() != selection["sha256"]:
        raise ValueError("Uploaded music content changed since job creation")
    return path


async def prepare_music(selection: dict[str, Any], data_dir: Path, work: Path,
                        duration: float, process: ProcessRunner) -> tuple[Path, dict[str, Any]]:
    if selection["mode"] == "upload":
        source = verified_upload(selection, data_dir)
        report = {"mode": "upload", "uploadId": selection["uploadId"], "sha256": selection["sha256"]}
    else:
        preset = selection.get("preset")
        if preset not in PRESETS:
            raise ValueError("Unknown automatic music preset")
        frequencies = PRESETS[preset]
        expression = "+".join(f"{amplitude:.3f}*sin(2*PI*{frequency:.2f}*t)"
                              for amplitude, frequency in zip((.11, .055, .035), frequencies))
        source = work / "automatic-music.wav"
        await process.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
                           f"aevalsrc={expression}:s=48000:d={duration:.3f}",
                           "-af", "lowpass=f=1800,aecho=0.8:0.45:70:0.12", "-c:a", "pcm_s16le", str(source)])
        report = {"mode": "auto", "preset": preset, "source": "system-generated"}
    probe = work / "music-probe.json"
    await process.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json",
                       str(source), "-o", str(probe)])
    metadata = json.loads(probe.read_text(encoding="utf-8"))
    if not any(stream.get("codec_type") == "audio" for stream in metadata.get("streams", [])):
        raise ValueError("Background music has no decodable audio stream")
    return source, report


async def mix_music(video: Path, selection: dict[str, Any], data_dir: Path,
                    work: Path, duration: float, process: ProcessRunner) -> dict[str, Any]:
    if selection.get("mode") == "none":
        return {"mode": "none", "applied": False}
    source, report = await prepare_music(selection, data_dir, work, duration, process)
    fade = min(1.2, max(.1, duration / 3))
    mix = (
        "[0:a]aresample=48000,volume=1.0[narration];"
        f"[1:a]aresample=48000,atrim=0:{duration:.3f},"
        f"afade=t=in:st=0:d={fade:.3f},afade=t=out:st={max(0, duration - fade):.3f}:d={fade:.3f},"
        "volume=0.12[music];"
        "[narration][music]amix=inputs=2:duration=first:dropout_transition=0,alimiter=limit=0.95[audio]"
    )
    mixed = work / "music-mixed.mp4"
    await process.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(video),
                       "-stream_loop", "-1", "-i", str(source), "-filter_complex", mix,
                       "-map", "0:v:0", "-map", "[audio]", "-c:v", "copy", "-c:a", "aac",
                       "-b:a", "160k", "-t", f"{duration:.3f}", "-movflags", "+faststart", str(mixed)])
    os.replace(mixed, video)
    return {**report, "applied": True, "music_volume": .12, "fade_seconds": fade}
