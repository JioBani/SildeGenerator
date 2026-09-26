import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from pydantic import ValidationError
from app.harness_sdk.hybrid import HybridScene, evaluate_hybrid, hybrid_output_schema, hybrid_planning_extension

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT / "scripts"))
sys.path.insert(0,str(ROOT / "harnesses/hybrid-story/src"))
from semantic_diagram_fixtures import cases
from hybrid_story.semantic_diagrams import markup
from hybrid_story.graphic_type import format_measure, lines_for


class SemanticDiagramTests(unittest.TestCase):
    def test_valid_contracts_and_distinct_geometry(self):
        outputs = []
        for case in cases():
            scene = SimpleNamespace(**case, layout={"hybrid":case["hybrid"]},transition="cut")
            self.assertEqual([], evaluate_hybrid([scene]))
            contract = HybridScene.model_validate(case["hybrid"])
            content, actions = markup(contract.diagram,0,15,0)
            self.assertTrue(actions)
            outputs.append(content)
        self.assertEqual(3,len(set(outputs)))
        self.assertIn("measure-",outputs[0])
        self.assertIn("누적 10권",outputs[1])
        self.assertIn("sequence-",outputs[2])
        self.assertIn('data-type-role="axis"', outputs[0])
        self.assertIn('data-type-role="value"', outputs[0])
        self.assertIn('data-type-role="annotation"', outputs[1])

    def test_korean_words_are_not_cut_and_overflow_stops_early(self):
        self.assertEqual('20분', format_measure(20, '분'))
        self.assertEqual('80%', format_measure(80, '%'))
        self.assertEqual('4 kg', format_measure(4, 'kg'))
        self.assertEqual(['빛의 영향', '수면 변화'], lines_for('빛의 영향 수면 변화', width=5))
        with self.assertRaisesRegex(ValueError, 'graphic_text_exceeds_role_bounds'):
            lines_for('띄어쓰기없는긴한글제목문자열', width=8)
        from hybrid_story.plugin import HybridStoryHarness
        case = cases()[0]
        case['hybrid']['diagram']['nodes'][0]['label'] = '띄어쓰기없는긴한글제목문자열'
        scene = SimpleNamespace(**case, layout={'hybrid':case['hybrid']}, transition='cut')
        self.assertTrue(any('graphic_typography:graphic_text_exceeds_role_bounds' in finding
                            for finding in HybridStoryHarness().validate_plan([scene], {})))

    def test_quantity_grounding_rejects_invented_value(self):
        case = cases()[0]
        case["hybrid"]["diagram"]["nodes"][0]["quantity"] = 21
        scene = SimpleNamespace(**case,layout={"hybrid":case["hybrid"]},transition="cut")
        self.assertIn("quantity_not_grounded",evaluate_hybrid([scene])[0])

    def test_accumulation_rejects_bad_scale_units_and_order(self):
        for alteration in ("scale", "unit", "order"):
            plan = cases()[1]["hybrid"]
            diagram = plan["diagram"]
            if alteration == "scale": diagram["comparison_scale_max"] = 5
            if alteration == "unit": diagram["nodes"][1]["unit"] = "분"
            if alteration == "order": diagram["nodes"][1]["change_at"] = .7
            with self.assertRaises(ValidationError): HybridScene.model_validate(plan)

    def test_sequence_rejects_reversed_connection(self):
        plan = cases()[2]["hybrid"]
        plan["diagram"]["edges"][0].update(source="item-1",target="item-0")
        with self.assertRaises(ValidationError): HybridScene.model_validate(plan)

    def test_repair_feedback_contains_specific_validator_reason(self):
        case = cases()[1]
        diagram = case["hybrid"]["diagram"]
        diagram["comparison_scale_max"] = 1
        scene = SimpleNamespace(**case, layout={"hybrid":case["hybrid"]}, transition="cut")
        findings = evaluate_hybrid([scene])
        self.assertTrue(any("accumulation_scale_or_units_mismatch" in f for f in findings))
        self.assertFalse(any("input_value" in f or "errors.pydantic.dev" in f for f in findings))

    def test_legacy_schema_excludes_new_grammar(self):
        base = json.loads((ROOT / "video-generator/schemas/scene-plan.schema.json").read_text())
        for version in ("hybrid-scene-0.1","hybrid-scene-0.2","hybrid-scene-0.3"):
            schema=hybrid_output_schema(base,{"hybrid_direction":hybrid_planning_extension(version)})
            self.assertEqual(version=="hybrid-scene-0.3", "source_quote" in schema["$defs"]["DiagramNode"]["properties"])
            self.assertEqual(version=="hybrid-scene-0.3", "cumulative_change" in schema["$defs"]["Diagram"]["properties"]["grammar"]["enum"])
        plan=cases()[1]["hybrid"]
        plan["version"]="hybrid-scene-0.2"
        with self.assertRaises(ValidationError): HybridScene.model_validate(plan)

    def test_insufficient_hold_is_not_silently_rendered(self):
        diagram=HybridScene.model_validate(cases()[1]["hybrid"]).diagram
        with self.assertRaisesRegex(ValueError,"reading_hold"): markup(diagram,0,2,0)

    def test_new_accumulation_uses_seconds_not_fraction_for_voice_spacing(self):
        from test_film_design import design
        data=cases()[1]['hybrid']; data.update(version='hybrid-scene-0.4',design=design())
        for i,node in enumerate(data['diagram']['nodes']):
            node.update(change_at=.2+i*.07,reveal_at=.05+i*.07,color=design()['palette']['accents'][i%2])
        contract=HybridScene.model_validate(data)
        markup(contract.diagram,0,30,0,contract.design)
        with self.assertRaisesRegex(ValueError,'voice_events_too_close'):
            markup(contract.diagram,0,5,0,contract.design)
        data.update(version='hybrid-scene-0.3',design=None)
        with self.assertRaisesRegex(ValidationError,'events_out_of_order'):
            HybridScene.model_validate(data)
