import importlib
import json
import subprocess
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from PIL import Image
from pydantic import ValidationError
from app.harness_sdk.film_design import FilmDesign, contrast, design_sha256, shared_design
from app.harness_sdk.hybrid import HybridScene, evaluate_hybrid, hybrid_output_schema, hybrid_planning_extension
from app.engine.harness_loader import HarnessRegistry
from test_hybrid_story import ROOT, route


def design():
    return json.loads((ROOT/'experiments/meaning-planning-v1/film-design-candidate.json').read_text())


def scene(kind='cinematic'):
    payload = route(kind)
    payload.update(version='hybrid-scene-0.4', design=design())
    if payload['diagram']:
        for i, node in enumerate(payload['diagram']['nodes']):
            node['color'] = design()['palette']['accents'][i]
    return SimpleNamespace(id='scene-001', layout={'hybrid': payload}, transition='cut',
        narration='A development fixture', duration_seconds=6)


class FilmDesignTests(unittest.TestCase):
    def test_palette_contrast_and_hash_are_deterministic(self):
        item = FilmDesign.model_validate(design())
        self.assertEqual(21, contrast('#ffffff', '#000000'))
        self.assertEqual(design_sha256(item), design_sha256(FilmDesign.model_validate(design())))

    def test_bad_text_graphic_duplicate_and_css_injection_rejected(self):
        for kind in ('text', 'line', 'duplicate', 'css'):
            item = design()
            if kind == 'text': item['palette']['text'] = item['palette']['background']
            if kind == 'line': item['palette']['line'] = item['palette']['background']
            if kind == 'duplicate': item['palette']['accents'][1] = item['palette']['accents'][0]
            if kind == 'css': item['palette']['background'] = 'red;display:none'
            with self.assertRaises(ValidationError): FilmDesign.model_validate(item)

    def test_required_version_and_off_palette_marks(self):
        item = scene('diagram')
        self.assertEqual([], evaluate_hybrid([item], expected_version='hybrid-scene-0.4'))
        item.layout['hybrid']['diagram']['nodes'][0]['color'] = '#ffffff'
        with self.assertRaisesRegex(ValidationError, 'outside_film_palette'):
            HybridScene.model_validate(item.layout['hybrid'])
        item = scene()
        item.layout['hybrid']['design'] = None
        with self.assertRaisesRegex(ValidationError, 'requires_scene_version'):
            HybridScene.model_validate(item.layout['hybrid'])
        item.layout['hybrid']['version'] = 'hybrid-scene-0.3'
        self.assertIn('scene-001:hybrid_contract_version_mismatch',
            evaluate_hybrid([item], expected_version='hybrid-scene-0.4'))

    def test_all_routes_share_the_same_design_not_only_id(self):
        items = [scene(kind) for kind in ('cinematic','diagram','source')]
        self.assertIsNotNone(shared_design(items))
        items[-1].layout['hybrid']['design']['typography']['title_px'] = 36
        self.assertIn('film_design_invalid_or_inconsistent', evaluate_hybrid(items))
        items[-1].layout['hybrid'] = route('source')
        self.assertIn('film_design_invalid_or_inconsistent', evaluate_hybrid(items))

    def test_new_schema_strict_and_old_schema_unchanged(self):
        base = json.loads((ROOT/'video-generator/schemas/scene-plan.schema.json').read_text())
        for version in ('hybrid-scene-0.1', 'hybrid-scene-0.3', 'hybrid-scene-0.4'):
            result = hybrid_output_schema(base, {'hybrid_direction': hybrid_planning_extension(version)})
            self.assertEqual(version.endswith('0.4'), 'design' in result['$defs']['HybridScene']['properties'])
            if version.endswith('0.4'):
                for key in ('HybridScene', 'FilmDesign', 'FilmTypography', 'FilmPalette'):
                    schema = result['$defs'][key]
                    self.assertEqual(set(schema['properties']), set(schema['required']))
                    self.assertFalse(schema['additionalProperties'])

    def test_subtitles_share_opaque_surface_and_source_not_double_labeled(self):
        HarnessRegistry(ROOT/'harnesses').load('hybrid-story')
        media = importlib.import_module('hybrid_story.effects.media')
        item = scene('source'); item.layout['genre_id'] = 'documentary'
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)/'captions.ass'
            media.write_subtitles([item], output, SimpleNamespace(width=1280,height=720), {})
            text = output.read_text(encoding='utf-8-sig')
            self.assertIn('&H00E5F0F2',text)
            self.assertIn('&H00323629',text)
            self.assertIn(',3,8,0,2,100,100,48,1',text)
            self.assertNotIn('Dialogue: 1',text)

    def test_image_prompt_receives_shared_design_and_local_route_fails(self):
        from app.image_prompts import scene_image_prompt
        from app.prompts import load_prompts
        from app.plan_compiler import compile_scene_plan
        # Use an existing validated plan fixture rather than guessing Scene fields.
        from test_semantic_planning import proposal
        from app.planner import compile_source_units
        script = 'One sentence. Another sentence.'
        plan, _ = compile_scene_plan(proposal(), script, compile_source_units(script), continuity_enabled=False)
        item = plan.scenes[0]
        item.layout['hybrid'] = scene().layout['hybrid']
        prompts,_ = load_prompts(ROOT/'harnesses/hybrid-story/prompts')
        rendered = scene_image_prompt(item, [], prompts)
        self.assertIn(design_sha256(FilmDesign.model_validate(design())), rendered)
        item.layout['hybrid'] = scene('diagram').layout['hybrid']
        with self.assertRaisesRegex(ValueError,'must_not_call_image_provider'):
            scene_image_prompt(item, [], prompts)


@unittest.skipUnless(Path('/app/hyperframes-runtime/node_modules/.bin/hyperframes').exists(), 'Pinned runtime required')
class FilmDesignPixels(unittest.TestCase):
    def test_comparison_accumulation_and_procedure_receive_same_style(self):
        import sys
        sys.path.insert(0, str(ROOT/'scripts'))
        from semantic_diagram_fixtures import cases
        HarnessRegistry(ROOT/'harnesses').load('hybrid-story')
        renderer = importlib.import_module('hybrid_story.hybrid_renderer')
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); items = []
            for i,case in enumerate(cases()):
                item = scene('diagram')
                item.id = f'scene-{i:03d}'; item.duration_seconds = 10
                item.layout['hybrid']['diagram'] = case['hybrid']['diagram']
                for j,node in enumerate(item.layout['hybrid']['diagram']['nodes']):
                    node['color'] = design()['palette']['accents'][j]
                items.append(item)
            project = root/'project'
            renderer.compile_project(items, project, SimpleNamespace(width=1280,height=720,fps=24))
            subprocess.run(['/app/hyperframes-runtime/node_modules/.bin/hyperframes','snapshot',str(project),
                '--at=9,19,29','--no-end','--describe=false'],check=True,capture_output=True,timeout=90)
            frames = sorted((project/'snapshots').glob('frame-*.png'))
            self.assertEqual(3, len(frames))
            hashes = []
            for path in frames:
                with Image.open(path) as image:
                    rgb = image.convert('RGB')
                    self.assertEqual((24,32,31), rgb.getpixel((50,200)))
                    pixels = list(rgb.getdata())
                    # The new foreground and accents must reach actual mounted pixels.
                    self.assertGreater(sum(max(abs(a-b) for a,b in zip(px,(242,240,229)))<8 for px in pixels),100)
                    self.assertGreater(sum(max(abs(a-b) for a,b in zip(px,(212,154,85)))<8 for px in pixels),50)
                    from app.tracking import sha256_file
                    hashes.append(sha256_file(path))
            self.assertEqual(3,len(set(hashes)))

    def test_rendered_background_text_and_source_pixels(self):
        HarnessRegistry(ROOT/'harnesses').load('hybrid-story')
        renderer = importlib.import_module('hybrid_story.hybrid_renderer')
        from app.tracking import sha256_file
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); asset = root/'original.png'
            Image.new('RGB',(1280,720),'#B36249').save(asset)
            items = [scene('diagram'),scene('source')]
            for i,s in enumerate(items):
                s.id = f'scene-{i:03d}'; s.image_path = str(asset)
            items[1].layout['hybrid_source'] = dict(prepared_by='trusted_source_registry',id='registered',
                prepared_sha256=sha256_file(asset),date_label='Development fixture',attribution='Original test pixels')
            project = root/'project'
            renderer.compile_project(items, project, SimpleNamespace(width=1280,height=720,fps=24))
            subprocess.run(['/app/hyperframes-runtime/node_modules/.bin/hyperframes','snapshot',str(project),
                '--at=5.7,7','--no-end','--describe=false'],check=True,capture_output=True,timeout=90)
            snapshots = sorted((project/'snapshots').glob('frame-*.png'))
            self.assertEqual(2,len(snapshots))
            with Image.open(snapshots[0]) as diagram:
                self.assertEqual((24,32,31),diagram.convert('RGB').getpixel((50,200)))
            with Image.open(snapshots[1]) as source:
                self.assertEqual((179,98,73),source.convert('RGB').getpixel((640,360)))
            manifest = json.loads((project/'design.json').read_text())
            self.assertEqual(design_sha256(FilmDesign.model_validate(design())),manifest['sha256'])
