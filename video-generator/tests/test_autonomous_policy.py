"""Policy logic fixtures are not evidence that a real film meets the benchmarks."""
import unittest
from copy import deepcopy

from app.autonomous_policy import CHECKS, HELD_OUT_TYPES, NEGATIVE_TYPES, RepairBudget, adoption_decision

CANDIDATE, BASELINE, REPORT = "a" * 64, "b" * 64, "c" * 64


def synthetic_complete():
    metrics = {name: {"passed": 100, "total": 100} for name in (
        "meaning_unit_coverage", "source_rights_hash_coverage", "motion_quantity_unit_coverage",
        "typography_role_coverage", "safe_area_coverage", "held_out_route_accuracy", "misrouting_detection",
        "evaluator_agreement", "negative_control_detection", "held_out_superiority")}
    return {"candidate_sha256": CANDIDATE, "baseline_sha256": BASELINE,
        "checks": {name: {"status": "PASS", "critical_failures": 0, "report_sha256": REPORT,
                          "candidate_sha256": CANDIDATE} for name in CHECKS}, "metrics": metrics,
        "benchmark": {"report_sha256": REPORT, "held_out_types": sorted(HELD_OUT_TYPES),
            "negative_types": sorted(NEGATIVE_TYPES), "development_script_hashes": ["dev"],
            "held_out_script_hashes": [f"held-{i}" for i in range(5)], "critical_regressions": 0},
        "blind_comparison": {"report_sha256": REPORT, "generator_run_id": "generator",
            "evaluator_run_id": "separate", "orders": ["AB", "BA"], "preferred_hashes": [CANDIDATE, CANDIDATE]},
        "concept_selection": {"report_sha256": REPORT, "candidate_hashes": ["first", "second", "third"],
            "names_hidden": True, "critical_failures": 0}}


def decide(evidence, trusted=frozenset({REPORT})):
    return adoption_decision(evidence, candidate_hash=CANDIDATE, baseline_hash=BASELINE, verified_report_hashes=trusted)


class AutonomousAdoptionTests(unittest.TestCase):
    def test_missing_evidence_is_not_quality_acceptance(self):
        result = decide({})
        self.assertEqual("GOAL_NOT_MET", result["status"])
        self.assertIn("missing_evaluation:output_frames", result["failures"])
        self.assertIsNone(result["human_approval"])
        self.assertFalse(result["production_deployment_authorized"])

    def test_only_fully_verified_fixture_passes(self):
        good = synthetic_complete()
        self.assertEqual("AUTO_VALIDATED", decide(good)["status"])
        self.assertEqual("GOAL_NOT_MET", decide(good, frozenset())["status"])

    def test_one_critical_failure_cannot_be_averaged_away(self):
        for name in CHECKS:
            bad = synthetic_complete()
            bad["checks"][name]["critical_failures"] = 1
            self.assertEqual("GOAL_NOT_MET", decide(bad)["status"], name)

    def test_zero_samples_and_threshold_shortfall_fail(self):
        bad = synthetic_complete()
        bad["metrics"]["negative_control_detection"] = {"passed": 0, "total": 0}
        self.assertIn("benchmark_target_not_met:negative_control_detection", decide(bad)["failures"])
        bad["metrics"]["negative_control_detection"] = {"passed": 94, "total": 100}
        self.assertEqual("GOAL_NOT_MET", decide(bad)["status"])

    def test_order_bias_stale_hash_and_training_leakage_are_rejected(self):
        bad = synthetic_complete()
        bad["blind_comparison"]["preferred_hashes"] = [CANDIDATE, BASELINE]
        bad["checks"]["output_frames"]["candidate_sha256"] = BASELINE
        bad["benchmark"]["held_out_script_hashes"][0] = "dev"
        result = decide(bad)
        for failure in ("candidate_not_superior_in_both_orders", "stale_evaluation:output_frames", "held_out_data_leakage"):
            self.assertIn(failure, result["failures"])

    def test_same_cause_stops_blind_regeneration_on_second_failure(self):
        budget = RepairBudget()
        self.assertEqual("REPAIR_TARGET_ONLY", budget.next_action("scene", cause="missing_neck", scene_id="one"))
        self.assertEqual("FIX_CAPABILITY_OR_EVALUATOR", budget.next_action("scene", cause="missing_neck", scene_id="one"))
        self.assertEqual(1, budget.scene_repairs["one"])

    def test_scoped_limits_and_no_extra_candidate(self):
        budget = RepairBudget()
        for i in range(5):
            self.assertEqual("REPAIR_TARGET_ONLY", budget.next_action("candidate", cause=f"cause-{i}"))
        self.assertEqual("GOAL_NOT_MET_CONTINUE_OTHER_SAFE_WORK", budget.next_action("candidate", cause="new-cause"))
        for i in range(3):
            self.assertEqual("REPAIR_TARGET_ONLY", budget.next_action("plan", cause=f"plan-{i}"))
        self.assertEqual("GOAL_NOT_MET_CONTINUE_OTHER_SAFE_WORK", budget.next_action("plan", cause="plan-last"))
        self.assertEqual("REPAIR_TARGET_ONLY", budget.next_action("scene", cause="new", scene_id="two"))


if __name__ == "__main__":
    unittest.main()
