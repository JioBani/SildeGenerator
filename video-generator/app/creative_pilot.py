"""Evidence gate for the isolated story-and-movable-design production pilot.

This gate records what is authored and reviewed. It never promotes an
experimental layer or a scoped human compliment into production approval.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


VERSION = "astra-creative-pilot-0.1"
ASSET_ROUTES = {"whole_frame_cutout", "separately_authored_layers", "editable_graphic"}
REVIEW_AXES = {"design", "acting", "comprehension", "immersion", "assembly"}
SCOPED_AXIS_SUPPORT = {
    "acting": {"performance_naturalness_vs_C", "character_response", "facial_expression"},
    "assembly": {"neck_clothing_join"},
}


def _artifact(root: Path, row: dict[str, Any], label: str) -> tuple[str | None, str | None]:
    relative = row.get("path")
    expected = row.get("sha256")
    if not isinstance(relative, str) or not relative or not isinstance(expected, str) or len(expected) != 64:
        return None, f"{label}:artifact_receipt_missing"
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        return None, f"{label}:artifact_missing_or_outside_root"
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    actual = digest.hexdigest()
    if actual != expected.lower():
        return None, f"{label}:artifact_hash_mismatch"
    return actual, None


def evaluate_pilot(contract: dict[str, Any], root: Path) -> dict[str, Any]:
    """Check an authored pilot without trusting its own readiness flags."""
    errors: list[str] = []
    pending: list[str] = []
    evidence: list[dict[str, str]] = []
    scoped_positives: list[dict[str, Any]] = []
    if contract.get("version") != VERSION:
        errors.append("contract_version_unsupported")
    scene_id = contract.get("scene_id")
    story = contract.get("story") or {}
    for key in ("audience_question", "subject", "subject_goal", "stimulus", "perception",
                "explanation", "resulting_state", "viewer_takeaway"):
        if not isinstance(story.get(key), str) or not story[key].strip():
            errors.append(f"story:{key}_missing")
    if not story.get("action_observed"):
        pending.append("story:subject_action_not_shown")
    if not story.get("viewer_change_observed"):
        pending.append("story:viewer_change_not_measured")
    fact_check = contract.get("fact_check") or {}
    if fact_check.get("status") not in {"VERIFIED", "EXPERIMENTAL_CLAIM"} or not fact_check.get("claim_scope"):
        errors.append("story:fact_check_contract_missing")
    if fact_check.get("status") != "VERIFIED":
        pending.append("story:fact_claim_requires_review")

    references = contract.get("references") or []
    if not references:
        errors.append("references:missing")
    reference_ids: set[str] = set()
    for card in references:
        ref_id = card.get("id")
        if not ref_id or ref_id in reference_ids:
            errors.append("references:id_missing_or_duplicate")
            continue
        reference_ids.add(ref_id)
        for key in ("source_url", "observed", "inferred_principle", "non_copy_boundary"):
            if not card.get(key):
                errors.append(f"references:{ref_id}:{key}_missing")
        if card.get("use") != "analysis_only" or card.get("asset_reuse") is not False:
            errors.append(f"references:{ref_id}:reuse_not_cleared")

    design = contract.get("design") or {}
    candidates = design.get("candidates") or []
    candidate_ids = [item.get("id") for item in candidates]
    if len(candidates) < 2 or None in candidate_ids or len(set(candidate_ids)) != len(candidate_ids):
        errors.append("design:two_distinct_candidates_required")
    if design.get("selected_id") not in candidate_ids:
        errors.append("design:selection_missing")
    if not design.get("selection_reason"):
        errors.append("design:selection_reason_missing")
    if not design.get("reference_ids") or not set(design["reference_ids"]).issubset(reference_ids):
        errors.append("design:reference_link_invalid")

    targets = contract.get("motion_targets") or []
    assets = contract.get("assets") or []
    by_target: dict[str, list[dict[str, Any]]] = {}
    for asset in assets:
        by_target.setdefault(asset.get("object_id", ""), []).append(asset)
        asset_id = asset.get("id") or "unknown"
        if asset.get("route") not in ASSET_ROUTES:
            errors.append(f"asset:{asset_id}:route_unsupported")
        for key in ("pivot", "draw_order", "hidden_area_policy", "states", "contact_points"):
            if key not in asset:
                errors.append(f"asset:{asset_id}:{key}_missing")
        pivot = asset.get("pivot")
        if not isinstance(pivot, list) or len(pivot) != 2 or any(
            not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= 1
            for value in pivot
        ):
            errors.append(f"asset:{asset_id}:pivot_invalid")
        layers = asset.get("layers") or []
        order = asset.get("draw_order") or []
        if not isinstance(layers, list) or not isinstance(order, list) or len(order) != len(set(order)) or not set(order).issubset(layers):
            errors.append(f"asset:{asset_id}:draw_order_invalid")
        for join in asset.get("joins") or []:
            covered, occluder = join.get("covered_layer"), join.get("occluder")
            if covered not in order or occluder not in order or order.index(covered) >= order.index(occluder):
                errors.append(f"asset:{asset_id}:occlusion_order_invalid")
            if not join.get("overlap_extent") or join.get("line_owner") != occluder:
                errors.append(f"asset:{asset_id}:join_authorship_missing")
        if asset.get("route") != "editable_graphic" and not asset.get("layers"):
            errors.append(f"asset:{asset_id}:layers_missing")
        if asset.get("rights") not in {"self_generated", "approved_license"}:
            errors.append(f"asset:{asset_id}:rights_unverified")
        for index, source in enumerate(asset.get("sources") or []):
            digest, error = _artifact(root, source, f"asset:{asset_id}:{index}")
            if error:
                errors.append(error)
            else:
                evidence.append({"kind": "asset", "id": asset_id, "sha256": digest})
        if not asset.get("sources"):
            pending.append(f"asset:{asset_id}:not_authored")
        if asset.get("human_review") != "APPROVED":
            pending.append(f"asset:{asset_id}:human_review_required")
        if asset.get("contact_points") and asset.get("contact_review") != "APPROVED":
            pending.append(f"asset:{asset_id}:contact_review_required")
    for target in targets:
        if not by_target.get(target):
            errors.append(f"motion_target:{target}:asset_plan_missing")

    samples = contract.get("samples") or []
    if not samples:
        pending.append("sample:representative_motion_missing")
    sample_hashes_by_path = {sample.get("path"): sample.get("sha256") for sample in samples}
    for sample in samples:
        sample_id = sample.get("id") or "unknown"
        digest, error = _artifact(root, sample, f"sample:{sample_id}")
        if error:
            errors.append(error)
            continue
        evidence.append({"kind": "sample", "id": sample_id, "sha256": digest})
        receipt = sample.get("scoped_review_receipt")
        if receipt:
            review_digest, review_error = _artifact(root, receipt, f"sample:{sample_id}:review")
            if review_error:
                errors.append(review_error)
            else:
                try:
                    review = json.loads((root / receipt["path"]).read_text(encoding="utf-8"))
                except (OSError, UnicodeError, json.JSONDecodeError):
                    review = {}
                if not isinstance(review, dict):
                    review = {}
                compared_path = review.get("compared_artifact")
                comparison_mismatch = bool(compared_path) and (
                    sample_hashes_by_path.get(compared_path) != review.get("compared_video_sha256"))
                if (review.get("video_sha256") != digest or comparison_mismatch or
                    review.get("resolved_artifact") != sample.get("path") or
                    review.get("decision") != "PARTIAL_APPROVAL" or
                    not review.get("verbatim_feedback")):
                    errors.append(f"sample:{sample_id}:scoped_review_artifact_mismatch")
                else:
                    scoped_positives.append({"sample_id": sample_id,
                                             "axes": review.get("approved_axes") or [],
                                             "video_sha256": digest})
                    evidence.append({"kind": "human_review", "id": sample_id, "sha256": review_digest})
        if sample.get("technical_review") != "PASS":
            pending.append(f"sample:{sample_id}:technical_review_required")
        if sample.get("full_motion_path_review") != "PASS":
            pending.append(f"sample:{sample_id}:full_motion_path_review_required")
        reviews = sample.get("human_reviews") or {}
        for axis in REVIEW_AXES:
            row = reviews.get(axis) or {}
            if row.get("video_sha256") != digest or row.get("decision") not in {"PASS", "REVISE", "FAIL"}:
                supported = next((item["axes"] for item in scoped_positives if item["sample_id"] == sample_id), [])
                qualifier = "full_review_required" if SCOPED_AXIS_SUPPORT.get(axis, set()).intersection(supported) else "review_required"
                pending.append(f"sample:{sample_id}:{axis}_{qualifier}")
            elif row["decision"] != "PASS":
                pending.append(f"sample:{sample_id}:{axis}_{row['decision'].lower()}")
    sample_ids = {sample.get("id") for sample in samples}
    for revision in contract.get("revisions") or []:
        revision_id = revision.get("id") or "unknown"
        if revision.get("before") not in sample_ids or revision.get("after") not in sample_ids:
            errors.append(f"revision:{revision_id}:sample_link_invalid")
        if not all(revision.get(key) for key in ("failure", "cause", "correction")):
            errors.append(f"revision:{revision_id}:reasoning_missing")
        if revision.get("human_outcome") == "PASS_SCOPED":
            pending.append(f"revision:{revision_id}:full_outcome_review_required")
        elif revision.get("human_outcome") != "PASS":
            pending.append(f"revision:{revision_id}:human_outcome_required")
    return {
        "version": VERSION,
        "scene_id": scene_id,
        "status": "INVALID_CONTRACT" if errors else "EXPERIMENT_REVIEW_REQUIRED",
        "production_ready": False,
        "errors": sorted(set(errors)),
        "pending": sorted(set(pending)),
        "evidence": evidence,
        "scoped_positives": scoped_positives,
        "claim_limit": "Experimental scene only; no automatic production or cross-script transfer approval.",
    }
