"""Evidence-bound research intake for reusable actor candidates.

This catalog cannot grant a production or acting approval. Production capability
authorization remains in director_safety and requires a separate human receipt.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


VERSION = "astra-actor-candidate-0.1"
ABILITY_STATUSES = {"VISUAL_EVIDENCE_ONLY", "NOT_BUILT"}


def _rectangle(value: Any, canvas: list[int], name: str) -> None:
    if (not isinstance(value, list) or len(value) != 4
            or any(type(item) not in (int, float) for item in value)):
        raise ValueError(f"actor_{name}_invalid")
    x, y, width, height = value
    if min(x, y) < 0 or width <= 0 or height <= 0 or x + width > canvas[0] or y + height > canvas[1]:
        raise ValueError(f"actor_{name}_out_of_canvas")


def _verified_file(root: Path, evidence: dict[str, Any]) -> Path:
    if not isinstance(evidence, dict):
        raise ValueError("actor_evidence_invalid")
    relative = evidence.get("path")
    expected = evidence.get("sha256")
    if not isinstance(relative, str) or not relative or not isinstance(expected, str) or len(expected) != 64:
        raise ValueError("actor_evidence_invalid")
    resolved_root = root.resolve()
    path = (resolved_root / relative).resolve()
    if resolved_root not in path.parents or not path.is_file():
        raise ValueError("actor_evidence_missing_or_unsafe")
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected.lower():
        raise ValueError("actor_evidence_hash_mismatch")
    return path


def validate_actor_candidate(document: dict[str, Any], *, root: Path) -> dict[str, Any]:
    if not isinstance(document, dict) or document.get("version") != VERSION:
        raise ValueError("actor_candidate_version_invalid")
    if document.get("production_ready") is not False:
        raise ValueError("actor_candidate_cannot_self_approve")
    if document.get("status") != "RESEARCH_CANDIDATE":
        raise ValueError("actor_candidate_status_invalid")
    for key in ("actor_id", "asset_version", "style_id"):
        if not isinstance(document.get(key), str) or not document[key]:
            raise ValueError(f"actor_candidate_{key}_missing")

    video = _verified_file(root, document.get("video"))
    review = _verified_file(root, document.get("human_review"))
    _verified_file(root, document.get("program"))
    review_record = json.loads(review.read_text(encoding="utf-8"))
    if review_record.get("video_sha256") != document["video"]["sha256"]:
        raise ValueError("actor_review_video_mismatch")
    approved_axes = review_record.get("approved_axes")
    if (review_record.get("production_ready") is not False
            or review_record.get("decision") != "PARTIAL_APPROVAL"
            or not isinstance(approved_axes, list)
            or any(not isinstance(axis, str) for axis in approved_axes)
            or not isinstance(document.get("approved_axes"), list)
            or any(not isinstance(axis, str) for axis in document["approved_axes"])
            or sorted(approved_axes) != sorted(document.get("approved_axes", []))):
        raise ValueError("actor_review_scope_mismatch")

    layers = document.get("layers")
    if not isinstance(layers, dict) or not layers:
        raise ValueError("actor_layers_missing")
    for evidence in layers.values():
        _verified_file(root, evidence)
    abilities = document.get("abilities")
    if not isinstance(abilities, dict) or not abilities:
        raise ValueError("actor_abilities_missing")
    if any(status not in ABILITY_STATUSES for status in abilities.values()):
        raise ValueError("actor_ability_cannot_self_approve")
    assembly = document.get("source_assembly")
    if not isinstance(assembly, dict):
        raise ValueError("actor_source_assembly_missing")
    canvas = assembly.get("canvas_px")
    if not isinstance(canvas, list) or len(canvas) != 2 or any(type(item) is not int or item <= 0 for item in canvas):
        raise ValueError("actor_canvas_invalid")
    _rectangle(assembly.get("torso_bounds_px"), canvas, "torso_bounds")
    _rectangle(assembly.get("head_bounds_px"), canvas, "head_bounds")
    pivot = assembly.get("head_pivot_local_px")
    head_width, head_height = assembly["head_bounds_px"][2:]
    if (not isinstance(pivot, list) or len(pivot) != 2
            or any(type(item) not in (int, float) for item in pivot)
            or not 0 <= pivot[0] <= head_width or not 0 <= pivot[1] <= head_height):
        raise ValueError("actor_head_pivot_invalid")
    order = assembly.get("draw_order")
    if (not isinstance(order, list) or len(order) < 2
            or any(not isinstance(item, str) or not item for item in order)
            or len(set(order)) != len(order)):
        raise ValueError("actor_draw_order_invalid")
    constraints = assembly.get("occlusion_constraints")
    if not isinstance(constraints, list) or not constraints:
        raise ValueError("actor_occlusion_constraints_missing")
    for constraint in constraints:
        if (not isinstance(constraint, dict)
                or constraint.get("behind") not in order
                or constraint.get("in_front") not in order
                or order.index(constraint["behind"]) >= order.index(constraint["in_front"])):
            raise ValueError("actor_occlusion_order_invalid")
    return {
        "actor_id": document["actor_id"],
        "asset_version": document["asset_version"],
        "status": "EVIDENCE_VERIFIED_HUMAN_SCOPE_LIMITED",
        "video_path": str(video),
        "approved_axes": approved_axes,
        "abilities": abilities,
        "source_assembly": assembly,
        "assembly_verified_against_program": False,
        "production_ready": False,
    }
