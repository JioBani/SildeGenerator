from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import httpx
from pydantic import ValidationError

from app.actor_scene import (
    ActorScenePerformance, actor_execution_packet, actor_planning_extension,
    scene_output_schema, validate_actor_proposal,
)
from app.models import ScenePlan
from app.plan_compiler import compile_scene_plan
from app.planner import compile_source_units, create_plan
from app.scene_contracts import build_production_pack
from app.tracking import Tracker
from test_planner import semantic_proposal


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads((ROOT / "video-generator/schemas/scene-plan.schema.json").read_text(encoding="utf-8"))
SCENARIO = "The report arrives. The lamp becomes too bright."
CONTRACT = {"version": "actor-research-planning-0.1", "actor_performance": actor_planning_extension()}
PROMPTS = {
    "director/system.md": "Plan the supplied narrative without rewriting it.",
    "narrative/story-intent.md": "{{SOURCE_UNITS}}",
    "narrative/analyze-sequences.md": "sequences", "narrative/analyze-scene-groups.md": "groups",
    "narrative/analyze-scenes.md": "scenes", "keycut/select-keycuts.md": "keycuts",
    "style/common.md": "{{IMAGE_STYLE}}", "style/presets/editorial-illustration.md": "editorial",
    "continuity/disabled.md": "no continuity generation", "image/system.md": "image",
    "image/build-image-prompt.md": "{{SCENE_JSON}}", "image/style-guide.md": "simple vector design",
}


def performance_fixture(curtain: bool = False) -> dict:
    return {
        "version": "actor-scene-0.1", "canvas": [1000, 820],
        "actors": [{"id": "performer", "asset_id": "astra-vector-standard-01", "origin": [500, 760]}],
        "objects": ([
            {"id": "lamp", "kind": "stimulus", "position": [220, 210]},
            {"id": "handle", "kind": "curtain_handle", "position": [315, 360]},
            {"id": "stop", "kind": "destination", "position": [370, 360]},
        ] if curtain else [
            {"id": "signal", "kind": "stimulus", "position": [725, 245]},
            {"id": "report", "kind": "report", "position": [700, 340]},
        ]),
        "intent": {
            "actor_object_id": "performer", "action": "grasp_pull" if curtain else "grasp_retain",
            "purpose": "Reduce glare by pulling the curtain" if curtain else "Receive and retain the report",
            "stimulus_id": "lamp" if curtain else "signal", "target_id": "handle" if curtain else "report",
            "destination_id": "stop" if curtain else None,
            "side": "left" if curtain else "right", "emotion": "discomfort" if curtain else "pleased",
            "start": .75, "speed": 1, "intensity": .75, "duration": 8,
        },
    }


def proposal_fixture() -> dict:
    proposal = semantic_proposal()
    proposal["continuity_assets"] = []
    for index, scene in enumerate(proposal["sequences"][0]["scene_groups"][0]["scenes"]):
        performance = performance_fixture(bool(index))
        scene["actor_performance"] = performance
        scene["object_states"] = [
            {"object_id": item["id"], "role": "actor" if "asset_id" in item else item["kind"],
             "initial": "rest", "final": "action completed", "isolation": "required",
             "region_hint": None, "depth_band": "foreground"}
            for item in [*performance["actors"], *performance["objects"]]
        ]
        scene["motion"] = [{"object_id": "scene", "kind": "hold", "phases": ["read", "hold"]}]
        scene["renderer_requirements"] = {"preferred": "hyperframes", "capabilities": ["actor_performance"]}
    return proposal


async def offline_director_plan(work: Path, proposal: dict | None = None, contract: dict | None = CONTRACT):
    """Exercise real create_plan/stream parsing/compiler. Transport never opens a socket."""
    proposal = proposal if proposal is not None else proposal_fixture()
    captured = []
    def respond(request: httpx.Request) -> httpx.Response:
        captured.append(json.loads(request.content))
        response = {"id": "offline-actor-fixture", "status": "completed", "usage": {},
                    "output": [{"type": "message", "content": [
                        {"type": "output_text", "text": json.dumps(proposal)},
                    ]}]}
        payload = {"type": "response.completed", "response": response}
        return httpx.Response(200, text="event: response.completed\ndata: " + json.dumps(payload) + "\n\n",
                              headers={"Content-Type": "text/event-stream"})
    client_class = httpx.AsyncClient
    transport = httpx.MockTransport(respond)
    settings = SimpleNamespace(
        runner_mode="live", schemas_dir=ROOT / "video-generator/schemas", codex_model="offline-fixture",
        codex_reasoning_effort="low", codex_fast_mode=False, codex_read_timeout_seconds=10,
        codex_connect_timeout_seconds=2, subscription_base_url="http://offline.invalid",
    )
    tracker = Tracker(work)
    with patch("app.planner.httpx.AsyncClient", side_effect=lambda **kwargs: client_class(transport=transport, **kwargs)):
        plan = await create_plan(SCENARIO, PROMPTS, settings, tracker, work,
                                 harness_id="astra-motion", harness_planning_contract=contract)
    return plan, captured


class ActorSceneTests(unittest.TestCase):
    def test_opt_in_does_not_mutate_default_schema(self):
        original = deepcopy(SCHEMA)
        enhanced = scene_output_schema(SCHEMA, CONTRACT)
        self.assertEqual(scene_output_schema(SCHEMA, None), original)
        self.assertEqual(SCHEMA, original)
        self.assertIn("actor_performance", enhanced["$defs"]["scene"]["required"])
        for name in ("ActorPlacement", "ActorSceneObject", "ActorActionIntent", "ActorScenePerformance"):
            node = enhanced["$defs"][name]
            self.assertFalse(node["additionalProperties"])
            self.assertEqual(set(node["required"]), set(node["properties"]))

    def test_unknown_planning_contract_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unsupported_actor_planning_contract"):
            scene_output_schema(SCHEMA, {"actor_performance": {"version": "other"}})

    def test_approval_code_and_scene_id_cannot_be_model_inputs(self):
        for key, value in [("approved", True), ("mode", "production"), ("scene_id", "scene-001"), ("code", "run()")]:
            candidate = performance_fixture()
            candidate["intent"][key] = value
            with self.subTest(key=key), self.assertRaises(ValidationError):
                ActorScenePerformance.model_validate(candidate)

    def test_wrong_actor_targets_and_duplicate_objects_rejected(self):
        mutations = [lambda p: p["actors"][0].update(asset_id="D"),
                     lambda p: p["intent"].update(target_id="missing"),
                     lambda p: p["objects"][0].update(id="performer"),
                     lambda p: p["objects"][1].update(kind="destination"),
                     lambda p: p["intent"].update(destination_id="signal")]
        for mutate in mutations:
            candidate = performance_fixture()
            mutate(candidate)
            with self.assertRaises(ValidationError):
                ActorScenePerformance.model_validate(candidate)

    def test_finite_numeric_and_settle_bounds(self):
        for value in [True, "1", float("nan"), float("inf"), 0, 3]:
            candidate = performance_fixture()
            candidate["intent"]["speed"] = value
            with self.subTest(value=value), self.assertRaises(ValidationError):
                ActorScenePerformance.model_validate(candidate)
        candidate = performance_fixture()
        candidate["intent"]["duration"] = 4
        with self.assertRaisesRegex(ValidationError, "settle_truncated"):
            ActorScenePerformance.model_validate(candidate)

    def test_scene_state_ids_cannot_drift_from_actor_inventory(self):
        proposal = proposal_fixture()
        proposal["sequences"][0]["scene_groups"][0]["scenes"][0]["object_states"].pop()
        with self.assertRaisesRegex(ValueError, "actor_inventory_not_in_scene"):
            compile_scene_plan(proposal, SCENARIO, compile_source_units(SCENARIO), continuity_enabled=False)

    def test_actor_output_without_opt_in_or_missing_choice_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "not_requested"):
            validate_actor_proposal(proposal_fixture(), None)
        proposal = proposal_fixture()
        del proposal["sequences"][0]["scene_groups"][0]["scenes"][0]["actor_performance"]
        with self.assertRaisesRegex(ValueError, "choice_missing"):
            validate_actor_proposal(proposal, CONTRACT)

    def test_nullable_no_action_does_not_require_actor(self):
        proposal = semantic_proposal()
        for scene in proposal["sequences"][0]["scene_groups"][0]["scenes"]:
            scene["actor_performance"] = None
        validate_actor_proposal(proposal, CONTRACT)

    def test_serialization_and_packet_use_runtime_assigned_id(self):
        plan, _ = compile_scene_plan(proposal_fixture(), SCENARIO, compile_source_units(SCENARIO), continuity_enabled=False)
        restored = ScenePlan.model_validate_json(plan.model_dump_json())
        scene = restored.scenes[1]
        packet = actor_execution_packet(scene.id, scene.actor_performance)
        self.assertEqual(packet["intent"]["scene_id"], "scene-002")
        self.assertEqual(packet["scene"]["objects"][1]["position"], [315, 360])
        self.assertNotIn("mode", packet["intent"])

    def test_production_pack_preserves_execution_but_blocks_fallback(self):
        plan, _ = compile_scene_plan(proposal_fixture(), SCENARIO, compile_source_units(SCENARIO), continuity_enabled=False)
        pack = build_production_pack(plan, duration_profile="episode_60", harness_id="classic-slide",
                                     capability_approvals=[{"approved": True, "capability": "actor_performance"}])
        self.assertEqual(pack["status"], "BLOCKED")
        self.assertIn("scene-001:actor_runtime_not_in_production_harness", pack["findings"])
        self.assertIn("scene-002:actor_action_human_review_required", pack["findings"])
        self.assertEqual(pack["scenes"][1]["actor_execution"]["intent"]["action"], "grasp_pull")


class ActorDirectorHandoffTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_planner_stream_schema_compiler_and_pack(self):
        with tempfile.TemporaryDirectory() as directory:
            plan, captured = await offline_director_plan(Path(directory))
        self.assertEqual(len(captured), 1)
        self.assertIn("actor_performance", captured[0]["text"]["format"]["schema"]["$defs"]["scene"]["properties"])
        self.assertIn("grasp_pull", captured[0]["input"][0]["content"][0]["text"])
        self.assertEqual("".join(scene.narration for scene in plan.scenes), SCENARIO)
        self.assertEqual(plan.scenes[1].actor_performance.intent.action, "grasp_pull")
        self.assertEqual(build_production_pack(plan, duration_profile="episode_60", harness_id="astra-motion")["status"], "BLOCKED")

    async def test_director_cannot_smuggle_actor_into_default_schema(self):
        with tempfile.TemporaryDirectory() as directory, self.assertRaisesRegex(RuntimeError, "actor_performance_not_requested"):
            await offline_director_plan(Path(directory), contract=None)

    async def test_service_stops_before_any_image_or_voice_submission(self):
        from app import main
        from app.engine.harness_loader import HarnessRegistry
        from app.models import RenderRequest

        plan, _ = compile_scene_plan(proposal_fixture(), SCENARIO, compile_source_units(SCENARIO), continuity_enabled=False)
        image = Mock(resume_job=Mock(), submit=AsyncMock(), cancel_job=AsyncMock())
        voice = Mock(resume_job=Mock(), submit=AsyncMock(), cancel_job=AsyncMock())
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(main, "_job_root", return_value=Path(directory)), \
                patch.object(main, "create_plan", AsyncMock(return_value=plan)), \
                patch.object(main, "harness_registry", HarnessRegistry(ROOT / "harnesses")), \
                patch.object(main, "image_broker", image), patch.object(main, "voice_broker", voice):
            result = await main._render(RenderRequest(job_id="00000000-0000-4000-8000-000000000001", scenario=SCENARIO))
            self.assertFalse(result.success)
            self.assertIn("actor_runtime_not_in_production_harness", result.message)
            self.assertEqual(result.production_pack["status"], "BLOCKED")
            self.assertTrue((Path(directory) / "work/scene-production-pack.json").is_file())
            self.assertEqual(result.production_pack["scenes"][0]["actor_execution"]["intent"]["action"], "grasp_retain")
        image.submit.assert_not_called()
        voice.submit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
