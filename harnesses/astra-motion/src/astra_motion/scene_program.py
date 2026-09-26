from __future__ import annotations

from typing import Any


VERSION = "astra-scene-program-1.4"
LAYOUTS = {"focus", "split", "comparison", "process", "diagram", "route"}
TRANSITIONS = {"cut", "crossfade", "dissolve"}
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
EFFECTS = {
    "camera_push", "camera_pull", "reveal", "emphasize", "progress",
    "path_follow", "state_change", "group_split", "reaction", "pulse", "hold",
}
PLANNABLE_EFFECTS = EFFECTS - {"emphasize", "progress"}


def _visual_variant(object_id: str, role: str) -> str:
    value = f"{object_id} {role}".lower()
    if any(token in value for token in ("card", "page", "fragment", "기억", "페이지")):
        return "cards"
    if any(token in value for token in ("spark", "stimulus", "자극")):
        return "sparks"
    if any(token in value for token in ("path", "route", "길")):
        return "path"
    if any(token in value for token in ("segment", "bar", "block", "비율", "시간")):
        return "bar"
    if any(token in value for token in ("walker", "person", "actor", "인물")):
        return "actor"
    return "symbol"


def compile_scene_program(scene: Any) -> dict[str, Any]:
    layout = getattr(scene, "layout", {}) or {}
    motion_style = layout.get("motion_style_id") if isinstance(layout, dict) else None
    mode = layout.get("mode") if isinstance(layout, dict) else None
    mode = mode if mode in LAYOUTS else "focus"
    transition = getattr(scene, "transition", "cut")
    transition = transition if transition in TRANSITIONS else "cut"
    if transition == "dissolve":
        transition = "crossfade"
    rhythm_name = getattr(scene, "rhythm", "read_then_move_then_hold")
    rhythm = RHYTHMS.get(rhythm_name, RHYTHMS["read_then_move_then_hold"])

    components: dict[str, str] = {"scene-image": "subject", "scene-title": "title", "progress-line": "progress"}
    object_to_component: dict[str, str] = {}
    decomposition = layout.get("layer_decomposition", {}) if isinstance(layout, dict) else {}
    decomposition_approved = (
        isinstance(decomposition, dict)
        and decomposition.get("status") == "TECHNICAL_PASS"
        and decomposition.get("production_ready") is True
    )
    extracted_layers = {
        str(item.get("object_id")): item
        for item in decomposition.get("layers", [])
        if isinstance(item, dict) and item.get("technical_ready") is True and item.get("rgba_path")
    } if decomposition_approved else {}
    semantic_objects: list[dict[str, Any]] = []
    for item in getattr(scene, "object_states", []) or []:
        if not isinstance(item, dict):
            continue
        object_id = item.get("object_id")
        role = item.get("role")
        component = ROLE_COMPONENTS.get(role)
        if isinstance(object_id, str) and object_id:
            extracted = extracted_layers.get(object_id)
            if extracted:
                semantic_objects.append({
                    "object_id": object_id,
                    "role": str(role or "semantic object"),
                    "variant": "layer-asset",
                    "asset_path": str(extracted["rgba_path"]),
                    "bounds": extracted.get("bounds"),
                    "depth_band": str(extracted.get("depth_band") or "midground"),
                })
            elif component and not (motion_style == "educational_info" and role != "subject"):
                object_to_component[object_id] = component
                components[component] = role
            else:
                if motion_style == "educational_info" and str(item.get("initial") or "").lower() in {"hidden", "context"} and str(item.get("final") or "").lower() in {"visible", "emphasized"}:
                    continue
                semantic_objects.append({
                    "object_id": object_id,
                    "role": str(role or "semantic object"),
                    "initial": str(item.get("initial") or ""),
                    "final": str(item.get("final") or ""),
                    "variant": _visual_variant(object_id, str(role or "")),
                })

    actions: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for action in getattr(scene, "motion", []) or []:
        if not isinstance(action, dict):
            continue
        effect = action.get("kind")
        target = object_to_component.get(action.get("object_id"))
        target_type = "component"
        if not target and any(item["object_id"] == action.get("object_id") for item in semantic_objects):
            target = str(action.get("object_id"))
            target_type = "semantic"
        if effect not in EFFECTS or not target:
            continue
        normalized = "progress" if target == "progress-line" else effect
        key = (target, normalized)
        if key not in seen:
            seen.add(key)
            actions.append({"target": target, "effect": normalized, "target_type": target_type})

    defaults = [
        {"target": "scene-title", "effect": "reveal", "target_type": "component"},
        {"target": "progress-line", "effect": "progress", "target_type": "component"},
    ]
    # A clean plate and its extracted layers share pixel coordinates. Moving only
    # the plate would detach the objects, so decomposed scenes keep the camera
    # locked until a shared camera rig is available.
    if not decomposition_approved and motion_style is None:
        defaults.insert(0, {"target": "scene-image", "effect": "camera_push", "target_type": "component"})
    if motion_style is not None:
        defaults = []
        actions = [action for action in actions if action["effect"] not in {"camera_push", "camera_pull"}]
    for action in defaults:
        key = (action["target"], action["effect"])
        if key not in seen:
            actions.append(action)
    return {
        "version": VERSION,
        "motion_style_id": motion_style,
        "local_visual": layout.get("local_visual") if isinstance(layout.get("local_visual"), dict) else None,
        "continuity_group": layout.get("continuity_group"),
        "visual_labels": [item for item in layout.get("visual_labels", []) if isinstance(item, dict)] if motion_style == "educational_info" else [],
        "scene_id": str(getattr(scene, "id", "scene")),
        "scene_function": str(getattr(scene, "scene_function", "explain")),
        "layout": mode,
        "transition": transition,
        "rhythm": rhythm_name if rhythm_name in RHYTHMS else "read_then_move_then_hold",
        "timing": rhythm,
        "components": sorted(components),
        "background_path": decomposition.get("background_path") if decomposition_approved else None,
        "decomposition_status": decomposition.get("status", "UNAVAILABLE") if isinstance(decomposition, dict) else "UNAVAILABLE",
        "semantic_objects": [] if layout.get("local_visual") else semantic_objects,
        "actions": [] if layout.get("local_visual") else actions,
        "ignored_motion_count": max(0, len(getattr(scene, "motion", []) or []) - len([
            item for item in actions if item.get("target_type") == "semantic" or item not in defaults
        ])),
    }
