"""Unified motion-graphics direction contract.

Legacy genre labels are retained only as scene-level strategy names. They are not
user-visible formats and must never select a fixed frame.
"""
from copy import deepcopy
import hashlib
import json

VERSION = "1.0.0"
SCENE_STRATEGIES = {
    "causal_explanation": {
        "use_when": "the viewer must understand why one state produces another",
        "grammar": ["question", "cause", "state_change", "consequence", "read_hold"],
    },
    "guided_sequence": {
        "use_when": "order, procedure or staged observation matters",
        "grammar": ["goal", "active_step", "action_or_observation", "result", "confirmation"],
    },
    "character_response": {
        "use_when": "a human or host reaction carries meaning",
        "grammar": ["stimulus", "gaze_acquire", "reaction", "explanation", "settle"],
    },
    "symbolic_compression": {
        "use_when": "an event benefits from concise visual exaggeration",
        "grammar": ["setup", "anticipation", "impact", "reaction", "consequence"],
    },
    "evidence_context": {
        "use_when": "the distinction between claim, evidence and reconstruction matters",
        "grammar": ["claim", "evidence", "source_status", "context", "interpretation"],
    },
}
PROFILES = {
    "motion_graphic": {
        "name": "모션그래픽",
        "purpose": "explain_with_designed_motion",
        "treatment": "director_authored_per_scene",
        "default_image_style": "graphic_explainer",
        "design": "Flat, editable visual objects whose layout and motion communicate the scene function.",
        "scene_strategies": list(SCENE_STRATEGIES),
        "requirements": [
            "strategy_selected_per_scene",
            "object_identity_preserved",
            "motion_has_semantic_reason",
            "read_hold_and_settle",
            "source_status_when_evidence_is_claimed",
        ],
        "signals": [],
    },
}


def snapshot(profile_id="motion_graphic"):
    if profile_id not in PROFILES:
        raise ValueError("Only the unified motion_graphic format is available")
    profile = {
        "id": profile_id,
        "version": VERSION,
        **deepcopy(PROFILES[profile_id]),
        "strategy_definitions": deepcopy(SCENE_STRATEGIES),
    }
    profile.pop("signals")
    encoded = json.dumps(profile, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {
        **profile,
        "sha256": hashlib.sha256(encoded.encode()).hexdigest(),
        "release_status": "human_review_required",
        "production_approved": False,
    }


def recommend(_scenario):
    return {
        "genre_id": "motion_graphic",
        "uncertain": False,
        "reason": "사용자 형식은 모션그래픽 하나이며 장면 전략은 감독이 내부적으로 선택합니다.",
        "requires_confirmation": False,
    }


def planning_instruction(profile_id="motion_graphic", image_style=None):
    profile = snapshot(profile_id)
    style = f"\nSurface art style: {image_style}." if image_style else ""
    return (
        "Unified motion-graphics contract:\n"
        + json.dumps(profile, ensure_ascii=False)
        + style
        + "\nFor every scene, choose exactly one primary scene strategy from the contract based on "
        "scene_function. A strategy is not a frame template. Design layout, object states, motion, "
        "transition and rhythm from the viewer takeaway. Preserve narration and source order. "
        "Motion must expose a state change, relation, attention shift or causal step; otherwise hold. "
        "Record evidence and reconstruction status whenever a scene may be read as factual material."
    )


def bind_plan(plan, profile_id="motion_graphic"):
    profile = snapshot(profile_id)
    result = plan.model_copy(deep=True)
    result.genre_contract = profile
    for scene in result.scenes:
        scene.layout = {
            **scene.layout,
            "production_format": "motion_graphic",
            "format_version": VERSION,
            "available_scene_strategies": list(SCENE_STRATEGIES),
        }
    return result
