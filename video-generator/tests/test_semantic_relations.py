import hashlib
import json
import unittest
from copy import deepcopy
from types import SimpleNamespace

from pydantic import ValidationError
from app.harness_sdk.semantic_beats import RelatedScriptAnalysis, ScriptAnalysis, inspect_analysis, analysis_sha256, bind_and_check_beats
from app.harness_sdk.direction import evaluate_direction
from app.semantic_planning import analysis_schema
from app.semantic_review import review_packet, packet_errors
from test_semantic_planning import analysis_payload, PARTS, SCRIPT, contract
from test_narrative_direction import shot


def typed_payload():
    value=analysis_payload()
    value["version"]="semantic-beats-0.2"
    for beat in value["beats"]:
        beat.pop("cause_beat_numbers")
        beat["relations"]=[]
    value["beats"][1]["relations"]=[dict(from_beat_number=1,kind="context",source_quote=PARTS[0].strip(),
        target_quote=PARTS[1],grounding="explicit",explanation="A hesitant traveller provides context for illumination, not its physical cause.")]
    return value


class GroundedRelationsTests(unittest.TestCase):
    def test_legacy_hash_and_parsing_are_preserved(self):
        value=analysis_payload()
        old_order=["literal_content","story_function","information_function","viewer_state_before","viewer_state_after","primary_purpose",
            "route","route_reason","rejected_routes","new_information","emotional_change","cause_beat_numbers","research_need","required_evidence",
            "grammar","transition_to_next","confidence"]
        for i,b in enumerate(value["beats"]): value["beats"][i]={k:b[k] for k in old_order}
        expected=hashlib.sha256(json.dumps(value,ensure_ascii=False,separators=(",", ":")).encode()).hexdigest()
        model=ScriptAnalysis.model_validate(value)
        self.assertEqual(expected,analysis_sha256(model))
        self.assertIn("cause_beat_numbers",review_packet(model)["beats"][1])
        self.assertNotIn("relations",review_packet(model)["beats"][1])

    def test_typed_context_has_grounded_endpoints_not_a_cause(self):
        model=RelatedScriptAnalysis.model_validate(typed_payload())
        self.assertEqual([],inspect_analysis(model,SCRIPT,contract("semantic-beats-0.2")))
        packet=review_packet(model)
        self.assertEqual([],packet_errors(packet,SCRIPT))
        self.assertNotIn("cause_beat_numbers",packet["beats"][1])
        self.assertEqual("context",packet["beats"][1]["relations"][0]["kind"])

    def test_future_wrong_quotes_and_duplicate_relations_fail(self):
        for change,expected in (("future","relation_not_earlier"),("source","relation_source_quote_not_grounded"),
                ("target","relation_target_quote_not_grounded"),("duplicate","duplicate_or_conflicting_relation")):
            value=typed_payload(); relations=value["beats"][1]["relations"]; link=relations[0]
            if change=="future": link["from_beat_number"]=2
            if change=="source": link["source_quote"]="Invented cause"
            if change=="target": link["target_quote"]="Invented result"
            if change=="duplicate": relations.append(dict(link,kind="event_cause"))
            self.assertIn("beat-002:"+expected,inspect_analysis(RelatedScriptAnalysis.model_validate(value),SCRIPT,contract("semantic-beats-0.2")))

    def test_unknown_kind_boolean_number_and_v1_upgrade_are_rejected(self):
        for key,value in (("kind","correlation_is_cause"),("from_beat_number",True)):
            data=typed_payload(); data["beats"][1]["relations"][0][key]=value
            with self.assertRaises(ValidationError): RelatedScriptAnalysis.model_validate(data)
        with self.assertRaises(ValidationError): RelatedScriptAnalysis.model_validate(analysis_payload())

    def test_scene_cannot_promote_context_to_cause(self):
        model=RelatedScriptAnalysis.model_validate(typed_payload())
        scenes=[SimpleNamespace(id=f"scene-{i:03d}",source_unit_ids=[f"unit-{i:03d}"],narration=b.literal_content,
            layout={"hybrid":{"route":b.route,"diagram":{"grammar":b.grammar}},"direction":{"cause_scene_number":None}})
            for i,b in enumerate(model.beats,1)]
        self.assertEqual([],bind_and_check_beats(scenes,model))
        scenes[1].layout["direction"]["cause_scene_number"]=1
        self.assertIn("scene-002:context_promoted_to_cause",bind_and_check_beats(scenes,model))

    def test_schema_all_properties_required_and_no_generic_cause_field(self):
        schema=analysis_schema("semantic-beats-0.2")
        self.assertNotIn('"cause_beat_numbers"',json.dumps(schema))
        def walk(value):
            if isinstance(value,dict):
                if value.get("type")=="object":
                    self.assertFalse(value["additionalProperties"])
                    self.assertEqual(set(value["properties"]),set(value["required"]))
                for child in value.values(): walk(child)
            elif isinstance(value,list):
                for child in value: walk(child)
        walk(schema)

    def test_factual_quotation_does_not_claim_semantic_truth(self):
        data=typed_payload()
        data["beats"][1]["relations"][0]["kind"]="event_cause"
        # The relation is semantically dubious but structurally grounded: independent critic must reject it.
        self.assertEqual([],inspect_analysis(RelatedScriptAnalysis.model_validate(data),SCRIPT,contract("semantic-beats-0.2")))


class NoInventedDilemmaTests(unittest.TestCase):
    def test_character_action_does_not_require_dilemma_in_v2(self):
        value=shot(); value.update(version="narrative-direction-0.2",mode="character_story",beat="action",choices=[])
        scene=SimpleNamespace(id="scene-001",layout={"direction":value})
        self.assertEqual([],evaluate_direction([scene],expected_version="narrative-direction-0.2")["findings"])
        value["version"]="narrative-direction-0.1"
        self.assertTrue(any("character_choice_missing" in f for f in evaluate_direction([scene])["findings"]))

    def test_new_contract_rejects_old_version_response(self):
        scene=SimpleNamespace(id="scene-001",layout={"direction":shot()})
        self.assertIn("scene-001:direction_version_mismatch",evaluate_direction([scene],expected_version="narrative-direction-0.2")["findings"])
