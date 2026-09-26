"""Replay observed stream failure locally and preserve independent review evidence."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"video-generator"))
from app.planning_stream_guard import PlanningStreamGuard
from app.tracking import atomic_json, sha256_file


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("director", type=Path)
    parser.add_argument("critic", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    failed_stream = args.director/"work/codex/attempt-1/output.txt"
    guard = PlanningStreamGuard()
    text = failed_stream.read_text(encoding="utf-8")
    rejection = None
    try:
        for char in text:
            guard.feed(char)
    except RuntimeError as error:
        rejection = str(error)
    director = json.loads((args.director/"receipt.json").read_text())
    critic = json.loads((args.critic/"receipt.json").read_text())
    orders = {name: json.loads((args.critic/f"work/{name}.json").read_text()) for name in ("ab", "ba")}
    route_negative = {}
    for order, report in orders.items():
        control_label = next(k for k, h in report["candidate_hashes"].items() if h == critic["control_sha256"])
        judgment = next(c for c in report["verdict"]["candidates"] if c["label"] == control_label)
        route_negative[order] = any(b["route_fit"] == "FAIL" for b in judgment["beats"])
    evidence_paths = [failed_stream, args.director/"receipt.json", args.critic/"receipt.json",
        args.critic/"work/ab.json", args.critic/"work/ba.json"]
    report = dict(status="GOAL_NOT_MET", scope="one development script; not held-out; no new rendered movie",
        stream_replay=dict(status="REGRESSION_REJECTED" if rejection else "NOT_DETECTED",
            error=rejection, consumed_characters=guard.total, recorded_characters=len(text), live_retry_performed=False),
        actual_director=dict(status=director["status"], error=director["error"], calls=len(director["usage"]),
            elapsed_seconds=director["elapsed_seconds"]),
        independent_critic=dict(status=critic["comparison"]["status"], route_control_rejected_per_order=route_negative,
            full_criteria_agreement=False, calls=len(critic["usage"]), elapsed_seconds=critic["elapsed_seconds"],
            observed_issue="context_or_motivation_conflated_with_event_causation"),
        evidence=[dict(path=p.resolve().relative_to(ROOT).as_posix(), sha256=sha256_file(p)) for p in evidence_paths],
        usage=director["usage"]+critic["usage"], paid_api_calls=0, image_calls=0, voice_calls=0,
        human_approval=None, production_ready=False,
        next_hypothesis="Separate event causation, motivation and contextual sequencing with grounded endpoints; revalidate critic on causal and noncausal controls.")
    atomic_json(args.output, report)
    print(json.dumps({key: report[key] for key in ("status", "stream_replay", "independent_critic")}, ensure_ascii=False))
    if not rejection:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
