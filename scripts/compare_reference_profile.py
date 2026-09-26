from __future__ import annotations

import json
import math
import statistics
import sys
from pathlib import Path


def load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def mean(rows: list[dict], key: str) -> float:
    return statistics.fmean(float(row[key]) for row in rows)


def percentile(values: list[float], fraction: float) -> float:
    values = sorted(values)
    if not values:
        return 0.0
    index = (len(values) - 1) * fraction
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return values[lower]
    weight = index - lower
    return values[lower] * (1 - weight) + values[upper] * weight


def palette_distance(reference: list[dict], candidate: list[dict]) -> float:
    reference_colors = [row["rgb"] for row in reference[:12]]
    candidate_colors = [row["rgb"] for row in candidate[:12]]
    if not reference_colors or not candidate_colors:
        return 1.0
    distances = []
    for color in candidate_colors:
        distances.append(min(
            math.sqrt(sum((left - right) ** 2 for left, right in zip(color, other))) / math.sqrt(3 * 255 ** 2)
            for other in reference_colors
        ))
    return statistics.fmean(distances)


def summarize(analysis: dict) -> dict:
    rows = analysis["per_second"]
    changes = [float(row["change_from_previous"]) for row in rows[1:]]
    duration = float(analysis["probe"]["format"]["duration"])
    return {
        "mean_luminance": round(mean(rows, "mean_luminance"), 4),
        "mean_saturation": round(mean(rows, "mean_saturation"), 4),
        "mean_edge_density": round(mean(rows, "edge_density"), 4),
        "motion_change_median": round(statistics.median(changes), 5) if changes else 0,
        "motion_change_p90": round(percentile(changes, .9), 5),
        "segment_candidates_per_minute": round(len(analysis["segments"]) / duration * 60, 2),
    }


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit("usage: compare_reference_profile.py <reference-analysis.json> <candidate-analysis.json> <output.json>")
    reference = load(sys.argv[1])
    candidate = load(sys.argv[2])
    reference_summary = summarize(reference)
    candidate_summary = summarize(candidate)
    result = {
        "version": "astra-reference-comparison-1.0",
        "reference": reference["source"],
        "candidate": candidate["source"],
        "reference_summary": reference_summary,
        "candidate_summary": candidate_summary,
        "palette_distance_0_exact_1_far": round(palette_distance(reference["global_palette"], candidate["global_palette"]), 4),
        "metric_deltas": {
            key: round(candidate_summary[key] - reference_summary[key], 5)
            for key in reference_summary
        },
        "interpretation": [
            "These measurements are evidence, not an aesthetic approval.",
            "A human must still review representation, composition, performance, and readability.",
            "Motion values are comparable only when both analyses use the same sampling rate."
        ],
    }
    output = Path(sys.argv[3])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
