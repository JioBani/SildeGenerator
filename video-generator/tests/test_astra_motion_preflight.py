import asyncio
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.engine.harness_loader import HarnessRegistry
from app.engine.harness_preflight import planning_contract, validate_harness_plan
from app.planner import _compose_prompt, compile_source_units, create_plan, deterministic_plan
from app.prompts import load_prompts
from app.scene_contracts import build_production_pack


ROOT = Path(__file__).resolve().parents[2]


def _scene():
    return deterministic_plan("첫 장면입니다.", "평면 그래픽").scenes[0]


def _findings(scene):
    harness = HarnessRegistry(ROOT / "harnesses").load("astra-motion")
    return validate_harness_plan(harness, [scene])


def test_selected_motion_harness_informs_director_before_planning():
    registry = HarnessRegistry(ROOT / "harnesses")
    motion = registry.load("astra-motion")
    contract = planning_contract(motion)
    assert "reaction" in contract["supported_effects"]
    assert "actor_performance" in contract["asset_routes"]
    assert "diagram" in contract["supported_layouts"]
    schema = json.loads((ROOT / "video-generator" / "schemas" / "scene-plan.schema.json").read_text(encoding="utf-8"))
    fields = schema["$defs"]["scene"]["properties"]
    assert set(contract["supported_layouts"]).issubset(fields["layout"]["properties"]["mode"]["enum"])
    assert set(contract["supported_effects"]).issubset(fields["motion"]["items"]["properties"]["kind"]["enum"])
    assert planning_contract(registry.load("classic-slide")) is None

    prompts, _ = load_prompts(motion.root / motion.manifest.prompts_dir)
    scenario = "인물이 창빛을 알아차립니다."
    args = (prompts, scenario, compile_source_units(scenario), False, "editorial_illustration")
    directed = _compose_prompt(*args, harness_planning_contract=contract)
    baseline = _compose_prompt(*args)
    assert "runtime/harness-planning-contract.json" in directed
    assert "moving_illustration" in directed
    assert "actor_performance" in directed
    assert "runtime/harness-planning-contract.json" not in baseline


def test_live_director_receives_selected_harness_contract():
    registry = HarnessRegistry(ROOT / "harnesses")
    contract = planning_contract(registry.load("astra-motion"))
    scenario = "인물이 창빛을 알아차립니다."
    model_call = AsyncMock(return_value=deterministic_plan(scenario, "평면 그래픽"))
    with tempfile.TemporaryDirectory() as temporary, patch("app.planner.plan_with_codex", model_call):
        asyncio.run(create_plan(
            scenario, {"image/style-guide.md": "평면 그래픽"},
            SimpleNamespace(runner_mode="live"), SimpleNamespace(usage=[]), Path(temporary),
            harness_id="astra-motion", harness_planning_contract=contract,
        ))
    assert model_call.await_args.kwargs["harness_planning_contract"] == contract


def test_legacy_supported_motion_still_passes():
    scene = _scene()
    assert _findings(scene) == []


def test_unsupported_motion_is_blocked_before_assets():
    scene = _scene()
    scene.motion[0]["kind"] = "bounce"
    findings = _findings(scene)
    assert "scene-001:unsupported_motion_effect:bounce" in findings
    plan = deterministic_plan("첫 장면입니다.", "평면 그래픽")
    pack = build_production_pack(plan, duration_profile="episode_60", harness_id="astra-motion", upstream_findings=findings)
    assert pack["status"] == "BLOCKED"


def test_independent_actor_reaction_needs_isolation_and_external_review():
    scene = _scene()
    scene.object_states = [{"object_id": "person", "role": "actor", "isolation": "not_needed", "region_hint": None}]
    scene.motion = [{"object_id": "person", "kind": "reaction", "phases": ["notice", "settle"]}]
    findings = _findings(scene)
    assert "scene-001:person:independent_motion_not_isolated" in findings
    assert "scene-001:person:region_hint_required" in findings
    assert "scene-001:person:actor_reaction_requires_external_review" in findings


def test_declared_actor_review_still_needs_real_approval():
    scene = _scene()
    scene.object_states = [{"object_id": "person", "role": "actor", "isolation": "required", "region_hint": [0.2, 0.2, 0.3, 0.5]}]
    scene.motion = [{"object_id": "person", "kind": "reaction", "phases": ["notice", "settle"]}]
    scene.renderer_requirements["experimental_capabilities"] = [{
        "capability": "actor_reaction",
        "contract": {
            "actor_asset_id": "actor-001", "actor_asset_sha256": "a" * 64,
            "rig_sha256": "b" * 64, "render_sha256": "c" * 64,
            "style_version": "style-v1", "event": "IMAGE_APPEARS",
            "gaze_target": "monitor_result", "frame_count": 120,
        },
    }]
    assert _findings(scene) == []
    plan = deterministic_plan("첫 장면입니다.", "평면 그래픽")
    plan.scenes[0] = scene
    pack = build_production_pack(plan, duration_profile="episode_60", harness_id="astra-motion")
    assert pack["status"] == "BLOCKED"
    assert any("human_approval_missing" in item for item in pack["findings"])


def test_unimplemented_layout_and_transition_are_not_silently_replaced():
    scene = _scene()
    scene.layout["mode"] = "reaction"
    scene.transition = "wipe"
    scene.rhythm = "unrecognized"
    findings = _findings(scene)
    assert "scene-001:unsupported_motion_layout" in findings
    assert "scene-001:unsupported_motion_transition" in findings
    assert "scene-001:unsupported_motion_rhythm" in findings
