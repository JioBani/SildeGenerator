"""Replay a frozen actual analysis through the current independent semantic gate."""
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
from app.harness_sdk.semantic_beats import analysis_model, analysis_sha256, inspect_analysis
from app.semantic_gate import review_sufficiency
from app.tracking import Tracker, atomic_json, sha256_file


async def main(args):
    if not args.allow_subscription_director:
        raise ValueError("explicit_subscription_director_flag_required")
    source = json.loads(args.analysis.read_text(encoding="utf-8"))
    analysis = analysis_model(source["analysis"]["version"]).model_validate(source["analysis"])
    script = ''.join(b.literal_content for b in analysis.beats)
    if (source["analysis_sha256"] != analysis_sha256(analysis)
            or source["script_sha256"] != hashlib.sha256(script.encode()).hexdigest()):
        raise ValueError("analysis_evidence_changed")
    loaded = HarnessRegistry(ROOT / "harnesses").load("hybrid-story")
    contract = loaded.instance.describe_planning_contract(loaded.config)
    contract.update(trusted_source_catalog=[], trusted_illustration_catalog=[])
    if args.source_root:
        from app.source_media import source_brief
        contract['trusted_source_catalog']=source_brief(args.source_root.resolve())
    if args.continue_design and args.expected!='PRE_RENDER_SEMANTICS_PASS':
        raise ValueError('cannot_design_expected_rejected_analysis')
    if args.continue_design and inspect_analysis(analysis,script,contract):
        raise ValueError('frozen_analysis_no_longer_structurally_valid')
    attempt=source.get('attempt')
    if args.continue_design and (type(attempt) is not int or not 0<=attempt<=3):
        raise ValueError('frozen_analysis_repair_budget_unknown')
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    work = out / "work"
    work.mkdir()
    tracker = Tracker(out)
    settings = SimpleNamespace(runner_mode='live',schemas_dir=ROOT/'video-generator/schemas',codex_model='gpt-6-sol',
        codex_reasoning_effort='low',codex_fast_mode=False,codex_read_timeout_seconds=180,codex_connect_timeout_seconds=10,
        subscription_base_url="http://image-oauth:10531")
    atomic_json(out / "input-evidence.json", dict(analysis_report_sha256=sha256_file(args.analysis),
        harness=loaded.snapshot.as_dict(), contract=contract, expected=args.expected,
        scope="Frozen development replay; expectation is not sent to the critic"))
    error = None
    report = None
    plan = None
    started = time.monotonic()
    try:
        if args.uncertain_review:
            from app.relation_alternatives import resolve_relation_uncertainty
            prior=json.loads(args.uncertain_review.read_text(encoding='utf-8'))
            atomic_json(out/'uncertain-review-input.json',dict(path=str(args.uncertain_review),sha256=sha256_file(args.uncertain_review)))
            analysis,attempt=await resolve_relation_uncertainty(analysis,script,prior,contract,settings,tracker,work,
                attempt=attempt,generator_model='gpt-6-sol')
            report=json.loads((work/f'semantic-sufficiency-{attempt}.json').read_text(encoding='utf-8'))
        else:
            report = await asyncio.wait_for(review_sufficiency(analysis,script,contract,settings,tracker,work,
                attempt=0,generator_model="gpt-6-sol"),timeout=240)
        if args.continue_design and report['status']=='PRE_RENDER_SEMANTICS_PASS':
            from app.concept_planning import select_concept
            from app.semantic_planning import analysis_units
            from app.planner import plan_with_codex
            from app.prompts import load_prompts
            concept=await select_concept(script,analysis,contract,settings,tracker,work,image_style='cinematic_realism')
            prompts,_=load_prompts(ROOT/'harnesses/hybrid-story/prompts')
            plan=await asyncio.wait_for(plan_with_codex(script,prompts,settings,tracker,work,image_style='cinematic_realism',
                harness_planning_contract=contract,source_units_override=analysis_units(analysis),semantic_analysis_result=analysis,
                selected_concept=concept,_repair_limit=3-attempt),timeout=600)
            atomic_json(out/'scene-plan.json',plan.model_dump(mode='json'))
    except Exception as exc:
        error = dict(type=type(exc).__name__, message=str(exc)[:800])
    matched = error is None and report is not None and report["status"] == args.expected and (not args.continue_design or plan is not None)
    receipt = dict(status="EXPECTED_REVIEW_OBSERVED" if matched else "GOAL_NOT_MET", goal_status="GOAL_NOT_MET",
        observed_status=report["status"] if report else None, findings=report["findings"] if report else [],
        expected=args.expected, error=error, usage=tracker.usage, elapsed_seconds=round(time.monotonic()-started,3),
        paid_api_calls=0, image_calls=0, voice_calls=0, human_approval=None, production_ready=False,
        continued_design=args.continue_design,scene_plan_created=plan is not None,
        scope='Hash-bound development replay of prior analysis, independent review and optional Core scene design; not a fresh end-to-end analysis or rendered film')
    atomic_json(out / "receipt.json", receipt)
    print(json.dumps({k:receipt[k] for k in ("status","observed_status","findings","error","elapsed_seconds")}),flush=True)
    if not matched: raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("analysis",type=Path)
    parser.add_argument("output",type=Path)
    parser.add_argument("--expected",choices=["REVISE","PRE_RENDER_SEMANTICS_PASS"],required=True)
    parser.add_argument("--allow-subscription-director",action="store_true")
    parser.add_argument('--continue-design',action='store_true')
    parser.add_argument('--source-root',type=Path)
    parser.add_argument('--uncertain-review',type=Path,help='Resume a hash-bound uncertainty without repeating the same critic judgment')
    asyncio.run(main(parser.parse_args()))
