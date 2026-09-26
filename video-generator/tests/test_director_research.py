from __future__ import annotations

import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.director_research import RESEARCH_ROOT, research_prompt, select_research_candidates
from app.planner import create_plan, deterministic_plan
from app.tracking import Tracker, sha256_file


class DirectorResearchTests(unittest.TestCase):
    def test_real_evidence_retrieves_a_risk_not_an_approval(self):
        brief = select_research_candidates(
            "두 세계를 비교한다", "astra-motion", root=RESEARCH_ROOT,
            planning_contract={"supported_effects": ["reveal"]},
        )
        self.assertEqual(brief["status"], "RESEARCH_ONLY")
        self.assertEqual(brief["candidates"][0]["id"], "light-pollution-split-clip-region")
        self.assertEqual(brief["candidates"][0]["unsupported_effects"], ["clip_region"])
        self.assertFalse(brief["candidates"][0]["production_authorized"])
        self.assertIn("not approved director rules", research_prompt(brief))

    def test_reference_reconstruction_measurement_is_retrieved_cross_domain(self):
        brief = select_research_candidates(
            "물고기가 강을 따라 이동한다", "astra-motion", root=RESEARCH_ROOT,
            planning_contract={"supported_effects": ["path_follow"]},
        )
        self.assertEqual(brief["candidates"][0]["id"], "transport-preserve-time-series")
        self.assertEqual(brief["candidates"][0]["reference_id"], "Ab9OZsDECZw")
        self.assertIn("transport_track", brief["candidates"][0]["unsupported_effects"])
        self.assertFalse(brief["candidates"][0]["production_authorized"])

    def test_changed_evidence_is_not_retrieved(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            evidence = root / "docs" / "evidence" / "frame.txt"
            evidence.parent.mkdir(parents=True)
            evidence.write_text("first", encoding="utf-8")
            case = {
                "id": "light-pollution-split-clip-region",
                "evidence": [{"path": "docs/evidence/frame.txt", "sha256": sha256_file(evidence)}],
                "required_effects": ["clip_region"],
            }
            ledger = root / "docs" / "director-learning-ledger.json"
            ledger.write_text(json.dumps({"schema_version": 1, "cases": [case]}), encoding="utf-8")
            self.assertEqual(len(select_research_candidates("비교", "astra-motion", root=root)["candidates"]), 1)
            evidence.write_text("changed", encoding="utf-8")
            self.assertEqual(select_research_candidates("비교", "astra-motion", root=root)["candidates"], [])

    def test_mock_records_but_does_not_claim_prompt_use(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            prompts = {"image/style-guide.md": "simple design"}
            settings = SimpleNamespace(runner_mode="mock", director_research_mode="pilot")
            asyncio.run(create_plan("두 세계를 비교한다.", prompts, settings, None, root,
                                    harness_id="astra-motion"))
            report = json.loads((root / "director-research-brief.json").read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "RESEARCH_ONLY")
            self.assertFalse(report["used_in_prompt"])

    def test_brief_is_indexed_in_job_asset_ledger(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            work = root / "work"
            work.mkdir()
            tracker = Tracker(root)
            asyncio.run(create_plan("두 세계를 비교한다.", {"image/style-guide.md": "simple design"},
                                    SimpleNamespace(runner_mode="mock"), tracker, work,
                                    harness_id="astra-motion"))
            self.assertEqual(tracker.assets[0]["asset_type"], "director_research_brief")
            self.assertEqual(tracker.assets[0]["relative_path"], "work/director-research-brief.json")
            self.assertEqual(tracker.assets[0]["metadata"]["research_status"], "RESEARCH_ONLY")

    def test_pilot_passes_brief_to_live_director_without_network(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            scenario = "두 세계를 비교한다."
            prompts = {"image/style-guide.md": "simple design"}
            settings = SimpleNamespace(runner_mode="live", director_research_mode="pilot")
            model = AsyncMock(return_value=deterministic_plan(scenario, "simple design", "editorial_illustration"))
            with patch("app.planner.plan_with_codex", model):
                asyncio.run(create_plan(scenario, prompts, settings, SimpleNamespace(usage=[]), root,
                                        harness_id="astra-motion"))
            brief = model.await_args.kwargs["research_brief"]
            self.assertEqual(brief["candidates"][0]["id"], "light-pollution-split-clip-region")
            report = json.loads((root / "director-research-brief.json").read_text(encoding="utf-8"))
            self.assertTrue(report["used_in_prompt"])

    def test_default_live_mode_keeps_research_out_of_prompt(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            scenario = "두 세계를 비교한다."
            prompts = {"image/style-guide.md": "simple design"}
            settings = SimpleNamespace(runner_mode="live")
            model = AsyncMock(return_value=deterministic_plan(scenario, "simple design", "editorial_illustration"))
            with patch("app.planner.plan_with_codex", model):
                asyncio.run(create_plan(scenario, prompts, settings, SimpleNamespace(usage=[]), root,
                                        harness_id="astra-motion"))
            self.assertIsNone(model.await_args.kwargs["research_brief"])
            report = json.loads((root / "director-research-brief.json").read_text(encoding="utf-8"))
            self.assertEqual(report["mode"], "off")
            self.assertFalse(report["used_in_prompt"])


if __name__ == "__main__":
    unittest.main()
