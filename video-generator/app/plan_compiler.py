from __future__ import annotations

from collections import Counter
from typing import Any

from .models import (
    ContinuityAsset,
    KeycutDNA,
    NarrativeSequence,
    RejectedContinuityCandidate,
    Scene,
    SceneGroup,
    ScenePlan,
    SourceUnit,
    StyleBible,
)


def _unique_valid_scene_numbers(values: list[int], scene_count: int) -> tuple[list[int], int]:
    accepted: list[int] = []
    rejected = 0
    for value in values:
        if value < 1 or value > scene_count or value in accepted:
            rejected += 1
            continue
        accepted.append(value)
    return accepted, rejected


def compile_scene_plan(
    proposal: dict[str, Any],
    scenario: str,
    source_units: list[SourceUnit],
    *,
    continuity_enabled: bool,
) -> tuple[ScenePlan, dict[str, int | str]]:
    """Compile semantic model output into the runtime ScenePlan contract.

    The model never owns runtime identifiers or foreign-key relationships.
    It proposes nested semantic structure and source-unit counts. This compiler
    assigns every ID, consumes every source unit exactly once, derives hierarchy
    ranges, keycut parents, continuity IDs, and per-scene asset references.
    """
    slots: list[tuple[int, int, dict[str, Any]]] = []
    sequences = proposal["sequences"]
    for sequence_index, sequence in enumerate(sequences):
        for group_index, group in enumerate(sequence["scene_groups"]):
            for scene in group["scenes"]:
                slots.append((sequence_index, group_index, scene))

    if not slots:
        raise ValueError("semantic plan must contain at least one scene proposal")

    maximum_scenes = min(300, len(source_units))
    dropped_scene_proposals = max(0, len(slots) - maximum_scenes)
    slots = slots[:maximum_scenes]

    requested_counts = [max(1, int(scene["source_unit_count"])) for _, _, scene in slots]
    assigned_counts: list[int] = []
    remaining = len(source_units)
    adjusted_counts = 0
    for index, requested in enumerate(requested_counts):
        remaining_slots = len(slots) - index - 1
        assigned = remaining if remaining_slots == 0 else min(requested, remaining - remaining_slots)
        assigned = max(1, assigned)
        assigned_counts.append(assigned)
        adjusted_counts += int(assigned != requested)
        remaining -= assigned

    retained_sequence_indexes = list(dict.fromkeys(sequence_index for sequence_index, _, _ in slots))
    sequence_id_by_index = {
        original: f"sequence-{compiled + 1:03d}"
        for compiled, original in enumerate(retained_sequence_indexes)
    }
    retained_groups = list(dict.fromkeys((sequence_index, group_index) for sequence_index, group_index, _ in slots))
    group_id_by_index = {
        pair: f"group-{compiled + 1:03d}"
        for compiled, pair in enumerate(retained_groups)
    }

    compiled_scenes: list[Scene] = []
    cursor = 0
    for scene_index, ((sequence_index, group_index, semantic), unit_count) in enumerate(zip(slots, assigned_counts), 1):
        selected_units = source_units[cursor:cursor + unit_count]
        cursor += unit_count
        compiled_scenes.append(Scene(
            id=f"scene-{scene_index:03d}",
            sequence_id=sequence_id_by_index[sequence_index],
            scene_group_id=group_id_by_index[(sequence_index, group_index)],
            source_unit_ids=[unit.id for unit in selected_units],
            role_in_group=semantic["role_in_group"],
            purpose=semantic["purpose"],
            viewer_takeaway=semantic["viewer_takeaway"],
            cut_role=semantic["cut_role"],
            narration="".join(unit.text for unit in selected_units),
            visual_summary=semantic["visual_summary"],
            image_prompt=semantic["image_prompt"],
        ))

    compiled_groups: list[SceneGroup] = []
    for sequence_index, group_index in retained_groups:
        semantic = sequences[sequence_index]["scene_groups"][group_index]
        members = [scene for scene in compiled_scenes if scene.scene_group_id == group_id_by_index[(sequence_index, group_index)]]
        compiled_groups.append(SceneGroup(
            id=group_id_by_index[(sequence_index, group_index)],
            sequence_id=sequence_id_by_index[sequence_index],
            source_unit_ids=[unit_id for scene in members for unit_id in scene.source_unit_ids],
            role_in_sequence=semantic["role_in_sequence"],
            purpose=semantic["purpose"],
            setup=semantic["setup"],
            payoff=semantic["payoff"],
            scene_ids=[scene.id for scene in members],
        ))

    compiled_sequences: list[NarrativeSequence] = []
    keycut_by_sequence: dict[str, str] = {}
    clamped_keycuts = 0
    for sequence_index in retained_sequence_indexes:
        semantic = sequences[sequence_index]
        sequence_id = sequence_id_by_index[sequence_index]
        members = [scene for scene in compiled_scenes if scene.sequence_id == sequence_id]
        requested_keycut = int(semantic["keycut_scene_number"])
        selected_position = min(max(1, requested_keycut), len(members))
        clamped_keycuts += int(selected_position != requested_keycut)
        keycut = members[selected_position - 1]
        keycut_by_sequence[sequence_id] = keycut.id
        dna = KeycutDNA.model_validate(semantic["keycut_dna"])
        for member in members:
            if member.id == keycut.id:
                member.cut_role = "keycut"
                member.parent_keycut_scene_id = None
                member.keycut_dna = dna
            else:
                member.parent_keycut_scene_id = keycut.id
                member.keycut_dna = None
        sequence_groups = [group for group in compiled_groups if group.sequence_id == sequence_id]
        compiled_sequences.append(NarrativeSequence(
            id=sequence_id,
            source_unit_ids=[unit_id for scene in members for unit_id in scene.source_unit_ids],
            role_in_story=semantic["role_in_story"],
            purpose=semantic["purpose"],
            viewer_state_before=semantic["viewer_state_before"],
            viewer_state_after=semantic["viewer_state_after"],
            scene_group_ids=[group.id for group in sequence_groups],
            keycut_scene_id=keycut.id,
        ))

    requested_master = int(proposal["master_keycut_sequence_number"])
    master_position = min(max(1, requested_master), len(compiled_sequences))
    master_keycut_scene_id = compiled_sequences[master_position - 1].keycut_scene_id

    compiled_assets: list[tuple[ContinuityAsset, set[str]]] = []
    dropped_assets = 0
    invalid_asset_scene_numbers = 0
    category_counts: Counter[str] = Counter()
    if continuity_enabled:
        for semantic in proposal["continuity_assets"]:
            appearances, rejected_appearances = _unique_valid_scene_numbers(
                semantic["appearing_scene_numbers"], len(compiled_scenes)
            )
            references, rejected_references = _unique_valid_scene_numbers(
                semantic["reference_scene_numbers"], len(compiled_scenes)
            )
            invalid_asset_scene_numbers += rejected_appearances + rejected_references
            if len(appearances) < 2:
                dropped_assets += 1
                continue
            category = semantic["category"]
            category_counts[category] += 1
            asset_id = f"asset-{category}-{category_counts[category]:03d}"
            appearance_ids = [compiled_scenes[number - 1].id for number in appearances]
            reference_ids = {
                compiled_scenes[number - 1].id
                for number in references
                if number in appearances
            }
            compiled_assets.append((ContinuityAsset(
                asset_id=asset_id,
                category=category,
                name=semantic["name"],
                canonical_identity=semantic["canonical_identity"],
                must_remain_consistent=semantic["must_remain_consistent"],
                allowed_variations=semantic["allowed_variations"],
                states=semantic["states"],
                appearing_scene_ids=appearance_ids,
                selection_reason_code=semantic["selection_reason_code"],
                selection_reason=semantic["selection_reason"],
                failure_if_inconsistent=semantic["failure_if_inconsistent"],
                confidence=semantic["confidence"],
                anchor_prompt=semantic["anchor_prompt"],
            ), reference_ids))

    for scene in compiled_scenes:
        present = [asset.asset_id for asset, _ in compiled_assets if scene.id in asset.appearing_scene_ids]
        references = [asset.asset_id for asset, reference_scenes in compiled_assets if scene.id in reference_scenes]
        scene.present_asset_ids = present
        scene.reference_asset_ids = references[:8 if scene.cut_role == "keycut" else 7]

    plan = ScenePlan(
        title=proposal["title"],
        core_question=proposal["core_question"],
        thesis=proposal["thesis"],
        audience_start_state=proposal["audience_start_state"],
        audience_end_state=proposal["audience_end_state"],
        master_keycut_scene_id=master_keycut_scene_id,
        style_bible=StyleBible.model_validate(proposal["style_bible"]),
        source_units=source_units,
        sequences=compiled_sequences,
        scene_groups=compiled_groups,
        continuity_assets=[asset for asset, _ in compiled_assets],
        rejected_borderline_candidates=[
            RejectedContinuityCandidate.model_validate(value)
            for value in proposal["rejected_borderline_candidates"]
        ],
        scenes=compiled_scenes,
    )
    return plan, {
        "compiler": "deterministic-v1",
        "source_units": len(source_units),
        "scene_proposals_dropped": dropped_scene_proposals,
        "source_unit_counts_adjusted": adjusted_counts,
        "keycut_positions_clamped": clamped_keycuts,
        "master_keycut_position_clamped": int(master_position != requested_master),
        "continuity_assets_dropped": dropped_assets,
        "asset_scene_numbers_ignored": invalid_asset_scene_numbers,
    }
