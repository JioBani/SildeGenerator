from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from typing import Any, Iterable

from .mesh_evidence import THRESHOLD_POLICY, evaluate_mesh_evidence


VERSION = "astra-director-safety-1.0"
SHA256_LENGTH = 64
MAX_EVIDENCE_FILE_BYTES = 2 * 1024 * 1024 * 1024
MESH_MAX_DISPLACEMENT_RATIO = THRESHOLD_POLICY["max_vertex_displacement_ratio"]


class Capability(StrEnum):
    ACTOR_REACTION = "actor_reaction"
    LIMITED_MESH = "limited_mesh"
    GRASP_AND_RETAIN = "grasp_and_retain"
    INTERACTION_READY = "interaction_ready"
    HYPERFRAMES_SCENE = "hyperframes_scene"
    THEORY_RULE = "theory_rule"


class Policy(StrEnum):
    HUMAN_REVIEW_REQUIRED = "human_review_required"
    EXPERIMENT_ONLY = "experiment_only"
    CANDIDATE_ONLY = "candidate_only"


POLICIES = {
    Capability.ACTOR_REACTION: Policy.HUMAN_REVIEW_REQUIRED,
    Capability.LIMITED_MESH: Policy.EXPERIMENT_ONLY,
    Capability.GRASP_AND_RETAIN: Policy.EXPERIMENT_ONLY,
    Capability.INTERACTION_READY: Policy.HUMAN_REVIEW_REQUIRED,
    Capability.HYPERFRAMES_SCENE: Policy.HUMAN_REVIEW_REQUIRED,
    Capability.THEORY_RULE: Policy.CANDIDATE_ONLY,
}

ACTING_CRITERIA = {
    "intent", "silhouette", "preparation", "weight", "gaze",
    "joint_coherence", "settle", "identity", "support", "style",
}
MESH_CRITERIA = {
    "same_camera_timing_expression", "hidden_regions", "neutral_reassembly",
    "no_tearing", "no_rubbery_distortion", "design_preserved",
    "benefit_over_baseline",
}
GRASP_CRITERIA = ACTING_CRITERIA | {
    "approach", "contact_alignment", "ownership_transfer", "retain_without_sliding",
}


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _inside_roots(path: Path, roots: Iterable[Path]) -> bool:
    resolved = path.resolve(strict=True)
    return any(resolved.is_relative_to(root.resolve(strict=True)) for root in roots)


def verify_bound_file(reference: dict[str, Any], *, roots: Iterable[Path]) -> Path:
    if not isinstance(reference, dict):
        raise ValueError("evidence_reference_invalid")
    raw_path = reference.get("path")
    expected = reference.get("sha256")
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise ValueError("evidence_path_missing")
    if not isinstance(expected, str) or len(expected) != SHA256_LENGTH:
        raise ValueError("evidence_sha256_invalid")
    path = Path(raw_path)
    if not path.is_absolute() or not path.is_file():
        raise ValueError("evidence_file_missing")
    if not _inside_roots(path, roots):
        raise ValueError("evidence_path_outside_workspace")
    if path.stat().st_size > MAX_EVIDENCE_FILE_BYTES:
        raise ValueError("evidence_file_too_large")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() != expected:
        raise ValueError("evidence_file_stale")
    return path.resolve()


def _parse_time(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field}_missing")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"{field}_invalid") from error
    if result.tzinfo is None:
        raise ValueError(f"{field}_timezone_missing")
    return result.astimezone(timezone.utc)


def _criteria_for(capability: Capability) -> set[str]:
    if capability == Capability.LIMITED_MESH:
        return MESH_CRITERIA
    if capability == Capability.GRASP_AND_RETAIN:
        return GRASP_CRITERIA
    if capability == Capability.ACTOR_REACTION:
        return ACTING_CRITERIA
    return {"scope", "evidence", "limitations"}


def validate_human_approval(
    approval: dict[str, Any],
    *,
    capability: Capability,
    scope_id: str,
    contract_sha256: str,
    frame_count: int | None = None,
    now: datetime | None = None,
) -> None:
    if not isinstance(approval, dict):
        raise ValueError("human_approval_missing")
    expected = {
        "version": VERSION,
        "capability": capability.value,
        "scope_id": scope_id,
        "contract_sha256": contract_sha256,
        "reviewer_kind": "human",
        "status": "APPROVED",
    }
    if any(approval.get(key) != value for key, value in expected.items()):
        raise ValueError("human_approval_binding_mismatch")
    if not isinstance(approval.get("reviewer_id"), str) or not approval["reviewer_id"].strip():
        raise ValueError("human_reviewer_missing")
    reviewed_at = _parse_time(approval.get("reviewed_at"), "reviewed_at")
    clock = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    if reviewed_at > clock:
        raise ValueError("reviewed_at_in_future")
    if approval.get("expires_at") is not None and _parse_time(approval["expires_at"], "expires_at") <= clock:
        raise ValueError("human_approval_expired")
    criteria = approval.get("criteria")
    required = _criteria_for(capability)
    if not isinstance(criteria, dict) or set(criteria) != required:
        raise ValueError("human_review_criteria_incomplete")
    for name in sorted(required):
        row = criteria[name]
        if not isinstance(row, dict) or row.get("status") != "PASS":
            raise ValueError(f"human_review_requires_revision:{name}")
        if not isinstance(row.get("reason"), str) or not row["reason"].strip():
            raise ValueError(f"human_review_reason_missing:{name}")
        frames = row.get("frames", [])
        if frame_count is not None:
            if not isinstance(frames, list) or not frames:
                raise ValueError(f"human_review_frame_evidence_missing:{name}")
            if any(type(frame) is not int or not 0 <= frame < frame_count for frame in frames):
                raise ValueError(f"human_review_frame_evidence_invalid:{name}")


def _validate_mesh_contract(contract: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if contract.get("contract_version") != "limited-mesh-v2":
        reasons.append("limited_mesh_v2_required")
    if contract.get("mode") != "limited_mesh":
        reasons.append("unsupported_mesh_mode")
    if not isinstance(contract.get("reason"), str) or not contract["reason"].strip():
        reasons.append("mesh_selection_reason_missing")
    regions = contract.get("regions")
    if not isinstance(regions, list) or not regions or not set(regions) <= {"neck", "shoulder", "torso"}:
        reasons.append("unsupported_mesh_regions")
    limit = contract.get("max_displacement_ratio")
    if type(limit) not in (int, float) or not math.isfinite(limit) or not 0 < limit <= MESH_MAX_DISPLACEMENT_RATIO:
        reasons.append("mesh_displacement_budget_exceeded")
    for field in (
        "asset_sha256", "rig_sha256", "hidden_region_sha256", "baseline_render_sha256",
        "candidate_render_sha256", "topology_sha256", "rest_mesh_sha256",
        "weight_map_sha256", "rigidity_map_sha256",
    ):
        value = contract.get(field)
        if not isinstance(value, str) or len(value) != SHA256_LENGTH:
            reasons.append(f"mesh_binding_missing:{field}")
    reference = contract.get("reference_length")
    if not isinstance(reference, dict) or reference.get("type") not in {"shoulder_width", "head_height"}:
        reasons.append("mesh_reference_length_type_invalid")
    elif type(reference.get("value_px")) not in (int, float) or not math.isfinite(reference["value_px"]) or reference["value_px"] <= 0:
        reasons.append("mesh_reference_length_value_invalid")
    boundaries = contract.get("boundaries")
    if not isinstance(boundaries, list) or not boundaries or not set(boundaries) <= {"head_neck", "neck_torso", "shoulder_torso"}:
        reasons.append("mesh_boundaries_invalid")
    occlusion = contract.get("occlusion_policy")
    if not isinstance(occlusion, dict) or occlusion.get("static_z_order") is not True:
        reasons.append("mesh_dynamic_occlusion_not_approved")
    reasons.extend(evaluate_mesh_evidence(contract.get("evidence", {}), contract.get("thresholds", {})))
    return reasons


def _validate_grasp_contract(contract: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if contract.get("action") != "GRASP_AND_RETAIN":
        reasons.append("unsupported_interaction_action")
    for field in ("actor_asset_sha256", "prop_asset_sha256", "rig_sha256", "render_sha256"):
        value = contract.get(field)
        if not isinstance(value, str) or len(value) != SHA256_LENGTH:
            reasons.append(f"interaction_binding_missing:{field}")
    for field in ("actor_asset_id", "prop_asset_id", "style_version", "renderer", "benchmark_id"):
        if not isinstance(contract.get(field), str) or not contract[field].strip():
            reasons.append(f"interaction_binding_missing:{field}")
    contacts = contract.get("contact_points")
    if not isinstance(contacts, dict) or not {"actor_grip", "prop_grip"} <= set(contacts):
        reasons.append("interaction_contact_points_missing")
    return reasons


def validate_capability_contract(capability: Capability, contract: dict[str, Any]) -> list[str]:
    if not isinstance(contract, dict):
        return ["capability_contract_invalid"]
    if capability == Capability.LIMITED_MESH:
        return _validate_mesh_contract(contract)
    if capability == Capability.GRASP_AND_RETAIN:
        return _validate_grasp_contract(contract)
    if capability == Capability.ACTOR_REACTION:
        reasons: list[str] = []
        for field in ("actor_asset_id", "style_version", "event", "gaze_target"):
            if not isinstance(contract.get(field), str) or not contract[field].strip():
                reasons.append(f"reaction_binding_missing:{field}")
        for field in ("actor_asset_sha256", "rig_sha256", "render_sha256"):
            value = contract.get(field)
            if not isinstance(value, str) or len(value) != SHA256_LENGTH:
                reasons.append(f"reaction_binding_missing:{field}")
        if type(contract.get("frame_count")) is not int or contract["frame_count"] <= 0:
            reasons.append("reaction_frame_count_invalid")
        return reasons
    if capability == Capability.INTERACTION_READY:
        reasons = []
        if contract.get("global_promotion") is not False:
            reasons.append("interaction_global_promotion_forbidden")
        for field in ("asset_pair_id", "production_version_id", "benchmark_id"):
            if not isinstance(contract.get(field), str) or not contract[field].strip():
                reasons.append(f"interaction_binding_missing:{field}")
        for field in ("actor_a_sha256", "actor_b_sha256", "action_evidence_sha256", "render_sha256"):
            value = contract.get(field)
            if not isinstance(value, str) or len(value) != SHA256_LENGTH:
                reasons.append(f"interaction_binding_missing:{field}")
        return reasons
    if capability == Capability.HYPERFRAMES_SCENE:
        reasons = []
        for field in ("scene_contract_sha256", "renderer_version", "composition_id"):
            if not isinstance(contract.get(field), str) or not contract[field].strip():
                reasons.append(f"hyperframes_binding_missing:{field}")
        operations = contract.get("operations")
        allowed_operations = {"independent_transform", "path_follow", "state_swap", "camera", "text", "mask", "timeline"}
        if not isinstance(operations, list) or not operations or not set(operations) <= allowed_operations:
            reasons.append("hyperframes_operations_not_allowlisted")
        return reasons
    if capability == Capability.THEORY_RULE:
        required = ("principle", "source", "scope", "expected_effect", "counterexamples", "failure_conditions")
        if any(not contract.get(field) for field in required):
            return ["theory_candidate_provenance_incomplete"]
        confidence = contract.get("confidence")
        if type(confidence) not in (int, float) or not 0 <= confidence <= 1:
            return ["theory_candidate_confidence_invalid"]
    return []


def authorize_capability(
    request: dict[str, Any],
    *,
    scope_id: str,
    approvals: Iterable[dict[str, Any]] = (),
    production: bool,
) -> dict[str, Any]:
    raw_capability = request.get("capability") if isinstance(request, dict) else None
    try:
        capability = Capability(raw_capability)
    except (TypeError, ValueError):
        return {"allowed": False, "capability": raw_capability, "reason_codes": ["unknown_capability"]}
    contract = request.get("contract")
    reasons = validate_capability_contract(capability, contract)
    contract_hash = canonical_sha256({"capability": capability.value, "scope_id": scope_id, "contract": contract})
    policy = POLICIES[capability]
    if production and policy in {Policy.EXPERIMENT_ONLY, Policy.CANDIDATE_ONLY}:
        reasons.append(f"policy_blocks_production:{policy.value}")
    matching = [value for value in approvals if isinstance(value, dict) and value.get("capability") == capability.value and value.get("scope_id") == scope_id]
    if not matching:
        reasons.append("human_approval_missing")
    else:
        try:
            validate_human_approval(
                matching[-1], capability=capability, scope_id=scope_id,
                contract_sha256=contract_hash, frame_count=contract.get("frame_count") if isinstance(contract, dict) else None,
            )
        except ValueError as error:
            reasons.append(str(error))
    return {
        "allowed": not reasons,
        "capability": capability.value,
        "policy": policy.value,
        "scope_id": scope_id,
        "contract_sha256": contract_hash,
        "reason_codes": sorted(set(reasons)),
        "promotion_scope": "production_version_only" if not reasons else "none",
        "automatic_promotion": False,
    }


def evaluate_scene_requests(
    renderer_requirements: dict[str, Any],
    *,
    scene_id: str,
    approvals: Iterable[dict[str, Any]] = (),
    production: bool,
) -> list[dict[str, Any]]:
    requests = renderer_requirements.get("experimental_capabilities", []) if isinstance(renderer_requirements, dict) else []
    if requests is None:
        requests = []
    if not isinstance(requests, list):
        return [{"allowed": False, "capability": None, "reason_codes": ["experimental_capabilities_invalid"]}]
    if len(requests) > len(Capability):
        return [{"allowed": False, "capability": None, "reason_codes": ["experimental_capabilities_limit_exceeded"]}]
    return [authorize_capability(request, scope_id=scene_id, approvals=approvals, production=production) for request in requests]
