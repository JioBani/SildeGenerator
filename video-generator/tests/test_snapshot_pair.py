import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from pydantic import ValidationError
from app.harness_sdk.hybrid import HybridScene,evaluate_hybrid,hybrid_output_schema,hybrid_planning_extension
from app.harness_sdk.snapshot_pair import SnapshotPair
from app.harness_sdk.direction import direction_output_schema
from app.harness_sdk.locked_scene_design import locked_scene_schema,expand_locked_scene_proposal

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
sys.path.insert(0,str(ROOT/'harnesses/hybrid-story/src'))
from snapshot_pair_fixtures import cases
from hybrid_story.snapshot_diagram import markup
from review_voice_cues import align_quantity_events
from audit_numeric_motion import observe


class SnapshotPairTests(unittest.TestCase):
    def test_increase_decrease_and_unchanged_keep_same_entity(self):
        for case in cases():
            scene=SimpleNamespace(id='scene-001',transition='cut',narration=case['narration'],layout={'hybrid':case['hybrid']})
            self.assertEqual([],evaluate_hybrid([scene]))
            hybrid=HybridScene.model_validate(case['hybrid'])
            content,actions=markup(hybrid.diagram,0,15,0,hybrid.design)
            self.assertIn('snapshot-0-0',content); self.assertIn('snapshot-0-1',content)
            self.assertNotIn('marker-end',content)
            self.assertEqual(2,len(actions))

    def test_forged_values_units_identity_times_and_scale_rejected(self):
        for kind in ('value','unit','entity','metric','time','scale','negative','nan'):
            p=deepcopy(cases()[0]['hybrid']['diagram']['snapshot_pair'])
            if kind=='value': p['after']['value']=99
            if kind=='unit': p['unit']='kg'
            if kind=='entity': p['entity']='다른 배터리'
            if kind=='metric': p['metric']='온도'
            if kind=='time': p['after']['show_at']=p['before']['show_at']
            if kind=='scale': p['scale_max']=50
            if kind=='negative': p['before']['value']=-1
            if kind=='nan': p['before']['value']=float('nan')
            with self.subTest(kind=kind),self.assertRaises(ValidationError): SnapshotPair.model_validate(p)

    def test_forged_and_reversed_quotations_fail_narration_check(self):
        case=cases()[0]; pair=SnapshotPair.model_validate(case['hybrid']['diagram']['snapshot_pair'])
        self.assertTrue(pair.grounding_findings('unrelated narration'))
        self.assertTrue(pair.grounding_findings(pair.after.source_quote+pair.before.source_quote))

    def test_payload_and_legacy_boundary(self):
        for kind in ('legacy','edges','nodes','scale','palette','long_title','long_time'):
            payload=deepcopy(cases()[0]['hybrid'])
            if kind=='legacy': payload['version']='hybrid-scene-0.4'
            if kind=='edges': payload['diagram']['edges']=[{}]
            if kind=='nodes': payload['diagram']['nodes']=[{}]
            if kind=='scale': payload['diagram']['comparison_scale_max']=100
            if kind=='palette': payload['diagram']['snapshot_pair']['color']='#ffffff'
            if kind=='long_title': payload['diagram']['title']='가'*27
            if kind=='long_time': payload['diagram']['snapshot_pair']['before']['time_label']='가'*13
            with self.subTest(kind=kind),self.assertRaises(ValidationError): HybridScene.model_validate(payload)

    def test_versioned_schema_and_locked_director_slot(self):
        from test_locked_scene_design import LockedSceneTests
        fixture=LockedSceneTests(); fixture.setUp()
        fixture.analysis.beats[1].grammar='before_after'
        fixture.contract['hybrid_direction']=hybrid_planning_extension('hybrid-scene-0.5')
        base=json.loads((ROOT/'video-generator/schemas/scene-plan.schema.json').read_text())
        schema=locked_scene_schema(hybrid_output_schema(direction_output_schema(base,fixture.contract),fixture.contract),fixture.analysis)
        diagram=schema['$defs']['BeatDesign2']['properties']['layout']['properties']['hybrid']['properties']['diagram']
        self.assertEqual({'title','snapshot_pair'},set(diagram['properties']))
        fixture.wire['beat_designs']['beat-002']['layout']['hybrid']['diagram']={
            'title':'전후 비교','snapshot_pair':cases()[0]['hybrid']['diagram']['snapshot_pair']}
        expanded=expand_locked_scene_proposal(fixture.wire,fixture.analysis,fixture.concept,hybrid_version='hybrid-scene-0.5')
        result=expanded['sequences'][0]['scene_groups'][0]['scenes'][1]['layout']['hybrid']
        self.assertEqual('hybrid-scene-0.5',result['version'])
        self.assertEqual([],result['diagram']['nodes'])
        for version in ('hybrid-scene-0.1','hybrid-scene-0.2','hybrid-scene-0.3','hybrid-scene-0.4'):
            legacy=hybrid_output_schema(base,{'hybrid_direction':hybrid_planning_extension(version)})
            self.assertNotIn('snapshot_pair',legacy['$defs']['Diagram']['properties'])
            self.assertNotIn('before_after',legacy['$defs']['Diagram']['properties']['grammar']['enum'])

    def test_voice_alignment_and_short_hold(self):
        case=cases()[0]; d=case['hybrid']['diagram']; p=d['snapshot_pair']; original=deepcopy(p)
        words=[dict(start=case['narration'].index(p[n]['source_quote']),length=3,seconds=t) for n,t in [('before',2),('after',7)]]
        anchors=align_quantity_events(d,case['narration'],words,15)
        self.assertEqual([2,7],[a['seconds'] for a in anchors])
        self.assertEqual(original['before']['value'],p['before']['value'])
        hybrid=HybridScene.model_validate(case['hybrid'])
        with self.assertRaisesRegex(ValueError,'reading_hold'): markup(hybrid.diagram,0,1,0,hybrid.design)

    def frames(self):
        diagram=cases()[0]['hybrid']['diagram']; p=diagram['snapshot_pair']
        frames=np.zeros((240,360,640,3),dtype=np.uint8)
        color=[int(p['color'][i:i+2],16) for i in (1,3,5)]
        for j,name in enumerate(('before','after')):
            s=p[name]; x=270+j*380; height=200*s['value']/p['scale_max']
            frames[round(s['show_at']*240):,round((420-height)*.6):252,round(20+(x-65)*.6):round(20+(x+65)*.6)]=color
        return diagram,frames

    def test_pixel_auditor_rejects_frozen_reverse_and_wrong_quantity(self):
        diagram,frames=self.frames()
        self.assertEqual([],observe(frames,diagram,10)['findings'])
        for bad in (frames[::-1],np.repeat(frames[:1],240,axis=0),np.repeat(frames[-1:],240,axis=0)):
            self.assertTrue(observe(bad,diagram,10)['findings'])
        frames[200:,:,400:]=0
        self.assertTrue(observe(frames,diagram,10)['findings'])


class SnapshotPlannerIntegration(unittest.IsolatedAsyncioTestCase):
    async def test_real_core_expands_pair_and_preserves_quotes_with_mock_transport(self):
        import tempfile
        from unittest.mock import patch
        import httpx
        from app.planner import plan_with_codex
        from app.prompts import load_prompts
        from app.tracking import Tracker
        from app.engine.harness_loader import HarnessRegistry
        from app.harness_sdk.semantic_beats import RelatedScriptAnalysis,inspect_analysis
        from app.semantic_planning import analysis_units
        from test_semantic_planning import analysis_payload,proposal
        from test_locked_scene_design import wire_proposal
        from test_concept_planning import batch
        case=cases()[0]; script=case['narration']
        data=analysis_payload(); beat=data['beats'][1]
        beat.pop('cause_beat_numbers')
        beat.update(literal_content=script,relations=[],grammar='before_after')
        analysis=RelatedScriptAnalysis(version='semantic-beats-0.2',script_type='quantitative_comparison',
            central_idea='Compare two observations without claiming a cause',beats=[beat])
        h=HarnessRegistry(ROOT/'harnesses').load('hybrid-story')
        contract=h.instance.describe_planning_contract(h.config)
        # This test isolates legacy0.9 scene expansion;0.10 gate integration has its own tests.
        contract.pop('semantic_review',None)
        contract.pop('visible_text_review',None)
        contract.pop('preproduction_brief',None)
        from app.harness_sdk.concept_design import concept_extension
        contract['concept_selection']=concept_extension()
        contract['hybrid_direction']=hybrid_planning_extension('hybrid-scene-0.5')
        self.assertEqual([],inspect_analysis(analysis,script,contract))
        value=proposal(); group=value['sequences'][0]['scene_groups'][0]
        group['scenes']=group['scenes'][1:]
        scene=group['scenes'][0]
        scene['layout']['direction'].update(version='narrative-direction-0.2',cause_scene_number=None)
        scene['layout']['hybrid']=case['hybrid']
        # Wire ownership means empty generic nodes/edges are supplied by Core.
        value=wire_proposal(value)
        d=value['beat_designs']['beat-001']['layout']['hybrid']['diagram']
        for k in ('nodes','edges','comparison_scale_max'): d.pop(k)
        calls=[]
        def respond(request):
            body=json.loads(request.content); calls.append(body)
            self.assertIn('SnapshotPair',body['text']['format']['schema']['$defs'])
            response={'type':'response.completed','response':{'id':'snapshot-mock','status':'completed','usage':{},
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
                plan=await plan_with_codex(script,prompts,settings,tracker,work,harness_planning_contract=contract,
                    source_units_override=analysis_units(analysis),semantic_analysis_result=analysis,
                    selected_concept=batch().candidates[0],continuity_enabled=False,_repair_limit=0)
            self.assertEqual(1,len(calls))
            self.assertEqual(script,plan.scenes[0].narration)
            hybrid=plan.scenes[0].layout['hybrid']
            self.assertEqual('hybrid-scene-0.5',hybrid['version'])
            self.assertEqual(case['hybrid']['diagram']['snapshot_pair'],hybrid['diagram']['snapshot_pair'])


if __name__=='__main__': unittest.main()
