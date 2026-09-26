from pathlib import Path
from types import SimpleNamespace

from app.engine.harness_loader import HarnessRegistry
from app.engine.harness_preflight import validate_harness_plan
from app.planner import deterministic_plan
from app.scene_contracts import build_production_pack

ROOT = Path(__file__).resolve().parents[2]


def test_preflight_checks_actual_harness_without_providers():
    harness = HarnessRegistry(ROOT / 'harnesses').load('cinematic-slide')
    plan = deterministic_plan('결과를 기다립니다. 결과가 나타납니다.', 'cute')
    assert validate_harness_plan(harness, plan.scenes) == []
    plan.scenes[1].layout = {'continuity_group': 'same', 'camera': {'mode': 'push'}}
    errors = validate_harness_plan(harness, plan.scenes)
    assert len(errors) == 1
    assert errors[0].startswith(plan.scenes[1].id + ':camera_contract:')
    assert not harness.manifest.public


def test_legacy_harness_has_no_new_preflight_requirement():
    harness = HarnessRegistry(ROOT / 'harnesses').load('classic-slide')
    assert validate_harness_plan(harness, []) == []


def test_cinematic_scene_budget_is_checked():
    plan = deterministic_plan(''.join(f'{i}번째 문장입니다.' for i in range(11)), 'cute')
    pack = build_production_pack(plan, duration_profile='episode_60', harness_id='cinematic-slide')
    assert 'scene_count_exceeds_episode_60' in pack['findings']


def test_malformed_hook_result_is_not_silently_accepted():
    harness = SimpleNamespace(instance=SimpleNamespace(validate_plan=lambda scenes, config: True), config={})
    try:
        validate_harness_plan(harness, [])
    except TypeError:
        pass
    else:
        raise AssertionError('invalid preflight contract accepted')
