"""Recheck a frozen development concept batch through the production critic path."""
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
from app.concept_planning import concept_context, review_concept_batch
from app.engine.harness_loader import HarnessRegistry
from app.harness_sdk.concept_design import ConceptBatch
from app.harness_sdk.semantic_beats import analysis_model
from app.tracking import Tracker, atomic_json, sha256_file


async def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('script',type=Path)
    parser.add_argument('probe',type=Path)
    parser.add_argument('output',type=Path)
    parser.add_argument('--allow-subscription-director',action='store_true')
    args=parser.parse_args()
    if not args.allow_subscription_director:
        raise ValueError('explicit_subscription_director_flag_required')
    script=args.script.read_text(encoding='utf-8')
    candidate_file=args.probe/'work/concept-candidates.json'
    candidate=json.loads(candidate_file.read_text(encoding='utf-8'))
    accepted=[]
    for path in sorted((args.probe/'work').glob('semantic-analysis-*.json')):
        value=json.loads(path.read_text(encoding='utf-8'))
        if value.get('status')=='STRUCTURAL_PASS' and value.get('analysis'):
            accepted.append((path,value))
    if len(accepted)!=1:
        raise ValueError('frozen_probe_needs_one_accepted_analysis')
    analysis_file,observed=accepted[0]
    script_hash=hashlib.sha256(script.encode()).hexdigest()
    if any(value['script_sha256']!=script_hash for value in (candidate,observed)):
        raise ValueError('frozen_probe_script_mismatch')
    batch=ConceptBatch.model_validate(candidate['batch'])
    analysis=analysis_model(observed['analysis']['version']).model_validate(observed['analysis'])
    loaded=HarnessRegistry(ROOT/'harnesses').load('hybrid-story')
    contract=loaded.instance.describe_planning_contract(loaded.config)
    context=concept_context(analysis,contract,'cinematic_realism')
    out=args.output.resolve(); out.mkdir(parents=True,exist_ok=False)
    tracker=Tracker(out)
    atomic_json(out/'input-evidence.json',{
        'script_sha256':script_hash,'candidates_sha256':sha256_file(candidate_file),
        'analysis_sha256':sha256_file(analysis_file),'context':context,
        'scope':'Frozen development candidates; no prior verdicts provided to critic'})
    settings=SimpleNamespace(codex_read_timeout_seconds=180,codex_connect_timeout_seconds=10,
        subscription_base_url='http://image-oauth:10531')
    started=time.monotonic(); comparison=None; error=None
    try:
        comparison=await asyncio.wait_for(review_concept_batch(script,batch,context,settings,tracker,out,
            critic=contract['concept_selection']['review_model']),timeout=370)
    except Exception as exc:
        error={'type':type(exc).__name__,'message':str(exc)[:1000]}
    finally:
        receipt={'status':'REVIEW_RECORDED' if comparison else 'REVIEW_FAILED','goal_status':'GOAL_NOT_MET',
            'comparison':comparison,'error':error,'usage':tracker.usage,'assets':tracker.assets,
            'elapsed_seconds':round(time.monotonic()-started,3),'image_calls':0,'voice_calls':0,'paid_api_calls':0,
            'human_approval':None,'production_ready':False,'held_out':False}
        atomic_json(out/'receipt.json',receipt)
        print(json.dumps({'status':receipt['status'],'comparison':comparison,'error':error,
                          'calls':len(tracker.usage),'elapsed_seconds':receipt['elapsed_seconds']}),flush=True)
    if error: raise SystemExit(1)


if __name__=='__main__': asyncio.run(main())
