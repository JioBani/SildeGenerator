import json
import unittest
from copy import deepcopy
from app.harness_sdk.locked_scene_design import (
    locked_scene_extension, locked_scene_enabled, locked_scene_schema, expand_locked_scene_proposal)
from app.harness_sdk.direction import direction_output_schema
from app.harness_sdk.hybrid import hybrid_output_schema
from app.harness_sdk.concept_design import concept_extension
from app.harness_sdk.semantic_beats import RelatedScriptAnalysis, bind_and_check_beats
from app.plan_compiler import compile_scene_plan, structural_repair_findings
from app.semantic_planning import analysis_units
from test_semantic_planning import ROOT, SCRIPT, analysis_payload, proposal, contract
from test_concept_planning import batch


def wire_proposal(value):
    value=deepcopy(value); entries={}; counter=0
    for seq in value['sequences']:
        for group in seq['scene_groups']:
            keys=[]
            for scene in group.pop('scenes'):
                counter+=1; key=f'beat-{counter:03d}'; keys.append(key)
                scene.pop('source_unit_count'); scene.pop('transition')
                layout=scene['layout']; layout.pop('authored_design',None); layout.pop('visual_labels',None)
                layout['direction'].pop('version')
                hybrid=layout.pop('hybrid')
                if hybrid['route']!='cinematic': layout.pop('camera',None)
                if hybrid['diagram']:
                    diagram=hybrid['diagram']; grammar=diagram.pop('grammar')
                    layout['hybrid']={'diagram':diagram}
                    if grammar=='transport_track': layout['hybrid']['composition']=hybrid.get('composition')
                entries[key]=scene
            group['beat_ids']=keys
    value['beat_designs']=entries
    return value


class LockedSceneTests(unittest.TestCase):
    def setUp(self):
        data=analysis_payload(); data['version']='semantic-beats-0.2'
        for b in data['beats']: b.pop('cause_beat_numbers'); b['relations']=[]
        self.analysis=RelatedScriptAnalysis.model_validate(data)
        self.concept=batch().candidates[0]
        self.wire=wire_proposal(proposal())
        self.contract=contract('semantic-beats-0.2',film=True)
        self.contract.update(concept_selection=concept_extension(),locked_scene_design=locked_scene_extension())

    def schema(self):
        base=json.loads((ROOT/'video-generator/schemas/scene-plan.schema.json').read_text())
        return locked_scene_schema(hybrid_output_schema(direction_output_schema(base,self.contract),self.contract),self.analysis)

    def test_exact_meaning_design_and_legacy_compiler_without_loss(self):
        before=deepcopy(self.wire)
        expanded=expand_locked_scene_proposal(self.wire,self.analysis,self.concept)
        plan,repairs=compile_scene_plan(expanded,SCRIPT,analysis_units(self.analysis),continuity_enabled=False)
        self.assertEqual([],structural_repair_findings(repairs))
        self.assertEqual([],bind_and_check_beats(plan.scenes,self.analysis))
        self.assertEqual(SCRIPT,''.join(s.narration for s in plan.scenes))
        for scene in plan.scenes:
            self.assertEqual(self.concept.design.model_dump(mode='json'),scene.layout['hybrid']['design'])
        self.assertEqual(before,self.wire)

    def test_missing_extra_reordered_and_duplicate_slots_rejected(self):
        for mode in ('missing','extra','reversed','duplicate'):
            wire=deepcopy(self.wire)
            if mode=='missing': wire['beat_designs'].pop('beat-001')
            if mode=='extra': wire['beat_designs']['beat-003']={}
            if mode=='reversed': wire['sequences'][0]['scene_groups'][0]['beat_ids'].reverse()
            if mode=='duplicate': wire['sequences'][0]['scene_groups'][0]['beat_ids'][1]='beat-001'
            with self.assertRaises(ValueError): expand_locked_scene_proposal(wire,self.analysis,self.concept)

    def test_owned_fields_cannot_be_smuggled_back(self):
        for mode in ('count','transition','design','grammar','camera','semantic'):
            wire=deepcopy(self.wire); scene=wire['beat_designs']['beat-002']; layout=scene['layout']
            if mode=='count': scene['source_unit_count']=2
            if mode=='transition': scene['transition']='fade'
            if mode=='design': layout['hybrid']['design']={}
            if mode=='grammar': layout['hybrid']['diagram']['grammar']='transport_track'
            if mode=='camera': layout['camera']={'mode':'push'}
            if mode=='semantic': layout['semantic_beat']={}
            with self.assertRaises(ValueError): expand_locked_scene_proposal(wire,self.analysis,self.concept)

    def test_source_binding_comes_only_from_analysis(self):
        beat=self.analysis.beats[1]
        from app.harness_sdk.semantic_beats import EvidenceNeed
        beat.route='source'; beat.grammar=None
        beat.required_evidence=[EvidenceNeed(claim_quote=beat.literal_content,source_id='registered',acceptance_criteria=['Exact observation'])]
        self.wire['beat_designs']['beat-002']['layout'].pop('hybrid')
        expanded=expand_locked_scene_proposal(self.wire,self.analysis,self.concept)
        self.assertEqual('registered',expanded['sequences'][0]['scene_groups'][0]['scenes'][1]['layout']['hybrid']['source_id'])

    def test_schema_is_strict_and_cause_selection_is_grounded(self):
        schema=self.schema()
        self.assertNotIn('FilmDesign',schema['$defs'])
        self.assertEqual(['beat-001','beat-002'],schema['properties']['beat_designs']['required'])
        second=schema['$defs']['BeatDesign2']['properties']['layout']
        self.assertNotIn('camera',second['properties'])
        self.assertEqual([2],second['properties']['direction']['properties']['cause_scene_number']['anyOf'][1]['enum'])
        def walk(value):
            if isinstance(value,dict):
                if value.get('type')=='object':
                    self.assertFalse(value['additionalProperties'])
                    self.assertEqual(set(value['properties']),set(value['required']))
                for child in value.values(): walk(child)
            elif isinstance(value,list):
                for child in value: walk(child)
        walk(schema)

    def test_numeric_schema_forbids_edges_before_generation(self):
        self.analysis.beats[1].grammar='cumulative_change'
        diagram=self.schema()['$defs']['BeatDesign2']['properties']['layout']['properties']['hybrid']['properties']['diagram']
        self.assertNotIn('grammar',diagram['properties'])
        self.assertEqual(0,diagram['properties']['edges']['maxItems'])

    def test_opt_in_dependencies_and_legacy_default(self):
        self.assertFalse(locked_scene_enabled({}))
        self.assertTrue(locked_scene_enabled(self.contract))
        self.contract.pop('semantic_analysis')
        with self.assertRaisesRegex(ValueError,'requires_meaning'): locked_scene_enabled(self.contract)
