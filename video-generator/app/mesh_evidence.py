from __future__ import annotations

import math
from typing import Any, Iterable


VERSION = "astra-mesh-evidence-1.0"

# Initial Gold benchmark limits. Scene contracts may request stricter values,
# but cannot relax these engine-owned safety bounds.
THRESHOLD_POLICY = {
    "max_vertex_displacement_ratio": 0.08,
    "edge_stretch_p95_max": 1.12,
    "edge_stretch_min": 0.88,
    "edge_stretch_max": 1.18,
    "triangle_area_ratio_min": 0.80,
    "triangle_area_ratio_max": 1.22,
    "triangle_flip_max": 0,
    "seam_gap_max_ratio": 0.02,
    "neutral_reassembly_max_error_ratio": 0.005,
}


def _point(value: Any, name: str) -> tuple[float, float]:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ValueError(f"{name}_invalid")
    point = (float(value[0]), float(value[1]))
    if not all(math.isfinite(item) for item in point):
        raise ValueError(f"{name}_not_finite")
    return point


def _distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _signed_double_area(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("metric_values_empty")
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def _index_pair(value: Any, name: str, count: int) -> tuple[int, int]:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ValueError(f"{name}_invalid")
    pair = (int(value[0]), int(value[1]))
    if any(index < 0 or index >= count for index in pair) or pair[0] == pair[1]:
        raise ValueError(f"{name}_out_of_range")
    return pair


def _triangle(value: Any, name: str, count: int) -> tuple[int, int, int]:
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ValueError(f"{name}_invalid")
    triangle = tuple(int(item) for item in value)
    if len(set(triangle)) != 3 or any(index < 0 or index >= count for index in triangle):
        raise ValueError(f"{name}_out_of_range")
    return triangle  # type: ignore[return-value]


def measure_mesh_deformation(
    *,
    rest_vertices: Iterable[Any],
    deformed_vertices: Iterable[Any],
    triangles: Iterable[Any],
    reference_length_px: float,
    seam_pairs: Iterable[Any] = (),
    neutral_vertices: Iterable[Any] | None = None,
) -> dict[str, Any]:
    rest = [_point(value, "rest_vertex") for value in rest_vertices]
    deformed = [_point(value, "deformed_vertex") for value in deformed_vertices]
    if not rest or len(rest) != len(deformed):
        raise ValueError("mesh_vertex_count_mismatch")
    reference = float(reference_length_px)
    if not math.isfinite(reference) or reference <= 0:
        raise ValueError("reference_length_invalid")
    faces = [_triangle(value, "triangle", len(rest)) for value in triangles]
    if not faces:
        raise ValueError("mesh_triangles_empty")

    edges = sorted({tuple(sorted((face[index], face[(index + 1) % 3]))) for face in faces for index in range(3)})
    stretch: list[float] = []
    for first, second in edges:
        original = _distance(rest[first], rest[second])
        if original <= 1e-9:
            raise ValueError("rest_edge_degenerate")
        stretch.append(_distance(deformed[first], deformed[second]) / original)

    area_ratios: list[float] = []
    flip_count = 0
    for first, second, third in faces:
        original = _signed_double_area(rest[first], rest[second], rest[third])
        changed = _signed_double_area(deformed[first], deformed[second], deformed[third])
        if abs(original) <= 1e-9:
            raise ValueError("rest_triangle_degenerate")
        if original * changed <= 0:
            flip_count += 1
        area_ratios.append(abs(changed / original))

    seams = [_index_pair(value, "seam_pair", len(rest)) for value in seam_pairs]
    seam_gaps = [_distance(deformed[first], deformed[second]) / reference for first, second in seams]
    displacement = [_distance(before, after) / reference for before, after in zip(rest, deformed)]

    neutral_error = None
    if neutral_vertices is not None:
        neutral = [_point(value, "neutral_vertex") for value in neutral_vertices]
        if len(neutral) != len(rest):
            raise ValueError("neutral_vertex_count_mismatch")
        neutral_error = max(_distance(before, after) / reference for before, after in zip(rest, neutral))

    return {
        "version": VERSION,
        "vertex_count": len(rest),
        "triangle_count": len(faces),
        "edge_count": len(edges),
        "reference_length_px": reference,
        "max_vertex_displacement_ratio": max(displacement),
        "edge_stretch_p50": _percentile(stretch, 0.50),
        "edge_stretch_p95": _percentile(stretch, 0.95),
        "edge_stretch_min": min(stretch),
        "edge_stretch_max": max(stretch),
        "triangle_area_ratio_min": min(area_ratios),
        "triangle_area_ratio_max": max(area_ratios),
        "triangle_flip_count": flip_count,
        "seam_gap_max_ratio": max(seam_gaps, default=0.0),
        "neutral_reassembly_max_error_ratio": neutral_error,
    }


def evaluate_mesh_evidence(metrics: dict[str, Any], thresholds: dict[str, Any]) -> list[str]:
    required_metrics = {
        "max_vertex_displacement_ratio", "edge_stretch_p95", "edge_stretch_min", "edge_stretch_max",
        "triangle_area_ratio_min", "triangle_area_ratio_max", "triangle_flip_count", "seam_gap_max_ratio",
        "neutral_reassembly_max_error_ratio",
    }
    if metrics.get("version") != VERSION or not required_metrics <= set(metrics):
        return ["mesh_evidence_incomplete"]
    required_thresholds = {
        "max_vertex_displacement_ratio", "edge_stretch_p95_max", "edge_stretch_min",
        "edge_stretch_max", "triangle_area_ratio_min", "triangle_area_ratio_max",
        "triangle_flip_max", "seam_gap_max_ratio", "neutral_reassembly_max_error_ratio",
    }
    if not isinstance(thresholds, dict) or not required_thresholds <= set(thresholds):
        return ["mesh_thresholds_incomplete"]
    for name in required_metrics:
        value = metrics[name]
        if type(value) not in (int, float) or not math.isfinite(value):
            return [f"mesh_metric_invalid:{name}"]
    for name in required_thresholds:
        value = thresholds[name]
        if type(value) not in (int, float) or not math.isfinite(value):
            return [f"mesh_threshold_invalid:{name}"]

    policy_checks = {
        "max_vertex_displacement_ratio": thresholds["max_vertex_displacement_ratio"] <= THRESHOLD_POLICY["max_vertex_displacement_ratio"],
        "edge_stretch_p95_max": thresholds["edge_stretch_p95_max"] <= THRESHOLD_POLICY["edge_stretch_p95_max"],
        "edge_stretch_min": thresholds["edge_stretch_min"] >= THRESHOLD_POLICY["edge_stretch_min"],
        "edge_stretch_max": thresholds["edge_stretch_max"] <= THRESHOLD_POLICY["edge_stretch_max"],
        "triangle_area_ratio_min": thresholds["triangle_area_ratio_min"] >= THRESHOLD_POLICY["triangle_area_ratio_min"],
        "triangle_area_ratio_max": thresholds["triangle_area_ratio_max"] <= THRESHOLD_POLICY["triangle_area_ratio_max"],
        "triangle_flip_max": thresholds["triangle_flip_max"] <= THRESHOLD_POLICY["triangle_flip_max"],
        "seam_gap_max_ratio": thresholds["seam_gap_max_ratio"] <= THRESHOLD_POLICY["seam_gap_max_ratio"],
        "neutral_reassembly_max_error_ratio": thresholds["neutral_reassembly_max_error_ratio"] <= THRESHOLD_POLICY["neutral_reassembly_max_error_ratio"],
    }
    failures = [f"mesh_threshold_policy_too_loose:{name}" for name, passed in policy_checks.items() if not passed]
    if failures:
        return failures
    checks = {
        "max_vertex_displacement": metrics["max_vertex_displacement_ratio"] <= thresholds["max_vertex_displacement_ratio"],
        "edge_stretch_p95": metrics["edge_stretch_p95"] <= thresholds["edge_stretch_p95_max"],
        "edge_stretch_min": metrics["edge_stretch_min"] >= thresholds["edge_stretch_min"],
        "edge_stretch_max": metrics["edge_stretch_max"] <= thresholds["edge_stretch_max"],
        "triangle_area_min": metrics["triangle_area_ratio_min"] >= thresholds["triangle_area_ratio_min"],
        "triangle_area_max": metrics["triangle_area_ratio_max"] <= thresholds["triangle_area_ratio_max"],
        "triangle_flip": metrics["triangle_flip_count"] <= thresholds["triangle_flip_max"],
        "seam_gap": metrics["seam_gap_max_ratio"] <= thresholds["seam_gap_max_ratio"],
        "neutral_reassembly": metrics["neutral_reassembly_max_error_ratio"] is not None
        and metrics["neutral_reassembly_max_error_ratio"] <= thresholds["neutral_reassembly_max_error_ratio"],
    }
    return [f"mesh_geometry_failed:{name}" for name, passed in checks.items() if not passed]
