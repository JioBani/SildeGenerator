"""Pre-asset evidence for narrative, reference, and movable-design readiness.

This is advisory until authored design and human review can be bound to an exact
production artifact. It must never turn a flattened scene into an approved rig.
"""

from __future__ import annotations

from typing import Any

from .models import ScenePlan


VERSION = "astra-creative-readiness-0.1"
INDEPENDENT_MOTION = {"path_follow", "group_split", "state_change", "reaction"}


def _asset_authoring_intent(subject: dict[str, Any], motion_kind: str) -> dict[str, Any]:
    role = str(subject.get("role") or "").lower()
    if any(token in role for token in ("actor", "person", "character", "human")):
        route = "separately_authored_layers"
        layers = ["torso", "head", "eyes", "eyebrows", "mouth"] if motion_kind == "reaction" else ["body", "moving_limb", "contact_surface"]
    elif any(token in role for token in ("graphic", "diagram", "label", "path", "number")):
        route = "editable_graphic"
        layers = ["editable_marks", "labels"]
    else:
        route = "whole_frame_cutout"
        layers = ["subject_rgba", "repaired_background", "occlusion_or_shadow"]
    return {
        "proposed_route": route,
        "required_layers": layers,
        "required_evidence": ["source_hash", "pivot_and_draw_order", "hidden_area_coverage", "full_motion_path_review", "human_design_review"],
        "assembly_requirements": ["motion_parent_separate_from_draw_order", "covered_layer", "front_occluder", "overlap_extent", "line_owner"] if route == "separately_authored_layers" else [],
        "route_approved": False,
    }


def evaluate_creative_readiness(
    plan: ScenePlan, *, harness_id: str, reference_cards: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    cards = reference_cards or []
    reference_ids = {card.get("id") for card in cards if isinstance(card, dict)}
    findings: list[str] = []
    scenes: list[dict[str, Any]] = []
    if not cards:
        findings.append("design_references_not_supplied")
    for scene in plan.scenes:
        objects = {row.get("object_id"): row for row in scene.object_states if isinstance(row, dict)}
        moving = []
        for action in scene.motion:
            if not isinstance(action, dict) or action.get("kind") not in INDEPENDENT_MOTION:
                continue
            object_id = action.get("object_id")
            subject = objects.get(object_id) or {}
            missing = []
            if not subject:
                missing.append("object_state")
            if subject.get("isolation") == "not_needed":
                missing.append("movable_object_not_isolated")
            if not subject.get("region_hint"):
                missing.append("region_hint")
            # Current ScenePlan cannot specify pivots or hidden-art coverage.
            missing.extend(("pivot", "hidden_area_policy", "reviewed_source_asset"))
            moving.append({
                "object_id": object_id, "motion_kind": action["kind"],
                "asset_route": "DESIGN_DECISION_REQUIRED", "missing": missing,
                "authoring_plan": _asset_authoring_intent(subject, action["kind"]),
            })
            findings.extend(f"{scene.id}:{object_id}:{item}" for item in missing)
        scene_card_ids = [card["id"] for card in cards if card.get("scene_id") == scene.id and card.get("id") in reference_ids]
        if not scene_card_ids:
            findings.append(f"{scene.id}:design_reference_missing")
        scenes.append({
            "scene_id": scene.id,
            "scene_function": scene.scene_function,
            "viewer_takeaway": scene.viewer_takeaway,
            "reference_card_ids": scene_card_ids,
            "narrative_subject": "NOT_SPECIFIED",
            "subject_goal": "NOT_SPECIFIED",
            "perception_or_decision": "NOT_SPECIFIED",
            "movable_asset_intents": moving,
        })
    return {
        "version": VERSION,
        "harness_id": harness_id,
        "status": "DESIGN_AND_STORY_REVIEW_REQUIRED",
        "core_question": plan.core_question,
        "audience_start_state": plan.audience_start_state,
        "audience_end_state": plan.audience_end_state,
        "reference_cards": cards,
        "scenes": scenes,
        "findings": sorted(set(findings)),
        "production_ready": False,
        "human_review_required": True,
    }
