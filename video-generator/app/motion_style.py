"""Versioned motion treatment; a production contract, not a quality approval."""
from __future__ import annotations

from typing import Any

from .models import ScenePlan


STYLE_VERSION = "1.0.0"
STYLE_IDS = {"narrative", "educational_info"}


def style_instruction(style: dict[str, Any]) -> str:
    style_id = style["id"]
    if style_id == "narrative":
        return (
            "Motion production style: NARRATIVE. Select one recurring subject from the script "
            "(person, object or phenomenon); do not insert a person by default. Give that subject "
            "the same object_id and layout.continuity_group in every relevant scene. Preserve its "
            "identity, silhouette and visual markers through local change, wider context and result. "
            "Choose each scene strategy by meaning, not by a fixed template. Specify what must be "
            "isolated before image generation. Put concise, script-specific Korean names for the "
            "visible objects in layout.visual_labels. Give each "
            "object a concrete role and initial/final state; put meaningful object motion in motion. "
            "Never request actor performance without a reviewed rig. "
            "Do not reproduce a reference video's distinctive composition or artwork."
        )
    if style_id == "educational_info":
        return (
            "Motion production style: EDUCATIONAL INFORMATION. Set up a viewer question, reveal "
            "the principle, visualize steps/comparisons/quantities, then confirm understanding. "
            "Choose each scene strategy by meaning. Put concise factual labels in layout.visual_labels "
            "as editable text with normalized coordinates; keep the image prompt free of lettering. "
            "Give each moving diagram object an object_state and a meaningful state change. "
            "Use script-specific Korean names in layout.visual_labels. Give each object a concrete "
            "role and initial/final state; put meaningful "
            "object motion in motion. "
            "Do not invent statistics or move objects merely for decoration. "
            "If a requested mechanism needs a missing asset or action, expose that requirement."
        )
    raise ValueError("unknown motion style")


def bind_motion_style(plan: ScenePlan, style: dict[str, Any], *, mock: bool = False) -> ScenePlan:
    if style.get("id") not in STYLE_IDS or style.get("version") != STYLE_VERSION:
        raise ValueError("unsupported motion style snapshot")
    result = plan.model_copy(deep=True)
    style_id = style["id"]
    subjects_by_group: dict[str, list[set[str]]] = {}
    for scene in result.scenes:
        layout = scene.layout if isinstance(scene.layout, dict) else {}
        scene.layout = {**layout, "motion_style_id": style_id, "motion_style_version": STYLE_VERSION}
        if style_id == "narrative":
            group = layout.get("continuity_group")
            if mock and not group:
                group = "mock-primary-subject"
                scene.layout["continuity_group"] = group
            if isinstance(group, str) and group.strip():
                subject_ids = {
                    str(item.get("object_id"))
                    for item in scene.object_states
                    if isinstance(item, dict)
                    and item.get("role") == "subject"
                    and isinstance(item.get("object_id"), str)
                    and item.get("object_id") not in {"scene", "scene-image"}
                }
                subjects_by_group.setdefault(group, []).append(subject_ids)
        else:
            labels = layout.get("visual_labels") or []
            if mock and not labels:
                scene.layout["visual_labels"] = [{"text": scene.viewer_takeaway[:42], "x": .50, "y": .36}]
    if style_id == "narrative" and len(result.scenes) > 1:
        if not any(len(subjects) >= 2 for subjects in subjects_by_group.values()):
            raise ValueError("내러티브형에 장면 간 동일 주체의 continuity_group이 없습니다.")
        if not mock and not any(
            first & second
            for subjects in subjects_by_group.values()
            for index, first in enumerate(subjects)
            for second in subjects[index + 1:]
        ):
            raise ValueError("내러티브형의 같은 주체가 장면 간 동일한 object_id로 유지되지 않았습니다.")
    if style_id == "educational_info" and any(not scene.layout.get("visual_labels") for scene in result.scenes):
        raise ValueError("교육·정보형 장면에 편집 가능한 visual_labels가 없습니다.")
    return result
