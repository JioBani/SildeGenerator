from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class VoiceSettings(BaseModel):
    provider: Literal["mock", "microsoft_edge", "elevenlabs"]
    model: str = Field(min_length=1, max_length=120)
    voice_id: str = Field(min_length=1, max_length=160)
    voice_name: str = Field(min_length=1, max_length=200)
    rate: str | None = Field(default=None, pattern=r"^[+-](?:100|[0-9]{1,2})%$")
    pitch: str | None = Field(default=None, pattern=r"^[+-](?:100|[0-9]{1,2})Hz$")
    volume: str | None = Field(default=None, pattern=r"^[+-](?:100|[0-9]{1,2})%$")
    stability: float | None = Field(default=None, ge=0, le=1)
    similarity_boost: float | None = Field(default=None, ge=0, le=1)
    speed: float | None = Field(default=None, ge=.7, le=1.2)
    version: int = Field(default=1, ge=1)


class VoiceSampleRequest(BaseModel):
    text: str = Field(min_length=1, max_length=200)
    voice_settings: VoiceSettings


class RenderRequest(BaseModel):
    job_id: str = Field(pattern=r"^[0-9a-fA-F-]{36}$")
    attempt: int = Field(default=1, ge=1, le=10)
    scenario: str = Field(min_length=1, max_length=20_000)
    codex_model: str | None = Field(default=None, min_length=1, max_length=100)
    codex_reasoning_effort: str | None = Field(default=None, pattern=r"^(low|medium|high|xhigh|max)$")
    codex_fast_mode: bool | None = None
    image_model: Literal["gpt-image-2", "gpt-image-2.5-sunburst", "gpt-image-2.5-flare"] | None = None
    continuity_enabled: bool = False
    image_style: Literal["editorial_illustration", "cinematic_realism", "graphic_explainer"] = "editorial_illustration"
    voice_settings: VoiceSettings | None = None
    harness_id: str = Field(default="classic-slide", pattern=r"^[a-z][a-z0-9-]{1,63}$")
    harness_snapshot: dict[str, Any] | None = None

    @field_validator("scenario")
    @classmethod
    def strip_scenario(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("scenario must not be blank")
        return value


AssetCategory = Literal["character", "object", "location", "vehicle", "graphic", "phenomenon"]
ImageStyle = Literal["editorial_illustration", "cinematic_realism", "graphic_explainer"]


class SourceUnit(BaseModel):
    id: str = Field(pattern=r"^unit-[0-9]{3,4}$")
    start_offset: int = Field(ge=0)
    end_offset: int = Field(gt=0)
    text: str = Field(min_length=1)


class StyleBible(BaseModel):
    preset_id: ImageStyle
    medium_and_rendering: str = Field(min_length=1, max_length=2000)
    palette: list[str] = Field(min_length=1, max_length=20)
    lighting: str = Field(min_length=1, max_length=1000)
    camera_and_depth: str = Field(min_length=1, max_length=1000)
    texture_and_detail: str = Field(min_length=1, max_length=1000)
    character_rendering: str = Field(min_length=1, max_length=1000)
    environment_rendering: str = Field(min_length=1, max_length=1000)
    composition_rules: list[str] = Field(min_length=1, max_length=20)
    forbidden_variations: list[str] = Field(min_length=1, max_length=20)


class KeycutDNA(BaseModel):
    story_meaning: str = Field(min_length=1, max_length=1000)
    composition_anchor: str = Field(min_length=1, max_length=1000)
    palette_anchor: list[str] = Field(min_length=1, max_length=20)
    lighting_anchor: str = Field(min_length=1, max_length=1000)
    symbol_anchor: list[str] = Field(default_factory=list, max_length=20)
    must_inherit: list[str] = Field(min_length=1, max_length=20)
    must_not_copy: list[str] = Field(min_length=1, max_length=20)


class NarrativeSequence(BaseModel):
    id: str = Field(pattern=r"^sequence-[0-9]{3}$")
    source_unit_ids: list[str] = Field(min_length=1, max_length=300)
    role_in_story: Literal["hook", "setup", "problem", "development", "escalation", "turning_point", "explanation", "application", "resolution", "outro", "other"]
    purpose: str = Field(min_length=1, max_length=1000)
    viewer_state_before: str = Field(min_length=1, max_length=1000)
    viewer_state_after: str = Field(min_length=1, max_length=1000)
    scene_group_ids: list[str] = Field(min_length=1, max_length=300)
    keycut_scene_id: str = Field(pattern=r"^scene-[0-9]{3}$")


class SceneGroup(BaseModel):
    id: str = Field(pattern=r"^group-[0-9]{3}$")
    sequence_id: str = Field(pattern=r"^sequence-[0-9]{3}$")
    source_unit_ids: list[str] = Field(min_length=1, max_length=300)
    role_in_sequence: Literal["introduce", "explain", "evidence", "example", "contrast", "deepen", "transition", "payoff", "recap", "other"]
    purpose: str = Field(min_length=1, max_length=1000)
    setup: str = Field(min_length=1, max_length=1000)
    payoff: str = Field(min_length=1, max_length=1000)
    scene_ids: list[str] = Field(min_length=1, max_length=300)


class ContinuityState(BaseModel):
    state_id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{0,63}$")
    description: str = Field(min_length=1, max_length=500)


class ContinuityAsset(BaseModel):
    asset_id: str = Field(pattern=r"^asset-(character|object|location|vehicle|graphic|phenomenon)-[0-9]{3}$")
    category: AssetCategory
    name: str = Field(min_length=1, max_length=120)
    canonical_identity: str = Field(min_length=1, max_length=2000)
    must_remain_consistent: list[str] = Field(default_factory=list, max_length=20)
    allowed_variations: list[str] = Field(default_factory=list, max_length=20)
    states: list[ContinuityState] = Field(default_factory=list, max_length=20)
    appearing_scene_ids: list[str] = Field(min_length=2, max_length=300)
    selection_reason_code: str = Field(min_length=1, max_length=80)
    selection_reason: str = Field(min_length=1, max_length=500)
    failure_if_inconsistent: str = Field(min_length=1, max_length=500)
    confidence: float = Field(ge=0, le=1)
    anchor_prompt: str = Field(min_length=1, max_length=4000)


class RejectedContinuityCandidate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    reason_code: str = Field(min_length=1, max_length=80)


class Scene(BaseModel):
    id: str = Field(pattern=r"^scene-[0-9]{3}$")
    sequence_id: str = Field(default="sequence-001", pattern=r"^sequence-[0-9]{3}$")
    scene_group_id: str = Field(default="group-001", pattern=r"^group-[0-9]{3}$")
    source_unit_ids: list[str] = Field(default_factory=lambda: ["unit-001"], min_length=1, max_length=300)
    role_in_group: str = Field(default="legacy scene", min_length=1, max_length=1000)
    purpose: str = Field(default="legacy prompt compilation", min_length=1, max_length=1000)
    viewer_takeaway: str = Field(default="legacy scene", min_length=1, max_length=1000)
    cut_role: Literal["keycut", "setup", "derived", "bridge", "evidence", "reaction", "detail", "transition", "payoff"] = "keycut"
    parent_keycut_scene_id: str | None = Field(default=None, pattern=r"^scene-[0-9]{3}$")
    keycut_dna: KeycutDNA | None = None
    narration: str = ""
    visual_summary: str
    image_prompt: str
    present_asset_ids: list[str] = Field(default_factory=list, max_length=16)
    reference_asset_ids: list[str] = Field(default_factory=list, max_length=16)
    duration_seconds: float = 0
    image_path: str = ""
    audio_path: str = ""


class ScenePlan(BaseModel):
    title: str
    core_question: str = Field(min_length=1, max_length=1000)
    thesis: str = Field(min_length=1, max_length=2000)
    audience_start_state: str = Field(min_length=1, max_length=1000)
    audience_end_state: str = Field(min_length=1, max_length=1000)
    master_keycut_scene_id: str = Field(pattern=r"^scene-[0-9]{3}$")
    style_bible: StyleBible
    source_units: list[SourceUnit] = Field(default_factory=list, max_length=1000)
    sequences: list[NarrativeSequence] = Field(min_length=1, max_length=300)
    scene_groups: list[SceneGroup] = Field(min_length=1, max_length=300)
    continuity_assets: list[ContinuityAsset] = Field(default_factory=list, max_length=100)
    rejected_borderline_candidates: list[RejectedContinuityCandidate] = Field(default_factory=list, max_length=10)
    scenes: list[Scene]


class RunnerResult(BaseModel):
    success: bool
    video_path: str
    message: str = ""
    stages: list[dict[str, Any]] = Field(default_factory=list)
    usage: list[dict[str, Any]] = Field(default_factory=list)
    assets: list[dict[str, Any]] = Field(default_factory=list)
    prompts: list[dict[str, Any]] = Field(default_factory=list)
    narrative_blueprint: dict[str, Any] | None = None
    harness_snapshot: dict[str, Any] | None = None
