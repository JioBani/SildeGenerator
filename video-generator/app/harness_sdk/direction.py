"""Versioned shot intent and provider-free checks shared with creative harnesses."""
from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError


DIRECTION_VERSION = "narrative-direction-0.1"
Text = Annotated[str, Field(min_length=1, max_length=800)]


class DirectionModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, str_strip_whitespace=True)


class DramaticChoice(DirectionModel):
    action: Text
    cost: Text


class ShotDirection(DirectionModel):
    version: Literal["narrative-direction-0.1"]
    mode: Literal["character_story", "observational"]
    subject_id: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,63}$")
    subject_description: Text
    goal: Text
    stakes: Text
    beat: Literal["setup", "pressure", "choice", "action", "reaction", "consequence", "explanation", "evidence", "resolution"]
    visible_action: Text
    state_before: Text
    state_after: Text
    new_information: Text
    shot_size: Literal["extreme_wide", "wide", "medium", "close", "detail"]
    viewpoint: Literal["observer", "subject"]
    focal_target: Text
    cut_reason: Text
    cause_scene_number: int | None = Field(ge=1, le=300)
    choices: list[DramaticChoice] = Field(max_length=3)
    continuity_note: Text | None
    repeat_of_scene_number: int | None = Field(ge=1, le=300)
    repeat_reason: Text | None


class GroundedShotDirection(ShotDirection):
    version: Literal["narrative-direction-0.2"]


def direction_planning_extension(version=DIRECTION_VERSION) -> dict[str, Any]:
    if version not in {DIRECTION_VERSION,"narrative-direction-0.2"}:
        raise ValueError("unsupported_narrative_direction_version")
    result = {
        "version": version,
        "review_mode": "automatic_contract",
        "constraints": [
            "Every scene needs layout.direction. Depict a visible event, not a topic label.",
            "character_story: establish one subject's goal/stakes and a choice with at least two competing costs; show its consequence.",
            "observational: use a persistent object, phenomenon or question; never invent a character dilemma or historical fact.",
            "Use stable state names. Explain off-screen state changes in continuity_note.",
            "A reaction/consequence refers to its cause with a 1-based scene number, including the same scene when visibly shown there.",
            "Repeat composition only for a deliberate callback or comparison; name an earlier scene and explain the new meaning.",
            "Specify shot size, focal target and cut reason; never alternate shots mechanically.",
            "layout.camera uses hold/push/pull and normalized focus; a still slide cannot perform articulated body animation.",
            "Automatic contract acceptance measures declared structure, not observed human emotion or final artwork quality.",
        ],
    }
    if version=="narrative-direction-0.2":
        result["constraints"][1] = "character_story: preserve the stated goal, obstacle and action. A character need not face a dilemma. Never invent alternatives or costs to meet a template."
        result["constraints"].extend([
            "Show choices only when the script actually supplies alternatives; choices belong only to a choice beat.",
            "Do not demand an extra consequence scene if the script ends at a decision/action. Never add narration or an invented result.",
            "Cross-beat cause_scene_number must be grounded in semantic event_cause or motivation, not context or sequence. The full typed semantic relations remain authoritative."])
    return result


def direction_enabled(contract: dict[str, Any] | None) -> bool:
    extension = (contract or {}).get("narrative_direction")
    if extension is None:
        return False
    if extension != direction_planning_extension(extension.get("version")):
        raise ValueError("unsupported_narrative_direction_contract")
    return True


def direction_output_schema(base: dict[str, Any], contract: dict[str, Any] | None) -> dict[str, Any]:
    result = deepcopy(base)
    if not direction_enabled(contract):
        return result
    model = GroundedShotDirection if contract["narrative_direction"]["version"]=="narrative-direction-0.2" else ShotDirection
    schema = model.model_json_schema()
    definitions = schema.pop("$defs", {})
    definitions["ShotDirection"] = schema
    if set(definitions) & set(result["$defs"]):
        raise ValueError("direction_schema_definition_collision")
    result["$defs"].update(definitions)
    layout = result["$defs"]["scene"]["properties"]["layout"]
    layout["properties"]["direction"] = {"$ref": "#/$defs/ShotDirection"}
    layout["required"].append("direction")
    return result


def _normal(value: str) -> str:
    return re.sub(r"[\W_]+", "", value.casefold())


def evaluate_direction(scenes, *, required: bool = True, expected_version: str | None = None) -> dict[str, Any]:
    """Inspect declared intent. Pixel/semantic critics must evaluate the rendered film."""
    findings: list[str] = []
    directions: list[ShotDirection | None] = []
    for scene in scenes:
        value = (getattr(scene, "layout", {}) or {}).get("direction")
        if value is None:
            if required:
                findings.append(f"{scene.id}:direction_missing")
            directions.append(None)
            continue
        try:
            if expected_version is not None and value.get("version") != expected_version:
                findings.append(f"{scene.id}:direction_version_mismatch")
            model = GroundedShotDirection if value.get("version")=="narrative-direction-0.2" else ShotDirection
            directions.append(model.model_validate(value))
        except ValidationError as error:
            locations = [".".join(map(str, item["loc"])) for item in error.errors()]
            findings.append(f"{scene.id}:invalid_direction:{','.join(locations)}")
            directions.append(None)

    previous: dict[str, ShotDirection] = {}
    signatures: dict[tuple[str, ...], int] = {}
    choices: list[tuple[int, ShotDirection]] = []
    story_subjects: set[str] = set()
    for index, (scene, shot) in enumerate(zip(scenes, directions), 1):
        if shot is None:
            continue
        if shot.mode == "character_story":
            story_subjects.add(shot.subject_id)
        cause = shot.cause_scene_number
        if cause is not None and (cause > index or directions[cause - 1] is None):
            findings.append(f"{scene.id}:cause_not_available")
        if shot.beat in {"reaction", "consequence"} and cause is None:
            findings.append(f"{scene.id}:cause_required")
        if shot.beat == "choice":
            if len(shot.choices) < 2 or len({_normal(c.action) for c in shot.choices}) != len(shot.choices):
                findings.append(f"{scene.id}:competing_choices_required")
            choices.append((index, shot))
        elif shot.choices:
            findings.append(f"{scene.id}:choices_require_choice_beat")
        repeat = shot.repeat_of_scene_number
        if repeat is not None:
            if repeat >= index or not shot.repeat_reason or directions[repeat - 1] is None:
                findings.append(f"{scene.id}:invalid_callback")
            elif directions[repeat - 1] is not None and _normal(directions[repeat - 1].new_information) == _normal(shot.new_information):
                findings.append(f"{scene.id}:callback_adds_no_information")
        elif shot.repeat_reason:
            findings.append(f"{scene.id}:callback_target_missing")
        signature = tuple(_normal(v) for v in (shot.subject_id, shot.shot_size, shot.viewpoint,
                          shot.visible_action, shot.state_before, shot.state_after))
        if signature in signatures and repeat != signatures[signature]:
            findings.append(f"{scene.id}:unmotivated_repeated_shot:{signatures[signature]}")
        signatures[signature] = index
        prior = previous.get(shot.subject_id)
        if prior and _normal(prior.state_after) != _normal(shot.state_before) and not shot.continuity_note:
            findings.append(f"{scene.id}:unexplained_subject_state_change")
        previous[shot.subject_id] = shot
    for subject in story_subjects:
        subject_choices = [(number, shot) for number, shot in choices if shot.subject_id == subject]
        legacy = any(shot and shot.subject_id==subject and shot.version==DIRECTION_VERSION for shot in directions)
        if not subject_choices and legacy:
            findings.append(f"{subject}:character_choice_missing")
        for number, choice in subject_choices:
            if choice.version==DIRECTION_VERSION and not any(shot and shot.subject_id == subject and shot.beat in {"consequence", "resolution"}
                       for shot in directions[number:]):
                findings.append(f"{subject}:choice_has_no_later_consequence:{number}")
    payload = [shot.model_dump(mode="json") if shot else None for shot in directions]
    return {
        "version": expected_version or DIRECTION_VERSION,
        "status": "REVISE" if findings else "CONTRACT_PASS",
        "findings": findings,
        "plan_sha256": hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
        "evaluated": ["declared_causality", "subject_state_chain", "shot_repetition", "choice_consequence"],
        "not_evaluated": ["rendered_visuals", "actual_emotion", "factual_accuracy"],
        "human_approval": None,
    }
