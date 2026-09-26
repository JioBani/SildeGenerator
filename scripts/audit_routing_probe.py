"""Hash-bound evidence summary; never turn narrow match counts into quality rates."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "video-generator"))
from app.semantic_review import compare_orders
from app.tracking import atomic_json, sha256_file


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--critic", type=Path, action="append", default=[])
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    evidence = []
    def read(path):
        evidence.append(dict(path=str(path), sha256=sha256_file(path)))
        return json.loads(path.read_text(encoding="utf-8"))
    initial = read(args.baseline / "receipt.json")
    later = read(args.candidate / "receipt.json")
    a = read(args.baseline / "frozen-input.json")
    b = read(args.candidate / "frozen-input.json")
    if a["suite_sha256"] != b["suite_sha256"]:
        raise ValueError("different_evaluation_inputs")
    if not b.get("baseline") or b["baseline"]["receipt_sha256"] != sha256_file(args.baseline / "receipt.json"):
        raise ValueError("candidate_not_bound_to_baseline")
    reviews = []
    for folder in args.critic:
        receipt = read(folder / "receipt.json")
        first, second = (read(folder / "work" / f"{order}.json") for order in ("ab", "ba"))
        comparison = compare_orders(first, second)
        reviews.append(dict(path=str(folder), comparison=comparison, calls=len(receipt["usage"]),
            elapsed_seconds=receipt["elapsed_seconds"], expected_winner=receipt.get("expected_winner"),
            scope="Pre-render semantic review only, not full-film approval"))
    report = dict(status="GOAL_NOT_MET", production_ready=False, human_approval=None,
        first_exposure=dict(raw_expectation_matches=initial["passed"], planned=initial["planned"], calls=initial["calls"],
            elapsed_seconds=initial["elapsed_seconds"]),
        development_replay=dict(raw_expectation_matches=later["passed"], planned=later["planned"], calls=later["calls"],
            elapsed_seconds=later["elapsed_seconds"]),
        critical_limit="Raw grammar-label matches are NOT routing accuracy, transfer quality or held-out superiority. "
            "A permissible alternate grammar and empty diagram fragments require separate adjudication. Never use this ratio for promotion.",
        reviews=reviews, evidence=evidence,
        subscription_calls=initial["calls"]+later["calls"]+sum(r["calls"] for r in reviews),
        paid_api_calls=0, image_calls=0, voice_calls=0,
        not_evaluated=["new_rendered_film", "scene_design", "whole_film_quality", "representative_held_out_accuracy", "audience_response"])
    atomic_json(args.output, report)
    print(json.dumps(dict(status=report["status"], subscription_calls=report["subscription_calls"],
        comparisons=[r["comparison"] for r in reviews]), ensure_ascii=False))


if __name__ == "__main__":
    main()
