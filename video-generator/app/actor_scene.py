"""Typed, opt-in handoff to the research actor runtime; never an approval source."""
from __future__ import annotations

from copy import deepcopy
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictFloat, model_validator


ACTOR_SCENE_VERSION = "actor-scene-0.1"
ACTOR_ID = "astra-vector-standard-01"
Identifier = Annotated[str, Field(pattern=r"^[A-Za-z][A-Za-z0-9_-]{0,79}$")]
Point = Annotated[list[StrictFloat], Field(min_length=2, max_length=2)]


class ActorContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class ActorPlacement(ActorContractModel):
    id: Identifier
    asset_id: Literal["astra-vector-standard-01"]
    origin: Point


class ActorSceneObject(ActorContractModel):
    id: Identifier
    kind: Literal["stimulus", "report", "curtain_handle", "destination"]
    position: Point


class ActorActionIntent(ActorContractModel):
    actor_object_id: Identifier
    action: Literal["grasp_retain", "grasp_pull"]
    purpose: str = Field(min_length=1, max_length=500)
    stimulus_id: Identifier
    target_id: Identifier
    destination_id: Identifier | None
    side: Literal["left", "right"]
    emotion: Literal["pleased", "discomfort"]
    start: StrictFloat = Field(ge=0, le=2)
    speed: StrictFloat = Field(ge=.65, le=1.4)
    intensity: StrictFloat = Field(ge=.3, le=1)
    duration: StrictFloat = Field(ge=4, le=10)


class ActorScenePerformance(ActorContractModel):
    version: Literal["actor-scene-0.1"]
    canvas: Point
    actors: list[ActorPlacement] = Field(min_length=1, max_length=1)
    objects: list[ActorSceneObject] = Field(min_length=2, max_length=3)
    intent: ActorActionIntent

    @model_validator(mode="after")
    def validate_references(self) -> "ActorScenePerformance":
        if self.canvas != [1000, 820] or self.actors[0].origin != [500, 760]:
            raise ValueError("actor_canvas_or_placement_not_supported")
        ids = [item.id for item in [*self.actors, *self.objects]]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate_actor_scene_object")
        intent = self.intent
        if intent.actor_object_id != self.actors[0].id:
            raise ValueError("actor_object_missing")
        objects = {item.id: item for item in self.objects}
        roles = [(intent.stimulus_id, {"stimulus"}),
                 (intent.target_id, {"report", "curtain_handle"})]
        if intent.action == "grasp_pull":
            roles.append((intent.destination_id, {"destination"}))
        elif intent.destination_id is not None:
            raise ValueError("retain_has_no_destination")
        for object_id, kinds in roles:
            if object_id not in objects or objects[object_id].kind not in kinds:
                raise ValueError("actor_target_missing_or_wrong_role")
        if set(objects) != {item[0] for item in roles}:
            raise ValueError("unused_actor_scene_object")
        for item in self.objects:
            if not (0 <= item.position[0] <= 1000 and 0 <= item.position[1] <= 820):
                raise ValueError("actor_object_outside_canvas")
        if not intent.purpose.strip():
            raise ValueError("actor_purpose_required")
        if intent.duration < intent.start + 6.1 / intent.speed:
            raise ValueError("actor_contact_settle_truncated")
        # Full IK/path feasibility remains the runtime compiler's responsibility.
        return self


def actor_planning_extension() -> dict[str, Any]:
    """Explicit research caller opt-in. Not used by released Harness defaults."""
    return {
        "version": ACTOR_SCENE_VERSION,
        "actor_id": ACTOR_ID,
        "actions": ["grasp_retain", "grasp_pull"],
        "constraints": [
            "Research only; no human approval or production readiness may be emitted.",
            "Use actor_performance=null if this scene does not need an actor action.",
            "Use one standard actor at [500,760] on a [1000,820] canvas.",
            "All actor/prop/stimulus/destination IDs must appear in scene.object_states.",
            "Inventory positions use canvas pixels, not actor-local or normalized coordinates.",
            "Contact actions include notice, expression, reach, grip, hold and settle.",
            "Target wrist workspace: side-local x 130..225, y -505..-340; grip anchor is 10px from wrist.",
            "Curtain: left hand, horizontal rightward pull 10..75px; no cloth simulation.",
            "Duration must contain start + 6.1/speed seconds; narration is not shortened.",
            "Scene IDs, rig paths, code, approval flags and production mode belong to the runtime, not the model.",
        ],
    }


def actor_contract_enabled(contract: dict[str, Any] | None) -> bool:
    extension = (contract or {}).get("actor_performance")
    if extension is None:
        return False
    if extension != actor_planning_extension():
        raise ValueError("unsupported_actor_planning_contract")
    return True


def scene_output_schema(base: dict[str, Any], contract: dict[str, Any] | None) -> dict[str, Any]:
    result = deepcopy(base)
    if not actor_contract_enabled(contract):
        return result
    actor = ActorScenePerformance.model_json_schema()
    definitions = actor.pop("$defs", {})
    definitions["ActorScenePerformance"] = actor
    if set(definitions) & set(result["$defs"]):
        raise ValueError("actor_schema_definition_collision")
    result["$defs"].update(definitions)
    scene = result["$defs"]["scene"]
    scene["required"].append("actor_performance")
    scene["properties"]["actor_performance"] = {
        "anyOf": [{"$ref": "#/$defs/ActorScenePerformance"}, {"type": "null"}],
    }
    return result


def validate_actor_proposal(proposal: dict[str, Any], contract: dict[str, Any] | None) -> None:
    enabled = actor_contract_enabled(contract)
    for sequence in proposal["sequences"]:
        for group in sequence["scene_groups"]:
            for scene in group["scenes"]:
                if not enabled and scene.get("actor_performance") is not None:
                    raise ValueError("actor_performance_not_requested")
                if enabled and "actor_performance" not in scene:
                    raise ValueError("actor_performance_choice_missing")
                value = scene.get("actor_performance")
                if value is not None:
                    performance = ActorScenePerformance.model_validate(value)
                    validate_actor_scene_objects(performance, scene["object_states"])


def validate_actor_scene_objects(performance: ActorScenePerformance, states: list[dict[str, Any]]) -> None:
    state_ids = [item.get("object_id") for item in states]
    required = {item.id for item in [*performance.actors, *performance.objects]}
    if any(state_ids.count(object_id) != 1 for object_id in required):
        raise ValueError("actor_inventory_not_in_scene_object_states")


def actor_execution_packet(scene_id: str, performance: ActorScenePerformance) -> dict[str, Any]:
    return {
        "intent": {"version": "actor-intent-0.1", "scene_id": scene_id,
                   **performance.intent.model_dump(mode="json")},
        "scene": {"id": scene_id, "canvas": performance.canvas,
                  "actors": [actor.model_dump(mode="json") for actor in performance.actors],
                  "objects": [obj.model_dump(mode="json") for obj in performance.objects]},
    }
