"""Offline service-planner handoff fixture, explicitly NOT a live director evaluation."""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "video-generator"), str(ROOT / "video-generator/tests")]

from app.scene_contracts import build_production_pack
from test_actor_scene import CONTRACT, SCENARIO, offline_director_plan, proposal_fixture


async def run(output: Path) -> None:
    if output.exists():
        raise ValueError("Choose a new output directory; evidence is not overwritten")
    output.mkdir(parents=True)
    work = output / "work"
    work.mkdir()
    plan, requests = await offline_director_plan(work)
    pack = build_production_pack(plan, duration_profile="episode_60", harness_id="astra-motion")
    if len(requests) != 1 or pack["status"] != "BLOCKED":
        raise AssertionError("Expected one offline model fixture and a production admission block")
    artifacts = {
        "scene-plan.json": plan.model_dump(mode="json"),
        "scene-production-pack.json": pack,
        "planning-contract.json": CONTRACT,
        "model-proposal-fixture.json": proposal_fixture(),
        "requested-schema.json": requests[0]["text"]["format"]["schema"],
        "execution-packets.json": [scene["actor_execution"] for scene in pack["scenes"]],
    }
    for name, value in artifacts.items():
        (output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    sources = ["video-generator/app/actor_scene.py", "video-generator/app/models.py",
               "video-generator/app/planner.py", "video-generator/app/plan_compiler.py",
               "video-generator/app/scene_contracts.py", "video-generator/tests/test_actor_scene.py",
               "scripts/smoke_actor_planner.py"]
    hash_file = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    report = {
        "version": "actor-planner-handoff-0.1", "transport": "httpx.MockTransport; no network",
        "director_output_origin": "authored_test_fixture_not_model_judgment",
        "scenario": SCENARIO, "narration_preserved": "".join(s.narration for s in plan.scenes) == SCENARIO,
        "offline_response_count": len(requests), "live_model_calls": 0, "image_calls": 0, "voice_calls": 0,
        "production_status": pack["status"], "human_review": "PENDING",
        "artifacts": {name: hash_file(output / name) for name in artifacts},
        "sources": {name: hash_file(ROOT / name) for name in sources},
    }
    (output / "receipt.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(output), "scenes": len(plan.scenes), "production_status": pack["status"], "live_calls": 0}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    asyncio.run(run(parser.parse_args().output.resolve()))
