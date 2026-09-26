"""Development-only critic calibration, not baseline/candidate film comparison."""
import argparse
import asyncio
from copy import deepcopy
import json
import hashlib
from pathlib import Path
import sys
import time
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"video-generator"))
from app.engine.harness_loader import HarnessRegistry
from app.harness_sdk.semantic_beats import analysis_model, analysis_sha256
from app.semantic_review import review_packet, review_pair, compare_orders, digest
from app.tracking import Tracker, atomic_json, sha256_file


def negative_packet(original, kind="route"):
    wrong = deepcopy(original)
    if kind == "snapshot_as_accumulation":
        mutation = next((b for b in wrong["beats"] if b["grammar"] == "before_after"), None)
        if mutation is None:
            raise ValueError("snapshot_beat_required_for_this_negative_control")
        mutation["grammar"] = "cumulative_change"
        change = dict(beat_id=mutation["beat_id"], field="grammar",
                      before="before_after", after="cumulative_change")
    elif kind == "route":
        mutation = next((b for b in wrong["beats"] if b["route"] == "diagram"), None)
        if mutation is None:
            raise ValueError("diagram_beat_required_for_this_negative_control")
        mutation.update(route="cinematic", grammar=None)
        change = dict(beat_id=mutation["beat_id"], field="route", before="diagram", after="cinematic")
    else:
        raise ValueError("unsupported_negative_control")
    return wrong, change


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("analysis", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--allow-subscription-director", action="store_true")
    parser.add_argument("--negative-kind", choices=["route", "snapshot_as_accumulation"], default="route")
    parser.add_argument("--alternative-analysis", type=Path,
                        help="Compare two actual analyses without an assumed winner or invalid control")
    args = parser.parse_args()
    if not args.allow_subscription_director:
        raise ValueError("explicit_subscription_director_flag_required")
    analysis_report = json.loads(args.analysis.read_text(encoding="utf-8"))
    if analysis_report.get("status") != "STRUCTURAL_PASS":
        raise ValueError("structurally_valid_analysis_required")
    analysis = analysis_model(analysis_report["analysis"]["version"]).model_validate(analysis_report["analysis"])
    if analysis_report.get("analysis_sha256") != analysis_sha256(analysis):
        raise ValueError("analysis_evidence_hash_mismatch")
    original = review_packet(analysis)
    script = ''.join(b.literal_content for b in analysis.beats)
    if analysis_report.get("script_sha256") != hashlib.sha256(script.encode()).hexdigest():
        raise ValueError("script_evidence_hash_mismatch")
    alternative = args.alternative_analysis is not None
    alternative_hash = None
    if alternative:
        other = json.loads(args.alternative_analysis.read_text(encoding="utf-8"))
        other_analysis = analysis_model(other["analysis"]["version"]).model_validate(other["analysis"])
        if (other.get("status") != "STRUCTURAL_PASS" or other.get("analysis_sha256") != analysis_sha256(other_analysis)
                or other.get("script_sha256") != analysis_report["script_sha256"]
                or ''.join(b.literal_content for b in other_analysis.beats) != script):
            raise ValueError("alternative_analysis_evidence_mismatch")
        wrong = review_packet(other_analysis)
        mutation = None
        alternative_hash = sha256_file(args.alternative_analysis)
        if digest(wrong) == digest(original):
            raise ValueError("identical_alternatives")
    else:
        wrong, mutation = negative_packet(original, args.negative_kind)
    out = args.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    work = out/"work"; work.mkdir()
    tracker = Tracker(out)
    loaded = HarnessRegistry(ROOT/"harnesses").load("hybrid-story")
    contract = loaded.instance.describe_planning_contract(loaded.config)
    context = {k: contract.get(k) for k in ("hybrid_direction", "visual_grammar_library")}
    context["trusted_source_catalog"] = []
    settings = SimpleNamespace(codex_model="gpt-6-sol", codex_read_timeout_seconds=180,
        codex_connect_timeout_seconds=10, subscription_base_url="http://image-oauth:10531")
    atomic_json(out/"inputs.json", dict(scope="development_alternative_review_no_expected_winner" if alternative else "development_negative_control_not_held_out", script=script,
        original=original, control=wrong, mutation=mutation, negative_kind=args.negative_kind,
        analysis_report_sha256=sha256_file(args.analysis), alternative_report_sha256=alternative_hash, context=context))
    reports = []
    started = time.monotonic(); error = None
    try:
        for review_id, packets in (("ab", {"A": original, "B": wrong}), ("ba", {"A": wrong, "B": original})):
            report = await asyncio.wait_for(review_pair(script, packets, context, settings, tracker, work,
                review_id=review_id, model="gpt-5.6-terra"), timeout=240)
            reports.append(report)
            print(json.dumps(dict(order=review_id, status=report["status"], preferred=(report.get("verdict") or {}).get("preferred"))), flush=True)
        comparison = compare_orders(*reports)
    except Exception as exc:
        error = dict(type=type(exc).__name__, message=str(exc)[:500])
        comparison = dict(status="REVIEW_INCOMPLETE", winner_sha256=None)
    control_rejected = comparison.get("winner_sha256") == digest(original) if not alternative else None
    review_complete = comparison.get("status") == "CONSISTENT_PRE_RENDER_REVIEW"
    status = ("ALTERNATIVE_REVIEW_COMPLETE" if review_complete else "GOAL_NOT_MET") if alternative else ("DEVELOPMENT_CONTROL_DETECTED" if control_rejected else "GOAL_NOT_MET")
    atomic_json(out/"receipt.json", dict(status=status,
        comparison=comparison, error=error, negative_control_detected=control_rejected,
        comparison_kind="actual_analyses" if alternative else args.negative_kind, expected_winner=None if alternative else digest(original),
        original_sha256=digest(original), control_sha256=digest(wrong),
        elapsed_seconds=round(time.monotonic()-started, 3), usage=tracker.usage, assets=tracker.assets,
        paid_api_calls=0, image_calls=0, voice_calls=0, human_approval=None, production_ready=False,
        not_evaluated=["rendered_quality", "held_out_accuracy", "film_superiority", "real_viewer_emotions"]))
    print(json.dumps(dict(status=comparison["status"], negative_control_detected=control_rejected, error=error)), flush=True)
    if error or (not review_complete if alternative else not control_rejected): raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
