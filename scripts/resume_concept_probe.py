"""Resume scene design from hash-checked development analysis and independent reviews.

Uses the same Core scene planner, validators and bounded repair loop. Does not
claim service/queue E2E or generate images/audio.
"""
import argparse
import asyncio
import hashlib
import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'video-generator'))
from app.concept_planning import concept_context
from app.engine.harness_loader import HarnessRegistry
from app.harness_sdk.concept_design import ConceptBatch, ConceptReview, anonymous, digest, compare_concept_orders, validate_review
from app.harness_sdk.semantic_beats import analysis_model, inspect_analysis
from app.semantic_planning import analysis_units
from app.planner import plan_with_codex
from app.prompts import load_prompts
from app.tracking import Tracker, atomic_json, sha256_file


def checked_resume(script, probe, review, contract):
    script_hash=hashlib.sha256(script.encode()).hexdigest()
    source=probe/'work/concept-candidates.json'
    candidate=json.loads(source.read_text(encoding='utf-8'))
    if candidate['script_sha256']!=script_hash: raise ValueError('resume_script_changed')
    batch=ConceptBatch.model_validate(candidate['batch'])
    accepted=[]
    for path in sorted((probe/'work').glob('semantic-analysis-*.json')):
        value=json.loads(path.read_text(encoding='utf-8'))
        if value.get('status')=='STRUCTURAL_PASS' and value.get('analysis'):
            accepted.append((path,value))
    if len(accepted)!=1: raise ValueError('resume_analysis_ambiguous')
    analysis_path,observed=accepted[0]
    if observed['script_sha256']!=script_hash: raise ValueError('resume_analysis_script_changed')
    analysis=analysis_model(observed['analysis']['version']).model_validate(observed['analysis'])
    findings=inspect_analysis(analysis,script,contract)
    if findings: raise ValueError(findings)
    context=concept_context(analysis,contract,'cinematic_realism')
    provenance=json.loads((review/'input-evidence.json').read_text(encoding='utf-8'))
    if provenance['candidates_sha256']!=sha256_file(source) or provenance['analysis_sha256']!=sha256_file(analysis_path):
        raise ValueError('resume_review_input_changed')
    reports=[]
    paths=[source,analysis_path,review/'input-evidence.json']
    for order in ('abc','cba'):
        path=review/f'concept-review-{order}.json'
        report=json.loads(path.read_text(encoding='utf-8'))
        if (report['script_sha256']!=script_hash or report['context_sha256']!=digest(context)
            or report['evaluator_version']!='concept-review-0.4'
            or report['model']!=contract['concept_selection']['review_model']):
            raise ValueError('resume_review_policy_changed')
        verdict=ConceptReview.model_validate(report['verdict'])
        if validate_review(verdict,script): raise ValueError('resume_invalid_review')
        reports.append(report); paths.append(path)
    comparison=compare_concept_orders(*reports,batch)
    if comparison['status']!='CONSISTENT_CONCEPT_SELECTION': raise ValueError(comparison['status'])
    concept=next(c for c in batch.candidates if digest(anonymous(c))==comparison['selected_sha256'])
    if not 0<=observed['attempt']<=3: raise ValueError('resume_repair_budget_invalid')
    return analysis,concept,3-observed['attempt'],comparison,paths


async def main():
    parser=argparse.ArgumentParser()
    for name in ('script','probe','review','output'): parser.add_argument(name,type=Path)
    parser.add_argument('--allow-subscription-director',action='store_true')
    parser.add_argument('--max-scene-repairs',type=int,choices=range(4),default=3)
    parser.add_argument('--prior-scene-attempt',type=Path,
                        help='Retain the failed baseline receipt when evaluating a changed engine')
    args=parser.parse_args()
    if not args.allow_subscription_director: raise ValueError('explicit_subscription_director_flag_required')
    script=args.script.read_text(encoding='utf-8')
    loaded=HarnessRegistry(ROOT/'harnesses').load('hybrid-story')
    contract=loaded.instance.describe_planning_contract(loaded.config)
    contract.update(trusted_source_catalog=[],trusted_illustration_catalog=[])
    analysis,concept,budget,comparison,paths=checked_resume(script,args.probe,args.review,contract)
    budget=min(budget,args.max_scene_repairs)
    prior=None
    if args.prior_scene_attempt:
        prior_path=args.prior_scene_attempt/'receipt.json'
        prior=json.loads(prior_path.read_text(encoding='utf-8'))
        if prior.get('status')!='GOAL_NOT_MET': raise ValueError('prior_scene_attempt_must_be_failed')
        if prior['harness']['source_sha256']==loaded.snapshot.as_dict()['source_sha256']:
            raise ValueError('unchanged_engine_cannot_reset_failed_attempt')
        paths.append(prior_path)
    out=args.output.resolve(); out.mkdir(parents=True,exist_ok=False)
    work=out/'work'; work.mkdir(); tracker=Tracker(out)
    atomic_json(out/'resume-evidence.json',{'status':'HASH_BOUND_DEVELOPMENT_RESUME','comparison':comparison,
        'inputs':[{'path':str(p),'sha256':sha256_file(p)} for p in paths],
        'semantic_analysis':analysis.model_dump(mode='json'),'selected_concept':concept.model_dump(mode='json'),
        'remaining_scene_repairs':budget,'prior_failed_harness':prior.get('harness') if prior else None,
        'human_approval':None})
    settings=SimpleNamespace(runner_mode='live',schemas_dir=ROOT/'video-generator/schemas',codex_model='gpt-6-sol',
        codex_reasoning_effort='low',codex_fast_mode=False,codex_read_timeout_seconds=180,codex_connect_timeout_seconds=10,
        subscription_base_url='http://image-oauth:10531')
    prompts,_=load_prompts(ROOT/'harnesses/hybrid-story/prompts')
    started=time.monotonic(); plan=None; error=None
    try:
        plan=await asyncio.wait_for(plan_with_codex(script,prompts,settings,tracker,work,image_style='cinematic_realism',
            harness_planning_contract=contract,source_units_override=analysis_units(analysis),semantic_analysis_result=analysis,
            selected_concept=concept,_repair_limit=budget),timeout=600)
        atomic_json(out/'scene-plan.json',plan.model_dump(mode='json'))
    except asyncio.CancelledError:
        error={'type':'CancelledError','message':'Interrupted; in-flight usage may be unknown'}
        raise
    except Exception as exc:
        error={'type':type(exc).__name__,'message':str(exc)[:1000]}
    finally:
        receipt={'status':'RESUMED_DIRECTOR_CONTRACT_PASS' if plan else 'GOAL_NOT_MET',
            'goal_status':'GOAL_NOT_MET','error':error,'usage':tracker.usage,'assets':tracker.assets,
            'harness':loaded.snapshot.as_dict(),'elapsed_seconds':round(time.monotonic()-started,3),
            'paid_api_calls':0,'image_calls':0,'voice_calls':0,'human_approval':None,
            'scope':'Development CLI using Core planner; not queue/service E2E or a rendered film'}
        atomic_json(out/'receipt.json',receipt)
        print(json.dumps({'status':receipt['status'],'error':error,'calls':len(tracker.usage),'seconds':receipt['elapsed_seconds']}),flush=True)
    if error: raise SystemExit(1)


if __name__=='__main__': asyncio.run(main())
