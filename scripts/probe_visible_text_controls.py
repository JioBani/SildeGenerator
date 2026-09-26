"""Authored development contrast set; expectations never enter critic input."""
import argparse
import asyncio
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'video-generator'))
from app.engine.harness_loader import HarnessRegistry
from app.models import ScenePlan
from app.tracking import Tracker, atomic_json, sha256_file
from app.visible_text_review import review_visible_text, text_packet


CASES = [
    ('같은 두 측정값', True, 'Valid concise noun heading'),
    ('중간 입출고는 알 수 없음', True, 'Complete uncertainty assertion'),
    ('중간 입출고 여부는 알 수', False, 'Incomplete assertion'),
    ('중간에는 입출고가 없었다', False, 'Unknown becomes asserted absence'),
    ('재고가 45개 증가했다', False, 'Equal endpoints become increase'),
    ('재고 단위는 kg', False, 'Count changed into mass'),
]


async def main(args):
    if not args.allow_subscription_director: raise ValueError('explicit_subscription_director_flag_required')
    plan = ScenePlan.model_validate_json(args.plan.read_text(encoding='utf-8'))
    if len(plan.scenes) != 1: raise ValueError('stock_fixture_requires_one_scene')
    pair = plan.scenes[0].layout['hybrid']['diagram']['snapshot_pair']
    if pair['before']['value'] != 45 or pair['after']['value'] != 45 or pair['unit'] != '개':
        raise ValueError('stock_control_fixture_mismatch')
    out = args.output.resolve(); out.mkdir(parents=True,exist_ok=False)
    work = out/'work'; work.mkdir()
    scenes=[]
    for i,(title,_,_) in enumerate(CASES,1):
        scene=plan.scenes[0].model_copy(deep=True); scene.id=f'scene-{i:03d}'
        scene.layout['hybrid']['diagram']['title']=title
        scenes.append(scene)
    plan.scenes=scenes
    loaded=HarnessRegistry(ROOT/'harnesses').load('hybrid-story')
    contract=loaded.instance.describe_planning_contract(loaded.config)
    settings=SimpleNamespace(codex_read_timeout_seconds=180,codex_connect_timeout_seconds=10,
        subscription_base_url='http://image-oauth:10531')
    tracker=Tracker(out); started=time.monotonic(); error=None; results=[]
    atomic_json(out/'input.json',dict(source_plan_sha256=sha256_file(args.plan),packet=text_packet(plan),
        expectations=[dict(scene_id=s.id,title=c[0],expected_pass=c[1],reason=c[2]) for s,c in zip(scenes,CASES)],
        scope='Authored development controls, not held-out or rendered films'))
    try:
        report=await review_visible_text(plan,contract,settings,tracker,work,generator_model='gpt-6-sol',name='visible-text-controls')
        verdict={v['text_id']:v for v in report['verdict']['texts']}
        for scene,case in zip(scenes,CASES):
            entries=[verdict[t['text_id']] for t in text_packet(plan)['texts'] if t['scene_id']==scene.id]
            passed=all(t[k]=='PASS' for t in entries for k in ('completeness','fidelity','referent_clarity'))
            results.append(dict(scene_id=scene.id,expected_pass=case[1],observed_pass=passed,
                matched=passed==case[1],judgments=entries))
    except Exception as exc: error=dict(type=type(exc).__name__,message=str(exc)[:800])
    matched=not error and all(r['matched'] for r in results) and len(results)==len(CASES)
    receipt=dict(status='CONTROLS_PASS' if matched else 'REVISE',goal_status='GOAL_NOT_MET',results=results,error=error,
        usage=tracker.usage,elapsed_seconds=round(time.monotonic()-started,3),paid_api_calls=0,human_approval=None,
        scope='Six authored text contrasts, not whole-film negative rate or transfer proof')
    atomic_json(out/'receipt.json',receipt)
    print(json.dumps(dict(status=receipt['status'],matched=sum(r['matched'] for r in results),error=error),ensure_ascii=False),flush=True)
    if not matched: raise SystemExit(1)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('plan',type=Path);parser.add_argument('output',type=Path)
    parser.add_argument('--allow-subscription-director',action='store_true')
    asyncio.run(main(parser.parse_args()))
