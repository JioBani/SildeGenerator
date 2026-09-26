import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import httpx
from pydantic import ValidationError
from app.harness_sdk.concept_design import (ConceptBatch, ConceptReview, CRITERIA, anonymous, digest,
    compare_concept_orders, validate_review, validate_batch, concept_extension, bind_selected_concept)
from app.harness_sdk.film_design import design_sha256
from test_film_design import design
from test_semantic_planning import analysis_payload, proposal, SCRIPT, ROOT, contract
from app.planner import create_plan
from app.prompts import load_prompts
from app.tracking import Tracker
from app.concept_planning import executable_design_context


def batch():
    candidates=[]
    for i in range(3):
        d=design(); d['concept_id']=f'candidate-{i}'
        candidates.append(dict(design=d,script_quote=SCRIPT[:10],
            viewer_journey=f'View obstacle then understand illumination approach {i}',
            visual_metaphor=f'Practical visibility as a visual motif approach {i}',
            world_description=f'Grounded streets with no invented outcome {i}',
            lighting_language=f'Practical light and darkness variation {i}',
            camera_language='Static cinematic stills and fixed diagrams, no articulated actors',
            motion_personality='Measured explanatory reveals followed by reading holds',
            shared_motifs=['Warm light retains its narrative meaning across route changes',
                           'Subject position maintains a consistent reading direction'],
            forbidden_variations=['Never invent a dilemma or a later arrival',
                                  'Do not modify authentic source pixels'],
            required_capabilities=['cinematic_still','editable_diagram','hold']))
    return ConceptBatch(version='film-concepts-0.1',candidates=candidates)


def verdict(preferred='A'):
    return dict(candidates=[dict(label=label,**{k:'PASS' for k in CRITERIA},script_quote=SCRIPT[:10],
        reason='Fixture only: proposed design is coherent with the supplied literal script.',repair_target=None) for label in 'ABC'],
        genuinely_distinct='PASS',distinctness_reason='Fixture only: three distinct staging concepts are represented.',
        preferred=[preferred],preference_reason='The fixture-selected concept best preserves the supplied experience.')


def reports():
    candidates=batch().candidates
    values=[]
    for number,order in enumerate(((0,1,2),(2,1,0))):
        values.append(dict(status='VALID_REVIEW',model='critic',evaluator_version='concept-review-0.1',
            script_sha256='script',context_sha256='context',response_id=f'response-{number}',
            candidate_hashes={label:digest(anonymous(candidates[i])) for label,i in zip('ABC',order)},
            verdict=verdict('A' if number==0 else 'C')))
    return values


class ConceptContractTests(unittest.TestCase):
    def test_capabilities_distinguish_marks_from_names(self):
        limits=executable_design_context()
        self.assertEqual({'cause_change_result','quantitative_comparison','transport_track',
                          'cumulative_change','step_sequence'},set(limits['diagram_marks']))
        self.assertIn('Fixed hold',limits['diagram_camera'])
        self.assertIn('No tables',limits['diagram_marks']['quantitative_comparison'])
        self.assertIn('corner brackets',limits['not_implemented'])
        limits['not_implemented'].clear()
        self.assertTrue(executable_design_context()['not_implemented'])

    def test_three_not_palette_only(self):
        value=batch().model_dump(mode='json')
        value['candidates'][1]=deepcopy(value['candidates'][0])
        value['candidates'][1]['design']['concept_id']='another-id'
        value['candidates'][1]['design']['palette']['accents'].reverse()
        with self.assertRaisesRegex(ValidationError,'more_than_palette'):
            ConceptBatch.model_validate(value)
        value['candidates'].pop()
        with self.assertRaises(ValidationError): ConceptBatch.model_validate(value)

    def test_grounding_and_anonymity(self):
        value=batch()
        self.assertEqual([],validate_batch(value,SCRIPT))
        self.assertNotIn('concept_id',json.dumps(anonymous(value.candidates[0])))
        value.candidates[0].script_quote='Not supplied in this script'
        self.assertIn('quote_not_grounded',validate_batch(value,SCRIPT)[0])

    def test_failed_or_unknown_cannot_win(self):
        for state in ('FAIL','UNKNOWN'):
            value=verdict(); value['candidates'][0]['executable']=state
            issues=validate_review(ConceptReview.model_validate(value),SCRIPT)
            self.assertIn('unpassed_concept_preferred',issues)
            self.assertIn('A:repair_target_missing',issues)

    def test_duplicate_labels_or_unread_distinctness_rejected(self):
        value=verdict(); value['candidates'][1]['label']='A'; value['genuinely_distinct']='UNKNOWN'
        issues=validate_review(ConceptReview.model_validate(value),SCRIPT)
        self.assertIn('concept_review_coverage_not_exact',issues)
        self.assertIn('indistinct_concepts_cannot_be_selected',issues)

    def test_counterbalanced_identity_not_position(self):
        first,second=reports()
        self.assertEqual('CONSISTENT_CONCEPT_SELECTION',compare_concept_orders(first,second,batch())['status'])
        second['verdict']['preferred']=['A']
        self.assertEqual('CONCEPT_ORDER_DISAGREEMENT',compare_concept_orders(first,second,batch())['status'])

    def test_losing_candidate_disagreement_is_quarantined_not_promoted(self):
        first,second=reports(); second['verdict']['candidates'][0]['source_integrity']='UNKNOWN'
        result=compare_concept_orders(first,second,batch())
        self.assertEqual('CONSISTENT_CONCEPT_SELECTION',result['status'])
        self.assertEqual([second['candidate_hashes']['A']],result['quarantined_sha256'])
        self.assertEqual(20,result['criteria_agreement']['matching'])

    def test_winner_disagreement_and_subthreshold_agreement_still_block(self):
        first,second=reports(); second['verdict']['candidates'][2]['executable']='UNKNOWN'
        self.assertEqual('CONCEPT_ORDER_DISAGREEMENT',compare_concept_orders(first,second,batch())['status'])
        first,second=reports()
        for key in CRITERIA[:3]: second['verdict']['candidates'][0][key]='UNKNOWN'
        self.assertEqual('CONCEPT_ORDER_DISAGREEMENT',compare_concept_orders(first,second,batch())['status'])

    def test_provenance_policy_and_candidate_mutation(self):
        first,second=reports(); second['response_id']=first['response_id']
        self.assertEqual('CONCEPT_REVIEW_PROVENANCE_INVALID',compare_concept_orders(first,second,batch())['status'])
        first,second=reports(); second['evaluator_version']='different'
        self.assertEqual('CONCEPT_REVIEW_POLICY_MISMATCH',compare_concept_orders(first,second,batch())['status'])
        first,second=reports(); changed=batch(); changed.candidates[0].design.typography.title_px=36
        self.assertEqual('CONCEPT_REVIEW_INPUT_MISMATCH',compare_concept_orders(first,second,changed)['status'])

    def test_selected_design_cannot_change_after_review(self):
        chosen=batch().candidates[0]
        scene=SimpleNamespace(id='scene-001',layout={'hybrid':{'design':chosen.design.model_dump(mode='json')}})
        self.assertEqual([],bind_selected_concept([scene],chosen))
        self.assertEqual(design_sha256(chosen.design),scene.layout['selected_concept']['design_sha256'])
        scene.layout['hybrid']['design']['typography']['title_px']=36
        self.assertEqual(['scene-001:selected_concept_design_changed'],bind_selected_concept([scene],chosen))

    def test_strict_output_schemas(self):
        def walk(value):
            if isinstance(value,dict):
                if value.get('type')=='object':
                    self.assertFalse(value['additionalProperties'])
                    self.assertEqual(set(value['properties']),set(value['required']))
                if 'const' in value: self.assertIn('type',value)
                for child in value.values(): walk(child)
            elif isinstance(value,list):
                for child in value: walk(child)
        walk(ConceptBatch.model_json_schema()); walk(ConceptReview.model_json_schema())


class ConceptPipelineTests(unittest.IsolatedAsyncioTestCase):
    async def run_case(self,mode):
        active=contract('semantic-beats-0.2',film=True)
        active['concept_selection']=concept_extension()
        if mode=='locked':
            from app.harness_sdk.locked_scene_design import locked_scene_extension
            active['locked_scene_design']=locked_scene_extension()
        calls=[]; counts={}
        def respond(request):
            body=json.loads(request.content); calls.append(body); name=body['text']['format']['name']
            counts[name]=counts.get(name,0)+1
            if name=='semantic_beats':
                value=analysis_payload(); value['version']='semantic-beats-0.2'
                for beat in value['beats']: beat.pop('cause_beat_numbers'); beat['relations']=[]
            elif name=='film_concepts':
                if mode=='unauthorized': return httpx.Response(401,json={'error':'offline fixture'})
                value=batch().model_dump(mode='json')
            elif name.startswith('concept_review_'):
                self.assertEqual([SCRIPT[:10].strip()],body['text']['format']['schema']['$defs']['ConceptJudgment']['properties']['script_quote']['enum'])
                self.assertIn('hybrid-design-capabilities-0.1',json.dumps(body))
                self.assertIn('diagram push/pull',json.dumps(body))
                value=verdict('A' if name.endswith('abc') or mode=='order_bias' else 'C')
                if mode=='unknown':
                    for c in value['candidates']: c.update(executable='UNKNOWN',repair_target='Establish executable capability evidence')
                    value['preferred']=[]
            else:
                value=proposal()
                for item in value['sequences'][0]['scene_groups'][0]['scenes']:
                    item['layout']['direction']['version']='narrative-direction-0.2'
                    hybrid=item['layout']['hybrid']
                    hybrid.update(version='hybrid-scene-0.4',design=batch().candidates[0].design.model_dump(mode='json'))
                    if mode=='drift_repair' and counts[name]==1:
                        hybrid['design']['typography']['title_px']=36
                    if hybrid['diagram']:
                        for i,n in enumerate(hybrid['diagram']['nodes']): n['color']=design()['palette']['accents'][i]
                if mode=='locked':
                    from test_locked_scene_design import wire_proposal
                    value=wire_proposal(value)
                    self.assertIn('beat_designs',body['text']['format']['schema']['properties'])
            response={'type':'response.completed','response':{'id':f'response-{len(calls)}','status':'completed','usage':{},
                'output':[{'content':[{'type':'output_text','text':json.dumps(value)}]}]}}
            return httpx.Response(200,text='event: response.completed\ndata: '+json.dumps(response)+'\n\n')
        settings=SimpleNamespace(runner_mode='live',schemas_dir=ROOT/'video-generator/schemas',codex_model='offline-generator',
            codex_reasoning_effort='low',codex_fast_mode=False,codex_read_timeout_seconds=10,codex_connect_timeout_seconds=2,
            subscription_base_url='http://offline.invalid')
        prompts,_=load_prompts(ROOT/'harnesses/hybrid-story/prompts')
        client=httpx.AsyncClient
        with tempfile.TemporaryDirectory() as temp:
            work=Path(temp); tracker=Tracker(work)
            with patch('app.planner.httpx.AsyncClient',side_effect=lambda **kw:client(transport=httpx.MockTransport(respond),**kw)):
                if mode in ('unauthorized','order_bias','unknown'):
                    with self.assertRaises((RuntimeError,ValueError)):
                        await create_plan(SCRIPT,prompts,settings,tracker,work,harness_planning_contract=active)
                    self.assertNotIn('scene_plan',counts)
                else:
                    plan=await create_plan(SCRIPT,prompts,settings,tracker,work,harness_planning_contract=active)
                    self.assertEqual(SCRIPT,''.join(s.narration for s in plan.scenes))
                    for s in plan.scenes:
                        self.assertEqual(digest(anonymous(batch().candidates[0])),s.layout['selected_concept']['sha256'])
                    self.assertIn('selected-film-concept.json',json.dumps(calls[-1]))
            result=json.loads((work/'concept-selection.json').read_text())
            self.assertEqual('PRE_RENDER_CONCEPT_SELECTED' if mode in ('ok','drift_repair','locked') else 'CONCEPT_SELECTION_INCOMPLETE',result['status'])
            self.assertEqual({'ok':5,'locked':5,'drift_repair':6,'order_bias':4,'unknown':4,'unauthorized':2}[mode],len(calls))
            self.assertFalse(any(u['stage'] in {'image_generation','voice_generation'} for u in tracker.usage))

    async def test_meaning_concepts_reviews_design_order(self): await self.run_case('ok')
    async def test_locked_slots_run_through_real_core_path(self): await self.run_case('locked')
    async def test_selected_design_drift_repairs_only_scene_plan(self): await self.run_case('drift_repair')
    async def test_order_bias_blocks_assets_and_scene_design(self): await self.run_case('order_bias')
    async def test_unknown_does_not_become_approval(self): await self.run_case('unknown')
    async def test_unauthorized_never_falls_back(self): await self.run_case('unauthorized')
