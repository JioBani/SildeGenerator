from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncIterator

import httpx

from .config import Settings
from .codex_transcript import CodexTranscript
from .director_learning import (
    learning_prompt, record_learning_application, record_learning_selection, select_director_rules,
)
from .director_research import record_research_brief, research_prompt, select_research_candidates
from .models import (
    ContinuityAsset, KeycutDNA, NarrativeSequence, Scene, SceneGroup,
    ScenePlan, SourceUnit, StyleBible,
)
from .plan_compiler import compile_scene_plan, structural_repair_findings
from .tracking import Tracker


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _iter_sse(response: httpx.Response) -> AsyncIterator[tuple[str | None, str]]:
    event_name: str | None = None
    data: list[str] = []
    async for line in response.aiter_lines():
        if line == "":
            if data:
                yield event_name, "\n".join(data)
            event_name, data = None, []
            continue
        if line.startswith(":"):
            continue
        field, separator, value = line.partition(":")
        if not separator:
            continue
        value = value[1:] if value.startswith(" ") else value
        if field == "event":
            event_name = value
        elif field == "data":
            data.append(value)
    if data:
        yield event_name, "\n".join(data)


def _extract_output_text(payload: dict[str, Any]) -> str:
    direct = payload.get("output_text")
    if isinstance(direct, str) and direct:
        return direct
    for item in payload.get("output") or []:
        if not isinstance(item, dict):
            continue
        for content in item.get("content") or []:
            if isinstance(content, dict) and content.get("type") == "output_text":
                text = content.get("text")
                if isinstance(text, str) and text:
                    return text
    return ""


# 한 장면이 담는 최대 글자 수. 한국어 평서문 한 문장은 보통 이 값을 넘지 않으므로
# 문장이 문장 중간에서 잘리지 않는다. 문장이 이 값을 넘을 때만 쉼표 등 절 경계에서 나눈다.
SCENE_CHARACTER_LIMIT = 45


def _split_long(text: str, limit: int = SCENE_CHARACTER_LIMIT) -> list[str]:
    if len(text) <= limit:
        return [text]
    units = [part.strip() for part in re.findall(r"[^,，;；:：]+[,，;；:：]?", text) if part.strip()]
    if len(units) == 1:
        units = text.split()
    chunks: list[str] = []
    current = ""
    for unit in units:
        candidate = f"{current} {unit}".strip()
        if current and len(candidate) > limit:
            chunks.append(current)
            current = unit
        else:
            current = candidate
    if current:
        chunks.append(current)
    if len(chunks) == 1 and len(chunks[0]) > limit:
        value = chunks[0]
        chunks = [value[index:index + limit] for index in range(0, len(value), limit)]
    return chunks


def _split_sentences(scenario: str) -> list[str]:
    """Split on sentence endings or line boundaries without dropping text.

    Script authors commonly use one clause per line and end those lines with a
    comma.  A regex that only accepts a terminal sentence mark before a newline
    silently skips those clauses.  Walking each non-empty line makes the line
    boundary an explicit split point while retaining every punctuation mark.
    """
    sentences: list[str] = []
    closing_quotes = r'["\'”’」』】）》]*'
    for raw_line in scenario.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        start = 0
        for match in re.finditer(rf"[.!?。！？]+{closing_quotes}", line):
            piece = line[start:match.end()].strip()
            if piece:
                sentences.append(piece)
            start = match.end()
        remainder = line[start:].strip()
        if remainder:
            sentences.append(remainder)
    return sentences


def deterministic_plan(scenario: str, style_guide: str) -> ScenePlan:
    sentences = _split_sentences(scenario)
    pieces: list[str] = []
    for sentence in sentences or [scenario.strip()]:
        pieces.extend(_split_long(sentence))
    scenes = [
        Scene(
            id=f"scene-{index:03d}",
            narration=text,
            visual_summary=text.rstrip(".!?。！？"),
            image_prompt=(
                f"{text.rstrip('.!?。！？')}의 핵심 의미를 한 장면으로 표현. "
                "명확한 단일 피사체, 시네마틱 에디토리얼 일러스트레이션, "
                "16:9 가로 구도, 하단 자막 안전 영역, 이미지 안에 글자나 로고 없음.\n"
                f"스타일 지침:\n{style_guide}"
            ),
        )
        for index, text in enumerate(pieces[:300], 1)
    ]
    return ScenePlan(title=scenes[0].visual_summary[:80] or "슬라이드 영상", scenes=scenes)


def _normalized(text: str) -> str:
    return re.sub(r"\s+", "", text)


def validate_plan(plan: ScenePlan, scenario: str) -> None:
    if not plan.scenes or len(plan.scenes) > 300:
        raise ValueError("scene count must be between 1 and 300")
    ids = [scene.id for scene in plan.scenes]
    expected = [f"scene-{index:03d}" for index in range(1, len(ids) + 1)]
    if ids != expected:
        raise ValueError("scene ids must be continuous")
    narration = "".join(scene.narration for scene in plan.scenes)
    if _normalized(narration) != _normalized(scenario):
        raise ValueError("scene narration must preserve the entire original script")
    if any(not scene.image_prompt.strip() for scene in plan.scenes):
        raise ValueError("every scene requires an image prompt")
    scene_ids = set(ids)
    asset_ids = [asset.asset_id for asset in plan.continuity_assets]
    if len(asset_ids) != len(set(asset_ids)):
        raise ValueError("continuity asset ids must be unique")
    known_assets = set(asset_ids)
    for asset in plan.continuity_assets:
        if not set(asset.appearing_scene_ids).issubset(scene_ids):
            raise ValueError(f"continuity asset {asset.asset_id} references an unknown scene")
        if len(asset.appearing_scene_ids) != len(set(asset.appearing_scene_ids)):
            raise ValueError(f"continuity asset {asset.asset_id} repeats an appearing scene")
    for scene in plan.scenes:
        if len(scene.present_asset_ids) != len(set(scene.present_asset_ids)):
            raise ValueError(f"scene {scene.id} repeats a present asset")
        if len(scene.reference_asset_ids) != len(set(scene.reference_asset_ids)):
            raise ValueError(f"scene {scene.id} repeats a reference asset")
        if len(scene.reference_asset_ids) > 8:
            raise ValueError(f"scene {scene.id} exceeds the default reference asset limit")
        if not set(scene.present_asset_ids).issubset(known_assets):
            raise ValueError(f"scene {scene.id} references an unknown present asset")
        if not set(scene.reference_asset_ids).issubset(set(scene.present_asset_ids)):
            raise ValueError(f"scene {scene.id} references an asset that is not present")


def reconcile_plan(plan: ScenePlan, scenario: str, style_guide: str) -> tuple[ScenePlan, dict[str, int]]:
    """Keep the script deterministic while reusing Codex's visual direction.

    A model may paraphrase narration or omit a scene even with a strict JSON
    schema. The runner, not the model, owns scene IDs and the spoken source
    text. Missing visual directions fall back to the deterministic planner.
    """
    baseline = deterministic_plan(scenario, style_guide)
    candidates = {scene.id: scene for scene in plan.scenes}
    baseline_ids = {scene.id for scene in baseline.scenes}
    surviving_assets: list[ContinuityAsset] = []
    dropped_assets = 0
    trimmed_appearances = 0
    for asset in plan.continuity_assets:
        appearances = list(dict.fromkeys(scene_id for scene_id in asset.appearing_scene_ids if scene_id in baseline_ids))
        trimmed_appearances += len(asset.appearing_scene_ids) - len(appearances)
        if len(appearances) < 2:
            dropped_assets += 1
            continue
        surviving_assets.append(asset.model_copy(update={"appearing_scene_ids": appearances}))
    surviving_ids = {asset.asset_id for asset in surviving_assets}
    scenes: list[Scene] = []
    missing_scenes = 0
    restored_narrations = 0
    for expected in baseline.scenes:
        candidate = candidates.get(expected.id)
        if candidate is None:
            missing_scenes += 1
            scenes.append(expected)
            continue
        if _normalized(candidate.narration) != _normalized(expected.narration):
            restored_narrations += 1
        scenes.append(Scene(
            id=expected.id,
            narration=expected.narration,
            visual_summary=candidate.visual_summary.strip() or expected.visual_summary,
            image_prompt=candidate.image_prompt.strip() or expected.image_prompt,
            present_asset_ids=[asset_id for asset_id in candidate.present_asset_ids if asset_id in surviving_ids],
            reference_asset_ids=[asset_id for asset_id in candidate.reference_asset_ids if asset_id in surviving_ids],
        ))
    reconciled = ScenePlan(
        title=plan.title.strip() or baseline.title,
        continuity_assets=surviving_assets,
        rejected_borderline_candidates=plan.rejected_borderline_candidates[:10],
        scenes=scenes,
    )
    validate_plan(reconciled, scenario)
    return reconciled, {
        "missing_scenes": missing_scenes,
        "extra_scenes": max(0, len(plan.scenes) - len(baseline.scenes)),
        "restored_narrations": restored_narrations,
        "dropped_assets_after_scene_reconcile": dropped_assets,
        "trimmed_asset_appearances": trimmed_appearances,
    }


def _compose_prompt(prompts: dict[str, str], scenario: str, continuity_enabled: bool) -> str:
    sections: list[str] = []
    names = [
        "director/system.md",
        "director/analyze-script.md",
        "storyboard/system.md",
        "storyboard/split-scenes.md",
    ]
    names.extend((
        "continuity/select-assets.md",
        "continuity/assign-scene-references.md",
    ) if continuity_enabled else ("continuity/disabled.md",))
    names.extend((
        "image/system.md",
        "image/build-image-prompt.md",
        "image/style-guide.md",
    ))
    for name in names:
        value = prompts[name].replace("{{SCENARIO}}", scenario)
        value = value.replace("{{SCENE_JSON}}", "각 장면의 narration과 visual_summary")
        sections.append(f"\n--- {name} ---\n{value}")
    return "\n".join(sections)


def compile_source_units(scenario: str) -> list[SourceUnit]:
    """Create stable, contiguous slices whose concatenation is the exact input."""
    boundaries: list[int] = []
    start = 0
    for index, char in enumerate(scenario):
        fractional_end = index + 1
        while fractional_end < len(scenario) and scenario[fractional_end].isdigit():
            fractional_end += 1
        decimal_point = (
            char == "." and index > 0 and index + 1 < len(scenario)
            and scenario[index - 1].isdigit() and scenario[index + 1].isdigit()
            and (fractional_end == len(scenario) or scenario[fractional_end] != ".")
        )
        boundary = (char in ".!?。！？\r\n" and not decimal_point) or (char in ",，" and index + 1 - start >= 90)
        if not boundary:
            continue
        end = index + 1
        while end < len(scenario) and scenario[end].isspace():
            end += 1
        if end > start:
            boundaries.append(end)
            start = end
    if start < len(scenario):
        boundaries.append(len(scenario))
    if len(boundaries) > 300:
        count = len(boundaries)
        boundaries = [boundaries[((index * count + 299) // 300) - 1] for index in range(1, 301)]
    units: list[SourceUnit] = []
    start = 0
    for end in boundaries:
        if end > start:
            units.append(SourceUnit(
                id=f"unit-{len(units) + 1:03d}", start_offset=start,
                end_offset=end, text=scenario[start:end],
            ))
            start = end
    if not units:
        units.append(SourceUnit(id="unit-001", start_offset=0, end_offset=len(scenario), text=scenario))
    return units


def compile_storyboard_units(scenario: str, visual_cues: list[dict[str, str]]) -> list[SourceUnit]:
    """Preserve each explicitly timed narration block as one contiguous source unit."""
    spoken = [str(cue.get("narration") or "").strip() for cue in visual_cues]
    if not spoken or any(not line for line in spoken) or scenario != "\n".join(spoken):
        raise ValueError("Storyboard narration does not match the production script")
    units: list[SourceUnit] = []
    start = 0
    for index, line in enumerate(spoken):
        end = start + len(line) + (1 if index < len(spoken) - 1 else 0)
        units.append(SourceUnit(id=f"unit-{index + 1:03d}", start_offset=start,
                                end_offset=end, text=scenario[start:end]))
        start = end
    return units


def _default_style_bible(image_style: str) -> StyleBible:
    descriptions = {
        "editorial_illustration": "정교한 에디토리얼 일러스트레이션, 절제된 상징과 명료한 서사",
        "cinematic_realism": "영화 스틸 같은 사실적 인물·공간·조명과 자연스러운 렌즈 깊이",
        "graphic_explainer": "정보 구조와 인과를 도형·공간 관계로 명료하게 설명하는 그래픽",
        "cute_character": "Original rounded 2D character, readable silhouette, consistent ink contour, flat pastel colors with distinct coral and jade accents, restrained paper grain.",
        "fantasy_anime": "Original Japanese fantasy animation aesthetic: hand-painted backgrounds, crisp cel-shaded characters, controlled atmospheric depth, no photorealism or imitation of named franchises.",
        "animation_3d": "Original dimensional animated-film stills: sculpted silhouettes, readable facial planes, tactile materials, soft area lighting, coherent modeled environments; not live action.",
        "disney_animation": "Disney-inspired hand-drawn animated storytelling with original characters, expressive silhouettes, controlled linework, painted backgrounds and legible emotional posing; no existing franchise characters or logos.",
        "dystopian": "Dystopian cinematic realism: oppressive spatial scale, worn infrastructure, restrained color with a story-driven accent, practical directional lighting and grounded human vulnerability; readable subjects, not arbitrary darkness.",
    }
    return StyleBible(
        preset_id=image_style, medium_and_rendering=descriptions[image_style],
        palette=["일관된 제한 팔레트", "강조색 한 가지"], lighting="영상 전체에서 방향성과 대비를 고정",
        camera_and_depth="16:9 프레임, 장면 목적에 맞는 시선과 깊이",
        texture_and_detail="주요 피사체는 선명하고 배경 디테일은 절제",
        character_rendering="동일 인물의 얼굴, 헤어, 의상 식별 특징 유지",
        environment_rendering="공간의 시대, 재질, 날씨 규칙을 영상 전체에서 유지",
        composition_rules=["자막 안전 영역 확보", "핵심 피사체와 시선 흐름을 명확히"],
        forbidden_variations=["장면별 매체 변경", "이미지 안의 글자나 로고", "무관한 장식"],
    )


def deterministic_plan(scenario: str, style_guide: str, image_style: str = "editorial_illustration") -> ScenePlan:
    units = compile_source_units(scenario)
    scenes: list[Scene] = []
    sequences: list[NarrativeSequence] = []
    groups: list[SceneGroup] = []
    for sequence_index, first in enumerate(range(0, len(units), 4), 1):
        selected = units[first:first + 4]
        sequence_id = f"sequence-{sequence_index:03d}"
        group_id = f"group-{sequence_index:03d}"
        scene_ids = [f"scene-{first + offset + 1:03d}" for offset in range(len(selected))]
        keycut_id = scene_ids[0]
        sequences.append(NarrativeSequence(
            id=sequence_id, source_unit_ids=[unit.id for unit in selected], role_in_story="development",
            purpose="대본의 다음 의미 단위를 전개한다", viewer_state_before="이전 내용을 이해한 상태",
            viewer_state_after="해당 의미 단위를 이해한 상태", scene_group_ids=[group_id], keycut_scene_id=keycut_id,
        ))
        groups.append(SceneGroup(
            id=group_id, sequence_id=sequence_id, source_unit_ids=[unit.id for unit in selected],
            role_in_sequence="explain", purpose="sequence의 핵심 내용을 시각적으로 전개한다",
            setup="앞선 맥락", payoff="다음 의미 단위로 연결", scene_ids=scene_ids,
        ))
        for offset, unit in enumerate(selected):
            scene_id = scene_ids[offset]
            is_keycut = offset == 0
            summary = unit.text.strip().rstrip(".!?。！？") or unit.text.strip()
            scenes.append(Scene(
                id=scene_id, sequence_id=sequence_id, scene_group_id=group_id,
                source_unit_ids=[unit.id], role_in_group="핵심 의미를 시각화",
                purpose="원문의 의미를 빠짐없이 전달", viewer_takeaway=summary,
                cut_role="keycut" if is_keycut else "derived",
                parent_keycut_scene_id=None if is_keycut else keycut_id,
                keycut_dna=KeycutDNA(
                    story_meaning=summary, composition_anchor="핵심 피사체와 맥락을 한 프레임에 배치",
                    palette_anchor=["Style Bible 팔레트"], lighting_anchor="Style Bible 조명",
                    symbol_anchor=[], must_inherit=["팔레트", "조명", "공간 문법"],
                    must_not_copy=["동일 포즈", "동일 배경", "동일 프레이밍"],
                ) if is_keycut else None,
                narration=unit.text, visual_summary=summary,
                image_prompt=f"{summary}. 16:9, 자막 안전 영역, 이미지 안 글자와 로고 없음.\n{style_guide}",
                scene_function="establish" if is_keycut else "explain",
                layout={"mode": "focus", "focal_order": ["subject", "evidence", "caption"], "safe_area": "title_top_caption_bottom"},
                object_states=[
                    {"object_id": "scene-image", "role": "subject", "initial": "context", "final": "emphasized"},
                    {"object_id": "evidence-card", "role": "evidence", "initial": "hidden", "final": "visible"},
                ],
                motion=[
                    {"object_id": "scene-image", "kind": "camera_push", "phases": ["read", "move", "settle"]},
                    {"object_id": "evidence-card", "kind": "reveal", "phases": ["anticipate", "reveal", "hold"]},
                ],
                transition="cut" if is_keycut else "crossfade",
                rhythm="read_then_move_then_hold",
                renderer_requirements={"preferred": "hyperframes", "capabilities": ["image", "text", "multi_phase_timeline", "settle"]},
            ))
    return ScenePlan(
        title=scenes[0].visual_summary[:80] or "슬라이드 영상", core_question="이 대본이 전달하는 핵심은 무엇인가?",
        thesis="원문의 의미를 순서대로 명료하게 전달한다", audience_start_state="내용을 접하기 전",
        audience_end_state="핵심 메시지를 이해한 상태", master_keycut_scene_id=sequences[0].keycut_scene_id,
        style_bible=_default_style_bible(image_style), source_units=units, sequences=sequences,
        scene_groups=groups, scenes=scenes,
    )


def compile_narration(plan: ScenePlan, scenario: str, source_units: list[SourceUnit]) -> ScenePlan:
    by_id = {unit.id: unit for unit in source_units}
    seen: list[str] = []
    compiled: list[Scene] = []
    for scene in plan.scenes:
        try:
            narration = "".join(by_id[unit_id].text for unit_id in scene.source_unit_ids)
        except KeyError as error:
            raise ValueError(f"scene {scene.id} uses unknown source unit {error.args[0]}") from error
        seen.extend(scene.source_unit_ids)
        compiled.append(scene.model_copy(update={"narration": narration}))
    if seen != [unit.id for unit in source_units]:
        raise ValueError("source units must be used exactly once in original order")
    return plan.model_copy(update={"source_units": source_units, "scenes": compiled})


def validate_plan(plan: ScenePlan, scenario: str) -> None:
    if not plan.scenes or len(plan.scenes) > 300:
        raise ValueError("scene count must be between 1 and 300")
    scene_ids = [scene.id for scene in plan.scenes]
    if scene_ids != [f"scene-{index:03d}" for index in range(1, len(scene_ids) + 1)]:
        raise ValueError("scene ids must be continuous")
    if "".join(unit.text for unit in plan.source_units) != scenario:
        raise ValueError("source units must preserve the exact original script")
    for unit in plan.source_units:
        if scenario[unit.start_offset:unit.end_offset] != unit.text:
            raise ValueError(f"source unit {unit.id} offset does not match the original script")
    if "".join(scene.narration for scene in plan.scenes) != scenario:
        raise ValueError("scene narration must preserve the exact original script")
    if any(not scene.image_prompt.strip() for scene in plan.scenes):
        raise ValueError("every scene requires an image prompt")
    asset_ids = [asset.asset_id for asset in plan.continuity_assets]
    if len(asset_ids) != len(set(asset_ids)):
        raise ValueError("continuity asset ids must be unique")
    known_assets = set(asset_ids)
    for asset in plan.continuity_assets:
        if not set(asset.appearing_scene_ids).issubset(set(scene_ids)):
            raise ValueError(f"continuity asset {asset.asset_id} references an unknown scene")
    for scene in plan.scenes:
        if len(scene.reference_asset_ids) != len(set(scene.reference_asset_ids)):
            raise ValueError(f"scene {scene.id} repeats a reference asset")
        if len(scene.reference_asset_ids) > (8 if scene.cut_role == "keycut" else 7):
            raise ValueError(f"scene {scene.id} exceeds its continuity reference limit")
        if not set(scene.present_asset_ids).issubset(known_assets):
            raise ValueError(f"scene {scene.id} references an unknown present asset")
        if not set(scene.reference_asset_ids).issubset(set(scene.present_asset_ids)):
            raise ValueError(f"scene {scene.id} references an asset that is not present")
    sequence_ids = [sequence.id for sequence in plan.sequences]
    if sequence_ids != [f"sequence-{index:03d}" for index in range(1, len(sequence_ids) + 1)]:
        raise ValueError("sequence ids must be continuous")
    group_ids = [group.id for group in plan.scene_groups]
    if group_ids != [f"group-{index:03d}" for index in range(1, len(group_ids) + 1)]:
        raise ValueError("scene group ids must be continuous")
    group_by_id = {group.id: group for group in plan.scene_groups}
    sequence_by_id = {sequence.id: sequence for sequence in plan.sequences}
    keycuts: set[str] = set()
    for sequence in plan.sequences:
        sequence_scenes = [scene for scene in plan.scenes if scene.sequence_id == sequence.id]
        if [scene.id for scene in sequence_scenes if scene.cut_role == "keycut"] != [sequence.keycut_scene_id]:
            raise ValueError(f"sequence {sequence.id} must have exactly one declared keycut")
        if [unit for scene in sequence_scenes for unit in scene.source_unit_ids] != sequence.source_unit_ids:
            raise ValueError(f"sequence {sequence.id} source units do not match its scenes")
        if sequence.scene_group_ids != [group.id for group in plan.scene_groups if group.sequence_id == sequence.id]:
            raise ValueError(f"sequence {sequence.id} scene groups do not match")
        keycuts.add(sequence.keycut_scene_id)
    if plan.master_keycut_scene_id not in keycuts:
        raise ValueError("master keycut must be one of the sequence keycuts")
    for group in plan.scene_groups:
        members = [scene for scene in plan.scenes if scene.scene_group_id == group.id]
        if not members or group.sequence_id not in sequence_by_id or [scene.id for scene in members] != group.scene_ids:
            raise ValueError(f"group {group.id} hierarchy does not match")
        if [unit for scene in members for unit in scene.source_unit_ids] != group.source_unit_ids:
            raise ValueError(f"group {group.id} source units do not match")
    for scene in plan.scenes:
        group = group_by_id.get(scene.scene_group_id)
        if not group or group.sequence_id != scene.sequence_id:
            raise ValueError(f"scene {scene.id} does not belong to its declared hierarchy")
        expected_parent = sequence_by_id[scene.sequence_id].keycut_scene_id
        if scene.cut_role == "keycut":
            if scene.parent_keycut_scene_id is not None or scene.keycut_dna is None:
                raise ValueError(f"keycut {scene.id} has invalid parent or missing DNA")
        elif scene.parent_keycut_scene_id != expected_parent:
            raise ValueError(f"scene {scene.id} must reference its sequence keycut")


def _compose_prompt(
    prompts: dict[str, str],
    scenario: str,
    source_units: list[SourceUnit],
    continuity_enabled: bool,
    image_style: str,
    repair_feedback: str | None = None,
    director_learning_context: str = "",
    director_research_context: str = "",
    harness_planning_contract: dict[str, Any] | None = None,
    visual_cues: list[dict[str, str]] | None = None,
    local_graphic: bool = False,
) -> str:
    names = [
        "director/system.md", "narrative/story-intent.md", "narrative/analyze-sequences.md",
        "narrative/analyze-scene-groups.md", "narrative/analyze-scenes.md",
        "keycut/select-keycuts.md", "style/common.md", f"style/presets/{image_style.replace('_', '-')}.md",
    ]
    names.extend(("continuity/select-assets.md", "continuity/assign-scene-references.md") if continuity_enabled else ("continuity/disabled.md",))
    names.extend(("image/system.md", "image/build-image-prompt.md", "image/style-guide.md"))
    source_json = json.dumps([unit.model_dump() for unit in source_units], ensure_ascii=False, indent=2)
    sections: list[str] = []
    for name in names:
        value = prompts[name].replace("{{SCENARIO}}", scenario).replace("{{SOURCE_UNITS}}", source_json)
        value = value.replace("{{IMAGE_STYLE}}", image_style).replace("{{SCENE_JSON}}", "source_unit_ids와 시각 설계")
        sections.append(f"\n--- {name} ---\n{value}")
    sections.append(
        "\n--- runtime/semantic-contract.md ---\n"
        f"- 입력 source unit은 정확히 {len(source_units)}개다. "
        "모든 scene의 source_unit_count 합은 반드시 이 개수와 같아야 한다.\n"
        "- master_keycut_sequence_number는 실제 sequences 개수 안의 1부터 시작하는 번호다.\n"
        "- keycut_scene_number는 해당 sequence에 실제로 작성한 scene 개수 안의 1부터 시작하는 번호다.\n"
        "- continuity asset의 scene number는 전체로 실제 작성한 scene 개수 안에서만 선택한다.\n"
        "- motion.object_id는 같은 scene의 object_states.object_id 중 하나여야 한다. "
        "단, 전체 카메라 또는 정지 연출은 object_id=scene을 쓸 수 있고 "
        "kind은 camera_push, camera_pull, hold 중 하나여야 한다.\n"
        "- phases에는 자연어 동작 단계만 적고 transition, rhythm, renderer_requirements 같은 "
        "스키마 필드명을 넣지 않는다.\n"
        "- 범위를 벗어난 번호나 누락된 대상을 런타임이 보정하도록 의도적으로 남겨두지 않는다.\n"
    )
    if repair_feedback:
        sections.append(
            "\n--- runtime/director-repair.md ---\n"
            "이전 감독안은 결정론적 컴파일러의 구조 검수에서 탈락했다. "
            "이전 장면 수나 배분을 답습하지 말고 대본 전체를 다시 설계한다.\n"
            f"{repair_feedback}\n"
            "모든 source unit을 정확히 한 번씩, 원래 순서대로 장면에 배정한다. "
            "scene별 source_unit_count의 합은 입력 source unit 총수와 정확히 같아야 한다.\n"
        )
    if director_learning_context:
        sections.append(director_learning_context)
    if director_research_context:
        sections.append(director_research_context)
    if harness_planning_contract:
        sections.append(
            "\n--- runtime/harness-planning-contract.json ---\n"
            "장면의 의미는 감독이 결정한다. 다음 계약은 선택된 렌더러의 실제 지원 범위와 자산 준비 요건이다. "
            "지원하지 않는 행동을 다른 효과로 조용히 대체하지 말고, 필요한 자산·능력을 계획에 드러낸다. "
            "자산 제작 계획이나 모델의 승인 문구는 사람 검수 통과가 아니다.\n"
            + json.dumps(harness_planning_contract, ensure_ascii=False, sort_keys=True)
        )
    if visual_cues:
        sections.append(
            "\n--- runtime/storyboard-visual-cues.json ---\n"
            "These user-supplied time ranges and visual directions are design references only. "
            "The scenario and source units above are the complete spoken narration; never place cue headings, "
            "screen directions, or timing markup in narration, subtitles, or on-screen labels. "
            "Use original illustrative examples instead of unlicensed film frames. "
            "Match each visual direction to its narration by meaning, adjusting timing to measured speech.\n"
            + json.dumps(visual_cues, ensure_ascii=False)
        )
        sections.append(
            "\n--- runtime/storyboard-scene-allocation.md ---\n"
            f"This timed storyboard has exactly {len(visual_cues)} narration units. "
            "Create exactly one scene for each unit in original order, and set every "
            "scene.source_unit_count to 1. Within a scene, use object motion phases for "
            "the user's requested visual changes; do not invent additional spoken lines."
        )
    if local_graphic:
        sections.append(
            "\n--- runtime/local-graphic-vocabulary.md ---\n"
            "This renderer draws editable local objects, not AI images or arbitrary film clips. "
            "Choose only objects that explain this script, never reuse a previous video's story. "
            "Supported geography and distance objects: ocean, land, location-marker, "
            "space-station, orbit, vertical-distance, distance-link, people. "
            "Supported diagram objects: travel-path, attention-dots, speech-wave, warning-mark, "
            "uncertainty-cloud, lock-pin. For film composition ONLY, these objects are available: "
            "frame-set (three original example frames), frame (single film frame), "
            "balanced-panel, offset-panel, tilting-frame, eye-symbol, eye-line, "
            "frame-grid, upper-third-guide, lock-pin, figure-frame, travel-path, "
            "attention-dots, speech-wave, warning-mark, phone-frame, uncertainty-cloud. "
            "Give each object a descriptive role, initial and final state, and matching "
            "motion object_id. Narrative scenes must mark one object's role as subject; "
            "keep that subject's ID stable across scenes. Use at most eight objects per scene. "
            "Object motion kinds are reveal, path_follow, state_change, group_split, pulse, hold. "
            "Do not request facial acting, arbitrary illustrations or unsupported assets. "
            "Each scene needs at least one executable object motion and "
            "a short visual label. Use original diagrammatic reconstruction, not copyrighted frames."
        )
    return "\n".join(sections)


def _repair_feedback(repairs: dict[str, Any], proposal: dict[str, Any], source_unit_count: int) -> str:
    sequences = proposal.get("sequences") if isinstance(proposal, dict) else None
    requested_counts: list[Any] = []
    keycut_diagnostics: list[str] = []
    for sequence_index, sequence in enumerate(sequences or [], 1):
        if not isinstance(sequence, dict):
            continue
        sequence_scenes = [
            scene
            for group in sequence.get("scene_groups") or []
            if isinstance(group, dict)
            for scene in group.get("scenes") or []
            if isinstance(scene, dict)
        ]
        requested_counts.extend(scene.get("source_unit_count") for scene in sequence_scenes)
        keycut_diagnostics.append(
            f"sequence {sequence_index}: scene {len(sequence_scenes)}개, "
            f"keycut_scene_number={sequence.get('keycut_scene_number')}"
        )
    requested_total = sum(value for value in requested_counts if type(value) is int)
    return (
        f"검수 결과: {', '.join(structural_repair_findings(repairs))}. "
        f"입력 source unit은 {source_unit_count}개인데 이전 장면 배분은 "
        f"{requested_counts} (합계 {requested_total})였다. "
        f"핵심 컷 진단은 [{'; '.join(keycut_diagnostics)}], "
        f"master_keycut_sequence_number={proposal.get('master_keycut_sequence_number')}이다. "
        "모든 검수 항목을 각각 수정한다. keycut 번호는 해당 sequence의 실제 scene 개수 안에 두고, "
        "master keycut 번호는 실제 sequence 개수 안에 둔다. 의미가 다른 후반 내용을 마지막 장면에 "
        "몰아넣지 말고, 필요한 장면을 추가해 각각 시각적으로 설계한다."
    )


async def plan_with_codex(
    scenario: str,
    prompts: dict[str, str],
    settings: Settings,
    tracker: Tracker,
    work_dir: Path,
    *,
    codex_model: str | None = None,
    codex_reasoning_effort: str | None = None,
    codex_fast_mode: bool | None = None,
    continuity_enabled: bool = False,
    image_style: str = "editorial_illustration",
    learning_selection: dict[str, Any] | None = None,
    research_brief: dict[str, Any] | None = None,
    harness_planning_contract: dict[str, Any] | None = None,
    source_units_override: list[SourceUnit] | None = None,
    semantic_analysis_result: Any | None = None,
    selected_concept: Any | None = None,
    visual_cues: list[dict[str, str]] | None = None,
    local_graphic: bool = False,
    _repair_limit: int = 2,
    _previous_failures: frozenset[str] | None = None,
    _repair_pass: int = 0,
    _repair_note: str | None = None,
) -> ScenePlan:
    from .actor_scene import scene_output_schema, validate_actor_proposal
    from .harness_sdk.direction import direction_enabled, direction_output_schema, evaluate_direction
    from .harness_sdk.hybrid import hybrid_enabled, hybrid_output_schema, evaluate_hybrid
    from .harness_sdk.semantic_beats import semantic_enabled
    from .harness_sdk.concept_design import concept_enabled, bind_selected_concept
    from .harness_sdk.locked_scene_design import locked_scene_enabled, locked_scene_schema, expand_locked_scene_proposal
    locked_design = locked_scene_enabled(harness_planning_contract)
    if semantic_enabled(harness_planning_contract) and semantic_analysis_result is None:
        raise ValueError("semantic_analysis_must_precede_scene_design")
    if concept_enabled(harness_planning_contract) and selected_concept is None:
        raise ValueError("independent_concept_selection_must_precede_scene_design")
    from .semantic_gate import require_acceptance
    semantic_acceptance = require_acceptance(work_dir, semantic_analysis_result, scenario, harness_planning_contract,
                                            codex_model or settings.codex_model)
    from .harness_sdk.preproduction import preproduction_enabled
    preproduction_brief = None
    if preproduction_enabled(harness_planning_contract):
        from .preproduction_brief import compile_preproduction_brief, require_matching_concept_brief
        preproduction_brief = compile_preproduction_brief(semantic_analysis_result, harness_planning_contract)
        if selected_concept is not None:
            selection_path = work_dir / "concept-selection.json"
            if not selection_path.exists():
                raise ValueError("preproduction_concept_record_missing")
            selection = json.loads(selection_path.read_text(encoding="utf-8"))
            require_matching_concept_brief(selection, preproduction_brief)
        brief_path = work_dir / "preproduction-brief.json"
        if brief_path.exists():
            if json.loads(brief_path.read_text(encoding="utf-8")) != preproduction_brief:
                raise ValueError("preproduction_brief_changed_during_repair")
        else:
            brief_path.write_text(json.dumps(preproduction_brief, ensure_ascii=False, indent=2), encoding="utf-8")
            tracker.add_asset(brief_path, "preproduction_brief")

    schema = scene_output_schema(
        json.loads((settings.schemas_dir / "scene-plan.schema.json").read_text(encoding="utf-8")),
        harness_planning_contract,
    )
    schema = direction_output_schema(schema, harness_planning_contract)
    schema = hybrid_output_schema(schema, harness_planning_contract)
    stream_guard = None
    if semantic_enabled(harness_planning_contract):
        from .planning_stream_guard import bounded_phase_schema, PlanningStreamGuard
        schema = bounded_phase_schema(schema)
        stream_guard = PlanningStreamGuard()
    if locked_design:
        schema = locked_scene_schema(schema, semantic_analysis_result)
    suffix = "" if _repair_pass == 0 else f".repair-{_repair_pass}"
    output = work_dir / f"scene-plan.codex{suffix}.json"
    source_units = source_units_override if source_units_override is not None else compile_source_units(scenario)
    prompt = _compose_prompt(
        prompts,
        scenario,
        source_units,
        continuity_enabled,
        image_style,
        repair_feedback=_repair_note,
        director_learning_context=learning_prompt(learning_selection) if learning_selection else "",
        director_research_context=research_prompt(research_brief) if research_brief else "",
        harness_planning_contract=harness_planning_contract,
        visual_cues=visual_cues,
        local_graphic=local_graphic,
    )
    if semantic_analysis_result is not None:
        prompt += ("\n--- runtime/accepted-meaning-analysis.json ---\n"
            "These exact semantic spans are the source units. Design one scene per beat, source_unit_count=1. "
            "Preserve the analyzed purpose, route, grammar, source claims and narration. Do not merge distinct viewer changes. "
            "Typed context/sequence relations are not event causes. Cross-scene cause_scene_number may only refer to an event_cause or motivation relation. "
            "A character story without a supplied dilemma needs no invented choices or consequences. "
            "Analysis is structurally checked, not independent factual or aesthetic approval.\n"
            "Motion phases are short labels (at most 240 characters each), not prose or repeated instructions.\n"
            + semantic_analysis_result.model_dump_json())
    if preproduction_brief is not None:
        prompt += ("\n--- runtime/preproduction-brief.json ---\n"
            "For each beat, stage its required visual events with the registered grammar. "
            "Respect its implementation limit and source boundary. A title alone is not an explanation. "
            "The brief is a structural production constraint, not independent meaning or image approval.\n"
            + json.dumps(preproduction_brief, ensure_ascii=False))
    if selected_concept is not None:
        prompt += ("\n--- runtime/selected-film-concept.json ---\n"
            "This concept passed independent pre-render comparison, not rendered quality approval. "
            "Copy its design exactly into every layout.hybrid.design. Use its route treatments and shared motifs in shots. "
            "Do not invent or substitute colors, text sizes, facts, events or camera capabilities. "
            "The generic style_bible must agree with this selected concept, not override it.\n" + selected_concept.model_dump_json())
    if locked_design:
        prompt += ("\n--- runtime/locked-scene-design-0.1 ---\n"
            "This wire format supersedes earlier instructions to emit full scenes or copy design tokens. "
            "Emit beat_designs with every exact beat-001, beat-002, etc. key required by the schema. "
            "Sequences/groups list beat_ids exactly once in source order, not embedded scenes. "
            "Core binds source_unit_count=1, route, grammar, source, transition=cut and selected design; OMIT those owned fields. "
            "Do not generate authored_design or visual_labels. Local diagrams/sources have Core-owned hold camera. "
            "Only diagram beats contain layout.hybrid with diagram and, for transport, optional composition. "
            "Cumulative nodes are increments, common unit/scale, NO edges; comparison also has NO edges. "
            "A simple intention or resolve is setup/action, not a choice with invented alternatives. "
            "A single still depicts one legible instant, not simultaneous stages of an action. "
            "Core ownership is not permission to omit objects, quantities, timing or shot design.\n")
    model = codex_model or settings.codex_model
    effort = codex_reasoning_effort or settings.codex_reasoning_effort
    fast_mode = settings.codex_fast_mode if codex_fast_mode is None else codex_fast_mode
    started_at = _now()
    loop = asyncio.get_running_loop()
    started = loop.time()
    request = {
        "model": model,
        "reasoning": {"effort": effort},
        "stream": True,
        "stream_options": {"include_obfuscation": False},
        "input": [{
            "role": "user",
            "content": [{"type": "input_text", "text": prompt}],
        }],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "scene_plan",
                "strict": True,
                "schema": schema,
            },
        },
    }
    # The subscription OAuth bridge rejects "auto" and the newer "fast" alias.
    # OpenAI documents "priority" as an equivalent Fast-mode request value, so
    # use that compatible spelling only when Fast mode is enabled.
    if fast_mode:
        request["service_tier"] = "priority"
    transcript = CodexTranscript(
        work_dir,
        tracker.attempt if _repair_pass == 0 else f"{tracker.attempt}-repair-{_repair_pass}",
        request,
        model=model,
        effort=effort,
        fast_mode=fast_mode,
    )
    usage_recorded = False
    try:
        completed: dict[str, Any] | None = None
        output_parts: list[str] = []
        timeout = httpx.Timeout(
            settings.codex_read_timeout_seconds,
            connect=settings.codex_connect_timeout_seconds,
            write=30.0,
            pool=settings.codex_connect_timeout_seconds,
        )
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream(
                "POST",
                f"{settings.subscription_base_url}/v1/responses",
                json=request,
            ) as response:
                if response.is_error:
                    body = (await response.aread()).decode("utf-8", errors="replace")
                    raise RuntimeError(
                        f"Codex subscription scene planning failed ({response.status_code}): "
                        f"{body[-1000:]}"
                    )
                async for event_name, raw_data in _iter_sse(response):
                    if raw_data == "[DONE]":
                        continue
                    try:
                        payload = json.loads(raw_data)
                    except json.JSONDecodeError:
                        transcript.record(event_name, raw_data, {"type": event_name or "unparsed"})
                        continue
                    if not isinstance(payload, dict):
                        continue
                    event_type = transcript.record(event_name, raw_data, payload)
                    if event_type == "response.output_text.delta":
                        delta = payload.get("delta")
                        if isinstance(delta, str):
                            output_parts.append(delta)
                            transcript.append_output(delta)
                            if stream_guard is not None:
                                stream_guard.feed(delta)
                    elif event_type == "response.completed":
                        value = payload.get("response")
                        if isinstance(value, dict):
                            completed = value
                            transcript.complete(value)
                    elif event_type in {"response.failed", "response.incomplete", "error"}:
                        value = payload.get("response") if isinstance(payload.get("response"), dict) else payload
                        detail = value.get("error") or value.get("incomplete_details") or value.get("message") or event_type
                        raise RuntimeError(f"Codex streaming response failed: {detail}")

        if completed is None:
            raise RuntimeError("Codex streaming response ended without response.completed")
        text = _extract_output_text(completed) or "".join(output_parts)
        if not text:
            raise RuntimeError("Codex subscription response did not contain a scene plan")
        if stream_guard is not None:
            # Some providers deliver text only in the completion object.
            final_guard = PlanningStreamGuard()
            final_guard.feed(text)
        transcript.replace_output(text)
        output.write_text(text, encoding="utf-8")

        finished_at = _now()
        duration_ms = round((loop.time() - started) * 1000)
        usage = completed.get("usage") or {}
        input_details = usage.get("input_tokens_details") or {}
        output_details = usage.get("output_tokens_details") or {}
        tracker.add_usage(
            provider="codex_subscription",
            model=model,
            stage="scene_planning",
            started_at=started_at,
            finished_at=finished_at,
            duration_ms=duration_ms,
            input_tokens=usage.get("input_tokens", 0),
            cached_input_tokens=input_details.get("cached_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            reasoning_tokens=output_details.get("reasoning_tokens", 0),
            effort=effort,
            raw_usage={
                "response_id": completed.get("id"),
                "status": completed.get("status"),
                "total_tokens": usage.get("total_tokens"),
                "reasoning_effort": effort,
                "fast_mode_requested": fast_mode,
                "service_tier_requested": "priority" if fast_mode else "default",
                "service_tier_actual": completed.get("service_tier"),
                "streaming": True,
                "transcript": "work/codex/attempt-%s" % (
                    tracker.attempt if _repair_pass == 0 else f"{tracker.attempt}-repair-{_repair_pass}"
                ),
                "timing": transcript.summary(),
            },
        )
        usage_recorded = True
        proposal = json.loads(text)
        if locked_design:
            proposal = expand_locked_scene_proposal(proposal, semantic_analysis_result, selected_concept,
                hybrid_version=harness_planning_contract['hybrid_direction']['version'])
            expanded_path = work_dir / f"scene-plan.expanded{suffix}.json"
            expanded_path.write_text(json.dumps(proposal, ensure_ascii=False, indent=2), encoding="utf-8")
            tracker.add_asset(expanded_path, "locked_scene_expansion", repair_pass=_repair_pass)
        validate_actor_proposal(proposal, harness_planning_contract)
        plan, repairs = compile_scene_plan(
            proposal,
            scenario,
            source_units,
            continuity_enabled=continuity_enabled,
        )
        if plan.style_bible.preset_id != image_style:
            raise ValueError("style bible preset does not match the requested image style")
        validate_plan(plan, scenario)
        if not continuity_enabled:
            removed_assets = len(plan.continuity_assets)
            plan = plan.model_copy(update={
                "continuity_assets": [],
                "rejected_borderline_candidates": [],
                "scenes": [scene.model_copy(update={
                    "present_asset_ids": [],
                    "reference_asset_ids": [],
                }) for scene in plan.scenes],
            })
            validate_plan(plan, scenario)
            repairs["continuity_disabled_assets_removed"] = removed_assets
        tracker.usage[-1]["raw_usage"]["deterministic_repairs"] = repairs
        blocking_repairs = structural_repair_findings(repairs)
        direction_findings: list[str] = []
        from .harness_sdk.engine_mode import evaluate_engine_mode
        boundary_findings = evaluate_engine_mode(plan.scenes, harness_planning_contract)
        blocking_repairs += boundary_findings
        if direction_enabled(harness_planning_contract):
            review = evaluate_direction(plan.scenes, expected_version=harness_planning_contract["narrative_direction"]["version"])
            review_path = work_dir / f"direction-review{suffix}.json"
            review_path.write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8")
            tracker.add_asset(review_path, "direction_review", repair_pass=_repair_pass)
            direction_findings = list(review["findings"])
            blocking_repairs += direction_findings
        direction_findings += boundary_findings
        if semantic_analysis_result is not None:
            from .harness_sdk.semantic_beats import bind_and_check_beats, analysis_sha256
            from .semantic_review import digest
            semantic_findings = bind_and_check_beats(plan.scenes, semantic_analysis_result)
            if preproduction_brief is not None:
                from .preproduction_brief import scene_brief_findings
                semantic_findings += scene_brief_findings(plan.scenes, preproduction_brief)
            if semantic_acceptance:
                for scene in plan.scenes:
                    scene.layout["semantic_sufficiency"] = dict(semantic_acceptance)
            binding_path = work_dir / f"semantic-binding{suffix}.json"
            binding_path.write_text(json.dumps({"status": "REVISE" if semantic_findings else "STRUCTURAL_PASS",
                "findings": semantic_findings, "selections": [s.layout.get("semantic_beat") for s in plan.scenes],
                "analysis_sha256": analysis_sha256(semantic_analysis_result),
                "preproduction_brief_sha256": digest(preproduction_brief) if preproduction_brief is not None else None,
                "independent_review": semantic_acceptance,
                "human_approval": None, "not_evaluated": ["rendered_quality", "factual_truth", "audience_response"] if semantic_acceptance else ["independent_semantics", "rendered_quality"]}, ensure_ascii=False, indent=2), encoding="utf-8")
            tracker.add_asset(binding_path, "semantic_binding", repair_pass=_repair_pass)
            direction_findings += semantic_findings
            blocking_repairs += semantic_findings
        if hybrid_enabled(harness_planning_contract):
            hybrid_findings = evaluate_hybrid(plan.scenes,
                {item["id"] for item in (harness_planning_contract or {}).get("trusted_source_catalog", [])},
                {item["id"] for item in (harness_planning_contract or {}).get("trusted_illustration_catalog", [])},
                expected_version=harness_planning_contract["hybrid_direction"]["version"])
            if selected_concept is not None:
                hybrid_findings += bind_selected_concept(plan.scenes, selected_concept)
            hybrid_review_path = work_dir / f"hybrid-review{suffix}.json"
            hybrid_review_path.write_text(json.dumps({
                "status": "REVISE" if hybrid_findings else "CONTRACT_PASS",
                "findings": hybrid_findings, "human_approval": None,
                "grammar_library_sha256": (harness_planning_contract or {}).get("visual_grammar_library", {}).get("sha256"),
                "selections": [{"scene_id": s.id,
                    "route": (s.layout.get("hybrid") or {}).get("route"),
                    "grammar": ((s.layout.get("hybrid") or {}).get("diagram") or {}).get("grammar"),
                    "reason": (s.layout.get("hybrid") or {}).get("reason"),
                } for s in plan.scenes],
                "not_evaluated": ["factual_accuracy", "rendered_semantics", "emotion"],
            }, ensure_ascii=False, indent=2), encoding="utf-8")
            tracker.add_asset(hybrid_review_path, "hybrid_review", repair_pass=_repair_pass)
            direction_findings += hybrid_findings
            blocking_repairs += hybrid_findings
        failure_causes = frozenset(f.split(":", 1)[-1] for f in blocking_repairs)
        repeated_causes = failure_causes.intersection(_previous_failures or ())
        if semantic_analysis_result is not None and repeated_causes:
            stop_path = work_dir / f"planning-stop{suffix}.json"
            stop_path.write_text(json.dumps({
                "policy_version": "planning-repeat-stop-0.2",
                "status": "ENGINE_WORK_REQUIRED",
                "repair_pass": _repair_pass,
                "repeated_causes": sorted(repeated_causes),
                "findings": blocking_repairs,
                "human_approval": None,
            }, ensure_ascii=False, indent=2), encoding="utf-8")
            tracker.add_asset(stop_path, "planning_stop", repair_pass=_repair_pass)
            raise ValueError("Repeated planning failure requires engine work: " + ", ".join(sorted(repeated_causes)))
        if blocking_repairs and _repair_pass < _repair_limit:
            note = _repair_feedback(repairs, proposal, len(source_units))
            if direction_findings:
                note += "\nRepair shot intent while preserving narration and source order:\n" + "\n".join(direction_findings)
            next_repair_pass = _repair_pass + 1
            repair_request = {
                "repair_pass": next_repair_pass,
                "reason": "director_structural_repair",
                "findings": blocking_repairs,
                "feedback": note,
                "original_proposal": output.name,
            }
            (work_dir / f"director-repair-request-{next_repair_pass}.json").write_text(
                json.dumps(repair_request, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            return await plan_with_codex(
                scenario,
                prompts,
                settings,
                tracker,
                work_dir,
                codex_model=codex_model,
                codex_reasoning_effort=codex_reasoning_effort,
                codex_fast_mode=codex_fast_mode,
                continuity_enabled=continuity_enabled,
                image_style=image_style,
                learning_selection=learning_selection,
                research_brief=research_brief,
                harness_planning_contract=harness_planning_contract,
                source_units_override=source_units_override,
                semantic_analysis_result=semantic_analysis_result,
                selected_concept=selected_concept,
                visual_cues=visual_cues,
                local_graphic=local_graphic,
                _repair_limit=_repair_limit,
                _previous_failures=failure_causes,
                _repair_pass=next_repair_pass,
                _repair_note=note,
            )
        if direction_findings:
            raise ValueError("Narrative direction needs repair: " + ", ".join(direction_findings))
        from .visible_text_review import ensure_visible_text
        plan = await ensure_visible_text(plan, harness_planning_contract, settings, tracker, work_dir,
            generator_model=model, repair_budget=max(0, _repair_limit-_repair_pass), attempt=_repair_pass)
        return plan
    except Exception as error:
        mapped = error
        if isinstance(error, httpx.ReadTimeout):
            mapped = RuntimeError(
                f"장면 구성 응답 시간 초과: Codex 스트림에서 "
                f"{settings.codex_read_timeout_seconds:g}초 동안 새 데이터를 받지 못했습니다."
            )
        elif isinstance(error, (json.JSONDecodeError, ValueError)):
            mapped = RuntimeError(f"codex returned an invalid scene plan: {error}")
        if transcript.status not in {"completed", "succeeded"}:
            transcript.fail(mapped)
        if not usage_recorded:
            finished_at = _now()
            tracker.add_usage(
                provider="codex_subscription",
                model=model,
                stage="scene_planning",
                started_at=started_at,
                finished_at=finished_at,
                duration_ms=round((loop.time() - started) * 1000),
                effort=effort,
                raw_usage={
                    "status": "failed",
                    "tokens_unknown": True,
                    "reasoning_effort": effort,
                    "fast_mode_requested": fast_mode,
                    "service_tier_requested": "priority" if fast_mode else "default",
                    "service_tier_actual": transcript.actual_service_tier,
                    "streaming": True,
                    "transcript": "work/codex/attempt-%s" % (
                        tracker.attempt if _repair_pass == 0 else f"{tracker.attempt}-repair-{_repair_pass}"
                    ),
                    "timing": transcript.summary(),
                    "error": str(mapped)[:1000],
                },
            )
        if mapped is error:
            raise
        raise mapped from error
    finally:
        summary = transcript.summary()
        for path, asset_type in transcript.paths():
            if path.is_file():
                tracker.add_asset(
                    path,
                    asset_type,
                    provider="codex_subscription",
                    model=model,
                    effort=effort,
                    attempt=tracker.attempt,
                    transcript_status=summary["status"],
                )


async def create_plan(
    scenario: str,
    prompts: dict[str, str],
    settings: Settings,
    tracker: Tracker,
    work_dir: Path,
    *,
    codex_model: str | None = None,
    codex_reasoning_effort: str | None = None,
    codex_fast_mode: bool | None = None,
    continuity_enabled: bool = False,
    image_style: str = "editorial_illustration",
    genre_id: str | None = None,
    harness_id: str = "classic-slide",
    duration_profile: str = "episode_60",
    harness_planning_contract: dict[str, Any] | None = None,
    motion_style: dict[str, Any] | None = None,
    visual_cues: list[dict[str, str]] | None = None,
) -> ScenePlan:
    from .genre_profiles import bind_plan, planning_instruction
    from .harness_sdk.semantic_beats import semantic_enabled
    if semantic_enabled(harness_planning_contract) and settings.runner_mode != "live":
        raise ValueError("semantic_analysis_requires_director_or_explicit_mock_transport; no deterministic fallback")
    if semantic_enabled(harness_planning_contract) and duration_profile != "episode_60":
        raise ValueError("semantic_analysis_long_form_not_supported; use the episode_60 contract")
    if genre_id is not None:
        prompts = dict(prompts)
        prompts["image/style-guide.md"] = prompts["image/style-guide.md"] + "\n\n" + planning_instruction(genre_id, image_style)
    if motion_style is not None:
        from .motion_style import style_instruction
        prompts = dict(prompts)
        prompts["image/style-guide.md"] += "\n\n" + style_instruction(motion_style)
    selection = select_director_rules(scenario, harness_id)
    record_learning_selection(work_dir, selection)
    research_mode = getattr(settings, "director_research_mode", "off")
    if research_mode not in {"off", "pilot"}:
        raise ValueError("Invalid director research mode")
    brief = select_research_candidates(scenario, harness_id, planning_contract=harness_planning_contract)
    record_research_brief(work_dir, brief, mode=research_mode,
                          used_in_prompt=research_mode == "pilot" and settings.runner_mode == "live")
    if tracker is not None and hasattr(tracker, "add_asset"):
        tracker.add_asset(work_dir / "director-research-brief.json", "director_research_brief",
                          harness_id=harness_id, research_mode=research_mode,
                          research_status=brief["status"])
    if settings.runner_mode == "live":
        from .long_form_plan import combine_plans, local_source_units, script_ranges

        global_units = compile_storyboard_units(scenario, visual_cues) if visual_cues else compile_source_units(scenario)
        ranges = script_ranges(scenario, global_units) if duration_profile == "single_30m" else [(0, len(scenario))]
        directed = []
        for index, (start, end) in enumerate(ranges, 1):
            part_work = work_dir if len(ranges) == 1 else work_dir / f"director-part-{index:03d}"
            part_work.mkdir(parents=True, exist_ok=True)
            part_prompts = dict(prompts)
            if directed:
                part_prompts["image/style-guide.md"] += (
                    "\n\nKeep this previously directed video's design system consistent:\n"
                    + directed[0][1].style_bible.model_dump_json()
                )
            usage_start = len(tracker.usage)
            part_brief = select_research_candidates(
                scenario[start:end], harness_id, planning_contract=harness_planning_contract
            ) if research_mode == "pilot" else None
            if part_work != work_dir and part_brief is not None:
                record_research_brief(part_work, part_brief, mode=research_mode, used_in_prompt=True)
            from .harness_sdk.semantic_beats import semantic_enabled
            analysis = None
            analysis_repairs = 0
            selected_concept = None
            part_units = local_source_units(global_units, start, end)
            if semantic_enabled(harness_planning_contract):
                from .semantic_planning import analyze_script, analysis_units
                analysis, analysis_repairs = await analyze_script(scenario[start:end], settings, tracker, part_work,
                    harness_planning_contract, model=codex_model, effort=codex_reasoning_effort, fast_mode=codex_fast_mode)
                part_units = analysis_units(analysis)
            from .harness_sdk.concept_design import concept_enabled
            if concept_enabled(harness_planning_contract):
                if analysis is None:
                    raise ValueError("concept_selection_requires_meaning_analysis")
                from .concept_planning import select_concept
                selected_concept = await select_concept(scenario[start:end], analysis, harness_planning_contract,
                    settings, tracker, part_work, model=codex_model, image_style=image_style)
            part = await plan_with_codex(
                scenario[start:end], part_prompts, settings, tracker, part_work,
                codex_model=codex_model, codex_reasoning_effort=codex_reasoning_effort,
                codex_fast_mode=codex_fast_mode, continuity_enabled=continuity_enabled,
                image_style=image_style, learning_selection=selection,
                research_brief=part_brief,
                harness_planning_contract=harness_planning_contract,
                source_units_override=part_units,
                semantic_analysis_result=analysis,
                selected_concept=selected_concept,
                visual_cues=[cue for cue in (visual_cues or []) if cue.get("narration", "") in scenario[start:end]],
                local_graphic=bool(motion_style and motion_style.get("productionRoute") == "local_graphic"),
                _repair_limit=3-analysis_repairs if analysis is not None else 2,
            )
            # Earlier repair passes are evidence, not defects in the returned plan.
            new_usage = tracker.usage[usage_start:]
            if new_usage:
                repairs = (new_usage[-1].get("raw_usage") or {}).get("deterministic_repairs")
                findings = structural_repair_findings(repairs)
                if findings:
                    raise ValueError("Director plan needs repair before asset work: " + ", ".join(findings))
            directed.append((start, part))
        plan = combine_plans(scenario, directed) if len(directed) > 1 else directed[0][1]
        plan = bind_plan(plan, genre_id) if genre_id is not None else plan
        record_learning_application(work_dir, selection, plan)
        return plan
    plan = deterministic_plan(scenario, prompts["image/style-guide.md"], image_style)
    validate_plan(plan, scenario)
    plan = bind_plan(plan, genre_id) if genre_id is not None else plan
    record_learning_application(work_dir, selection, plan)
    return plan
