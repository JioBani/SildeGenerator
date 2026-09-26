from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import httpx

from app.codex_transcript import CodexTranscript
from app.planner import (
    _compose_prompt, _extract_output_text, _iter_sse, _repair_feedback, compile_narration,
    compile_source_units, compile_storyboard_units, create_plan, deterministic_plan, validate_plan,
)
from app.plan_compiler import compile_scene_plan, structural_repair_findings
from app.tracking import Tracker


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
        "scene_function": "explain",
        "layout": {"mode": "focus", "focal_order": ["subject", "evidence"], "safe_area": "title_top_caption_bottom",
                   "camera": None, "continuity_group": None, "authored_design": None, "visual_labels": []},
        "object_states": [
            {"object_id": "scene-image", "role": "subject", "initial": "context", "final": "emphasized"},
            {"object_id": "evidence-card", "role": "evidence", "initial": "hidden", "final": "visible"},
        ],
        "motion": [
            {"object_id": "scene-image", "kind": "camera_push", "phases": ["read", "move", "settle"]},
            {"object_id": "evidence-card", "kind": "reveal", "phases": ["anticipate", "reveal", "hold"]},
        ],
        "transition": "cut",
        "rhythm": "read_then_move_then_hold",
        "renderer_requirements": {"preferred": "hyperframes", "capabilities": ["multi_phase_timeline", "settle"]},
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


class ScenePlanSchemaTests(unittest.TestCase):
    def test_const_nodes_declare_types_for_structured_output(self):
        schema_path = Path(__file__).parents[1] / "schemas" / "scene-plan.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        missing: list[str] = []

        def walk(node, path: str = "#") -> None:
            if isinstance(node, dict):
                if "const" in node and "type" not in node:
                    missing.append(path)
                for key, value in node.items():
                    walk(value, f"{path}/{key}")
            elif isinstance(node, list):
                for index, value in enumerate(node):
                    walk(value, f"{path}/{index}")

        walk(schema)
        self.assertEqual([], missing)


class SourceUnitCompilerTests(unittest.TestCase):
    def test_timed_storyboard_uses_explicit_narration_blocks(self) -> None:
        cues = [
            {"timeCue": "00~03초", "direction": "대칭 프레임", "narration": "첫 문장입니다. 두 번째 문장입니다."},
            {"timeCue": "03~20초", "direction": "시선 가이드", "narration": "왜 그럴까요? 기준선 때문입니다."},
        ]
        scenario = "\n".join(cue["narration"] for cue in cues)
        units = compile_storyboard_units(scenario, cues)
        self.assertEqual(len(units), 2)
        self.assertEqual("".join(unit.text for unit in units), scenario)
        self.assertEqual([scenario[unit.start_offset:unit.end_offset] for unit in units],
                         [unit.text for unit in units])
        with self.assertRaisesRegex(ValueError, "does not match"):
            compile_storyboard_units(scenario + "!", cues)

    def test_runtime_contract_states_exact_source_budget_and_motion_targets(self) -> None:
        scenario = "첫 문장입니다. 두 번째 문장입니다."
        units = compile_source_units(scenario)
        prompts = {
            "director/system.md": "system",
            "narrative/story-intent.md": "{{SOURCE_UNITS}}",
            "narrative/analyze-sequences.md": "sequences",
            "narrative/analyze-scene-groups.md": "groups",
            "narrative/analyze-scenes.md": "scenes",
            "keycut/select-keycuts.md": "keycuts",
            "style/common.md": "{{IMAGE_STYLE}}",
            "style/presets/editorial-illustration.md": "style",
            "continuity/disabled.md": "disabled",
            "image/system.md": "image",
            "image/build-image-prompt.md": "{{SCENE_JSON}}",
            "image/style-guide.md": "guide",
        }

        prompt = _compose_prompt(
            prompts, scenario, units, False, "editorial_illustration",
        )

        self.assertIn(f"source unit은 정확히 {len(units)}개", prompt)
        self.assertIn("motion.object_id는 같은 scene의 object_states.object_id", prompt)
        self.assertIn("object_id=scene", prompt)

        directed = _compose_prompt(
            prompts, scenario, units, False, "editorial_illustration",
            visual_cues=[{"timeCue": "20~40초", "direction": "인물의 눈에 격자선", "narration": "첫 문장입니다."}],
            local_graphic=True,
        )
        self.assertIn("runtime/storyboard-visual-cues.json", directed)
        self.assertIn("인물의 눈에 격자선", directed)
        self.assertIn("never place cue headings", directed)
        self.assertIn("one scene for each unit", directed)
        self.assertIn("runtime/local-graphic-vocabulary.md", directed)
        self.assertIn("frame-grid", directed)
        self.assertIn("For film composition ONLY", directed)
        self.assertIn("space-station", directed)
        self.assertIn("at most eight objects", directed)
        self.assertIn("role as subject", directed)

    def test_repair_feedback_exposes_the_missing_source_budget(self) -> None:
        repairs = {"source_unit_counts_adjusted": 1}
        proposal = {
            "master_keycut_sequence_number": 1,
            "sequences": [{
                "keycut_scene_number": 5,
                "scene_groups": [{"scenes": [
                    {"source_unit_count": 1},
                    {"source_unit_count": 1},
                    {"source_unit_count": 2},
                    {"source_unit_count": 1},
                ]}],
            }],
        }

        feedback = _repair_feedback(repairs, proposal, 10)

        self.assertIn("입력 source unit은 10개", feedback)
        self.assertIn("[1, 1, 2, 1] (합계 5)", feedback)
        self.assertIn("director_structural_repair:source_unit_counts_adjusted:1", feedback)
        self.assertIn("scene 4개, keycut_scene_number=5", feedback)

    def test_repair_prompt_requires_a_fresh_complete_design(self) -> None:
        scenario = "첫 문장입니다. 두 번째 문장입니다."
        units = compile_source_units(scenario)
        prompts = {
            "director/system.md": "system",
            "narrative/story-intent.md": "{{SOURCE_UNITS}}",
            "narrative/analyze-sequences.md": "sequences",
            "narrative/analyze-scene-groups.md": "groups",
            "narrative/analyze-scenes.md": "scenes",
            "keycut/select-keycuts.md": "keycuts",
            "style/common.md": "{{IMAGE_STYLE}}",
            "style/presets/editorial-illustration.md": "style",
            "continuity/disabled.md": "disabled",
            "image/system.md": "image",
            "image/build-image-prompt.md": "{{SCENE_JSON}}",
            "image/style-guide.md": "guide",
        }

        prompt = _compose_prompt(
            prompts,
            scenario,
            units,
            False,
            "editorial_illustration",
            repair_feedback="이전 합계는 1이었다.",
        )

        self.assertIn("runtime/director-repair.md", prompt)
        self.assertIn("이전 장면 수나 배분을 답습하지 말고", prompt)
        self.assertIn("정확히 한 번씩", prompt)

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

    def test_decimal_point_does_not_split_a_temperature(self) -> None:
        scenario = "절대영도는 영하 273.15도입니다. 우주는 조금 더 따뜻합니다."
        units = compile_source_units(scenario)
        self.assertEqual(len(units), 2)
        self.assertIn("273.15도", units[0].text)
        self.assertEqual("".join(unit.text for unit in units), scenario)


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

    def test_lossy_structural_repairs_become_blocking_findings(self):
        findings = structural_repair_findings({
            "compiler": "deterministic-v1",
            "source_units": 5,
            "source_unit_counts_adjusted": 1,
            "keycut_positions_clamped": 1,
            "continuity_disabled_assets_removed": 2,
        })
        self.assertEqual(findings, [
            "director_structural_repair:source_unit_counts_adjusted:1",
            "director_structural_repair:keycut_positions_clamped:1",
        ])

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


class FinalDirectorRepairGateTests(unittest.IsolatedAsyncioTestCase):
    async def _plan_with_repairs(self, repair_history: list[dict[str, int]]) -> None:
        scenario = "첫 장면입니다. 두 번째 장면입니다."
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tracker = Tracker(root)

            async def director(*args, **kwargs):
                for repairs in repair_history:
                    tracker.add_usage(raw_usage={"deterministic_repairs": repairs})
                return deterministic_plan(scenario, "guide")

            with patch("app.planner.plan_with_codex", side_effect=director):
                await create_plan(
                    scenario, {"image/style-guide.md": "guide"},
                    SimpleNamespace(runner_mode="live"), tracker, root,
                )

    async def test_repaired_final_plan_is_not_blocked_by_prior_attempt(self) -> None:
        await self._plan_with_repairs([
            {"keycut_positions_clamped": 1},
            {"keycut_positions_clamped": 0, "source_unit_counts_adjusted": 0},
        ])

    async def test_unrepaired_final_plan_still_blocks_asset_work(self) -> None:
        with self.assertRaisesRegex(ValueError, "source_unit_counts_adjusted:1"):
            await self._plan_with_repairs([
                {"keycut_positions_clamped": 1},
                {"source_unit_counts_adjusted": 1},
            ])


class OutputExtractionTests(unittest.TestCase):
    def test_extracts_structured_output_text(self) -> None:
        payload = {"output": [{"content": [{"type": "output_text", "text": '{"title":"원문"}'}]}]}
        self.assertEqual(_extract_output_text(payload), '{"title":"원문"}')


if __name__ == "__main__":
    unittest.main()
