"""Prepare exact director inputs; optional explicitly requested planning-only run."""
import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
# This tool never reads deployment settings or credentials.
os.environ['RUNNER_ENV_FILE'] = str(ROOT / 'nonexistent-benchmark-settings.fixture')
sys.path.insert(0, str(ROOT / 'video-generator'))
from app.genre_profiles import snapshot, planning_instruction
from app.director_research import research_prompt, select_research_candidates
from app.plan_compiler import structural_repair_findings
from app.planner import _compose_prompt, compile_source_units, create_plan
from app.prompts import load_prompts
from app.tracking import Tracker, atomic_json
from app.engine.harness_loader import HarnessRegistry
from app.engine.harness_preflight import planning_contract, validate_harness_plan


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('script', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--variant', choices=['baseline', 'research_pilot'])
    parser.add_argument('--style', choices=['graphic_explainer', 'editorial_illustration', 'cinematic_realism'],
        default='graphic_explainer')
    parser.add_argument('--model', choices=['gpt-5.6-terra', 'gpt-5.6-sol'], default='gpt-5.6-terra')
    parser.add_argument('--subscription-base-url',
        choices=['http://127.0.0.1:10531', 'http://image-oauth:10531'],
        default='http://127.0.0.1:10531',
        help='Approved local subscription bridge only; remote endpoints are rejected')
    parser.add_argument('--execute-subscription', action='store_true', help='Requires explicit approval; one planning request only, no retry')
    args = parser.parse_args()
    if args.execute_subscription and args.variant is None:
        parser.error('Execute only one explicitly selected variant per approved run')
    variants = [args.variant] if args.variant else ['baseline', 'research_pilot']
    source = args.script.read_text(encoding='utf-8-sig')
    if not source.strip() or len(source) > 20000:
        parser.error('Script must contain 1..20000 characters')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    prompts, _ = load_prompts(ROOT / 'harnesses/astra-motion/prompts')
    schema = ROOT / 'video-generator/schemas/scene-plan.schema.json'
    harness = HarnessRegistry(ROOT / 'harnesses').load('astra-motion')
    contract = planning_contract(harness)
    settings = SimpleNamespace(runner_mode='live', schemas_dir=schema.parent,
        subscription_base_url=args.subscription_base_url, codex_model=args.model,
        codex_reasoning_effort='low', codex_fast_mode=False,
        codex_read_timeout_seconds=300, codex_connect_timeout_seconds=10)
    for variant in variants:
        work = output / variant
        work.mkdir()
        selected = dict(prompts)
        selected['image/style-guide.md'] += '\n\n' + planning_instruction('motion_graphic', args.style)
        brief = select_research_candidates(source, 'astra-motion', planning_contract=contract)
        prompt = _compose_prompt(
            selected, source, compile_source_units(source), True, args.style,
            director_research_context=research_prompt(brief) if variant == 'research_pilot' else '',
            harness_planning_contract=contract,
        )
        (work / 'director-input.txt').write_text(prompt, encoding='utf-8')
        record = {'status': 'PREPARED_NOT_EXECUTED', 'genre': snapshot('motion_graphic'),
            'variant': variant, 'research_brief': brief, 'style': args.style,
            'model': args.model, 'effort': 'low', 'harness': harness.snapshot.as_dict(),
            'source_sha256': hashlib.sha256(source.encode()).hexdigest(),
            'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(),
            'schema_sha256': hashlib.sha256(schema.read_bytes()).hexdigest(),
            'planning_requests_attempted': 0, 'automatic_retry': False,
            'image_tasks': 0, 'voice_tasks': 0, 'render_jobs': 0, 'human_approved': False}
        atomic_json(work / 'review.json', record)
        if not args.execute_subscription:
            continue
        tracker = Tracker(output)
        settings.director_research_mode = 'pilot' if variant == 'research_pilot' else 'off'
        record.update(status='PLANNING', planning_requests_attempted=1)
        atomic_json(work / 'review.json', record)
        try:
            plan = await create_plan(source, prompts, settings, tracker, work,
                genre_id='motion_graphic', harness_id='astra-motion', image_style=args.style,
                harness_planning_contract=contract, continuity_enabled=True,
                codex_model=args.model, codex_reasoning_effort='low', codex_fast_mode=False)
            findings = validate_harness_plan(harness, plan.scenes)
            repairs = {}
            if tracker.usage:
                repairs = (tracker.usage[-1].get('raw_usage') or {}).get('deterministic_repairs') or {}
                findings = structural_repair_findings(repairs) + findings
            atomic_json(work / 'director-repairs.json', repairs)
            atomic_json(work / 'scene-plan.json', plan.model_dump(mode='json'))
            record.update(status='REVISE' if findings else 'DESIGN_REVIEW_REQUIRED', findings=findings,
                scene_count=len(plan.scenes), scenes=[{'id': s.id, 'function': s.scene_function,
                    'layout': s.layout, 'transition': s.transition, 'rhythm': s.rhythm,
                    'narration': s.narration} for s in plan.scenes])
        except Exception as error:
            record.update(status='FAILED_NO_RETRY', error_type=type(error).__name__)
            raise
        finally:
            record['usage'] = tracker.usage
            atomic_json(work / 'review.json', record)
    print(f'{len(variants)} director input(s): {output}')


if __name__ == '__main__':
    asyncio.run(main())
