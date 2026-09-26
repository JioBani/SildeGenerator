from app.planner import deterministic_plan
from app.scene_contracts import build_production_pack, evaluate_quality_gates


def test_genre_episode_uses_same_scene_budget():
    plan = deterministic_plan("".join(f"{index}번째 문장입니다." for index in range(11)), "평면 그래픽")
    pack = build_production_pack(plan, duration_profile="episode_60", harness_id="genre-slide")
    assert pack['status']=='BLOCKED'
    assert 'scene_count_exceeds_episode_60' in pack['findings']


def test_scene_contract_compiles_into_production_pack():
    plan = deterministic_plan("첫 장면입니다. 다음 장면입니다.", "평면 그래픽")
    pack = build_production_pack(plan, duration_profile="episode_60", harness_id="astra-motion")
    assert pack["status"] == "READY_FOR_COMPILATION"
    assert pack["scenes"][0]["scene_function"] == "establish"
    assert pack["scenes"][0]["motion"][0]["object_id"] == "scene-image"
    report = evaluate_quality_gates(pack, rendered_seconds=58.5)
    assert report["status"] == "TECHNICAL_PASS_HUMAN_PENDING"
    assert report["checks"]["P3_MOTION_AUDIO"] is True


def test_episode_contract_blocks_too_many_scenes_before_render():
    plan = deterministic_plan("".join(f"{index}번째 문장입니다." for index in range(11)), "평면 그래픽")
    pack = build_production_pack(plan, duration_profile="episode_60", harness_id="astra-motion")
    assert pack["status"] == "BLOCKED"
    assert "scene_count_exceeds_episode_60" in pack["findings"]


def test_experimental_capability_is_blocked_before_compilation():
    plan = deterministic_plan("첫 장면입니다.", "평면 그래픽")
    plan.scenes[0].renderer_requirements["experimental_capabilities"] = [{
        "capability": "actor_reaction",
        "contract": {
            "actor_asset_id": "actor-001", "actor_asset_sha256": "a" * 64,
            "rig_sha256": "b" * 64, "render_sha256": "c" * 64,
            "style_version": "style-v1", "event": "IMAGE_APPEARS",
            "gaze_target": "monitor_result", "frame_count": 120,
        },
    }]
    pack = build_production_pack(plan, duration_profile="episode_60", harness_id="astra-motion")
    assert pack["status"] == "BLOCKED"
    assert any("experimental_capability_blocked:actor_reaction:human_approval_missing" in item for item in pack["findings"])


def test_director_structural_repair_blocks_before_asset_work():
    plan = deterministic_plan("첫 장면입니다. 다음 장면입니다.", "평면 그래픽")
    finding = "director_structural_repair:source_unit_counts_adjusted:1"
    pack = build_production_pack(
        plan,
        duration_profile="episode_60",
        harness_id="cinematic-slide",
        upstream_findings=[finding],
    )
    assert pack["status"] == "BLOCKED"
    assert finding in pack["findings"]


def test_scene_virtual_motion_target_is_limited_to_camera_and_hold():
    plan = deterministic_plan("첫 장면입니다.", "평면 그래픽")
    plan.scenes[0].motion = [
        {"object_id": "scene", "kind": "camera_push", "phases": ["read", "settle"]},
    ]
    pack = build_production_pack(plan, duration_profile="episode_60", harness_id="classic-slide")
    assert "scene-001:motion_target_missing" not in pack["findings"]

    plan.scenes[0].motion = [
        {"object_id": "scene", "kind": "reveal", "phases": ["read", "settle"]},
    ]
    pack = build_production_pack(plan, duration_profile="episode_60", harness_id="classic-slide")
    assert "scene-001:motion_target_missing" in pack["findings"]
