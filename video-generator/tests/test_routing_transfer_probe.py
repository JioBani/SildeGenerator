import json
from pathlib import Path
import sys
import unittest
from copy import deepcopy

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from probe_routing_transfer import inspect_case, load_suite
from probe_independent_semantics import negative_packet


class RoutingTransferProbeTests(unittest.TestCase):
    def setUp(self):
        self.suite = load_suite(ROOT / "experiments/meaning-planning-v1/routing-transfer-v1.json")
        self.case = self.suite["cases"][0]
        self.report = dict(status="STRUCTURAL_PASS", findings=[], analysis=dict(beats=[dict(
            literal_content=self.case["script"], route="diagram", grammar="before_after")]))

    def test_route_and_grammar_are_separate(self):
        self.assertEqual([], inspect_case(self.case, self.report))
        for field, value, finding in [("route", "cinematic", "wrong_route"),
                                      ("grammar", "quantitative_comparison", "wrong_grammar")]:
            changed = deepcopy(self.report)
            changed["analysis"]["beats"][0][field] = value
            self.assertIn(finding, inspect_case(self.case, changed))

    def test_missing_output_never_passes_an_expected_block(self):
        self.assertEqual(["analysis_missing"], inspect_case(self.suite["cases"][-1], None))

    def test_correct_block_is_not_a_render_success(self):
        case = self.suite["cases"][-1]
        report = dict(status="REVISE", findings=["beat-001:grammar_not_supported"],
            analysis=dict(beats=[dict(literal_content=case["script"], route="diagram", grammar="map_spatial")]))
        self.assertEqual([], inspect_case(case, report))
        report["status"] = "STRUCTURAL_PASS"
        self.assertIn("missing_required_block", inspect_case(case, report))
        report["status"] = "REVISE"
        report["findings"] = ["beat-001:SOURCE_NOT_AVAILABLE"]
        self.assertIn("wrong_block_reason", inspect_case(case, report))

    def test_connected_quantities_and_disclaimers_cannot_be_lost(self):
        changed = deepcopy(self.report)
        split = self.case["script"].index("저녁")
        changed["analysis"]["beats"] = [dict(literal_content=t, route="diagram", grammar="before_after")
            for t in (self.case["script"][:split], self.case["script"][split:])]
        self.assertIn("connected_information_split", inspect_case(self.case, changed))
        changed["analysis"]["beats"][0]["literal_content"] = ""
        self.assertIn("source_coverage", inspect_case(self.case, changed))

    def test_snapshot_negative_changes_only_grammar_not_script_or_route(self):
        original = dict(beats=[dict(beat_id="beat-001", route="diagram", grammar="before_after",
            literal_content=self.case["script"], evidence=[], relations=[])])
        wrong, mutation = negative_packet(original, "snapshot_as_accumulation")
        self.assertEqual("before_after", original["beats"][0]["grammar"])
        self.assertEqual("cumulative_change", wrong["beats"][0]["grammar"])
        self.assertEqual("grammar", mutation["field"])
        wrong["beats"][0]["grammar"] = "before_after"
        self.assertEqual(original, wrong)
        with self.assertRaisesRegex(ValueError, "unsupported"):
            negative_packet(original, "unknown")


if __name__ == "__main__":
    unittest.main()
