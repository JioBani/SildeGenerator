from __future__ import annotations

import sys
from pathlib import Path

from app.creative_pilot import evaluate_pilot
from app.creative_readiness import evaluate_creative_readiness
from app.planner import deterministic_plan


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.audit_light_pollution_creative_pilot import STUDY, build_contract  # noqa: E402


def test_light_pollution_evidence_is_valid_but_not_promoted():
    contract = build_contract()
    result = evaluate_pilot(contract, STUDY)
    assert result["status"] == "EXPERIMENT_REVIEW_REQUIRED"
    assert result["errors"] == []
    assert result["production_ready"] is False
    assert "story:subject_action_not_shown" in result["pending"]
    assert "sample:D-collar:comprehension_review_required" in result["pending"]
    assert "sample:D-collar:acting_full_review_required" in result["pending"]
    assert "sample:D-collar:assembly_full_review_required" in result["pending"]
    assert "revision:C-to-D-collar:full_outcome_review_required" in result["pending"]
    assert len(result["evidence"]) == 9
    assert {item["sample_id"]: item["axes"] for item in result["scoped_positives"]}["D-collar"] == [
        "performance_naturalness_vs_C", "neck_clothing_join"]


def test_changed_artwork_invalidates_receipt():
    contract = build_contract()
    contract["assets"][0]["sources"][0]["sha256"] = "0" * 64
    result = evaluate_pilot(contract, STUDY)
    assert result["status"] == "INVALID_CONTRACT"
    assert "asset:person-reaction:0:artifact_hash_mismatch" in result["errors"]


def test_reference_reuse_and_escaping_artifact_are_rejected():
    contract = build_contract()
    contract["references"][0]["asset_reuse"] = True
    contract["samples"][0]["path"] = "../outside.mp4"
    result = evaluate_pilot(contract, STUDY)
    assert "references:ref-night-lights:reuse_not_cleared" in result["errors"]
    assert "sample:C-reaction:artifact_missing_or_outside_root" in result["errors"]


def test_collar_cannot_draw_behind_neck():
    contract = build_contract()
    contract["assets"][0]["draw_order"] = ["torso", "collar-front", "head_and_neck"]
    result = evaluate_pilot(contract, STUDY)
    assert "asset:person-reaction:occlusion_order_invalid" in result["errors"]


def test_user_review_is_bound_to_exact_video_and_receipt():
    contract = build_contract()
    contract["samples"][1]["sha256"] = contract["samples"][0]["sha256"]
    result = evaluate_pilot(contract, STUDY)
    assert result["status"] == "INVALID_CONTRACT"
    assert not any(item["sample_id"] == "D-collar" for item in result["scoped_positives"])


def test_claimed_reviews_cannot_automatically_approve_experimental_asset():
    contract = build_contract()
    for asset in contract["assets"]:
        asset["human_review"] = "APPROVED"
    for sample in contract["samples"]:
        sample["human_reviews"] = {
            axis: {"video_sha256": sample["sha256"], "decision": "PASS"}
            for axis in ("design", "acting", "comprehension", "immersion", "assembly")
        }
    result = evaluate_pilot(contract, STUDY)
    assert result["production_ready"] is False
    assert "story:subject_action_not_shown" in result["pending"]


def test_director_readiness_exposes_asset_authoring_before_generation():
    plan = deterministic_plan("창밖 빛을 본 인물이 눈을 찡그립니다.", "flat illustration")
    scene = plan.scenes[0]
    scene.motion = [{"object_id": "person", "kind": "reaction", "phases": ["notice", "settle"]}]
    scene.object_states = [{"object_id": "person", "role": "actor", "initial": "tired", "final": "notice",
                            "region_hint": [0.5, 0.2, 0.3, 0.7]}]
    result = evaluate_creative_readiness(plan, harness_id="astra-motion")
    intent = result["scenes"][0]["movable_asset_intents"][0]["authoring_plan"]
    assert intent["proposed_route"] == "separately_authored_layers"
    assert "eyes" in intent["required_layers"]
    assert "full_motion_path_review" in intent["required_evidence"]
    assert "front_occluder" in intent["assembly_requirements"]
    assert intent["route_approved"] is False
