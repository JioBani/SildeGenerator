from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.director_safety import ACTING_CRITERIA, Capability, VERSION, authorize_capability, canonical_sha256, validate_human_approval


def _approval(capability: Capability, scope_id: str, contract: dict, criteria: set[str], *, frame_count: int | None = None) -> dict:
    contract_hash = canonical_sha256({"capability": capability.value, "scope_id": scope_id, "contract": contract})
    frames = [0, max(0, (frame_count or 1) - 1)] if frame_count is not None else []
    return {
        "version": VERSION, "capability": capability.value, "scope_id": scope_id,
        "contract_sha256": contract_hash, "reviewer_kind": "human", "reviewer_id": "reviewer-001",
        "reviewed_at": (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(), "status": "APPROVED",
        "criteria": {name: {"status": "PASS", "reason": "verified", "frames": frames} for name in criteria},
    }


def test_actor_reaction_requires_external_human_approval() -> None:
    contract = {
        "actor_asset_id": "actor-1", "actor_asset_sha256": "a" * 64, "rig_sha256": "b" * 64,
        "render_sha256": "c" * 64, "style_version": "style-v1", "event": "IMAGE_APPEARS",
        "gaze_target": "monitor_result", "frame_count": 120,
    }
    request = {"capability": "actor_reaction", "contract": contract}
    denied = authorize_capability(request, scope_id="scene-001", production=True)
    assert denied["allowed"] is False
    assert "human_approval_missing" in denied["reason_codes"]
    approval = _approval(Capability.ACTOR_REACTION, "scene-001", contract, ACTING_CRITERIA, frame_count=120)
    allowed = authorize_capability(request, scope_id="scene-001", approvals=[approval], production=True)
    assert allowed["allowed"] is True
    assert allowed["automatic_promotion"] is False
    assert allowed["promotion_scope"] == "production_version_only"


def test_model_supplied_approval_inside_contract_is_ignored() -> None:
    contract = {
        "actor_asset_id": "actor-1", "actor_asset_sha256": "a" * 64, "rig_sha256": "b" * 64,
        "render_sha256": "c" * 64, "style_version": "style-v1", "event": "IMAGE_APPEARS",
        "gaze_target": "monitor_result", "frame_count": 120, "approval": {"status": "APPROVED"},
    }
    decision = authorize_capability({"capability": "actor_reaction", "contract": contract}, scope_id="scene-001", production=True)
    assert decision["allowed"] is False
    assert "human_approval_missing" in decision["reason_codes"]


def test_approval_is_invalidated_when_contract_changes() -> None:
    original = {
        "actor_asset_id": "actor-1", "actor_asset_sha256": "a" * 64, "rig_sha256": "b" * 64,
        "render_sha256": "c" * 64, "style_version": "style-v1", "event": "IMAGE_APPEARS",
        "gaze_target": "monitor_result", "frame_count": 120,
    }
    changed = {**original, "render_sha256": "d" * 64}
    approval = _approval(Capability.ACTOR_REACTION, "scene-001", original, ACTING_CRITERIA, frame_count=120)
    decision = authorize_capability({"capability": "actor_reaction", "contract": changed}, scope_id="scene-001", approvals=[approval], production=True)
    assert decision["allowed"] is False
    assert "human_approval_binding_mismatch" in decision["reason_codes"]


def test_grasp_is_never_generalized_to_production() -> None:
    contract = {
        "action": "GRASP_AND_RETAIN", "actor_asset_id": "patient-v1", "prop_asset_id": "report-v1",
        "actor_asset_sha256": "a" * 64, "prop_asset_sha256": "b" * 64, "rig_sha256": "c" * 64,
        "render_sha256": "d" * 64, "style_version": "style-v1", "renderer": "hyperframes-0.8.46",
        "benchmark_id": "gold-grasp-001", "contact_points": {"actor_grip": [0.5, 0.5], "prop_grip": [0.3, 0.4]},
    }
    decision = authorize_capability({"capability": "grasp_and_retain", "contract": contract}, scope_id="scene-002", production=True)
    assert decision["allowed"] is False
    assert "policy_blocks_production:experiment_only" in decision["reason_codes"]


def test_interaction_ready_cannot_be_global() -> None:
    decision = authorize_capability({"capability": "interaction_ready", "contract": {"global_promotion": True}}, scope_id="asset-pair-001", production=False)
    assert decision["allowed"] is False
    assert "interaction_global_promotion_forbidden" in decision["reason_codes"]


def test_hyperframes_scene_operations_are_allowlisted() -> None:
    contract = {
        "scene_contract_sha256": "a" * 64, "renderer_version": "0.8.46",
        "composition_id": "scene-001", "operations": ["timeline", "raw_javascript"],
    }
    decision = authorize_capability({"capability": "hyperframes_scene", "contract": contract}, scope_id="scene-001", production=False)
    assert decision["allowed"] is False
    assert "hyperframes_operations_not_allowlisted" in decision["reason_codes"]


def test_theory_rule_remains_candidate_in_production() -> None:
    contract = {
        "principle": "event then reaction", "source": "film-theory-source", "scope": "project",
        "expected_effect": "human stakes remain legible", "counterexamples": ["continuous action"],
        "failure_conditions": ["reaction interrupts urgent action"], "confidence": 0.7,
    }
    decision = authorize_capability({"capability": "theory_rule", "contract": contract}, scope_id="project-001", production=True)
    assert decision["allowed"] is False
    assert "policy_blocks_production:candidate_only" in decision["reason_codes"]


def test_expired_approval_is_rejected() -> None:
    contract = {
        "actor_asset_id": "actor-1", "actor_asset_sha256": "a" * 64, "rig_sha256": "b" * 64,
        "render_sha256": "c" * 64, "style_version": "style-v1", "event": "IMAGE_APPEARS",
        "gaze_target": "monitor_result", "frame_count": 120,
    }
    approval = _approval(Capability.ACTOR_REACTION, "scene-001", contract, ACTING_CRITERIA, frame_count=120)
    approval["expires_at"] = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
    with pytest.raises(ValueError, match="human_approval_expired"):
        validate_human_approval(approval, capability=Capability.ACTOR_REACTION, scope_id="scene-001", contract_sha256=approval["contract_sha256"], frame_count=120)
