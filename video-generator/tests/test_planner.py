from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import httpx

from app.codex_transcript import CodexTranscript
from app.planner import (
    _extract_output_text, _iter_sse, compile_narration,
    compile_source_units, deterministic_plan, validate_plan,
)
from app.plan_compiler import compile_scene_plan


def semantic_proposal(*, source_counts: list[int] | None = None) -> dict:
    counts = source_counts or [1, 1]
    scenes = [{
        "source_unit_count": count,
        "role_in_group": "story beat",
        "purpose": "advance the story",
        "viewer_takeaway": f"beat {index}",
        "cut_role": "derived",
        "visual_summary": f"visual {index}",
        "image_prompt": f"prompt {index}",
    } for index, count in enumerate(counts, 1)]
    return {
        "title": "compiled plan",
        "core_question": "what changes?",
        "thesis": "structure is compiled",
        "audience_start_state": "before",
        "audience_end_state": "after",
        "master_keycut_sequence_number": 1,
        "style_bible": {
            "preset_id": "editorial_illustration",
            "medium_and_rendering": "editorial",
            "palette": ["navy"],
            "lighting": "soft",
            "camera_and_depth": "wide",
            "texture_and_detail": "paper",
            "character_rendering": "consistent",
            "environment_rendering": "consistent",
            "composition_rules": ["safe area"],
            "forbidden_variations": ["text"],
        },
        "sequences": [{
            "role_in_story": "development",
            "purpose": "develop",
            "viewer_state_before": "before",
            "viewer_state_after": "after",
            "keycut_scene_number": 2,
            "keycut_dna": {
                "story_meaning": "turn",
                "composition_anchor": "center",
                "palette_anchor": ["navy"],
                "lighting_anchor": "soft",
                "symbol_anchor": [],
                "must_inherit": ["palette"],
                "must_not_copy": ["pose"],
            },
            "scene_groups": [{
                "role_in_sequence": "explain",
                "purpose": "explain",
                "setup": "setup",
                "payoff": "payoff",
                "scenes": scenes,
            }],
        }],
        "continuity_assets": [{
            "category": "character",
            "name": "owner",
            "canonical_identity": "same adult owner",
            "must_remain_consistent": ["face"],
            "allowed_variations": ["pose"],
            "states": [{"state_id": "owner-calm", "description": "calm"}],
            "appearing_scene_numbers": [1, 2],
            "reference_scene_numbers": [1, 2],
            "selection_reason_code": "RECURRING_CHARACTER",
            "selection_reason": "recurs",
            "failure_if_inconsistent": "identity breaks",
            "confidence": 1,
            "anchor_prompt": "adult owner",
        }],
        "rejected_borderline_candidates": [],
    }


class SourceUnitCompilerTests(unittest.TestCase):
    def test_preserves_every_character_offset_and_order(self) -> None:
        scenario = "첫 줄입니다.  \n같은 골목을 지나고,\n\n마지막 줄입니다."
        units = compile_source_units(scenario)
        self.assertEqual("".join(unit.text for unit in units), scenario)
        self.assertEqual([scenario[unit.start_offset:unit.end_offset] for unit in units], [unit.text for unit in units])
        self.assertEqual([unit.id for unit in units], [f"unit-{index:03d}" for index in range(1, len(units) + 1)])

    def test_compile_rejects_omitted_or_reordered_source_units(self) -> None:
        scenario = "첫 문장입니다. 두 번째 문장입니다."
        units = compile_source_units(scenario)
        plan = deterministic_plan(scenario, "스타일")
        plan.scenes[0].source_unit_ids = [units[-1].id]
        with self.assertRaisesRegex(ValueError, "exactly once"):
            compile_narration(plan, scenario, units)

    def test_many_short_sentences_are_coalesced_without_loss(self) -> None:
        scenario = "".join(f"{index}." for index in range(400))
        units = compile_source_units(scenario)
        self.assertEqual(len(units), 300)
        self.assertEqual("".join(unit.text for unit in units), scenario)
        validate_plan(deterministic_plan(scenario, "스타일"), scenario)


class NarrativeHierarchyTests(unittest.TestCase):
    def test_model_schema_cannot_emit_runtime_ids_or_foreign_keys(self) -> None:
        schema = json.loads((Path(__file__).parents[1] / "schemas" / "scene-plan.schema.json").read_text(encoding="utf-8"))
        root_properties = schema["properties"]
        scene_properties = schema["$defs"]["scene"]["properties"]
        asset_properties = schema["$defs"]["continuityAsset"]["properties"]

        self.assertNotIn("master_keycut_scene_id", root_properties)
        self.assertTrue({"id", "sequence_id", "scene_group_id", "parent_keycut_scene_id", "present_asset_ids", "reference_asset_ids"}.isdisjoint(scene_properties))
        self.assertNotIn("asset_id", asset_properties)

    def test_compiler_owns_all_runtime_ids_and_asset_relations(self) -> None:
        scenario = "first. second."
        units = compile_source_units(scenario)
        plan, repairs = compile_scene_plan(
            semantic_proposal(), scenario, units, continuity_enabled=True,
        )

        validate_plan(plan, scenario)
        self.assertEqual(repairs["compiler"], "deterministic-v1")
        self.assertEqual([scene.id for scene in plan.scenes], ["scene-001", "scene-002"])
        self.assertEqual(plan.sequences[0].id, "sequence-001")
        self.assertEqual(plan.scene_groups[0].id, "group-001")
        self.assertEqual(plan.sequences[0].keycut_scene_id, "scene-002")
        self.assertEqual(plan.scenes[0].parent_keycut_scene_id, "scene-002")
        self.assertEqual(plan.continuity_assets[0].asset_id, "asset-character-001")
        self.assertEqual(plan.scenes[0].present_asset_ids, ["asset-character-001"])
        self.assertEqual(plan.scenes[0].reference_asset_ids, ["asset-character-001"])

    def test_compiler_consumes_every_source_unit_without_model_ids(self) -> None:
        scenario = "one. two. three."
        units = compile_source_units(scenario)
        plan, repairs = compile_scene_plan(
            semantic_proposal(source_counts=[99, 99]), scenario, units, continuity_enabled=False,
        )

        validate_plan(plan, scenario)
        self.assertEqual("".join(scene.narration for scene in plan.scenes), scenario)
        self.assertGreater(repairs["source_unit_counts_adjusted"], 0)
        self.assertEqual(plan.continuity_assets, [])

    def test_each_sequence_has_one_real_scene_keycut_and_valid_parents(self) -> None:
        scenario = "하나입니다. 둘입니다. 셋입니다. 넷입니다. 다섯입니다."
        plan = deterministic_plan(scenario, "스타일", "cinematic_realism")
        validate_plan(plan, scenario)
        self.assertEqual(plan.style_bible.preset_id, "cinematic_realism")
        self.assertEqual(len(plan.sequences), 2)
        self.assertIn(plan.master_keycut_scene_id, {sequence.keycut_scene_id for sequence in plan.sequences})
        for sequence in plan.sequences:
            members = [scene for scene in plan.scenes if scene.sequence_id == sequence.id]
            self.assertEqual([scene.id for scene in members if scene.cut_role == "keycut"], [sequence.keycut_scene_id])
            for scene in members:
                self.assertEqual(scene.parent_keycut_scene_id, None if scene.cut_role == "keycut" else sequence.keycut_scene_id)

    def test_derived_scene_continuity_budget_is_seven(self) -> None:
        scenario = "첫 장면입니다. 두 번째 장면입니다."
        plan = deterministic_plan(scenario, "스타일")
        plan.scenes[1].reference_asset_ids = [f"asset-character-{index:03d}" for index in range(1, 9)]
        with self.assertRaisesRegex(ValueError, "continuity reference limit"):
            validate_plan(plan, scenario)

    def test_parent_keycut_cannot_cross_sequence(self) -> None:
        scenario = "하나. 둘. 셋. 넷. 다섯. 여섯."
        plan = deterministic_plan(scenario, "스타일")
        plan.scenes[-1].parent_keycut_scene_id = plan.sequences[0].keycut_scene_id
        with self.assertRaisesRegex(ValueError, "sequence keycut"):
            validate_plan(plan, scenario)


class StreamingResponseTests(unittest.IsolatedAsyncioTestCase):
    async def test_parses_multiline_sse_without_losing_original_data(self) -> None:
        response = httpx.Response(200, content=(
            'event: response.output_text.delta\n'
            'data: {"type":"response.output_text.delta",\n'
            'data: "delta":"안녕"}\n\n'
            'data: [DONE]\n\n'
        ).encode("utf-8"))
        events = [event async for event in _iter_sse(response)]
        self.assertEqual(events[0][0], "response.output_text.delta")
        self.assertEqual(json.loads(events[0][1])["delta"], "안녕")
        self.assertEqual(events[1], (None, "[DONE]"))

    async def test_transcript_preserves_request_events_and_output_as_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            transcript = CodexTranscript(Path(directory), 2, {"model": "gpt-5.6-luna", "input": "원문"}, model="gpt-5.6-luna", effort="max", fast_mode=True)
            raw = '{"type":"response.output_text.delta","delta":"결과"}'
            transcript.record(None, raw, json.loads(raw))
            transcript.append_output("결과")
            transcript.complete({"id": "resp_1", "status": "completed", "service_tier": "priority"})
            self.assertEqual(transcript.output_path.read_text(encoding="utf-8"), "결과")
            self.assertEqual(json.loads(transcript.events_path.read_text(encoding="utf-8"))["data"], raw)
            self.assertEqual(transcript.summary()["service_tier_actual"], "priority")


class OutputExtractionTests(unittest.TestCase):
    def test_extracts_structured_output_text(self) -> None:
        payload = {"output": [{"content": [{"type": "output_text", "text": '{"title":"원문"}'}]}]}
        self.assertEqual(_extract_output_text(payload), '{"title":"원문"}')


if __name__ == "__main__":
    unittest.main()
