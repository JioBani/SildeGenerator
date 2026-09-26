import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import httpx

from app.engine.harness_loader import HarnessRegistry
from app.harness_sdk.direction import direction_planning_extension
from app.harness_sdk.hybrid import hybrid_planning_extension
from app.planner import create_plan
from app.prompts import load_prompts
from app.tracking import Tracker
from test_hybrid_story import route
from test_narrative_direction import shot
from test_planner import semantic_proposal

ROOT = Path(__file__).resolve().parents[2]


class HybridPlannerIntegration(unittest.IsolatedAsyncioTestCase):
    async def test_unknown_source_repaired_without_changing_narration(self):
        await self.run_case(exhaust=False)

    async def test_unknown_source_never_silently_becomes_a_generated_image(self):
        await self.run_case(exhaust=True)

    async def run_case(self, exhaust):
        loaded = HarnessRegistry(ROOT / "harnesses").load("hybrid-story")
        contract = loaded.instance.describe_planning_contract(loaded.config)
        # Preserve the pre-analysis protocol as a backward-compatibility test.
        contract.pop("semantic_analysis", None)
        contract.pop("semantic_review", None)
        contract.pop("concept_selection", None)
        contract.pop("locked_scene_design", None)
        contract.pop("preproduction_brief", None)
        contract["narrative_direction"] = direction_planning_extension("narrative-direction-0.1")
        contract["hybrid_direction"] = hybrid_planning_extension("hybrid-scene-0.1")
        contract["trusted_source_catalog"] = [{"id": "registered", "meaning_limit": "A modern observation, not historical evidence"}]
        prompts, _ = load_prompts(ROOT / "harnesses/hybrid-story/prompts")
        bad = semantic_proposal()
        bad["continuity_assets"] = []
        items = bad["sequences"][0]["scene_groups"][0]["scenes"]
        for index, item in enumerate(items):
            item["layout"]["direction"] = shot(subject_id=f"subject-{index}", new_information=f"Observation {index}")
            item["layout"]["hybrid"] = route("cinematic" if index == 0 else "source")
        items[1]["layout"]["hybrid"]["source_id"] = "invented"
        good = deepcopy(bad)
        good["sequences"][0]["scene_groups"][0]["scenes"][1]["layout"]["hybrid"]["source_id"] = "registered"
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
        scenario = "An explorer faces the ice. A modern observation shows the sea ice."
        with tempfile.TemporaryDirectory() as folder:
            work, tracker = Path(folder), Tracker(Path(folder))
            with patch("app.planner.httpx.AsyncClient", side_effect=lambda **kwargs: client(transport=httpx.MockTransport(respond), **kwargs)):
                if exhaust:
                    with self.assertRaisesRegex(RuntimeError, "source_not_registered"):
                        await create_plan(scenario, prompts, settings, tracker, work,
                            harness_id="hybrid-story", harness_planning_contract=contract)
                else:
                    plan = await create_plan(scenario, prompts, settings, tracker, work,
                        harness_id="hybrid-story", harness_planning_contract=contract)
                    self.assertEqual(scenario, "".join(s.narration for s in plan.scenes))
                    self.assertEqual("source", plan.scenes[1].layout["hybrid"]["route"])
                    self.assertEqual("registered", plan.scenes[1].layout["hybrid"]["source_id"])
            self.assertEqual(3 if exhaust else 2, len(requests))
            self.assertIn("source_not_registered", json.dumps(requests[1]))
            self.assertIn('"HybridScene"', json.dumps(requests[0]))
            self.assertIn("visual_grammar_library", json.dumps(requests[0]))
            self.assertIn("do_not_use_when", json.dumps(requests[0]))
            reviews = [a for a in tracker.assets if a["asset_type"] == "hybrid_review"]
            self.assertEqual(len(requests), len(reviews))
            result = json.loads((work / reviews[-1]["relative_path"]).read_text())
            self.assertEqual("REVISE" if exhaust else "CONTRACT_PASS", result["status"])
            self.assertIsNone(result["human_approval"])
            self.assertEqual(contract["visual_grammar_library"]["sha256"], result["grammar_library_sha256"])


if __name__ == "__main__":
    unittest.main()
