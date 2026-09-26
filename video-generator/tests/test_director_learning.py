from __future__ import annotations

import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.director_learning import (
    _digest, learning_prompt, record_learning_application, record_learning_selection,
    select_director_rules,
)
from app.planner import create_plan, deterministic_plan


def sample_rule() -> dict:
    return {
        "id": "test-contrast-boundary",
        "trigger_terms": ["대비"],
        "supported_harnesses": ["astra-motion"],
        "scene_function": "contrast",
        "motion_kind": "reveal",
        "conditions": ["Two domains need comparison"],
        "counterexamples": ["A deliberate crossing may be useful"],
        "correction": "Keep each object in its intended region",
        "evidence": [{"path": "evidence/frame.txt", "sha256": "0" * 64}],
    }


class DirectorLearningTests(unittest.TestCase):
    def write_catalog(self, root: Path, rule: dict | None = None, approved: bool = False) -> Path:
        (root / "evidence").mkdir(exist_ok=True)
        evidence_file = root / "evidence" / "frame.txt"
        evidence_file.write_text("frame", encoding="utf-8")
        if rule:
            from app.tracking import sha256_file
            rule["evidence"][0]["sha256"] = sha256_file(evidence_file)
        rules = [rule] if rule else []
        approvals = {rule["id"]: {"decision": "APPROVED", "rule_sha256": _digest(rule)}} if rule and approved else {}
        path = root / "catalog.json"
        path.write_text(json.dumps({"schema_version": 1, "rules": rules, "human_approvals": approvals}), encoding="utf-8")
        return path

    def test_packaged_catalog_has_no_unapproved_research_cases(self):
        selection = select_director_rules("빛 공해 대비", "astra-motion")
        self.assertEqual(selection["selected"], [])
        self.assertEqual(learning_prompt(selection), "")

    def test_approval_hash_harness_and_trigger_are_all_required(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            rule = sample_rule()
            path = self.write_catalog(root, rule)
            self.assertEqual(select_director_rules("대비", "astra-motion", catalog_path=path)["selected"], [])
            path = self.write_catalog(root, rule, approved=True)
            self.assertEqual(len(select_director_rules("대비", "astra-motion", catalog_path=path)["selected"]), 1)
            self.assertEqual(select_director_rules("대비", "classic-slide", catalog_path=path)["selected"], [])
            self.assertEqual(select_director_rules("다른 대본", "astra-motion", catalog_path=path)["selected"], [])
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["rules"][0]["correction"] = "unreviewed change"
            path.write_text(json.dumps(payload), encoding="utf-8")
            self.assertEqual(select_director_rules("대비", "astra-motion", catalog_path=path)["selected"], [])

    def test_changed_or_escaping_evidence_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            rule = sample_rule()
            path = self.write_catalog(root, rule, approved=True)
            (root / "evidence" / "frame.txt").write_text("changed", encoding="utf-8")
            result = select_director_rules("대비", "astra-motion", catalog_path=path)
            self.assertEqual(result["rejected"][0]["reason"], "missing_changed_or_unsafe_evidence")
            rule["evidence"][0]["path"] = "../outside.txt"
            path = self.write_catalog(root, rule, approved=True)
            result = select_director_rules("대비", "astra-motion", catalog_path=path)
            self.assertEqual(result["rejected"][0]["reason"], "missing_changed_or_unsafe_evidence")

    def test_declared_harness_does_not_authorize_unimplemented_motion(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            rule = sample_rule()
            rule["motion_kind"] = "clip_region"
            path = self.write_catalog(root, rule, approved=True)
            result = select_director_rules("대비", "astra-motion", catalog_path=path)
            self.assertEqual(result["selected"], [])
            self.assertEqual(result["rejected"][0]["reason"], "unsupported_motion_kind")

    def test_selection_and_application_are_separate_from_quality_approval(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            selection = select_director_rules("대비", "astra-motion", catalog_path=self.write_catalog(root, sample_rule(), True))
            self.assertIn("test-contrast-boundary", learning_prompt(selection))
            record_learning_selection(root, selection)
            scene = SimpleNamespace(id="scene-001", scene_function="contrast",
                                    motion=[{"kind": "reveal"}])
            record_learning_application(root, selection, SimpleNamespace(scenes=[scene]))
            result = json.loads((root / "director-learning-application.json").read_text(encoding="utf-8"))
            self.assertEqual(result["assessments"][0]["status"], "STRUCTURE_PRESENT_UNREVIEWED")
            self.assertFalse(result["visual_quality_reviewed"])

    def test_mock_planner_writes_no_approved_match_without_model_call(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            prompts = {"image/style-guide.md": "simple design"}
            with patch("app.planner.plan_with_codex") as model_call:
                asyncio.run(create_plan("밤하늘에 별이 보입니다.", prompts,
                                        SimpleNamespace(runner_mode="mock"), None, root))
            model_call.assert_not_called()
            selection = json.loads((root / "director-learning-selection.json").read_text(encoding="utf-8"))
            self.assertEqual(selection["status"], "NO_APPROVED_MATCH")
            self.assertTrue((root / "director-learning-application.json").is_file())

    def test_live_planner_receives_approved_selection_without_network(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            scenario = "빛 공해를 대비합니다."
            prompts = {"image/style-guide.md": "simple design"}
            selection = select_director_rules(scenario, "astra-motion",
                                              catalog_path=self.write_catalog(root, sample_rule(), True))
            fake_model = AsyncMock(return_value=deterministic_plan(scenario, "simple design", "editorial_illustration"))
            with patch("app.planner.select_director_rules", return_value=selection), patch(
                "app.planner.plan_with_codex", fake_model
            ):
                asyncio.run(create_plan(scenario, prompts, SimpleNamespace(runner_mode="live"), SimpleNamespace(usage=[]),
                                        root, harness_id="astra-motion"))
            self.assertEqual(fake_model.await_args.kwargs["learning_selection"]["selected"][0]["id"],
                             "test-contrast-boundary")
            application = json.loads((root / "director-learning-application.json").read_text(encoding="utf-8"))
            self.assertEqual(application["assessments"][0]["status"], "NOT_DEMONSTRATED")


if __name__ == "__main__":
    unittest.main()
