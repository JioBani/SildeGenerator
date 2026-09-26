from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.layer_decomposition import VERSION, requested_objects, validate_manifest


def test_only_moving_objects_with_region_hints_are_requested() -> None:
    scene = SimpleNamespace(
        object_states=[
            {"object_id": "actor", "role": "person", "region_hint": [0.5, 0.1, 0.3, 0.8], "isolation": "required", "depth_band": "foreground"},
            {"object_id": "room", "role": "background", "region_hint": None, "isolation": "not_needed", "depth_band": "background"},
        ],
        motion=[
            {"object_id": "actor", "kind": "reaction"},
            {"object_id": "room", "kind": "camera_push"},
        ],
    )

    assert requested_objects(scene) == [{
        "object_id": "actor", "role": "person", "region_hint": [0.5, 0.1, 0.3, 0.8], "depth_band": "foreground",
    }]


def test_ready_layer_requires_rgba_evidence() -> None:
    with pytest.raises(ValueError, match="rgba_path_missing"):
        validate_manifest({
            "version": VERSION, "status": "TECHNICAL_PASS",
            "layers": [{"object_id": "actor", "bounds": [0.1, 0.1, 0.5, 0.7], "technical_ready": True}],
        })
