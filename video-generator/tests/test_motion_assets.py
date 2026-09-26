from __future__ import annotations

import pytest

from app.motion_assets import VERSION, require_anchors, validate_manifest


def _asset(**updates):
    value = {
        "id": "actor-001", "kind": "character", "source": "actor.svg", "source_sha256": "a" * 64,
        "source_type": "svg", "motion_use": "deformable_rig", "anchor": [0.5, 0.8], "pivot": [0.5, 0.5],
        "depth_band": "midground", "states": ["neutral", "notice"], "contact_points": {"right_hand": [0.8, 0.5]},
        "runtime_anchors": {"right_hand": "css:#right-hand"}, "joints": ["shoulder", "elbow"],
        "hidden_area_policy": "resolved", "reviews": {"silhouette": True, "alpha_edge": True, "contact": True, "style_consistency": True},
        "rights": "approved", "production_ready": True, "maturity": "MOTION_READY",
    }
    value.update(updates)
    return value


def _manifest(asset):
    return {"version": VERSION, "id": "manifest-001", "target": "production", "style_id": "style-v1", "assets": [asset]}


def test_motion_ready_asset_can_pass_production_contract() -> None:
    assert validate_manifest(_manifest(_asset()))["assets"][0]["maturity"] == "MOTION_READY"


def test_interaction_ready_cannot_self_promote_in_manifest() -> None:
    with pytest.raises(ValueError, match="interaction_ready_requires_external_human_approval"):
        validate_manifest(_manifest(_asset(maturity="INTERACTION_READY")))


def test_flattened_raster_cannot_be_rigged() -> None:
    with pytest.raises(ValueError, match="flattened_source_forbidden"):
        validate_manifest(_manifest(_asset(source_type="raster_rgb")))


def test_runtime_anchor_type_is_bound_to_renderer_source() -> None:
    with pytest.raises(ValueError, match="runtime_anchor_type_mismatch"):
        validate_manifest(_manifest(_asset(runtime_anchors={"right_hand": "bone:right_hand"})))


def test_scene_anchor_requirements_are_checked() -> None:
    with pytest.raises(ValueError, match="runtime_anchors_missing"):
        require_anchors(_manifest(_asset()), {"actor-001": ["left_hand"]})
