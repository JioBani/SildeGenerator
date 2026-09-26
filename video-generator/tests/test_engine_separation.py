import unittest
from types import SimpleNamespace
from pathlib import Path

from app.engine.harness_loader import HarnessRegistry
from app.engine.harness_preflight import planning_contract, validate_harness_plan
from app.harness_sdk.engine_mode import evaluate_engine_mode
from test_narrative_direction import shot
from test_hybrid_story import route

ROOT = Path(__file__).resolve().parents[2]


class EngineSeparationTests(unittest.TestCase):
    def scene(self, hybrid=None):
        layout = {"direction": shot(), "camera": {"mode": "hold"}}
        if hybrid is not None:
            layout["hybrid"] = hybrid
        return SimpleNamespace(id="scene-001", layout=layout, transition="cut")

    def test_independent_planning_and_runtime_contracts(self):
        registry = HarnessRegistry(ROOT / "harnesses")
        slide, hybrid = registry.load("narrative-slide"), registry.load("hybrid-story")
        self.assertEqual("slide", planning_contract(slide)["engine_family"])
        self.assertEqual("hybrid", planning_contract(hybrid)["engine_family"])
        self.assertNotIn("hybrid_direction", planning_contract(slide))
        self.assertNotIn("visual_grammar_library", planning_contract(slide))
        self.assertIn("hybrid_direction", planning_contract(hybrid))
        self.assertNotEqual(slide.manifest.entrypoint, hybrid.manifest.entrypoint)
        self.assertFalse(slide.manifest.public)
        self.assertFalse(hybrid.manifest.public)

    def test_slide_rejects_each_hybrid_route_instead_of_ignoring_it(self):
        slide = HarnessRegistry(ROOT / "harnesses").load("narrative-slide")
        self.assertEqual([], validate_harness_plan(slide, [self.scene()]))
        for kind in ("cinematic", "diagram", "source"):
            self.assertIn("scene-001:slide_engine_rejects_hybrid_route",
                validate_harness_plan(slide, [self.scene(route(kind))]))

    def test_hybrid_never_assumes_a_missing_route_is_a_slide(self):
        hybrid = HarnessRegistry(ROOT / "harnesses").load("hybrid-story")
        self.assertIn("scene-001:hybrid_engine_requires_explicit_route", validate_harness_plan(hybrid, [self.scene()]))
        self.assertEqual([], validate_harness_plan(hybrid, [self.scene(route("cinematic"))]))

    def test_legacy_contract_is_unchanged(self):
        self.assertEqual([], evaluate_engine_mode([self.scene()], None))


if __name__ == "__main__":
    unittest.main()
