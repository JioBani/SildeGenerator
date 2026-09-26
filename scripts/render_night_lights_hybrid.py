"""Render a new-script, authored three-route hybrid transfer probe."""
from __future__ import annotations

import asyncio
import argparse
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
from app.rendered_review import file_sha256, inspect_render
from app.source_media import source_brief


def design():
    return {
        "version": "film-design-0.3",
        "concept_id": "night_lights_observer",
        "central_idea": "An observer's night question becomes a grounded satellite procedure and a dated map, then returns to the observer.",
        "cinematic_language": "Two distinct rooftop shots of the same rust-jacketed observer. Restrained camera push or pull; no fabricated actor animation.",
        "diagram_language": "Three editable, sequentially revealed stages with ample reading hold. Amber, cyan and coral echo the night-city palette.",
        "source_treatment": "Show NASA's complete 2016 composite with persistent date and attribution; never imply one-night photography or star visibility measurement.",
        "palette": {
            "background": "#18201f", "text": "#f2f0e5", "secondary_text": "#e0ded2",
            "surface": "#333e3b", "line": "#d49a55",
            "accents": ["#d49a55", "#6bc3c0", "#ef8f8b"],
        },
        "typography": {"font": "Noto Sans CJK KR", "title_px": 34,
                       "caption_px": 36, "caption_margin_y": 48},
        "line_width": 3, "snapshot_layout": "columns", "comparison_layout": "rows",
        "type_treatment": "documentary",
    }


def diagram():
    return {
        "title": "밤의 빛은 어떻게 지도가 될까",
        "grammar": "step_sequence", "comparison_scale_max": None,
        "snapshot_pair": None, "spatial_map": None,
        "nodes": [
            {"id": "observe", "label": "야간 관측", "before": "관측 전", "after": "빛 기록",
             "x": .2, "y": .4, "color": "#d49a55", "reveal_at": 0, "change_at": .12,
             "quantity": None, "unit": None, "source_quote": None},
            {"id": "select", "label": "구름 없는 날", "before": "선택 전", "after": "관측 선택",
             "x": .5, "y": .4, "color": "#6bc3c0", "reveal_at": .22, "change_at": .42,
             "quantity": None, "unit": None, "source_quote": None},
            {"id": "combine", "label": "지도 합성", "before": "합성 전", "after": "한 장의 지도",
             "x": .8, "y": .4, "color": "#ef8f8b", "reveal_at": .46, "change_at": .72,
             "quantity": None, "unit": None, "source_quote": None},
        ],
        "edges": [
            {"source": "observe", "target": "select", "label": "선택", "start_at": .24, "end_at": .36},
            {"source": "select", "target": "combine", "label": "합성", "start_at": .49, "end_at": .65},
        ],
    }


def direction(scene, index):
    route = scene["route"]
    return {
        "version": "narrative-direction-0.1", "mode": "observational",
        "subject_id": "rooftop_observer" if route == "cinematic" else route,
        "subject_description": "Same rooftop observer" if route == "cinematic" else "Satellite data or its explanation",
        "goal": "Understand what the city lights look like from above",
        "stakes": "Do not confuse lived experience with the satellite evidence",
        "beat": ("setup", "explanation", "evidence", "resolution")[index],
        "visible_action": "Looks toward city lights" if index == 0 else "Looks up again" if index == 3 else "Shows the stated information",
        "state_before": "new perspective" if index == 3 else "question",
        "state_after": "reflection" if index == 3 else "new perspective",
        "new_information": scene["narration"], "shot_size": "medium", "viewpoint": "observer",
        "focal_target": "Observer" if route == "cinematic" else "Procedure or registered map",
        "cut_reason": "Move from personal experience to process and evidence, then back",
        "cause_scene_number": None, "choices": [], "continuity_note": None,
        "repeat_of_scene_number": 1 if index == 3 else None,
        "repeat_reason": "Return to the observer after NASA evidence with a new frame and understanding" if index == 3 else None,
    }


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", nargs="?", type=Path,
                        default=ROOT / "output/night-lights-hybrid-transfer-v1")
    args = parser.parse_args()
    fixture = ROOT / "experiments/night-lights-transfer-v1"
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(output)
    voice = json.loads((fixture / "voice-v2/manifest.json").read_text(encoding="utf-8"))
    brief = json.loads((fixture / "scene-brief.json").read_text(encoding="utf-8"))
    measured = {row["id"]: row for row in voice["scenes"]}
    assert [s["id"] for s in brief["scenes"]] == list(measured)
    assert len(source_brief(fixture / "source-media")) == 1
    output.mkdir(parents=True)
    work = output / "work"
    (work / "render-segments").mkdir(parents=True)
    (output / "delivery").mkdir()
    loaded = HarnessRegistry(ROOT / "harnesses").load("hybrid-story")
    assert loaded.snapshot.version == "0.18.1"
    settings = SimpleNamespace(width=1280, height=720, fps=24, crossfade_seconds=0,
                               ffmpeg_preset="fast", subtitles_enabled=True)
    shared = design()
    scenes = []
    for index, item in enumerate(brief["scenes"]):
        route = item["route"]
        hybrid = {"version": "hybrid-scene-0.6", "route": route,
                  "reason": item["purpose"], "diagram": diagram() if route == "diagram" else None,
                  "source_id": item.get("source_id"), "composition": None, "design": shared}
        image = fixture / item["image"] if route == "cinematic" else None
        layout = {"hybrid": hybrid, "direction": direction(item, index),
                  "subtitle_cues": measured[item["id"]]["subtitle_cues"],
                  "camera": {"mode": "push" if index == 0 else "pull", "focus": [.68, .48], "strength": .035}
                  if route == "cinematic" else {"mode": "hold"}}
        scene = SimpleNamespace(id=item["id"], narration=item["narration"],
            duration_seconds=measured[item["id"]]["duration"],
            audio_path=str(fixture / "voice-v2" / measured[item["id"]]["file"]),
            image_path=str(image) if image else None, transition="cut", layout=layout)
        if route != "cinematic":
            prepared = work / f"{scene.id}.png"
            prepare_local_asset(scene, loaded, fixture / "source-media", prepared, settings)
            scene.image_path = str(prepared)
        scenes.append(scene)
    findings = validate_harness_plan(loaded, scenes)
    if findings:
        raise ValueError(findings)
    config = {**loaded.config, "subtitle_size": 40, "subtitle_margin_vertical": 75,
              "crossfade_seconds": 0}

    async def operation(name, **metadata):
        context = HarnessContext("night-lights-transfer", output, settings, ProcessRunner(),
            ArtifactStore(output), LocalLeaseProvider(),
            metadata={"operation": name, "config": config, **metadata})
        await GraphExecutor(loaded.snapshot).execute(await loaded.instance.build_pipeline(context), context)

    segment = work / "render-segments/segment.mp4"
    await operation("render_segment", scenes=scenes, subtitles=work / "captions.ass", output=segment)
    await operation("audio_assembly", scenes=scenes, work=work)
    final = output / "delivery/night-lights.mp4"
    await operation("video_assembly", segments=[segment], audio=work / "narration.m4a", output=final)
    inspection = inspect_render(final, scenes, width=1280, height=720, fps=24)
    receipt = {
        "status": "TECHNICAL_REVIEW_ONLY", "goal_status": "GOAL_NOT_MET",
        "scope": "New-script authored transfer film; not autonomous director, acting, or audience-understanding approval",
        "harness": loaded.snapshot.as_dict(), "render_config": config,
        "routes": [item["route"] for item in brief["scenes"]],
        "source_catalog": source_brief(fixture / "source-media"),
        "scenes": [{"id": scene.id, "narration": scene.narration,
                    "duration_seconds": scene.duration_seconds,
                    "image_sha256": file_sha256(Path(scene.image_path)),
                    "audio_sha256": file_sha256(Path(scene.audio_path)),
                    "layout": scene.layout} for scene in scenes],
        "inspection": inspection, "paid_api_calls": 0, "built_in_image_calls": 2,
        "human_approved": False,
    }
    (output / "receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(inspection, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
