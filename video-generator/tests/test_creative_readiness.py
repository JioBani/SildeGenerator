from app.creative_readiness import evaluate_creative_readiness
from app.planner import deterministic_plan
from app.scene_contracts import build_production_pack, evaluate_quality_gates


def test_missing_story_reference_and_rig_data_are_not_invented():
    plan = deterministic_plan("밤의 빛이 창으로 들어옵니다.", "flat illustration")
    scene = plan.scenes[0]
    scene.motion = [{"object_id": "person", "kind": "reaction", "phases": ["notice", "settle"]}]
    scene.object_states = [{"object_id": "person", "role": "actor", "initial": "neutral",
                            "final": "noticing", "isolation": "preferred", "region_hint": None}]
    result = evaluate_creative_readiness(plan, harness_id="astra-motion")
    assert result["production_ready"] is False
    assert result["scenes"][0]["subject_goal"] == "NOT_SPECIFIED"
    assert result["scenes"][0]["movable_asset_intents"][0]["asset_route"] == "DESIGN_DECISION_REQUIRED"
    assert "scene-001:person:region_hint" in result["findings"]
    assert "scene-001:person:reviewed_source_asset" in result["findings"]
    assert "scene-001:design_reference_missing" in result["findings"]


def test_reference_cards_are_attached_to_exact_scene_only():
    plan = deterministic_plan("첫 장면입니다. 다음 장면입니다.", "flat illustration")
    result = evaluate_creative_readiness(plan, harness_id="astra-motion", reference_cards=[
        {"id": "ref-1", "scene_id": "scene-001", "url": "https://example.org/study", "role": "layout"},
    ])
    assert result["scenes"][0]["reference_card_ids"] == ["ref-1"]
    assert result["scenes"][1]["reference_card_ids"] == []
    assert "scene-002:design_reference_missing" in result["findings"]


def test_asset_authoring_intent_reaches_production_pack_without_self_approval():
    plan = deterministic_plan("밤의 빛이 창으로 들어옵니다.", "flat illustration")
    scene = plan.scenes[0]
    scene.motion = [{"object_id": "person", "kind": "reaction", "phases": ["notice", "settle"]}]
    scene.object_states = [{"object_id": "person", "role": "actor", "initial": "neutral",
                            "final": "noticing", "isolation": "required", "region_hint": [0.1, 0.1, 0.5, 0.7]}]
    readiness = evaluate_creative_readiness(plan, harness_id="astra-motion")
    pack = build_production_pack(plan, duration_profile="episode_60", harness_id="astra-motion",
                                 creative_readiness=readiness)
    assert pack["creative_readiness"]["production_ready"] is False
    intent = pack["scenes"][0]["asset_authoring"]["movable_asset_intents"][0]
    assert intent["authoring_plan"]["proposed_route"] == "separately_authored_layers"
    assert intent["authoring_plan"]["route_approved"] is False
    gates = evaluate_quality_gates(pack)
    assert "P2_ART_AND_COMPOSITION" in gates["pending"]
    assert gates["automatic_production_approval"] is False
    assert gates["human_review_axes"]["actor_performance"] == "PENDING"
    assert gates["human_review_axes"]["story_comprehension"] == "PENDING"
