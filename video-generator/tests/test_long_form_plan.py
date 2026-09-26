from app.long_form_plan import combine_plans, local_source_units, script_ranges
from app.planner import compile_source_units, deterministic_plan, validate_plan
from app.scene_contracts import build_production_pack, evaluate_quality_gates


def test_directed_ranges_form_one_plan_without_dropping_script():
    scenario = "".join(f"{index}번째 문장이 이어집니다.\n" for index in range(1, 81))
    ranges = script_ranges(scenario, compile_source_units(scenario), max_characters=260)
    assert len(ranges) > 1
    parts = [(start, deterministic_plan(scenario[start:end], "일관된 삽화")) for start, end in ranges]
    combined = combine_plans(scenario, parts)
    validate_plan(combined, scenario)
    assert "".join(scene.narration for scene in combined.scenes) == scenario
    assert combined.scenes[-1].id == f"scene-{len(combined.scenes):03d}"
    assert combined.sequences[-1].keycut_scene_id in {scene.id for scene in combined.scenes}


def test_ten_minute_shape_still_has_contiguous_ids_and_one_script():
    scenario = "".join(f"그해의 {index}번째 이야기는 다음 사건으로 이어집니다.\n" for index in range(1, 251))
    ranges = script_ranges(scenario, compile_source_units(scenario))
    combined = combine_plans(scenario, [
        (start, deterministic_plan(scenario[start:end], "일관된 삽화")) for start, end in ranges
    ])
    assert len(combined.scenes) == 250
    assert combined.scenes[-1].id == "scene-250"
    assert "".join(unit.text for unit in combined.source_units) == scenario


def test_short_lines_keep_global_source_budget_when_partitioned():
    scenario = "".join(f"{index}.\n" for index in range(1000))
    units = compile_source_units(scenario)
    ranges = script_ranges(scenario, units)
    local = [local_source_units(units, start, end) for start, end in ranges]
    assert len(units) <= 300
    assert sum(len(part) for part in local) == len(units)
    assert "".join(unit.text for part in local for unit in part) == scenario


def test_slide_long_form_policy_preserves_episode_limit():
    plan = deterministic_plan("짧은 이야기입니다.", "삽화")
    long_pack = build_production_pack(plan, duration_profile="single_30m", harness_id="classic-slide")
    assert long_pack["status"] == "READY_FOR_COMPILATION"
    assert evaluate_quality_gates(long_pack, rendered_seconds=1799)["status"] != "BLOCKED"
    assert evaluate_quality_gates(long_pack, rendered_seconds=1801)["status"] == "BLOCKED"
    episode_pack = build_production_pack(plan, duration_profile="episode_60", harness_id="classic-slide")
    assert evaluate_quality_gates(episode_pack, rendered_seconds=61)["status"] == "BLOCKED"
    assert "long_form_requires_slide_harness" in build_production_pack(
        plan, duration_profile="single_30m", harness_id="astra-motion"
    )["findings"]


def test_cinematic_long_form_is_not_capped_at_ten_scenes():
    scenario = "".join(f"{index}번째 사건이 일어났습니다.\n" for index in range(1, 31))
    plan = deterministic_plan(scenario, "삽화")
    long_pack = build_production_pack(plan, duration_profile="single_30m", harness_id="cinematic-slide")
    assert len(plan.scenes) > 10
    assert long_pack["status"] == "READY_FOR_COMPILATION"
    short_pack = build_production_pack(plan, duration_profile="episode_60", harness_id="cinematic-slide")
    assert "scene_count_exceeds_episode_60" in short_pack["findings"]
