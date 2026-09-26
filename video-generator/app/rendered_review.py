"""Deterministic observations from real output pixels, separate from story critique."""
from __future__ import annotations

import hashlib
import json
import math
import statistics
import subprocess
from pathlib import Path


VERSION = "rendered-observations-0.2"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def probe_video(path: Path) -> dict:
    return json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path),
    ], timeout=30))


def sample_rgb(path: Path, seconds: float) -> bytes:
    pixels = subprocess.check_output([
        "ffmpeg", "-v", "error", "-ss", f"{seconds:.6f}", "-i", str(path),
        "-frames:v", "1", "-vf", "scale=64:36:flags=area", "-pix_fmt", "rgb24",
        "-f", "rawvideo", "pipe:1",
    ], timeout=30)
    if len(pixels) != 64 * 36 * 3:
        raise ValueError("sample_frame_missing")
    return pixels


def spatial_variation(pixels: bytes) -> float:
    """Measure content, not differences between RGB channels of a flat color."""
    return max(statistics.pstdev(pixels[channel::3]) for channel in range(3))


def inspect_for_contract(path, scenes, contract, *, width, height, fps):
    requested = (contract or {}).get("rendered_observation_gate")
    if requested is None:
        return None
    if requested != VERSION:
        raise ValueError("unsupported_rendered_observation_gate")
    return inspect_render(path, scenes, width=width, height=height, fps=fps)


def inspect_render(path: Path, scenes, *, width: int, height: int, fps: float) -> dict:
    durations = [float(scene.duration_seconds) for scene in scenes]
    if not durations or any(not math.isfinite(value) or value <= 0 for value in durations):
        raise ValueError("positive_measured_scene_durations_required")
    metadata = probe_video(path)
    video = next((s for s in metadata["streams"] if s["codec_type"] == "video"), None)
    audio = next((s for s in metadata["streams"] if s["codec_type"] == "audio"), None)
    findings = []
    if not video:
        raise ValueError("video_stream_missing")
    if not audio:
        findings.append("audio_stream_missing")
    if (video["width"], video["height"]) != (width, height):
        findings.append("dimensions_mismatch")
    numerator, denominator = map(float, video["avg_frame_rate"].split("/"))
    if denominator <= 0 or abs(numerator / denominator - fps) > .05:
        findings.append("fps_mismatch")
    duration = float(metadata["format"]["duration"])
    if abs(duration - sum(durations)) > max(.15, 2 / fps):
        findings.append("narration_timeline_mismatch")
    observations, middle_frames = [], []
    cursor = 0.0
    for index, (scene, seconds) in enumerate(zip(scenes, durations), 1):
        samples = []
        raw = []
        for fraction in (.2, .5, .8):
            time = cursor + seconds * fraction
            try:
                pixels = sample_rgb(path, time)
            except (ValueError, subprocess.SubprocessError):
                findings.append(f"{scene.id}:sample_missing:{fraction}")
                continue
            raw.append(pixels)
            samples.append({"time_seconds": round(time, 6), "pixel_sha256": hashlib.sha256(pixels).hexdigest(),
                            "mean": statistics.mean(pixels), "stddev": statistics.pstdev(pixels)})
        # A subtitle can make a blank frame non-uniform. Inspect the upper 75% too.
        if raw and all(spatial_variation(p[:64 * 27 * 3]) < 1.5 for p in raw):
            findings.append(f"{scene.id}:near_uniform_picture")
        mid = raw[1] if len(raw) == 3 else None
        direction = (getattr(scene, "layout", {}) or {}).get("direction", {})
        if mid is not None:
            for prior_index, prior in middle_frames:
                distance = sum(abs(a - b) for a, b in zip(mid, prior)) / (len(mid) * 255)
                if distance < .006 and direction.get("repeat_of_scene_number") != prior_index:
                    findings.append(f"{scene.id}:near_duplicate_picture:{prior_index}")
            middle_frames.append((index, mid))
        observation = {"scene_id": scene.id, "samples": samples}
        hybrid = (getattr(scene, "layout", {}) or {}).get("hybrid", {})
        diagram = hybrid.get("diagram") or {}
        expects_change = diagram.get("snapshot_pair") or diagram.get("edges") or any(
            node.get("before") != node.get("after") or node.get("reveal_at", 0) > .1
            for node in diagram.get("nodes", []))
        if hybrid.get("route") == "diagram" and expects_change:
            try:
                start = sample_rgb(path, cursor + seconds * .05)[:64 * 27 * 3]
                end = sample_rgb(path, cursor + seconds * .95)[:64 * 27 * 3]
                delta = sum(abs(a - b) for a, b in zip(start, end)) / (len(start) * 255)
                observation["diagram_picture_change"] = delta
                # This detects frozen output, not correctness of the relationship.
                if delta < .0005:
                    findings.append(f"{scene.id}:declared_diagram_change_not_visible")
            except (ValueError, subprocess.SubprocessError):
                findings.append(f"{scene.id}:diagram_change_sample_missing")
        observations.append(observation)
        cursor += seconds
    contract = [{"id": s.id, "duration_seconds": s.duration_seconds,
                 "narration": s.narration, "layout": s.layout} for s in scenes]
    return {"version": VERSION, "status": "REVISE" if findings else "PIXEL_CHECKS_PASS",
            "video_sha256": file_sha256(path), "findings": findings, "samples": observations,
            "plan_sha256": hashlib.sha256(json.dumps(contract, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
            "duration_seconds": duration,
            "not_evaluated": ["emotion", "factual_accuracy", "semantic_alignment", "ocr", "articulated_acting"],
            "human_approval": None}
