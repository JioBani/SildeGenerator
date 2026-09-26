import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import httpx

from app.semantic_review import PairVerdict, review_packet, validate_verdict, compare_orders, review_pair, digest
from app.harness_sdk.semantic_beats import ScriptAnalysis
from app.tracking import Tracker
from test_semantic_planning import analysis_payload, SCRIPT


def packets():
    original = review_packet(ScriptAnalysis.model_validate(analysis_payload()))
    wrong = deepcopy(original)
    wrong["beats"][1].update(route="cinematic", grammar=None)
    return {"A": original, "B": wrong}


def verdict():
    candidates = []
    for label, packet in packets().items():
        beats = []
        for i, beat in enumerate(packet["beats"]):
            bad = label == "B" and i == 1
            beats.append(dict(beat_id=beat["beat_id"], route_fit="FAIL" if bad else "PASS", grammar_fit="PASS",
                meaning_preserved="PASS", causality="PASS", script_quote=beat["literal_content"],
                explanation="Explaining change requires a visible relationship" if bad else "Matches this script span",
                repair_target="route" if bad else None, recheck_scope="beat-002" if bad else None))
        candidates.append(dict(label=label, beats=beats))
    return dict(candidates=candidates, preferred="A", reason="Only A preserves the explanatory route")


def reports():
    first = dict(status="VALID_REVIEW", response_id="response-1", script_sha256="script", context_sha256="context",
        candidate_hashes={k: digest(v) for k, v in packets().items()}, verdict=verdict())
    second = deepcopy(first)
    second["response_id"] = "response-2"
    second["candidate_hashes"] = {"A": first["candidate_hashes"]["B"], "B": first["candidate_hashes"]["A"]}
    for v in second["verdict"]["candidates"]:
        v["label"] = "B" if v["label"] == "A" else "A"
    second["verdict"]["preferred"] = "B"
    return first, second


class IndependentReviewTests(unittest.TestCase):
    def test_generator_confidence_and_reason_are_not_critic_input(self):
        serialized = json.dumps(packets())
        for field in ("confidence", "route_reason", "rejected_routes", "approval"):
            self.assertNotIn(field, serialized)

    def test_grounded_complete_review(self):
        self.assertEqual([], validate_verdict(PairVerdict.model_validate(verdict()), packets(), SCRIPT))

    def test_missing_or_duplicate_candidate_rejected(self):
        value = verdict()
        value["candidates"][1]["label"] = "A"
        self.assertIn("candidate_coverage_not_exact", validate_verdict(PairVerdict.model_validate(value), packets(), SCRIPT))

    def test_missing_beat_and_fabricated_quote_rejected(self):
        for change in ("missing", "quote", "repair"):
            value = verdict()
            if change == "missing": value["candidates"][0]["beats"].pop()
            if change == "quote": value["candidates"][0]["beats"][0]["script_quote"] = "Invented quotation"
            if change == "repair": value["candidates"][1]["beats"][1]["repair_target"] = None
            self.assertTrue(validate_verdict(PairVerdict.model_validate(value), packets(), SCRIPT))

    def test_failure_or_unknown_cannot_win(self):
        for status in ("FAIL", "UNKNOWN"):
            value = verdict()
            value["candidates"][0]["beats"][0]["causality"] = status
            self.assertIn("preferred_candidate_not_passed", validate_verdict(PairVerdict.model_validate(value), packets(), SCRIPT))
        value = verdict(); value["preferred"] = "TIE"
        self.assertIn("tie_contains_unpassed_candidate", validate_verdict(PairVerdict.model_validate(value), packets(), SCRIPT))

    def test_reversed_order_binds_content_not_labels(self):
        outcome = compare_orders(*reports())
        self.assertEqual("CONSISTENT_PRE_RENDER_REVIEW", outcome["status"])
        self.assertEqual(digest(packets()["A"]), outcome["winner_sha256"])
        self.assertFalse(outcome["production_ready"])

    def test_order_bias_and_dimension_disagreement_fail(self):
        for change in ("winner", "criterion"):
            first, second = reports()
            if change == "winner": second["verdict"]["preferred"] = "A"
            else: second["verdict"]["candidates"][0]["beats"][0]["causality"] = "UNKNOWN"
            result = compare_orders(first, second)
            self.assertEqual("ORDER_DISAGREEMENT", result["status"])
            self.assertIsNone(result["winner_sha256"])
            self.assertEqual(change == "criterion", result["diagnostics"]["preference_consistent"])
            self.assertEqual(15/16 if change == "criterion" else 1, result["diagnostics"]["agreement_ratio"])
            if change == "criterion":
                self.assertEqual("causality", result["diagnostics"]["disagreements"][0]["criterion"])

    def test_incomplete_identical_response_and_changed_context_fail(self):
        for key, value, expected in (("status", "REVIEW_INCOMPLETE", "REVIEW_INCOMPLETE"),
                ("response_id", "response-1", "INVALID_REVIEW_PROVENANCE"),
                ("context_sha256", "changed", "REVIEW_INPUT_MISMATCH")):
            first, second = reports(); second[key] = value
            self.assertEqual(expected, compare_orders(first, second)["status"])
        first, second = reports(); second["candidate_hashes"] = first["candidate_hashes"]
        self.assertEqual("INVALID_COUNTERBALANCE", compare_orders(first, second)["status"])

    def test_different_rubrics_cannot_be_combined(self):
        first,second=reports()
        first["evaluator_version"]="semantic-review-0.1"
        second["evaluator_version"]="semantic-review-0.2"
        self.assertEqual("REVIEW_POLICY_MISMATCH",compare_orders(first,second)["status"])


class ReviewTransportTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_transport_with_mock_and_401_no_fallback(self):
        for unauthorized in (False, True):
            calls = []
            def respond(request):
                calls.append(json.loads(request.content))
                if unauthorized:
                    return httpx.Response(401, json={"error": {"type": "invalid_request_error", "code": "invalid_api_key",
                        "message": "Incorrect API key provided: sk-svcac-sample-private"}})
                payload = {"type": "response.completed", "response": {"id": "test-response", "usage": {},
                    "output": [{"content": [{"type": "output_text", "text": json.dumps(verdict())}]}]}}
                return httpx.Response(200, text="event: response.completed\ndata: " + json.dumps(payload) + "\n\n")
            settings = SimpleNamespace(codex_model="generator", codex_read_timeout_seconds=10, codex_connect_timeout_seconds=2,
                subscription_base_url="http://offline.invalid")
            original = httpx.AsyncClient
            with tempfile.TemporaryDirectory() as folder:
                work = Path(folder); tracker = Tracker(work)
                with patch("app.semantic_review.httpx.AsyncClient", side_effect=lambda **kw: original(transport=httpx.MockTransport(respond), **kw)):
                    if unauthorized:
                        with self.assertRaisesRegex(RuntimeError, "401") as caught:
                            await review_pair(SCRIPT, packets(), {}, settings, tracker, work, review_id="ab", model="critic")
                        self.assertIn("invalid_api_key", str(caught.exception))
                        self.assertNotIn("sk-svcac", str(caught.exception))
                    else:
                        result = await review_pair(SCRIPT, packets(), {}, settings, tracker, work, review_id="ab", model="critic")
                        self.assertEqual("VALID_REVIEW", result["status"])
                    with self.assertRaisesRegex(ValueError, "separate_model"):
                        await review_pair(SCRIPT, packets(), {}, settings, tracker, work, review_id="self", model="generator")
                self.assertEqual(1, len(calls))
                self.assertEqual(1, len(tracker.usage))
                saved = json.loads((work/"ab.json").read_text())
                self.assertFalse(saved["production_ready"])
                self.assertEqual("REVIEW_INCOMPLETE" if unauthorized else "VALID_REVIEW", saved["status"])
