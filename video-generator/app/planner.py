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
from .models import (
    ContinuityAsset, KeycutDNA, NarrativeSequence, Scene, SceneGroup,
    ScenePlan, SourceUnit, StyleBible,
)
from .plan_compiler import compile_scene_plan
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
        boundary = char in ".!?。！？\r\n" or (char in ",，" and index + 1 - start >= 90)
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


def _default_style_bible(image_style: str) -> StyleBible:
    descriptions = {
        "editorial_illustration": "정교한 에디토리얼 일러스트레이션, 절제된 상징과 명료한 서사",
        "cinematic_realism": "영화 스틸 같은 사실적 인물·공간·조명과 자연스러운 렌즈 깊이",
        "graphic_explainer": "정보 구조와 인과를 도형·공간 관계로 명료하게 설명하는 그래픽",
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


def _compose_prompt(prompts: dict[str, str], scenario: str, source_units: list[SourceUnit], continuity_enabled: bool, image_style: str) -> str:
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
    return "\n".join(sections)


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
) -> ScenePlan:
    schema = settings.schemas_dir / "scene-plan.schema.json"
    output = work_dir / "scene-plan.codex.json"
    source_units = compile_source_units(scenario)
    prompt = _compose_prompt(prompts, scenario, source_units, continuity_enabled, image_style)
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
                "schema": json.loads(schema.read_text(encoding="utf-8")),
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
        tracker.attempt,
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
                "transcript": "work/codex/attempt-%d" % tracker.attempt,
                "timing": transcript.summary(),
            },
        )
        usage_recorded = True
        proposal = json.loads(text)
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
                    "reasoning_effort": effort,
                    "fast_mode_requested": fast_mode,
                    "service_tier_requested": "priority" if fast_mode else "default",
                    "service_tier_actual": transcript.actual_service_tier,
                    "streaming": True,
                    "transcript": "work/codex/attempt-%d" % tracker.attempt,
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
) -> ScenePlan:
    if settings.runner_mode == "live":
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
        )
    plan = deterministic_plan(scenario, prompts["image/style-guide.md"], image_style)
    validate_plan(plan, scenario)
    return plan
