from __future__ import annotations

from typing import Any

from .actor_scene import actor_execution_packet, validate_actor_scene_objects

from .director_safety import evaluate_scene_requests
from .models import ScenePlan
from .toolchain_policy import plan_scene_toolchain


VERSION = "astra-scene-production-pack-0.2"
EPISODE_60 = {
    "id": "episode_60",
    "target_seconds": 50,
    "planned_max_seconds": 54,
    "rendered_max_seconds": 60,
    "max_scenes": 10,
    "max_utterances": 16,
    "max_assets": 20,
}
SINGLE_30M = {
    "id": "single_30m",
    "target_seconds": 1800,
    "planned_max_seconds": 1800,
    "rendered_max_seconds": 1800,
    "max_scenes": 300,
}
DURATION_POLICIES = {item["id"]: item for item in (EPISODE_60, SINGLE_30M)}


def validate_scene_contract(
    plan: ScenePlan, *, duration_profile: str, harness_id: str,
    capability_approvals: list[dict[str, Any]] | None = None,
) -> list[str]:
    findings: list[str] = []
    policy = DURATION_POLICIES.get(duration_profile)
    if policy is None:
        findings.append("unsupported_duration_profile")
    if duration_profile == SINGLE_30M["id"] and harness_id not in ("classic-slide", "cinematic-slide"):
        findings.append("long_form_requires_slide_harness")
    limited = duration_profile == EPISODE_60["id"] and (
        plan.genre_contract is not None or harness_id in ("astra-motion", "genre-slide", "cinematic-slide")
    )
    if limited and len(plan.scenes) > EPISODE_60["max_scenes"]:
        findings.append("scene_count_exceeds_episode_60")
    if limited and len(plan.scenes) > EPISODE_60["max_utterances"]:
        findings.append("utterance_count_exceeds_episode_60")
    asset_count = len(plan.scenes) + len(plan.continuity_assets)
    if limited and asset_count > EPISODE_60["max_assets"]:
        findings.append("asset_count_exceeds_episode_60")
    for scene in plan.scenes:
        if scene.actor_performance is not None:
            # No released renderer consumes this research contract yet. Generic
            # capability approvals must not turn it into a silent slide fallback.
            findings.extend([
                f"{scene.id}:actor_runtime_not_in_production_harness",
                f"{scene.id}:actor_action_human_review_required",
            ])
            try:
                validate_actor_scene_objects(scene.actor_performance, scene.object_states)
            except ValueError as error:
                findings.append(f"{scene.id}:{error}")
        object_ids = {str(item.get("object_id", "")) for item in scene.object_states}
        if not object_ids or "" in object_ids:
            findings.append(f"{scene.id}:object_states_missing")
        for action in scene.motion:
            target = action.get("object_id")
            kind = action.get("kind")
            virtual_scene_target = target == "scene" and kind in {"camera_push", "camera_pull", "hold"}
            if target not in object_ids and not virtual_scene_target:
                findings.append(f"{scene.id}:motion_target_missing")
            phases = action.get("phases")
            if not isinstance(phases, list) or len(phases) < 2:
                findings.append(f"{scene.id}:motion_phases_missing")
        capabilities = scene.renderer_requirements.get("capabilities")
        if not isinstance(capabilities, list) or not capabilities:
            findings.append(f"{scene.id}:renderer_capabilities_missing")
        decisions = evaluate_scene_requests(
            scene.renderer_requirements,
            scene_id=scene.id,
            approvals=capability_approvals or [],
            production=True,
        )
        for decision in decisions:
            if not decision.get("allowed"):
                capability = decision.get("capability") or "unknown"
                for reason in decision.get("reason_codes", []):
                    findings.append(f"{scene.id}:experimental_capability_blocked:{capability}:{reason}")
    return findings


def build_production_pack(
    plan: ScenePlan, *, duration_profile: str, harness_id: str,
    capability_approvals: list[dict[str, Any]] | None = None,
    upstream_findings: list[str] | None = None,
    creative_readiness: dict[str, Any] | None = None,
) -> dict[str, Any]:
    approvals = capability_approvals or []
    findings = validate_scene_contract(
        plan, duration_profile=duration_profile, harness_id=harness_id,
        capability_approvals=approvals,
    )
    findings.extend(upstream_findings or [])
    authoring_by_scene = {
        item["scene_id"]: item for item in creative_readiness.get("scenes", [])
        if isinstance(item, dict) and isinstance(item.get("scene_id"), str)
    } if creative_readiness else {}
    return {
        "version": VERSION,
        "duration_policy": DURATION_POLICIES.get(duration_profile, EPISODE_60),
        "renderer": harness_id,
        "status": "BLOCKED" if findings else "READY_FOR_COMPILATION",
        "findings": findings,
        "creative_readiness": {
            "status": creative_readiness["status"],
            "production_ready": creative_readiness["production_ready"],
            "findings": creative_readiness["findings"],
        } if creative_readiness else None,
        "scenes": [{
            "scene_id": scene.id,
            "sequence_id": scene.sequence_id,
            "scene_function": scene.scene_function,
            "layout": scene.layout,
            "object_states": scene.object_states,
            "motion": scene.motion,
            "transition": scene.transition,
            "rhythm": scene.rhythm,
            "renderer_requirements": scene.renderer_requirements,
            **({"actor_execution": actor_execution_packet(scene.id, scene.actor_performance)}
               if scene.actor_performance is not None else {}),
            "asset_authoring": authoring_by_scene.get(scene.id),
            "toolchain_plan": plan_scene_toolchain(
                scene.renderer_requirements,
                selected_harness=harness_id,
            ),
            "capability_decisions": evaluate_scene_requests(
                scene.renderer_requirements,
                scene_id=scene.id,
                approvals=approvals,
                production=True,
            ),
        } for scene in plan.scenes],
        "automatic_production_approval": False,
        "human_gold_review_required": True,
    }


def evaluate_quality_gates(pack: dict[str, Any], *, rendered_seconds: float | None = None) -> dict[str, Any]:
    max_seconds = pack.get("duration_policy", EPISODE_60)["rendered_max_seconds"]
    checks = {
        "P0_SCRIPT_AND_DIRECTION": pack.get("status") == "READY_FOR_COMPILATION",
        "P1_SCENE_CONTRACT": not pack.get("findings"),
        "P2_ART_AND_COMPOSITION": None,
        "P3_MOTION_AUDIO": None if rendered_seconds is None else rendered_seconds <= max_seconds,
        "P4_GOLD_REGRESSION": None,
    }
    blocking = [key for key, value in checks.items() if value is False]
    actor_present = any(
        any(
            isinstance(obj, dict) and any(
                token in str(obj.get("role") or "").lower()
                for token in ("actor", "person", "character", "human", "인물", "배우", "캐릭터")
            )
            for obj in scene.get("object_states", [])
        )
        for scene in pack.get("scenes", [])
    )
    return {
        "version": "astra-quality-gates-0.1",
        "status": "BLOCKED" if blocking else "TECHNICAL_PASS_HUMAN_PENDING",
        "checks": checks,
        "blocking": blocking,
        "pending": [key for key, value in checks.items() if value is None],
        "automatic_production_approval": False,
        "human_review_axes": {
            "design": "PENDING",
            "story_comprehension": "PENDING",
            "actor_performance": "PENDING" if actor_present else "NOT_REQUESTED",
            "gold_regression": "PENDING",
        },
        "human_review_required": ["P2_ART_AND_COMPOSITION", "P4_GOLD_REGRESSION"],
    }
