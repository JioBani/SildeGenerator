"""Join independently directed script ranges into one production plan."""

from __future__ import annotations

from collections import Counter

from .models import ScenePlan, SourceUnit
from .planner import validate_plan


def script_ranges(scenario: str, source_units: list, max_characters: int = 1400) -> list[tuple[int, int]]:
    """Partition at source boundaries without changing or dropping a character."""
    if not source_units:
        return []
    ranges: list[tuple[int, int]] = []
    start = source_units[0].start_offset
    end = start
    for unit in source_units:
        if end > start and unit.end_offset - start > max_characters:
            ranges.append((start, end))
            start = end
        end = unit.end_offset
    ranges.append((start, end))
    if start != ranges[-1][0] or scenario != "".join(scenario[a:b] for a, b in ranges):
        raise ValueError("Long-form partition did not preserve the original script")
    return ranges


def local_source_units(source_units: list[SourceUnit], start: int, end: int) -> list[SourceUnit]:
    selected = [unit for unit in source_units if start <= unit.start_offset and unit.end_offset <= end]
    if not selected or selected[0].start_offset != start or selected[-1].end_offset != end:
        raise ValueError("Directed range does not align with source units")
    return [unit.model_copy(update={
        "id": f"unit-{index:03d}",
        "start_offset": unit.start_offset - start,
        "end_offset": unit.end_offset - start,
    }) for index, unit in enumerate(selected, 1)]


def combine_plans(scenario: str, chunks: list[tuple[int, ScenePlan]]) -> ScenePlan:
    if not chunks:
        raise ValueError("No directed script ranges")
    units = []
    sequences = []
    groups = []
    scenes = []
    assets = []
    asset_numbers: Counter[str] = Counter()
    rejected = []
    first = chunks[0][1]
    last = chunks[-1][1]
    for offset, part in chunks:
        unit_map = {unit.id: f"unit-{len(units) + index:03d}" for index, unit in enumerate(part.source_units, 1)}
        sequence_map = {seq.id: f"sequence-{len(sequences) + index:03d}" for index, seq in enumerate(part.sequences, 1)}
        group_map = {group.id: f"group-{len(groups) + index:03d}" for index, group in enumerate(part.scene_groups, 1)}
        scene_map = {scene.id: f"scene-{len(scenes) + index:03d}" for index, scene in enumerate(part.scenes, 1)}
        asset_map = {}
        for asset in part.continuity_assets:
            asset_numbers[asset.category] += 1
            asset_map[asset.asset_id] = f"asset-{asset.category}-{asset_numbers[asset.category]:03d}"
        units.extend(unit.model_copy(update={
            "id": unit_map[unit.id], "start_offset": unit.start_offset + offset,
            "end_offset": unit.end_offset + offset,
        }) for unit in part.source_units)
        sequences.extend(seq.model_copy(update={
            "id": sequence_map[seq.id],
            "source_unit_ids": [unit_map[item] for item in seq.source_unit_ids],
            "scene_group_ids": [group_map[item] for item in seq.scene_group_ids],
            "keycut_scene_id": scene_map[seq.keycut_scene_id],
        }) for seq in part.sequences)
        groups.extend(group.model_copy(update={
            "id": group_map[group.id], "sequence_id": sequence_map[group.sequence_id],
            "source_unit_ids": [unit_map[item] for item in group.source_unit_ids],
            "scene_ids": [scene_map[item] for item in group.scene_ids],
        }) for group in part.scene_groups)
        assets.extend(asset.model_copy(update={
            "asset_id": asset_map[asset.asset_id],
            "appearing_scene_ids": [scene_map[item] for item in asset.appearing_scene_ids],
        }) for asset in part.continuity_assets)
        scenes.extend(scene.model_copy(update={
            "id": scene_map[scene.id], "sequence_id": sequence_map[scene.sequence_id],
            "scene_group_id": group_map[scene.scene_group_id],
            "source_unit_ids": [unit_map[item] for item in scene.source_unit_ids],
            "parent_keycut_scene_id": scene_map[scene.parent_keycut_scene_id] if scene.parent_keycut_scene_id else None,
            "present_asset_ids": [asset_map[item] for item in scene.present_asset_ids],
            "reference_asset_ids": [asset_map[item] for item in scene.reference_asset_ids],
        }) for scene in part.scenes)
        rejected.extend(part.rejected_borderline_candidates)
    if len(scenes) > 300 or len(sequences) > 300 or len(groups) > 300:
        raise ValueError("Long-form plan exceeds the current scene contract; combine source units before direction")
    result = ScenePlan(
        title=first.title, core_question=first.core_question, thesis=first.thesis,
        audience_start_state=first.audience_start_state,
        audience_end_state=last.audience_end_state,
        master_keycut_scene_id=first.master_keycut_scene_id, style_bible=first.style_bible,
        source_units=units, sequences=sequences, scene_groups=groups,
        continuity_assets=assets, rejected_borderline_candidates=rejected[:10], scenes=scenes,
    )
    validate_plan(result, scenario)
    return result
