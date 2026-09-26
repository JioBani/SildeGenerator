import importlib
import subprocess
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from pydantic import ValidationError
from app.concept_planning import concept_context, concept_schema, design_scope_findings
from app.harness_sdk.concept_design import ConceptBatch, concept_extension, concept_enabled
from app.harness_sdk.film_design import FilmDesign, GraphicFilmDesign, DirectedGraphicFilmDesign, parse_design, design_sha256
from app.harness_sdk.hybrid import HybridScene
from app.harness_sdk.semantic_beats import RelatedScriptAnalysis
from app.engine.harness_loader import HarnessRegistry
from test_concept_planning import batch
from test_film_design import design
from test_semantic_planning import analysis_payload, ROOT
from test_snapshot_pair import cases


def context():
    b=analysis_payload()['beats'][1]; b.pop('cause_beat_numbers')
    b.update(grammar='before_after',relations=[])
    a=RelatedScriptAnalysis(version='semantic-beats-0.2',script_type='quantitative_comparison',
        central_idea='Compare two measurements, without inventing a cause',beats=[b])
    h=HarnessRegistry(ROOT/'harnesses').load('hybrid-story')
    return concept_context(a,h.instance.describe_planning_contract(h.config))


def graphic_batch():
    raw=batch().model_dump(mode='json')
    for c,layout in zip(raw['candidates'],('columns','rows','dot_tracks')):
        c['design'].update(version='film-design-0.2',snapshot_layout=layout)
        c['required_capabilities']=['editable_diagram','hold']
    return ConceptBatch.model_validate(raw)


class GraphicConceptTests(unittest.TestCase):
    def test_old_design_dump_hash_unchanged_and_new_hash_changes(self):
        old=FilmDesign.model_validate(design())
        self.assertEqual(old.model_dump(),parse_design(design()).model_dump())
        self.assertEqual(design_sha256(old),design_sha256(parse_design(design())))
        values=[c.design for c in graphic_batch().candidates]
        self.assertEqual(3,len({design_sha256(v) for v in values}))

    def test_route_scope_and_strict_schema(self):
        c=context()
        self.assertEqual([dict(beat_id='beat-001',route='diagram',grammar='before_after')],c['route_scope']['existing_beats'])
        schema=concept_schema(c)
        self.assertEqual({'$ref':'#/$defs/DirectedGraphicFilmDesign'},schema['$defs']['Concept']['properties']['design'])
        self.assertIn('graphic_design_required',','.join(design_scope_findings(graphic_batch(),c)))
        legacy_context=deepcopy(c)
        legacy_context['execution']['design_contract']='film-design-0.2'
        self.assertEqual([],design_scope_findings(graphic_batch(),legacy_context))
        legacy={'execution':{}}
        self.assertEqual([],design_scope_findings(batch(),legacy))
        self.assertTrue(design_scope_findings(graphic_batch(),legacy))

    def test_invented_stills_and_palette_only_variants_rejected(self):
        value=graphic_batch(); value.candidates[0].required_capabilities.append('cinematic_still')
        self.assertIn('candidate-0:capability_outside_accepted_routes',design_scope_findings(value,context()))
        value=graphic_batch(); value.candidates[1].design.snapshot_layout='columns'
        self.assertIn('snapshot_concepts_need_three_executable_layouts',design_scope_findings(value,context()))

    def test_comparison_layouts_are_executable_and_type_treatments_are_bounded(self):
        from test_semantic_diagrams import cases as semantic_cases
        markup=importlib.import_module('hybrid_story.semantic_diagrams').markup
        contract=HybridScene.model_validate(semantic_cases()[0]['hybrid'])
        outputs=[]
        for layout in ('rows','columns','dot_tracks'):
            value={**design(),'version':'film-design-0.3','snapshot_layout':'columns',
                   'comparison_layout':layout,'type_treatment':'documentary'}
            selected=DirectedGraphicFilmDesign.model_validate(value)
            content,actions=markup(contract.diagram,0,15,0,selected)
            self.assertIn('20분',content)
            self.assertIn('Noto Serif CJK KR',content)
            self.assertTrue(actions)
            outputs.append(content)
        self.assertEqual(3,len(set(outputs)))
        self.assertIn('attr:{y:',str(markup(contract.diagram,0,15,0,
            DirectedGraphicFilmDesign.model_validate({**value,'comparison_layout':'columns'}))[1]))
        with self.assertRaises(ValidationError):
            DirectedGraphicFilmDesign.model_validate({**value,'comparison_layout':'radial'})

    def test_quantitative_only_concepts_require_three_layouts(self):
        from app.harness_sdk.concept_design import ConceptBatch
        c=context()
        c['route_scope']['existing_beats'][0]['grammar']='quantitative_comparison'
        raw=graphic_batch().model_dump(mode='json')
        for candidate,layout in zip(raw['candidates'],('rows','columns','dot_tracks')):
            candidate['design'].update(version='film-design-0.3',comparison_layout=layout,
                                       type_treatment='explainer')
        selected=ConceptBatch.model_validate(raw)
        self.assertEqual([],design_scope_findings(selected,c))
        selected.candidates[1].design.comparison_layout='rows'
        self.assertIn('comparison_concepts_need_three_executable_layouts',design_scope_findings(selected,c))

    @unittest.skipUnless(Path('/app/hyperframes-runtime/node_modules/.bin/hyperframes').exists(), 'Pinned runtime required')
    def test_comparison_layouts_reach_distinct_rendered_pixels(self):
        from PIL import Image
        from hybrid_story.hybrid_renderer import compile_project
        from test_semantic_diagrams import cases as semantic_cases
        from app.tracking import sha256_file
        hashes=[]
        with tempfile.TemporaryDirectory() as folder:
            for layout in ('rows','columns','dot_tracks'):
                payload=semantic_cases()[0]['hybrid']
                payload['version']='hybrid-scene-0.6'
                payload['diagram']['snapshot_pair']=None
                payload['diagram']['spatial_map']=None
                payload['design']={**design(),'version':'film-design-0.3',
                    'snapshot_layout':'columns','comparison_layout':layout,
                    'type_treatment':'explainer'}
                accents=payload['design']['palette']['accents']
                for i,node in enumerate(payload['diagram']['nodes']): node['color']=accents[i%len(accents)]
                item=SimpleNamespace(id='comparison',layout={'hybrid':payload},duration_seconds=10)
                project=Path(folder)/layout
                compile_project([item],project,SimpleNamespace(width=1280,height=720,fps=24))
                subprocess.run(['/app/hyperframes-runtime/node_modules/.bin/hyperframes','snapshot',str(project),
                    '--at=9','--no-end','--describe=false'],check=True,capture_output=True,timeout=90)
                frame=next((project/'snapshots').glob('frame-*.png'))
                with Image.open(frame) as image:
                    self.assertEqual((1280,720),image.size)
                    self.assertGreater(len(image.getcolors(maxcolors=1280*720) or []),10)
                hashes.append(sha256_file(frame))
        self.assertEqual(3,len(set(hashes)))

    def test_version_and_arbitrary_geometry_rejected(self):
        h=cases()[0]['hybrid']; h['design']=graphic_batch().candidates[0].design.model_dump()
        with self.assertRaisesRegex(ValidationError,'graphic_design_requires_scene_version_06'):
            HybridScene.model_validate(h)
        h['version']='hybrid-scene-0.6'
        self.assertEqual('columns',HybridScene.model_validate(h).design.snapshot_layout)
        h['design']['snapshot_layout']='invented_table'
        with self.assertRaises(ValidationError): HybridScene.model_validate(h)
        with self.assertRaisesRegex(ValueError,'scene_version_06'):
            concept_enabled(dict(concept_selection=concept_extension(graphic_design=True),hybrid_direction={'version':'hybrid-scene-0.5'}))

    def test_three_actual_geometries_share_values_scale_and_time(self):
        HarnessRegistry(ROOT/'harnesses').load('hybrid-story')
        markup=importlib.import_module('hybrid_story.snapshot_diagram').markup
        h=cases()[0]['hybrid']; old=HybridScene.model_validate(h)
        legacy_html,legacy_actions=markup(old.diagram,0,20,0,old.design)
        outputs=[]
        for layout in ('columns','rows','dot_tracks'):
            d=GraphicFilmDesign(**{**design(),'version':'film-design-0.2','snapshot_layout':layout})
            html,actions=markup(old.diagram,0,20,0,d)
            self.assertEqual(legacy_actions,actions)
            self.assertIn('80%',html); self.assertIn('35%',html)
            self.assertNotIn('marker-end',html)
            outputs.append(html)
        self.assertEqual(legacy_html,outputs[0])
        self.assertEqual(3,len(set(outputs)))
        self.assertIn('width="448.0"',outputs[1])
        self.assertIn('cx="668.0"',outputs[2])
        self.assertIn('cx="416.0"',outputs[2])


if __name__=='__main__': unittest.main()
