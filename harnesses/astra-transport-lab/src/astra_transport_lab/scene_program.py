from __future__ import annotations

from typing import Any
from .transport import compile_tracks, compile_columns


VERSION = "astra-scene-program-1.0"
LAYOUTS = {"focus", "split", "comparison", "process", "diagram"}
TRANSITIONS = {"cut", "crossfade"}
RHYTHMS = {
    "read_then_move_then_hold": {"enter": 0.14, "move": 0.66, "settle": 0.20},
    "move_then_read_then_hold": {"enter": 0.22, "move": 0.58, "settle": 0.20},
    "compare_then_resolve": {"enter": 0.18, "move": 0.62, "settle": 0.20},
}
ROLE_COMPONENTS = {
    "subject": "scene-image",
    "evidence": "evidence-card",
    "highlight": "accent-orbit",
    "progress": "progress-line",
    "title": "scene-title",
}
EFFECTS = {"camera_push", "reveal", "emphasize", "progress", "transport_track"}


def compile_scene_program(scene: Any) -> dict[str, Any]:
    tracks=compile_tracks(scene)
    if any(not isinstance(a,dict) or a.get('kind') not in EFFECTS for a in getattr(scene,'motion',[]) or []):
        raise ValueError('Unsupported motion request in transport lab')
    layout = getattr(scene, "layout", {}) or {}
    mode = layout.get("mode") if isinstance(layout, dict) else None
    mode = mode if mode in LAYOUTS else "focus"
    transition = getattr(scene, "transition", "cut")
    transition = transition if transition in TRANSITIONS else "cut"
    rhythm_name = getattr(scene, "rhythm", "read_then_move_then_hold")
    rhythm = RHYTHMS.get(rhythm_name, RHYTHMS["read_then_move_then_hold"])

    components: dict[str, str] = {"scene-image": "subject", "scene-title": "title", "progress-line": "progress"}
    object_to_component: dict[str, str] = {}
    for item in getattr(scene, "object_states", []) or []:
        if not isinstance(item, dict):
            continue
        object_id = item.get("object_id")
        role = item.get("role")
        component = ROLE_COMPONENTS.get(role)
        if isinstance(object_id, str) and component:
            object_to_component[object_id] = component
            components[component] = role

    actions: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for action in getattr(scene, "motion", []) or []:
        if not isinstance(action, dict):
            continue
        effect = action.get("kind")
        target = object_to_component.get(action.get("object_id"))
        if effect not in EFFECTS or not target:
            continue
        normalized = "progress" if target == "progress-line" else effect
        key = (target, normalized)
        if key not in seen:
            seen.add(key)
            actions.append({"target": target, "effect": normalized})

    defaults = [
        {"target": "scene-image", "effect": "camera_push"},
        {"target": "scene-title", "effect": "reveal"},
        {"target": "progress-line", "effect": "progress"},
    ]
    for action in defaults:
        key = (action["target"], action["effect"])
        if key not in seen:
            actions.append(action)
    return {
        "transport_tracks": tracks,
        "transport_columns": compile_columns(scene),
        "version": VERSION,
        "scene_id": str(getattr(scene, "id", "scene")),
        "scene_function": str(getattr(scene, "scene_function", "explain")),
        "layout": mode,
        "transition": transition,
        "rhythm": rhythm_name if rhythm_name in RHYTHMS else "read_then_move_then_hold",
        "timing": rhythm,
        "components": sorted(components),
        "actions": actions,
        "ignored_motion_count": max(0, len(getattr(scene, "motion", []) or []) - len(tracks) - len([item for item in actions if item not in defaults])),
    }
