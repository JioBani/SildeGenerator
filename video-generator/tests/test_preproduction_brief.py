import hashlib
from copy import deepcopy
from types import SimpleNamespace
import unittest

from app.concept_planning import concept_context
from app.engine.harness_loader import HarnessRegistry
from app.harness_sdk.semantic_beats import EvidenceNeed, RelatedScriptAnalysis
from app.preproduction_brief import compile_preproduction_brief, require_matching_concept_brief, scene_brief_findings
from app.semantic_review import digest
from test_semantic_planning import ROOT, analysis_payload


def fixture():
    loaded = HarnessRegistry(ROOT / 'harnesses').load('hybrid-story')
    contract = loaded.instance.describe_planning_contract(loaded.config)
    data = analysis_payload()
    data['version'] = 'semantic-beats-0.2'
    for beat in data['beats']:
        beat.pop('cause_beat_numbers')
        beat['relations'] = []
    return RelatedScriptAnalysis.model_validate(data), contract


class PreproductionBriefTests(unittest.TestCase):
    def test_mixed_beat_brief_reaches_concept_context(self):
        analysis, contract = fixture()
        brief = compile_preproduction_brief(analysis, contract)
        self.assertEqual(brief, concept_context(analysis, contract)['preproduction_brief'])
        self.assertEqual(['cinematic_still', 'editable_diagram'],
                         [b['execution']['route'] for b in brief['beats']])
        self.assertEqual('cause_change_result', brief['beats'][1]['grammar'])
        self.assertIn('change_affected_target', brief['beats'][1]['execution']['required_visual_events'])
        self.assertEqual(hashlib.sha256(analysis.beats[1].literal_content.encode()).hexdigest(),
                         brief['beats'][1]['source_sha256'])
        self.assertEqual('STRUCTURAL_ONLY', brief['approval'])
        self.assertEqual('preproduction-brief-0.3', brief['version'])
        self.assertEqual('NO_RESEARCH_REQUESTED', brief['research_status'])
        self.assertEqual(brief['beats'][1]['viewer_change']['to'],
                         brief['beats'][1]['scene_design']['viewer_end'])
        self.assertIn('change_affected_target', brief['beats'][1]['scene_design']['visual_events'])
        self.assertEqual('NO_RESEARCH_TASK', brief['beats'][1]['scene_design']['evidence_status'])

    def test_research_need_is_a_grounded_task_not_false_source_approval(self):
        analysis, contract = fixture()
        beat = analysis.beats[1]
        beat.research_need = 'historical'
        brief = compile_preproduction_brief(analysis, contract)
        task = brief['research_tasks'][0]
        self.assertEqual(beat.literal_content, task['source_excerpt'])
        self.assertEqual('DISCOVERY_REQUIRED', task['status'])
        self.assertFalse(task['fact_verified'])
        self.assertEqual([],task['candidate_records'])
        self.assertEqual('NOT_APPLICABLE_UNTIL_MEDIA_SELECTED', task['rights_review'])
        self.assertEqual('fact', task['needed_for'])
        self.assertIn(beat.literal_content.strip(), task['research_question'])
        self.assertTrue(task['preferred_primary_sources'])
        self.assertEqual(task['beat_id'], brief['beats'][1]['research_task_id'])
        self.assertEqual(beat.transition_to_next, brief['beats'][1]['transition_intent'])
        self.assertEqual('RESEARCH_PENDING',brief['beats'][1]['scene_design']['evidence_status'])

    def test_legacy_brief_does_not_gain_new_fields(self):
        from app.harness_sdk.preproduction import preproduction_extension
        analysis, contract = fixture()
        contract['preproduction_brief'] = preproduction_extension()
        brief = compile_preproduction_brief(analysis, contract)
        self.assertEqual('preproduction-brief-0.1', brief['version'])
        self.assertNotIn('research_tasks', brief)

    def test_missing_capability_and_unregistered_source_stop_before_design(self):
        analysis, contract = fixture()
        analysis.beats[1].grammar = 'whole_detail'
        with self.assertRaisesRegex(ValueError, 'diagram_grammar_not_executable'):
            compile_preproduction_brief(analysis, contract)
        analysis, contract = fixture()
        analysis.beats[1].route = 'source'
        analysis.beats[1].primary_purpose = 'verify'
        analysis.beats[1].grammar = None
        analysis.beats[1].required_evidence = [EvidenceNeed(claim_quote=analysis.beats[1].literal_content,
            source_id='unregistered', acceptance_criteria=['Verify observation'])]
        with self.assertRaisesRegex(ValueError, 'source_not_registered'):
            compile_preproduction_brief(analysis, contract)

    def test_registered_source_keeps_claim_and_meaning_limit(self):
        analysis, contract = fixture()
        beat = analysis.beats[1]
        beat.route = 'source'
        beat.primary_purpose = 'verify'
        beat.grammar = None
        beat.required_evidence = [EvidenceNeed(claim_quote=beat.literal_content,
            source_id='observation', acceptance_criteria=['Shows the observation'])]
        contract['trusted_source_catalog'] = [{'id':'observation',
            'meaning_limit':'A modern observation, not an image of the fictional event',
            'attribution':'Test archive'}]
        item = compile_preproduction_brief(analysis, contract)['beats'][1]['execution']
        self.assertEqual('observation',item['source_id'])
        self.assertEqual([beat.literal_content],item['claims'])
        self.assertIn('not an image',item['catalog_entry']['meaning_limit'])
        task = compile_preproduction_brief(analysis, contract)['research_tasks'][0]
        self.assertEqual('source', task['needed_for'])
        self.assertEqual('REGISTERED_CANDIDATE', task['status'])
        self.assertEqual([{'id':'observation','meaning_limit':
            'A modern observation, not an image of the fictional event'}],task['candidate_records'])
        self.assertEqual('REQUIRED_BEFORE_VIDEO_USE', task['rights_review'])
        self.assertFalse(task['fact_verified'])

    def test_concept_and_scene_must_share_the_same_brief(self):
        analysis, contract = fixture()
        brief = compile_preproduction_brief(analysis, contract)
        selection = {'status':'PRE_RENDER_CONCEPT_SELECTED',
                     'preproduction_brief_sha256':digest(brief)}
        require_matching_concept_brief(selection, brief)
        changed = deepcopy(brief)
        changed['source_catalog_sha256'] = 'changed'
        with self.assertRaisesRegex(ValueError,'preproduction_concept_brief_mismatch'):
            require_matching_concept_brief(selection, changed)

    def test_causal_diagram_must_visibly_change_affected_object(self):
        analysis, contract = fixture()
        brief = compile_preproduction_brief(analysis, contract)
        scenes = [SimpleNamespace(id='scene-1', layout={'hybrid': {'route': 'cinematic'}}),
                  SimpleNamespace(id='scene-2', layout={'hybrid': {'route': 'diagram', 'diagram': {
                      'grammar': 'cause_change_result',
                      'nodes': [{'id': 'cause', 'before': 'off', 'after': 'on'},
                                {'id': 'effect', 'before': 'dark', 'after': 'dark'}],
                      'edges': [{'source': 'cause', 'target': 'effect'}]}}})]
        self.assertEqual(['scene-2:cause_target_has_no_visible_change'],scene_brief_findings(scenes,brief))
        scenes[1].layout['hybrid']['diagram']['nodes'][1]['after']='bright'
        self.assertEqual([],scene_brief_findings(scenes,brief))
        drift=deepcopy(scenes)
        drift[1].layout['hybrid']['diagram']['grammar']='step_sequence'
        self.assertIn('scene-2:preproduction_grammar_drift',scene_brief_findings(drift,brief))


if __name__ == '__main__': unittest.main()
