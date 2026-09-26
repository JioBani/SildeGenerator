"""Bounded subscription-only director probe. Never calls image/voice providers."""
import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"video-generator"))
from app.engine.harness_loader import HarnessRegistry
from app.planner import create_plan
from app.prompts import load_prompts
from app.tracking import Tracker, atomic_json, sha256_file


def engine_image_style(requested):
    # Preserve the existing API ID without implying licensed characters or IP.
    return 'disney_animation' if requested == 'family_fairytale' else requested


async def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("script",type=Path)
    parser.add_argument("output",type=Path)
    parser.add_argument("--allow-subscription-director",action="store_true")
    parser.add_argument('--source-root',type=Path,help='Explicit trusted local source registry, never model-selected paths')
    parser.add_argument('--image-style',default='cinematic_realism',choices=['cinematic_realism','animation_3d','family_fairytale','dystopian'])
    args=parser.parse_args()
    if not args.allow_subscription_director:
        raise ValueError("explicit_subscription_director_flag_required")
    out=args.output.resolve()
    out.mkdir(parents=True,exist_ok=False)
    work=out/"work";work.mkdir()
    script=args.script.read_text(encoding="utf-8")
    loaded=HarnessRegistry(ROOT/"harnesses").load("hybrid-story")
    prompts,_=load_prompts(ROOT/"harnesses/hybrid-story/prompts")
    contract=loaded.instance.describe_planning_contract(loaded.config)
    from app.source_media import source_brief
    contract["trusted_source_catalog"]=source_brief(args.source_root.resolve()) if args.source_root else []
    contract["trusted_illustration_catalog"]=[]
    settings=SimpleNamespace(runner_mode="live",schemas_dir=ROOT/"video-generator/schemas",codex_model="gpt-6-sol",
        codex_reasoning_effort="low",codex_fast_mode=False,codex_read_timeout_seconds=180,codex_connect_timeout_seconds=10,
        subscription_base_url="http://image-oauth:10531")
    tracker=Tracker(out)
    started=time.monotonic()
    error=None;plan=None
    try:
        plan=await asyncio.wait_for(create_plan(script,prompts,settings,tracker,work,harness_id="hybrid-story",
            harness_planning_contract=contract,image_style=engine_image_style(args.image_style)),timeout=600)
        atomic_json(out/"scene-plan.json",plan.model_dump(mode="json"))
    except asyncio.CancelledError:
        error={"type":"CancelledError","message":"Probe interrupted; in-flight usage may be unknown"}
        raise
    except Exception as exc:
        error={"type":type(exc).__name__,"message":str(exc)[:1000]}
    finally:
        report=dict(status="DIRECTOR_CONTRACT_PASS" if plan else "GOAL_NOT_MET",scope="Development script; actual subscription director, no rendered film or independent approval",
            harness=loaded.snapshot.as_dict(),script_sha256=sha256_file(args.script),usage=tracker.usage,assets=tracker.assets,
            elapsed_seconds=round(time.monotonic()-started,3),error=error,paid_api_calls=0,image_calls=0,voice_calls=0,
            human_approval=None,not_evaluated=["independent_semantics","visual_quality","held_out_transfer","actual_frames"],
            interrupted_usage_unknown=bool(error and error['type']=='CancelledError'))
        report['source_catalog']=contract['trusted_source_catalog']
        report['source_catalog_sha256']=sha256_file(args.source_root/'catalog.json') if args.source_root else None
        report['image_style']=args.image_style
        report['engine_image_style']=engine_image_style(args.image_style)
        atomic_json(out/"receipt.json",report)
        print(json.dumps({"status":report["status"],"error":error,"calls":len(tracker.usage),"elapsed_seconds":report["elapsed_seconds"]},ensure_ascii=False),flush=True)
    if error: raise SystemExit(1)


if __name__=="__main__": asyncio.run(main())
