from __future__ import annotations

from typing import Any


VERSION = "astra-motion-asset-manifest-2.0"
INDEPENDENT_USES = {"independent_transform", "path_follow", "state_swap", "deformable_rig"}
SEPARATED_SOURCES = {"raster_rgba", "layered_raster", "svg", "rive", "lottie", "three_d", "procedural"}
REVIEW_KEYS = {"silhouette", "alpha_edge", "contact", "style_consistency"}
RUNTIME_ANCHOR_PREFIXES = {
    "rive": "rive_transform:", "svg": "css:", "three_d": "bone:",
    "lottie": "layer:", "procedural": "css:",
}


def _point(value: Any, name: str, *, allow_none: bool = True) -> list[float] | None:
    if value is None and allow_none:
        return None
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError(f"{name} must be a normalized [x, y] pair")
    pair = [float(value[0]), float(value[1])]
    if any(item < 0 or item > 1 for item in pair):
        raise ValueError(f"{name} must stay inside normalized bounds")
    return pair


def validate_asset(asset: dict[str, Any], *, target: str) -> dict[str, Any]:
    required = {
        "id", "kind", "source", "source_sha256", "source_type", "motion_use",
        "anchor", "pivot", "depth_band", "states", "contact_points",
        "hidden_area_policy", "reviews", "rights", "production_ready",
    }
    missing = sorted(required - set(asset))
    if missing:
        raise ValueError("motion_asset_missing:" + ",".join(missing))
    asset_id = asset["id"]
    source_sha256 = asset["source_sha256"]
    if not isinstance(source_sha256, str) or len(source_sha256) != 64:
        raise ValueError(f"{asset_id}.source_sha256_invalid")
    use = asset["motion_use"]
    source_type = asset["source_type"]
    anchor = _point(asset["anchor"], f"{asset_id}.anchor")
    pivot = _point(asset["pivot"], f"{asset_id}.pivot")
    states = asset["states"]
    contacts = asset["contact_points"]
    runtime_anchors = asset.get("runtime_anchors", {})
    if not isinstance(states, list) or len(states) != len(set(states)):
        raise ValueError(f"{asset_id}.states_not_unique")
    if not isinstance(contacts, dict):
        raise ValueError(f"{asset_id}.contact_points_invalid")
    contacts = {name: _point(value, f"{asset_id}.contact_points.{name}", allow_none=False) for name, value in contacts.items()}
    if not isinstance(runtime_anchors, dict):
        raise ValueError(f"{asset_id}.runtime_anchors_invalid")
    if use in INDEPENDENT_USES and source_type not in SEPARATED_SOURCES:
        raise ValueError(f"{asset_id}.flattened_source_forbidden")
    if use in {"independent_transform", "path_follow", "deformable_rig"} and pivot is None:
        raise ValueError(f"{asset_id}.pivot_required")
    if use in {"independent_transform", "path_follow"} and anchor is None:
        raise ValueError(f"{asset_id}.anchor_required")
    if use == "path_follow" and not contacts:
        raise ValueError(f"{asset_id}.contact_point_required")
    if use == "state_swap" and len(states) < 2:
        raise ValueError(f"{asset_id}.state_swap_requires_two_states")
    if use == "deformable_rig" and (len(asset.get("joints", [])) < 2 or len(states) < 2):
        raise ValueError(f"{asset_id}.deformable_rig_incomplete")
    reviews = asset["reviews"]
    if not isinstance(reviews, dict) or set(reviews) != REVIEW_KEYS:
        raise ValueError(f"{asset_id}.review_shape_invalid")
    if target == "production":
        if use == "deformable_rig" and contacts:
            missing_bindings = sorted(set(contacts) - set(runtime_anchors))
            if missing_bindings:
                raise ValueError(f"{asset_id}.runtime_anchor_missing:" + ",".join(missing_bindings))
            prefix = RUNTIME_ANCHOR_PREFIXES.get(source_type)
            if prefix and any(not isinstance(runtime_anchors[name], str) or not runtime_anchors[name].startswith(prefix) for name in contacts):
                raise ValueError(f"{asset_id}.runtime_anchor_type_mismatch")
        if asset["production_ready"] is not True:
            raise ValueError(f"{asset_id}.production_ready_false")
        if asset["rights"] != "approved":
            raise ValueError(f"{asset_id}.rights_not_approved")
        if not all(value is True for value in reviews.values()):
            raise ValueError(f"{asset_id}.reviews_incomplete")
        if asset["hidden_area_policy"] == "prototype_unresolved":
            raise ValueError(f"{asset_id}.hidden_areas_unresolved")
        if use == "deformable_rig" and asset.get("maturity") == "INTERACTION_READY":
            raise ValueError(f"{asset_id}.interaction_ready_requires_external_human_approval")
    return {**asset, "anchor": anchor, "pivot": pivot, "contact_points": contacts, "runtime_anchors": runtime_anchors}


def validate_manifest(document: dict[str, Any], *, force_target: str | None = None) -> dict[str, Any]:
    required = {"version", "id", "target", "style_id", "assets"}
    missing = sorted(required - set(document))
    if missing:
        raise ValueError("motion_manifest_missing:" + ",".join(missing))
    if document["version"] != VERSION:
        raise ValueError("motion_manifest_version_unsupported")
    target = force_target or document["target"]
    if target not in {"prototype", "production"}:
        raise ValueError("motion_manifest_target_invalid")
    assets = document["assets"]
    if not isinstance(assets, list) or not assets:
        raise ValueError("motion_manifest_assets_empty")
    ids = [row.get("id") for row in assets if isinstance(row, dict)]
    if len(ids) != len(assets) or None in ids or len(ids) != len(set(ids)):
        raise ValueError("motion_manifest_asset_ids_invalid")
    return {**document, "target": target, "assets": [validate_asset(row, target=target) for row in assets]}


def require_anchors(document: dict[str, Any], requirements: dict[str, list[str]], *, force_target: str | None = None) -> dict[str, Any]:
    value = validate_manifest(document, force_target=force_target)
    by_id = {asset["id"]: asset for asset in value["assets"]}
    for asset_id, names in requirements.items():
        if asset_id not in by_id:
            raise ValueError(f"required_anchor_asset_missing:{asset_id}")
        if len(names) != len(set(names)):
            raise ValueError(f"required_anchors_not_unique:{asset_id}")
        missing = sorted(set(names) - set(by_id[asset_id]["runtime_anchors"]))
        if missing:
            raise ValueError(f"runtime_anchors_missing:{asset_id}:" + ",".join(missing))
    return value
