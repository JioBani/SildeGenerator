"""Real hybrid graph delivery with local voice, generated still and registered data."""
from __future__ import annotations
import argparse
import asyncio
import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "video-generator"))
from app.engine.graph_executor import GraphExecutor, LocalLeaseProvider
from app.engine.harness_loader import HarnessRegistry
from app.engine.harness_preflight import validate_harness_plan
from app.engine.process_runner import ProcessRunner
from app.harness_sdk.artifacts import ArtifactStore
from app.harness_sdk.context import HarnessContext
from app.hybrid_assets import prepare_local_asset
from app.rendered_review import file_sha256, inspect_render, probe_video


def diagram():
    return {"title": "길이 막히면, 구조도 늦어진다", "grammar": "cause_change_result", "comparison_scale_max": None,
        "nodes": [{"id": id, "label": label, "before": before, "after": after, "x": x, "y": .4,
                   "color": color, "reveal_at": 0, "change_at": at, "quantity": None, "unit": None}
                  for id, label, before, after, x, color, at in [
                    ("ice", "얼음", "열린 길", "막힌 길", .2, "#427c91", .15),
                    ("travel", "이동", "진행", "지연", .5, "#d76952", .45),
                    ("rescue", "구조", "접근", "기다림", .8, "#398066", .8)]],
        "edges": [{"source": "ice", "target": "travel", "label": "길 차단", "start_at": .2, "end_at": .4},
                  {"source": "travel", "target": "rescue", "label": "도착 지연", "start_at": .5, "end_at": .75}]}


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    work = out / "work"
    (work / "render-segments").mkdir(parents=True)
    (out / "delivery").mkdir()
    fixtures = ROOT / "experiments/hybrid-story-v1"
    lines = json.loads((fixtures / "voice-input.json").read_text(encoding="utf-8"))
    loaded = HarnessRegistry(ROOT / "harnesses").load("hybrid-story")
    settings = SimpleNamespace(width=1280, height=720, fps=24, crossfade_seconds=0,
                               ffmpeg_preset="fast", subtitles_enabled=True)
    scenes = []
    for index, (line, route) in enumerate(zip(lines, ["cinematic", "diagram", "source", "cinematic"]), 1):
        audio = fixtures / (line["id"] + ".wav")
        direction = {"version": "narrative-direction-0.1", "mode": "observational",
            "subject_id": "expedition" if route == "cinematic" else route,
            "subject_description": "Fictional expedition" if route == "cinematic" else "Relationship or modern observation",
            "goal": "Understand the situation", "stakes": "Separate experience, explanation and evidence",
            "beat": "setup" if index == 1 else "explanation" if route == "diagram" else "evidence" if route == "source" else "resolution",
            "visible_action": "Looks back at the companion" if route == "cinematic" else "Shows the declared relationship",
            "state_before": "visible", "state_after": "visible", "new_information": line["narration"],
            "shot_size": "medium", "viewpoint": "observer", "focal_target": "Meaningful subject",
            "cut_reason": "Shift from experience to explanation to authentic observation",
            "cause_scene_number": None, "choices": [], "continuity_note": None,
            "repeat_of_scene_number": 1 if index == 4 else None,
            "repeat_reason": "Return to the same dilemma after separating explanation and evidence" if index == 4 else None}
        scene = SimpleNamespace(**line, duration_seconds=float(probe_video(audio)["format"]["duration"]),
            audio_path=str(audio), image_path=str(ROOT / "web/public/style-previews/cinematic-realism-v1.png"),
            transition="cut", layout={"camera": {"mode": "hold"}, "direction": direction,
                "hybrid": {"version": "hybrid-scene-0.1", "route": route,
                    "reason": "Show emotion" if route == "cinematic" else "Explain causality" if route == "diagram" else "Show a dated real observation",
                    "diagram": diagram() if route == "diagram" else None,
                    "source_id": "antarctic-sea-ice-2016" if route == "source" else None}})
        if route != "cinematic":
            path = work / f"{scene.id}.png"
            prepare_local_asset(scene, loaded, fixtures / "source-media", path, settings)
            scene.image_path = str(path)
        scenes.append(scene)
    findings = validate_harness_plan(loaded, scenes)
    if findings:
        raise ValueError(findings)
    config = {**loaded.config, "subtitle_size": 40, "subtitle_margin_vertical": 75, "crossfade_seconds": 0}
    async def operation(name, **metadata):
        context = HarnessContext("hybrid-smoke", out, settings, ProcessRunner(), ArtifactStore(out),
            LocalLeaseProvider(), metadata={"operation": name, "config": config, **metadata})
        await GraphExecutor(loaded.snapshot).execute(await loaded.instance.build_pipeline(context), context)
    segment = work / "render-segments/segment.mp4"
    await operation("render_segment", scenes=scenes, subtitles=work / "captions.ass", output=segment)
    await operation("audio_assembly", scenes=scenes, work=work)
    video = out / "delivery/hybrid.mp4"
    await operation("video_assembly", segments=[segment], audio=work / "narration.m4a", output=video)
    inspection = inspect_render(video, scenes, width=1280, height=720, fps=24)
    receipt = {"harness": loaded.snapshot.as_dict(), "render_config": config, "inspection": inspection,
        "routes": [s.layout["hybrid"]["route"] for s in scenes],
        "scenes": [{"id": s.id, "layout": s.layout, "narration": s.narration, "duration_seconds": s.duration_seconds,
                    "image_sha256": file_sha256(Path(s.image_path)), "audio_sha256": file_sha256(Path(s.audio_path))} for s in scenes],
        "scope": "Authored mixed-route demonstration, not historical reconstruction or live autonomous director E2E",
        "paid_api_calls": 0, "image_calls_this_run": 0, "human_approved": False}
    (out / "receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(inspection, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
