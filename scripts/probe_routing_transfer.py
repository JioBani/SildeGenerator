"""Frozen, expectation-blind subscription routing probe; no asset generation."""
import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "video-generator"))
from app.engine.harness_loader import HarnessRegistry
from app.semantic_planning import analyze_script
from app.tracking import Tracker, atomic_json, sha256_file


def inspect_case(case, report):
    """Score observed output against withheld expectations, including fail-closed cases."""
    failures = []
    analysis = (report or {}).get("analysis") or {}
    beats = analysis.get("beats", [])
    if not beats:
        return ["analysis_missing"]
    if ''.join(b["literal_content"] for b in beats) != case["script"]:
        failures.append("source_coverage")
    for beat in beats:
        if beat["route"] != case["expected_route"]:
            failures.append("wrong_route")
        if case["expected_grammars"]:
            if beat["grammar"] not in case["expected_grammars"]:
                failures.append("wrong_grammar")
        elif beat["grammar"] is not None:
            failures.append("unexpected_grammar")
    quotes = case["keep_together"]
    if quotes and not any(all(q in b["literal_content"] for q in quotes) for b in beats):
        failures.append("connected_information_split")
    findings = (report or {}).get("findings", [])
    if case["expected_gate"] == "accept":
        if report.get("status") != "STRUCTURAL_PASS" or findings:
            failures.append("unexpected_gate_failure")
    else:
        if report.get("status") == "STRUCTURAL_PASS":
            failures.append("missing_required_block")
        if not any(f.endswith(":" + case["expected_gate"]) for f in findings):
            failures.append("wrong_block_reason")
    return sorted(set(failures))


def load_suite(path):
    suite = json.loads(path.read_text(encoding="utf-8"))
    if suite.get("version") != "routing-transfer-probe-0.1":
        raise ValueError("unsupported_routing_probe")
    cases = suite["cases"]
    ids = [c["id"] for c in cases]
    if not 1 <= len(cases) <= 20 or len(set(ids)) != len(ids):
        raise ValueError("invalid_case_ids")
    for case in cases:
        if not case["id"].replace('_', '').isalnum() or not case["script"].strip():
            raise ValueError("invalid_case")
        if any(q not in case["script"] for q in case["keep_together"]):
            raise ValueError("expectation_quote_not_grounded")
    return suite


async def run(args):
    if not args.allow_subscription_director:
        raise ValueError("explicit_subscription_director_flag_required")
    suite = load_suite(args.suite)
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    loaded = HarnessRegistry(ROOT / "harnesses").load("hybrid-story")
    baseline = None
    if args.baseline_probe:
        baseline_input = json.loads((args.baseline_probe / "frozen-input.json").read_text(encoding="utf-8"))
        if baseline_input["suite_sha256"] != sha256_file(args.suite):
            raise ValueError("paired_probe_suite_changed")
        if baseline_input["harness"]["source_sha256"] == loaded.snapshot.as_dict()["source_sha256"]:
            raise ValueError("unchanged_engine_cannot_reset_failed_probe")
        baseline = dict(receipt_sha256=sha256_file(args.baseline_probe / "receipt.json"),
            input_sha256=sha256_file(args.baseline_probe / "frozen-input.json"),
            path=str(args.baseline_probe), scope="Development regression replay, no longer first-exposure evidence")
    contract = loaded.instance.describe_planning_contract(loaded.config)
    contract.update(trusted_source_catalog=[], trusted_illustration_catalog=[])
    settings = SimpleNamespace(codex_model="gpt-6-sol", codex_reasoning_effort="low",
        codex_fast_mode=False, codex_read_timeout_seconds=180, codex_connect_timeout_seconds=10,
        subscription_base_url="http://image-oauth:10531")
    # The frozen suite is evidence, never an argument to the model. Only script and
    # the existing runtime capability contract reach analyze_script.
    atomic_json(out / "frozen-input.json", dict(suite=suite, suite_sha256=sha256_file(args.suite),
        harness=loaded.snapshot.as_dict(), contract=contract,
        analysis_code_sha256=sha256_file(ROOT / "video-generator/app/semantic_planning.py"),
        evaluator_code_sha256=sha256_file(Path(__file__)), baseline=baseline))
    started = time.monotonic()
    results = []
    for case in suite["cases"]:
        folder = out / case["id"]
        work = folder / "work"
        work.mkdir(parents=True)
        tracker = Tracker(folder)
        error = None
        observed = None
        begin = time.monotonic()
        try:
            await asyncio.wait_for(analyze_script(case["script"], settings, tracker, work, contract), timeout=600)
        except Exception as exc:
            error = dict(type=type(exc).__name__, message=str(exc)[:800])
        reports = sorted(work.glob("semantic-analysis-*.json"))
        if reports:
            observed = json.loads(reports[-1].read_text(encoding="utf-8"))
        failures = inspect_case(case, observed)
        if observed and observed.get("status") == "STRUCTURAL_PASS" and error:
            failures.append("execution_error_after_acceptance")
        result = dict(id=case["id"], status="EXPECTED_ROUTING_OBSERVED" if not failures else "REVISE",
            failures=failures, error=error, report_sha256=sha256_file(reports[-1]) if reports else None,
            script_sha256=hashlib.sha256(case["script"].encode()).hexdigest(),
            report_path=str(reports[-1]) if reports else None,
            elapsed_seconds=round(time.monotonic()-begin, 3), usage=tracker.usage,
            routes=[b["route"] for b in (observed or {}).get("analysis", {}).get("beats", [])] if (observed or {}).get("analysis") else [],
            grammars=[b["grammar"] for b in (observed or {}).get("analysis", {}).get("beats", [])] if (observed or {}).get("analysis") else [])
        atomic_json(folder / "receipt.json", result)
        results.append(result)
        print(json.dumps({k: result[k] for k in ("id", "status", "failures", "routes", "grammars", "elapsed_seconds")}, ensure_ascii=False), flush=True)
        # A transport/auth problem is not evidence about routing. Stop the batch,
        # without re-login or fallback; preserve all completed cases.
        if not reports:
            break
    passed = sum(r["status"] == "EXPECTED_ROUTING_OBSERVED" for r in results)
    receipt = dict(status="ROUTING_PROBE_PASS" if passed == len(suite["cases"]) else "GOAL_NOT_MET",
        goal_status="GOAL_NOT_MET", cases=results, passed=passed, planned=len(suite["cases"]),
        completed=len(results), elapsed_seconds=round(time.monotonic()-started, 3),
        calls=sum(len(r["usage"]) for r in results), paid_api_calls=0, image_calls=0, voice_calls=0,
        human_approval=None, production_ready=False,
        baseline=baseline,
        scope="Frozen short-script routing only. No held-out film superiority, scene design, actual frames, independent review or audience testing.")
    atomic_json(out / "receipt.json", receipt)
    print(json.dumps({k: receipt[k] for k in ("status", "passed", "planned", "calls", "elapsed_seconds")}), flush=True)
    if receipt["status"] != "ROUTING_PROBE_PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("suite", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--allow-subscription-director", action="store_true")
    parser.add_argument("--baseline-probe", type=Path)
    asyncio.run(run(parser.parse_args()))
