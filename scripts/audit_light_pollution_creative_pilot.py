"""Bind the existing light-pollution A/B/C/D evidence to the new pilot gate."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "experiments" / "light-pollution-story-asset-v1"


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_contract() -> dict:
    brief = _json(STUDY / "creative-brief.json")
    c_receipt = _json(STUDY / "C" / "revision-contract.json")
    d_receipt = _json(STUDY / "D" / "receipt.json")
    return {
        "version": "astra-creative-pilot-0.1",
        "scene_id": brief["scene_id"],
        "story": {
            "audience_question": brief["audience_question"],
            "subject": brief["narrative_subject"],
            "subject_goal": "Sleep without intrusive street light",
            "stimulus": brief["stimulus"],
            "perception": brief["perception"],
            "explanation": "Outdoor light enters a bedroom and interrupts the person's rest.",
            "resulting_state": brief["subject_state_after"],
            "viewer_takeaway": brief["viewer_takeaway"],
            "action_observed": False,
            "viewer_change_observed": False,
        },
        "fact_check": {
            "status": "EXPERIMENTAL_CLAIM",
            "claim_scope": "The scene depicts noticed bedroom light, not a diagnosed sleep or health effect.",
            "source_reference_ids": ["ref-human-health"],
        },
        "references": [{
            "id": row["id"], "source_url": row["url"], "observed": row["observed"],
            "inferred_principle": row["role"],
            "non_copy_boundary": "Use the causal design principle, not the source composition or artwork.",
            "use": "analysis_only", "asset_reuse": False,
        } for row in brief["references"]],
        "design": {
            "candidates": [
                {"id": "A-diagram", "story": "Explain external light as a diagram", "asset_route": "editable_graphic"},
                {"id": "B-lived-room", "story": "Show light affecting a tired person", "asset_route": "separately_authored_layers"},
            ],
            "selected_id": "B-lived-room",
            "selection_reason": "Test whether a visible cause followed by a human reaction improves understanding; not yet demonstrated.",
            "reference_ids": [row["id"] for row in brief["references"]],
            "style": brief["design_decision"],
        },
        "motion_targets": ["person", "light"],
        "assets": [
            {
                "id": "person-reaction", "object_id": "person", "route": "separately_authored_layers",
                "layers": ["torso", "head_and_neck", "collar-front", "eyes", "mouth"],
                "pivot": [1336 / 1920, 566 / 1080], "draw_order": d_receipt["draw_order"],
                "joins": [{"occluder": d_receipt["occluder"], **d_receipt["join"]}],
                "hidden_area_policy": "authored neck tail under collar; limited head rotation",
                "states": ["tired", "notice", "squint"], "contact_points": ["head-neck", "hand-cheek"],
                "rights": "self_generated", "human_review": "PENDING", "contact_review": "PENDING",
                "sources": [
                    {"path": "assets/person-body.png", "sha256": c_receipt["asset_sha256"]["person-body.png"]},
                    {"path": "assets/person-head-neutral.png", "sha256": c_receipt["asset_sha256"]["person-head-neutral.png"]},
                    {"path": "assets/person-head-squint-v3.png", "sha256": c_receipt["asset_sha256"]["person-head-squint-v3.png"]},
                    {"path": "assets/person-neck-overlap-v4b.png", "sha256": d_receipt["neck_asset_sha256"]},
                ],
            },
            {
                "id": "window-light", "object_id": "light", "route": "editable_graphic",
                "layers": ["room", "streetlamp", "beam", "face-illumination", "person"],
                "pivot": [0.28, 0.25], "draw_order": ["room", "beam", "person"],
                "hidden_area_policy": "not applicable to authored light geometry",
                "states": ["off", "on", "face-lit"], "contact_points": [],
                "rights": "self_generated", "human_review": "PENDING",
                "sources": [{"path": "C/project/index.html", "sha256": c_receipt["html_sha256"]}],
            },
        ],
        "samples": [
            {"id": "C-reaction", "path": "C/comparison.mp4", "sha256": c_receipt["video_sha256"],
             "technical_review": "PASS", "full_motion_path_review": "PENDING", "human_reviews": {},
             "scoped_review_receipt": {"path": "C/human-review-lighting-acting.json",
                                       "sha256": "5e2791b0b4efcd741ff1e45ee82348c3f1e42e013764f1695649ee69de3194c0"}},
            {"id": "D-collar", "path": "D/comparison.mp4", "sha256": d_receipt["video_sha256"],
             "technical_review": "PASS", "full_motion_path_review": "PENDING", "human_reviews": {},
             "scoped_review_receipt": {"path": "D/human-review-naturalness.json",
                                       "sha256": "61cf3cf34461341e676c6bb24f9461d096ac10a767ae6f13456e98f6844c1b24"}},
        ],
        "revisions": [{
            "id": "C-to-D-collar", "before": "C-reaction", "after": "D-collar",
            "failure": "Visible neckline gap and skin shading boundary",
            "cause": "Head-neck artwork ended in the visible shirt opening; an opaque patch did not match shaded skin.",
            "correction": "Extend authored neck under a front collar layer while preserving the partially approved light and face timing.",
            "human_outcome": "PASS_SCOPED",
        }],
        "best_human_approved_sample": None,
        "preferred_sample_for_naturalness_and_join": "D-collar",
        "cost": {"paid_api_calls": 0, "additional_generation": False},
    }


def main() -> None:
    sys.path.insert(0, str(ROOT / "video-generator"))
    from app.creative_pilot import evaluate_pilot

    contract = build_contract()
    result = evaluate_pilot(contract, STUDY)
    (STUDY / "creative-pilot-contract.json").write_text(
        json.dumps(contract, ensure_ascii=False, indent=2), encoding="utf-8")
    (STUDY / "creative-pilot-audit.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": result["status"], "errors": result["errors"],
                      "pending": result["pending"], "evidence_count": len(result["evidence"])},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
