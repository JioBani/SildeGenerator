import unittest
from copy import deepcopy
from types import SimpleNamespace

from app.genre_profiles import (
    PROFILES,
    SCENE_STRATEGIES,
    bind_plan,
    planning_instruction,
    recommend,
    snapshot,
)


class FakePlan(SimpleNamespace):
    def model_copy(self, deep=False):
        return deepcopy(self)


class MotionGraphicFormatTests(unittest.TestCase):
    def test_one_user_format_contains_scene_level_strategies(self):
        self.assertEqual(list(PROFILES), ["motion_graphic"])
        contract = snapshot()
        self.assertEqual(contract["id"], "motion_graphic")
        self.assertEqual(set(contract["scene_strategies"]), set(SCENE_STRATEGIES))
        self.assertFalse(contract["production_approved"])

    def test_snapshot_cannot_mutate_registry(self):
        value = snapshot()
        value["requirements"].clear()
        value["strategy_definitions"]["causal_explanation"]["grammar"].clear()
        self.assertIn("motion_has_semantic_reason", snapshot()["requirements"])
        grammar = snapshot()["strategy_definitions"]["causal_explanation"]["grammar"]
        self.assertIn("state_change", grammar)

    def test_recommendation_does_not_create_fake_genre_differences(self):
        for scenario in ("GPU 계산 원리", "1914년 탐험 역사", "캐릭터 반응", ""):
            recommendation = recommend(scenario)
            self.assertEqual(recommendation["genre_id"], "motion_graphic")
            self.assertFalse(recommendation["requires_confirmation"])

    def test_rejects_retired_formats(self):
        for retired in ("knowledge", "history", "tutorial", "character", "cartoon", "documentary"):
            with self.assertRaises(ValueError):
                snapshot(retired)

    def test_source_and_existing_motion_are_preserved(self):
        source = FakePlan(scenes=[SimpleNamespace(
            narration="원문 그대로.",
            layout={"mode": "focus"},
            motion=[{"kind": "reveal"}],
        )])
        result = bind_plan(source)
        self.assertEqual(result.scenes[0].narration, source.scenes[0].narration)
        self.assertEqual(result.scenes[0].motion, source.scenes[0].motion)
        self.assertNotIn("production_format", source.scenes[0].layout)
        self.assertEqual(result.genre_contract["id"], "motion_graphic")
        self.assertEqual(result.scenes[0].layout["production_format"], "motion_graphic")

    def test_prompt_requires_strategy_without_fixed_frames(self):
        instruction = planning_instruction("motion_graphic", "fantasy_anime")
        self.assertIn("choose exactly one primary scene strategy", instruction)
        self.assertIn("A strategy is not a frame template", instruction)
        self.assertIn("Preserve narration and source order", instruction)
        self.assertIn("Surface art style: fantasy_anime", instruction)


if __name__ == "__main__":
    unittest.main()
