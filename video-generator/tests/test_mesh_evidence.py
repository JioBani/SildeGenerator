from __future__ import annotations

from app.mesh_evidence import THRESHOLD_POLICY, evaluate_mesh_evidence, measure_mesh_deformation


THRESHOLDS = dict(THRESHOLD_POLICY)


def test_small_shape_preserving_deformation_passes() -> None:
    rest = [[0, 0], [100, 0], [100, 100], [0, 100], [0, 0]]
    changed = [[0, 0], [102, 1], [101, 100], [0, 100], [0.5, 0]]
    metrics = measure_mesh_deformation(
        rest_vertices=rest,
        deformed_vertices=changed,
        triangles=[[0, 1, 2], [0, 2, 3]],
        reference_length_px=100,
        seam_pairs=[[0, 4]],
        neutral_vertices=rest,
    )
    assert metrics["triangle_flip_count"] == 0
    assert evaluate_mesh_evidence(metrics, THRESHOLDS) == []


def test_triangle_flip_is_blocking() -> None:
    rest = [[0, 0], [100, 0], [0, 100]]
    changed = [[0, 0], [0, 100], [100, 0]]
    metrics = measure_mesh_deformation(
        rest_vertices=rest,
        deformed_vertices=changed,
        triangles=[[0, 1, 2]],
        reference_length_px=100,
        neutral_vertices=rest,
    )
    assert metrics["triangle_flip_count"] == 1
    assert "mesh_geometry_failed:triangle_flip" in evaluate_mesh_evidence(metrics, THRESHOLDS)


def test_neutral_reassembly_drift_is_blocking() -> None:
    rest = [[0, 0], [100, 0], [0, 100]]
    metrics = measure_mesh_deformation(
        rest_vertices=rest,
        deformed_vertices=rest,
        triangles=[[0, 1, 2]],
        reference_length_px=100,
        neutral_vertices=[[0, 0], [102, 0], [0, 100]],
    )
    assert "mesh_geometry_failed:neutral_reassembly" in evaluate_mesh_evidence(metrics, THRESHOLDS)


def test_scene_cannot_relax_engine_threshold_policy() -> None:
    rest = [[0, 0], [100, 0], [0, 100]]
    metrics = measure_mesh_deformation(
        rest_vertices=rest,
        deformed_vertices=rest,
        triangles=[[0, 1, 2]],
        reference_length_px=100,
        neutral_vertices=rest,
    )
    thresholds = dict(THRESHOLDS)
    thresholds["triangle_flip_max"] = 99

    assert evaluate_mesh_evidence(metrics, thresholds) == [
        "mesh_threshold_policy_too_loose:triangle_flip_max"
    ]


def test_non_finite_metric_is_blocked() -> None:
    rest = [[0, 0], [100, 0], [0, 100]]
    metrics = measure_mesh_deformation(
        rest_vertices=rest,
        deformed_vertices=rest,
        triangles=[[0, 1, 2]],
        reference_length_px=100,
        neutral_vertices=rest,
    )
    metrics["edge_stretch_p95"] = float("nan")

    assert evaluate_mesh_evidence(metrics, THRESHOLDS) == [
        "mesh_metric_invalid:edge_stretch_p95"
    ]
