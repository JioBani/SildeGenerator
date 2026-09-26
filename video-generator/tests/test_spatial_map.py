import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from pydantic import ValidationError
from app.harness_sdk.hybrid import HybridScene,evaluate_hybrid,hybrid_output_schema,hybrid_planning_extension
from app.harness_sdk.spatial_map import SpatialMap,direct_relation_quote
from app.harness_sdk.direction import direction_output_schema
from app.harness_sdk.locked_scene_design import locked_scene_schema,expand_locked_scene_proposal

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
sys.path.insert(0,str(ROOT/'harnesses/hybrid-story/src'))
from spatial_map_fixtures import cases
from review_voice_cues import align_spatial_events
from hybrid_story.spatial_diagram import markup


class SpatialTests(unittest.TestCase):
    def test_three_domains_grounded_geometry_and_fixed_markers(self):
        for case in cases():
            scene=SimpleNamespace(id='scene-001',transition='cut',narration=case['narration'],layout={'hybrid':case['hybrid']})
            self.assertEqual([],evaluate_hybrid([scene]))
            hybrid=HybridScene.model_validate(case['hybrid'])
            content,actions=markup(hybrid.diagram,0,20,0,hybrid.design)
            self.assertIn('거리 비례 아님',content)
            self.assertNotIn('marker-end',content)
            self.assertNotIn('attr:',str(actions))
            self.assertIn('spatial-relation-0-1',content)

    def test_reversed_axes_overlap_unexplained_or_unreferenced_fail(self):
        for kind in ('horizontal','vertical','overlap','extra','missing','nan','late_referent','duplicate'):
            value=deepcopy(cases()[0]['hybrid']['diagram']['spatial_map'])
            if kind=='horizontal':
                for p in value['places']: p['x']=1-p['x']
            if kind=='vertical':
                for p in value['places']: p['y']=.94-p['y']
            if kind=='overlap': value['places'][2].update(x=.23,y=.17)
            if kind=='extra': value['places'].append(dict(id='unused',label='별관',x=.78,y=.78,reveal_at=0,color='#ffffff'))
            if kind=='missing': value['relations'][0]['subject']='missing'
            if kind=='nan': value['places'][0]['x']=float('nan')
            if kind=='late_referent': value['places'][0]['reveal_at']=.5
            if kind=='duplicate': value['places'][1]['label']=value['places'][0]['label']
            with self.subTest(kind=kind),self.assertRaises(ValidationError): SpatialMap.model_validate(value)

    def test_region_boundary_header_and_wrong_membership_fail(self):
        for kind in ('outside','inside','border','header','overlap'):
            value=deepcopy(cases()[2]['hybrid']['diagram']['spatial_map'])
            if kind=='outside': value['relations'][0]['relation']='outside'
            if kind=='inside': value['relations'][1]['relation']='inside'
            if kind=='border': value['places'][0]['x']=.57
            if kind=='header': value['places'][0]['y']=.15
            if kind=='overlap': value['regions'].append(dict(id='r2',label='두번째영역',left=.05,top=.05,right=.7,bottom=.9,reveal_at=0))
            with self.subTest(kind=kind),self.assertRaises(ValidationError): SpatialMap.model_validate(value)

    def test_exact_quotes_and_order_and_names(self):
        case=cases()[0]; spatial=SpatialMap.model_validate(case['hybrid']['diagram']['spatial_map'])
        self.assertTrue(spatial.grounding_findings('unrelated'))
        self.assertTrue(spatial.grounding_findings(' '.join(r.source_quote for r in reversed(spatial.relations))))
        spatial.relations[0].source_quote='가상의 배치를 설명합니다.'
        self.assertTrue(spatial.grounding_findings(case['narration']))

    def test_predicate_is_grounded_not_just_mentioned_names(self):
        self.assertTrue(direct_relation_quote('연못은 정문의 북쪽에 있습니다.','연못','정문','north_of'))
        self.assertTrue(direct_relation_quote('Lake is north of Gate.','Lake','Gate','north_of'))
        for quote in ('연못은 정문의 남쪽에 있습니다.','정문은 연못의 북쪽에 있습니다.','연못은 정문의 북쪽에 없습니다.','연못은 정문의 북쪽에 있다고 가정합니다.'):
            self.assertFalse(direct_relation_quote(quote,'연못','정문','north_of'))

    def test_version_palette_payload_and_reading_hold(self):
        for kind in ('legacy','color','quantity','edges'):
            value=deepcopy(cases()[0]['hybrid'])
            if kind=='legacy': value['version']='hybrid-scene-0.5'
            if kind=='color': value['diagram']['spatial_map']['places'][0]['color']='#ffffff'
            if kind=='quantity': value['diagram']['comparison_scale_max']=100
            if kind=='edges': value['diagram']['edges']=[{}]
            with self.subTest(kind=kind),self.assertRaises(ValidationError): HybridScene.model_validate(value)
        hybrid=HybridScene.model_validate(cases()[0]['hybrid'])
        with self.assertRaisesRegex(ValueError,'reading_hold'): markup(hybrid.diagram,0,1,0,hybrid.design)

    def test_schema_legacy_and_locked_slot(self):
        from test_locked_scene_design import LockedSceneTests
        fixture=LockedSceneTests(); fixture.setUp()
        fixture.analysis.beats[1].grammar='map_spatial'
        fixture.contract['hybrid_direction']=hybrid_planning_extension('hybrid-scene-0.6')
        base=json.loads((ROOT/'video-generator/schemas/scene-plan.schema.json').read_text())
        schema=locked_scene_schema(hybrid_output_schema(direction_output_schema(base,fixture.contract),fixture.contract),fixture.analysis)
        diagram=schema['$defs']['BeatDesign2']['properties']['layout']['properties']['hybrid']['properties']['diagram']
        self.assertEqual({'title','spatial_map'},set(diagram['properties']))
        fixture.wire['beat_designs']['beat-002']['layout']['hybrid']['diagram']={'title':'상대 위치','spatial_map':cases()[0]['hybrid']['diagram']['spatial_map']}
        expanded=expand_locked_scene_proposal(fixture.wire,fixture.analysis,fixture.concept,hybrid_version='hybrid-scene-0.6')
        actual=expanded['sequences'][0]['scene_groups'][0]['scenes'][1]['layout']['hybrid']['diagram']
        self.assertEqual('map_spatial',actual['grammar'])
        self.assertEqual([],actual['nodes'])
        for version in ('hybrid-scene-0.1','hybrid-scene-0.2','hybrid-scene-0.3','hybrid-scene-0.4','hybrid-scene-0.5'):
            legacy=hybrid_output_schema(base,{'hybrid_direction':hybrid_planning_extension(version)})
            self.assertNotIn('SpatialMap',legacy['$defs'])
            self.assertNotIn('spatial_map',legacy['$defs']['Diagram']['properties'])
            self.assertNotIn('map_spatial',legacy['$defs']['Diagram']['properties']['grammar']['enum'])

    def test_voice_events_preserve_coordinates(self):
        case=cases()[0]; diagram=case['hybrid']['diagram']; spatial=diagram['spatial_map']
        before=[(p['x'],p['y']) for p in spatial['places']]
        words=[dict(start=case['narration'].index(r['source_quote']),length=3,seconds=t) for r,t in zip(spatial['relations'],[3,8])]
        result=align_spatial_events(diagram,case['narration'],words,18)
        self.assertEqual([3,8],[a['seconds'] for a in result])
        self.assertEqual(before,[(p['x'],p['y']) for p in spatial['places']])
        SpatialMap.model_validate(spatial)

    def test_voice_alignment_refuses_missing_ambiguous_and_unmeasured(self):
        for kind in ('missing','ambiguous','duration'):
            case=cases()[0]; script=case['narration']; d=case['hybrid']['diagram']
            if kind=='ambiguous': script+=' '+d['spatial_map']['relations'][0]['source_quote']
            with self.subTest(kind=kind),self.assertRaises(ValueError):
                align_spatial_events(d,script,[],0 if kind=='duration' else 18)

    def test_current_planning_contract_is_bounded_and_names_capability(self):
        from app.engine.harness_loader import HarnessRegistry
        from app.engine.harness_preflight import planning_contract
        h=HarnessRegistry(ROOT/'harnesses').load('hybrid-story')
        contract=planning_contract(h)
        self.assertEqual('hybrid-scene-0.6',contract['hybrid_direction']['version'])
        self.assertIn('map_spatial',contract['hybrid_direction']['grammars'])
        self.assertLessEqual(len(json.dumps(contract,ensure_ascii=False)),12000)
