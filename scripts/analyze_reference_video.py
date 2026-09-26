from __future__ import annotations

import json
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image


def run(*command: str) -> str:
    result = subprocess.run(command, check=True, capture_output=True, text=True, encoding="utf-8")
    return result.stdout


def probe(video: Path) -> dict:
    return json.loads(run(
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration:stream=codec_name,width,height,r_frame_rate",
        "-of", "json", str(video),
    ))


def parse_srt(path: Path | None) -> list[dict]:
    if path is None or not path.is_file():
        return []
    text = path.read_text(encoding="utf-8-sig")
    blocks = re.split(r"\n\s*\n", text.strip())
    utterances = []
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        timing_index = next((index for index, line in enumerate(lines) if "-->" in line), None)
        if timing_index is None:
            continue
        start_text, end_text = [value.strip() for value in lines[timing_index].split("-->", 1)]

        def seconds(value: str) -> float:
            hours, minutes, rest = value.replace(",", ".").split(":")
            return int(hours) * 3600 + int(minutes) * 60 + float(rest)

        utterances.append({
            "start": seconds(start_text),
            "end": seconds(end_text),
            "text": " ".join(lines[timing_index + 1:]),
        })
    return utterances


def frame_metrics(path: Path, previous: np.ndarray | None) -> tuple[dict, np.ndarray]:
    with Image.open(path) as image:
        rgb_image = image.convert("RGB")
        pixels = np.asarray(rgb_image, dtype=np.float32) / 255.0
        reduced = np.asarray(rgb_image.resize((160, 90)), dtype=np.float32) / 255.0
        quantized = rgb_image.resize((160, 90)).quantize(colors=8, method=Image.Quantize.MEDIANCUT).convert("RGB")
        colors = quantized.getcolors(maxcolors=160 * 90) or []
    maximum = pixels.max(axis=2)
    minimum = pixels.min(axis=2)
    saturation = np.zeros_like(maximum)
    np.divide(maximum - minimum, maximum, out=saturation, where=maximum > 1e-6)
    gray = pixels.mean(axis=2)
    gradient_x = np.abs(np.diff(gray, axis=1)).mean()
    gradient_y = np.abs(np.diff(gray, axis=0)).mean()
    difference = 0.0 if previous is None else float(np.abs(reduced - previous).mean())
    palette = [
        {"rgb": list(color), "share": round(count / (160 * 90), 4)}
        for count, color in sorted(colors, reverse=True)[:8]
    ]
    return ({
        "mean_rgb": [round(float(value), 4) for value in pixels.mean(axis=(0, 1))],
        "mean_luminance": round(float(gray.mean()), 4),
        "mean_saturation": round(float(saturation.mean()), 4),
        "edge_density": round(float(gradient_x + gradient_y), 4),
        "change_from_previous": round(difference, 5),
        "palette": palette,
    }, reduced)


def main() -> None:
    if len(sys.argv) not in (3, 4):
        raise SystemExit("usage: analyze_reference_video.py <video.mp4> <output-directory> [subtitles.srt]")
    video = Path(sys.argv[1]).resolve()
    output = Path(sys.argv[2]).resolve()
    subtitles = Path(sys.argv[3]).resolve() if len(sys.argv) == 4 else None
    frames = output / "frames-1fps"
    if frames.exists():
        shutil.rmtree(frames)
    frames.mkdir(parents=True, exist_ok=True)
    run("ffmpeg", "-v", "error", "-y", "-i", str(video), "-vf", "fps=1,scale=640:-2", str(frames / "frame-%05d.png"))

    rows = []
    previous = None
    for index, frame in enumerate(sorted(frames.glob("frame-*.png"))):
        metrics, previous = frame_metrics(frame, previous)
        rows.append({"second": index, "frame": frame.name, **metrics})

    changes = np.asarray([row["change_from_previous"] for row in rows[1:]], dtype=np.float32)
    threshold = float(np.percentile(changes, 82)) if len(changes) else math.inf
    boundaries = [0]
    for row in rows[1:]:
        if row["change_from_previous"] >= threshold and row["second"] - boundaries[-1] >= 2:
            boundaries.append(row["second"])
    duration = float(probe(video)["format"]["duration"])
    if not boundaries or duration - boundaries[-1] >= 1:
        boundaries.append(round(duration, 3))
    segments = [
        {"start": boundaries[index], "end": boundaries[index + 1], "duration": round(boundaries[index + 1] - boundaries[index], 3)}
        for index in range(len(boundaries) - 1)
    ]

    utterances = parse_srt(subtitles)
    for segment in segments:
        segment["utterances"] = [
            utterance for utterance in utterances
            if utterance["start"] < segment["end"] and utterance["end"] > segment["start"]
        ]
    global_palette: dict[tuple[int, int, int], float] = {}
    for row in rows:
        for color in row["palette"][:4]:
            key = tuple(color["rgb"])
            global_palette[key] = global_palette.get(key, 0.0) + color["share"]
    palette = [
        {"rgb": list(color), "weight": round(weight / max(1, len(rows)), 4)}
        for color, weight in sorted(global_palette.items(), key=lambda item: item[1], reverse=True)[:16]
    ]
    result = {
        "version": "astra-reference-analysis-1.0",
        "source": video.name,
        "probe": probe(video),
        "sample_rate_fps": 1,
        "scene_change_threshold": round(threshold, 5) if math.isfinite(threshold) else None,
        "global_palette": palette,
        "per_second": rows,
        "segments": segments,
        "utterances": utterances,
    }
    (output / "analysis.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "duration": duration,
        "secondsAnalyzed": len(rows),
        "segmentCandidates": len(segments),
        "analysis": str(output / "analysis.json"),
    }))


if __name__ == "__main__":
    main()
