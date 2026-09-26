"""Review or repair one frozen plan's visible text without regenerating its scenes."""
import argparse
import asyncio
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'video-generator'))
from app.engine.harness_loader import HarnessRegistry
from app.models import ScenePlan
from app.tracking import Tracker, atomic_json, sha256_file
from app.visible_text_review import ensure_visible_text, review_visible_text


async def main(args):
    if not args.allow_subscription_director:
        raise ValueError('explicit_subscription_director_flag_required')
    plan = ScenePlan.model_validate_json(args.plan.read_text(encoding='utf-8'))
    out = args.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    work = out/'work'; work.mkdir()
    loaded = HarnessRegistry(ROOT/'harnesses').load('hybrid-story')
    contract = loaded.instance.describe_planning_contract(loaded.config)
    contract.update(trusted_source_catalog=[], trusted_illustration_catalog=[])
    if any(s.layout.get('hybrid', {}).get('route') == 'source' for s in plan.scenes):
        raise ValueError('source_plan_requires_registered_replay_context')
    settings = SimpleNamespace(codex_read_timeout_seconds=180, codex_connect_timeout_seconds=10,
        subscription_base_url='http://image-oauth:10531')
    tracker = Tracker(out); started = time.monotonic(); error = None; status = None
    atomic_json(out/'input-evidence.json', dict(plan_sha256=sha256_file(args.plan), harness=loaded.snapshot.as_dict(),
        scope='Frozen development plan, not new end-to-end planning or film approval'))
    try:
        if args.repair:
            updated = await ensure_visible_text(plan, contract, settings, tracker, work,
                generator_model='gpt-6-sol', repair_budget=1, attempt=0)
            atomic_json(out/'scene-plan.json', updated.model_dump(mode='json'))
            status = 'VISIBLE_TEXT_PASS'
        else:
            report = await review_visible_text(plan, contract, settings, tracker, work,
                generator_model='gpt-6-sol', name='visible-text-probe')
            status = report['status']
    except Exception as exc:
        error = {'type': type(exc).__name__, 'message': str(exc)[:1000]}
    receipt = dict(status=status or 'REVIEW_INCOMPLETE', error=error, goal_status='GOAL_NOT_MET',
        elapsed_seconds=round(time.monotonic()-started,3), usage=tracker.usage, paid_api_calls=0,
        image_calls=0, voice_calls=0, human_approval=None, production_ready=False,
        scope='Visible text gate only; repair budget1, not held-out or full-film validation')
    atomic_json(out/'receipt.json', receipt)
    print(json.dumps({k:receipt[k] for k in ('status','error','elapsed_seconds')},ensure_ascii=False),flush=True)
    if error: raise SystemExit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('plan', type=Path); parser.add_argument('output', type=Path)
    parser.add_argument('--repair', action='store_true')
    parser.add_argument('--allow-subscription-director', action='store_true')
    asyncio.run(main(parser.parse_args()))
