from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import httpx

from app.harness_sdk.direction import direction_output_schema, direction_planning_extension, evaluate_direction
from app.image_prompts import scene_image_prompt
from app.planner import create_plan, deterministic_plan
from app.prompts import load_prompts
from app.tracking import Tracker
from test_planner import semantic_proposal

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = {"narrative_direction": direction_planning_extension()}


def shot(**changes):
    result = {
        "version": "narrative-direction-0.1", "mode": "observational", "subject_id": "traveller",
        "subject_description": "Traveller in the same red coat", "goal": "Find shelter",
        "stakes": "Cold exposure", "beat": "setup", "visible_action": "Looks toward a lit window",
        "state_before": "outside", "state_after": "outside", "new_information": "A room has light",
        "shot_size": "wide", "viewpoint": "observer", "focal_target": "traveller and window",
        "cut_reason": "Establish the reachable destination", "cause_scene_number": None,
        "choices": [], "continuity_note": None, "repeat_of_scene_number": None, "repeat_reason": None,
    }
    return {**result, **changes}


def scenes(*directions):
    return [SimpleNamespace(id=f"scene-{i:03d}", layout={"direction": value})
            for i, value in enumerate(directions, 1)]


class DirectionChecks(unittest.TestCase):
    def test_unmotivated_duplicate_is_detected_but_meaningful_callback_is_allowed(self):
        self.assertIn("scene-002:unmotivated_repeated_shot:1", evaluate_direction(scenes(shot(), shot()))["findings"])
        callback = shot(repeat_of_scene_number=1, repeat_reason="The same light now indicates a rescue signal",
                        new_information="The window light is a coded signal")
        self.assertEqual([], evaluate_direction(scenes(shot(), callback))["findings"])

    def test_future_cause_and_state_jump_require_repair(self):
        review = evaluate_direction(scenes(shot(), shot(beat="reaction", cause_scene_number=3,
                    state_before="indoors", visible_action="Turns toward a sound")))
        self.assertIn("scene-002:cause_not_available", review["findings"])
        self.assertIn("scene-002:unexplained_subject_state_change", review["findings"])

    def test_character_choice_requires_competing_costs_and_a_later_result(self):
        decision = shot(mode="character_story", beat="choice", choices=[
            {"action": "Continue alone", "cost": "Risk exposure"},
            {"action": "Return for companion", "cost": "Lose the shelter before dark"}])
        self.assertIn("traveller:choice_has_no_later_consequence:1", evaluate_direction(scenes(decision))["findings"])
        result = shot(mode="character_story", beat="consequence", cause_scene_number=1,
                      visible_action="Returns with companion", state_after="together", shot_size="medium")
        review = evaluate_direction(scenes(decision, result))
        self.assertEqual("CONTRACT_PASS", review["status"])
        self.assertIsNone(review["human_approval"])
        self.assertIn("actual_emotion", review["not_evaluated"])

    def test_schema_is_opt_in_and_does_not_mutate_baseline(self):
        base = json.loads((ROOT / "video-generator/schemas/scene-plan.schema.json").read_text())
        original = deepcopy(base)
        schema = direction_output_schema(base, CONTRACT)
        self.assertEqual(base, original)
        self.assertEqual(base, direction_output_schema(base, None))
        self.assertIn("direction", schema["$defs"]["scene"]["properties"]["layout"]["required"])
        node = schema["$defs"]["ShotDirection"]
        self.assertEqual(set(node["properties"]), set(node["required"]))

    def test_shot_intent_reaches_image_provider(self):
        plan = deterministic_plan("A traveller looks at a window.", "guide")
        plan.scenes[0].layout["direction"] = shot()
        prompts, _ = load_prompts(ROOT / "harnesses/narrative-slide/prompts")
        prompt = scene_image_prompt(plan.scenes[0], [], prompts, plan.style_bible)
        self.assertIn('"shot_size": "wide"', prompt)
        self.assertIn("Looks toward a lit window", prompt)


class DirectionRepairIntegration(unittest.IsolatedAsyncioTestCase):
    async def test_real_director_repair_loop_corrects_duplicate_without_live_call(self):
        await self.run_repair_case(exhaust=False)

    async def test_repair_exhaustion_never_approves_a_repeated_shot(self):
        await self.run_repair_case(exhaust=True)

    async def run_repair_case(self, *, exhaust):
        prompts, _ = load_prompts(ROOT / "harnesses/narrative-slide/prompts")
        scenario = "A traveller waits. A window opens."
        bad = semantic_proposal()
        for item in bad["sequences"][0]["scene_groups"][0]["scenes"]:
            item["layout"]["direction"] = shot()
        good = deepcopy(bad)
        good["sequences"][0]["scene_groups"][0]["scenes"][1]["layout"]["direction"] = shot(
            beat="reaction", cause_scene_number=2, visible_action="Sees the opening window", shot_size="close",
            new_information="Someone is offering shelter")
        requests = []

        def respond(request):
            requests.append(json.loads(request.content))
            proposal = bad if exhaust or len(requests) == 1 else good
            payload = {"type": "response.completed", "response": {"id": "offline", "status": "completed",
                       "usage": {}, "output": [{"content": [{"type": "output_text", "text": json.dumps(proposal)}]}]}}
            return httpx.Response(200, text="event: response.completed\ndata: " + json.dumps(payload) + "\n\n")

        client = httpx.AsyncClient
        settings = SimpleNamespace(runner_mode="live", schemas_dir=ROOT / "video-generator/schemas",
            codex_model="offline", codex_reasoning_effort="low", codex_fast_mode=False,
            codex_read_timeout_seconds=10, codex_connect_timeout_seconds=2, subscription_base_url="http://offline.invalid")
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            tracker = Tracker(work)
            with patch("app.planner.httpx.AsyncClient", side_effect=lambda **kwargs: client(transport=httpx.MockTransport(respond), **kwargs)):
                if exhaust:
                    with self.assertRaisesRegex(RuntimeError, "Narrative direction needs repair"):
                        await create_plan(scenario, prompts, settings, tracker, work,
                                          harness_id="narrative-slide", harness_planning_contract=CONTRACT)
                    self.assertEqual(3, len(requests))
                    reviews = [asset for asset in tracker.assets if asset["asset_type"] == "direction_review"]
                    self.assertEqual(3, len(reviews))
                    self.assertEqual("REVISE", json.loads((work / reviews[-1]["relative_path"]).read_text())["status"])
                    return
                plan = await create_plan(scenario, prompts, settings, tracker, work,
                                         harness_id="narrative-slide", harness_planning_contract=CONTRACT)
            self.assertEqual(2, len(requests))
            self.assertIn("unmotivated_repeated_shot", json.dumps(requests[1]))
            self.assertEqual(scenario, "".join(scene.narration for scene in plan.scenes))
            reviews = [asset for asset in tracker.assets if asset["asset_type"] == "direction_review"]
            self.assertEqual(2, len(reviews))
            self.assertEqual("CONTRACT_PASS", json.loads((work / reviews[-1]["relative_path"]).read_text())["status"])


if __name__ == "__main__":
    unittest.main()
