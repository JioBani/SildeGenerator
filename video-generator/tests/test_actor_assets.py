from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from app.actor_assets import validate_actor_candidate


ROOT = Path(__file__).resolve().parents[2]
CANDIDATE = ROOT / "docs" / "actor-assets" / "d-nightlight-candidate.json"


class ActorCandidateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.document = json.loads(CANDIDATE.read_text(encoding="utf-8"))

    def test_d_candidate_verifies_evidence_without_production_approval(self) -> None:
        result = validate_actor_candidate(self.document, root=ROOT)
        self.assertEqual(result["status"], "EVIDENCE_VERIFIED_HUMAN_SCOPE_LIMITED")
        self.assertFalse(result["production_ready"])
        self.assertFalse(result["assembly_verified_against_program"])
        self.assertEqual(result["approved_axes"], ["performance_naturalness_vs_C", "neck_clothing_join"])
        self.assertEqual(result["abilities"]["grasp"], "NOT_BUILT")

    def test_changed_layer_hash_invalidates_candidate(self) -> None:
        document = copy.deepcopy(self.document)
        document["layers"]["head_notice"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "actor_evidence_hash_mismatch"):
            validate_actor_candidate(document, root=ROOT)

    def test_evidence_cannot_escape_repository(self) -> None:
        document = copy.deepcopy(self.document)
        document["program"]["path"] = "../outside.html"
        with self.assertRaisesRegex(ValueError, "actor_evidence_missing_or_unsafe"):
            validate_actor_candidate(document, root=ROOT)

    def test_cannot_expand_human_review_scope(self) -> None:
        document = copy.deepcopy(self.document)
        document["approved_axes"].append("curtain_contact")
        with self.assertRaisesRegex(ValueError, "actor_review_scope_mismatch"):
            validate_actor_candidate(document, root=ROOT)

    def test_candidate_cannot_self_approve_actor_or_action(self) -> None:
        document = copy.deepcopy(self.document)
        document["production_ready"] = True
        with self.assertRaisesRegex(ValueError, "actor_candidate_cannot_self_approve"):
            validate_actor_candidate(document, root=ROOT)
        document = copy.deepcopy(self.document)
        document["abilities"]["grasp"] = "PRODUCTION_APPROVED"
        with self.assertRaisesRegex(ValueError, "actor_ability_cannot_self_approve"):
            validate_actor_candidate(document, root=ROOT)

    def test_source_assembly_must_keep_pivot_and_occlusion_order(self) -> None:
        document = copy.deepcopy(self.document)
        document["source_assembly"]["head_pivot_local_px"] = [999, 999]
        with self.assertRaisesRegex(ValueError, "actor_head_pivot_invalid"):
            validate_actor_candidate(document, root=ROOT)
        document = copy.deepcopy(self.document)
        document["source_assembly"]["draw_order"] = ["collar_front", "head_faces", "torso", "neck_underlay"]
        with self.assertRaisesRegex(ValueError, "actor_occlusion_order_invalid"):
            validate_actor_candidate(document, root=ROOT)
