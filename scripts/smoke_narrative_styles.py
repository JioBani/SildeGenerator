"""Render real generated style assets through the candidate harness; no model calls."""
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
from app.harness_sdk.direction import evaluate_direction
from app.rendered_review import file_sha256, inspect_render, probe_video


STYLES = {"cinematic_realism": "cinematic-realism-v1", "animation_3d": "animation-3d-v1",
          "disney_animation": "disney-animation-v1", "dystopian": "dystopian-v1"}


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--voice-work", type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    voice = args.voice_work.resolve()
    line = json.loads((voice / "voice-input.json").read_text(encoding="utf-8"))[0]
    audio = voice / "scene-001.wav"
    duration = float(probe_video(audio)["format"]["duration"])
    loaded = HarnessRegistry(ROOT / "harnesses").load("narrative-slide")
    settings = SimpleNamespace(width=1280, height=720, fps=24, crossfade_seconds=0,
                               ffmpeg_preset="fast", subtitles_enabled=True)
    receipts = []
    for style, image in STYLES.items():
        work = out / style / "work"
        (work / "render-segments").mkdir(parents=True)
        delivery = out / style / "delivery"
        delivery.mkdir()
        scene = SimpleNamespace(**line, duration_seconds=duration, audio_path=str(audio),
            image_path=str(ROOT / "web/public/style-previews" / (image + ".png")),
            transition="cut", layout={"camera": {"mode": "push", "focus": [.5, .5], "strength": .035},
                "direction": {"version": "narrative-direction-0.1", "mode": "observational",
                "subject_id": "expedition-leader", "subject_description": "Original leader wearing a red scarf",
                "goal": "Help the stranded companion", "stakes": "The available escape route is closing",
                "beat": "pressure", "visible_action": "Looks back toward the companion",
                "state_before": "holding-boat", "state_after": "holding-boat",
                "new_information": "The companion is still separated from the boat", "shot_size": "medium",
                "viewpoint": "observer", "focal_target": "leader and companion", "cut_reason": "Establish the problem",
                "cause_scene_number": None, "choices": [], "continuity_note": None,
                "repeat_of_scene_number": None, "repeat_reason": None}})
        findings = validate_harness_plan(loaded, [scene])
        if findings:
            raise ValueError(findings)
        config = {**loaded.config, "subtitle_size": 44, "subtitle_margin_vertical": 100, "crossfade_seconds": 0}
        async def operation(name, **metadata):
            context = HarnessContext("narrative-style-smoke", out / style, settings, ProcessRunner(),
                ArtifactStore(out / style), LocalLeaseProvider(),
                metadata={"operation": name, "config": config, **metadata})
            graph = await loaded.instance.build_pipeline(context)
            await GraphExecutor(loaded.snapshot).execute(graph, context)
        segment = work / "render-segments/segment.mp4"
        await operation("render_segment", scenes=[scene], subtitles=work / "captions.ass", output=segment)
        await operation("audio_assembly", scenes=[scene], work=work)
        video = delivery / "preview.mp4"
        await operation("video_assembly", segments=[segment], audio=work / "narration.m4a", output=video)
        inspection = inspect_render(video, [scene], width=1280, height=720, fps=24)
        receipt = {"style": style, "harness": loaded.snapshot.as_dict(), "render_config": config,
            "settings": vars(settings), "inspection": inspection,
            "direction": evaluate_direction([scene]), "image_sha256": file_sha256(Path(scene.image_path)),
            "voice_sha256": file_sha256(audio), "paid_api_calls": 0,
            "scope": "One authored fictional style shot. Not a held-out film, live planner call or site E2E.",
            "voice_provider": "Windows SAPI offline", "file": str(video.relative_to(out))}
        (work / "receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
        receipts.append(receipt)
        print(style, inspection["status"], flush=True)
    if len({r["image_sha256"] for r in receipts}) != 4:
        raise ValueError("styles_reused_same_image")
    (out / "receipts.json").write_text(json.dumps(receipts, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
