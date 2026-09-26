import json
import unittest
from pathlib import Path

from app.plan_compiler import compile_scene_plan
from app.planner import compile_source_units, validate_plan
from app.engine.harness_loader import HarnessRegistry
from app.engine.harness_preflight import validate_harness_plan
from test_planner import semantic_proposal

ROOT = Path(__file__).resolve().parents[2]


class DirectorVisualContractTests(unittest.TestCase):
    def setUp(self):
        self.schema = json.loads((ROOT / 'video-generator/schemas/scene-plan.schema.json').read_text())
        self.proposal = semantic_proposal()
        self.scene = self.proposal['sequences'][0]['scene_groups'][0]['scenes'][0]

    def test_camera_survives_schema_compile_and_harness_preflight(self):
        self.scene['layout'].update(camera={'mode': 'push', 'focus': [.7, .3], 'strength': .025},
                                    visual_labels=[{'text': '결과', 'x': .7, 'y': .3}])
        self.scene['renderer_requirements']['preferred'] = 'cinematic-slide'
        script = 'first. second.'
        plan, _ = compile_scene_plan(self.proposal, script, compile_source_units(script), continuity_enabled=False)
        validate_plan(plan, script)
        self.assertEqual(plan.scenes[0].layout['camera'], self.scene['layout']['camera'])
        self.assertEqual(plan.scenes[0].layout['visual_labels'], self.scene['layout']['visual_labels'])
        harness = HarnessRegistry(ROOT / 'harnesses').load('cinematic-slide')
        self.assertEqual(validate_harness_plan(harness, plan.scenes), [])

    def test_strict_objects_have_all_properties_required(self):
        def visit(value):
            if isinstance(value, dict):
                if value.get('type') == 'object':
                    self.assertFalse(value['additionalProperties'])
                    self.assertEqual(set(value['required']), set(value['properties']))
                for child in value.values():
                    visit(child)
            elif isinstance(value, list):
                for child in value:
                    visit(child)
        visit(self.schema)
