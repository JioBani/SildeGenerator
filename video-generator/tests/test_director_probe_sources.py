import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from render_director_probe import source_binding
from probe_meaning_planning import engine_image_style
from app.source_media import prepare_source


class DirectorProbeSourceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        Image.new('RGB', (32, 24), '#267a84').save(self.root / 'source.png')
        self.record = dict(id='record-1', title='Test observation', source_url='https://example.org/source',
            rights_url='https://example.org/rights', usage_basis='Synthetic test fixture',
            attribution='Test fixture', date_label='2026', meaning_limit='Test only',
            sha256=hashlib.sha256((self.root / 'source.png').read_bytes()).hexdigest(),
            file='source.png', origin='observational_visualization')
        self.write_catalog()
        self.plan = SimpleNamespace(scenes=[SimpleNamespace(layout={'hybrid': {'route': 'source', 'source_id': 'record-1'}})])

    def write_catalog(self):
        (self.root / 'catalog.json').write_text(json.dumps({'version': 'source-media-0.1', 'assets': [self.record]}), encoding='utf-8')

    def test_source_free_plan_needs_no_registry(self):
        plan = SimpleNamespace(scenes=[SimpleNamespace(layout={'hybrid': {'route': 'diagram'}})])
        self.assertIsNone(source_binding(plan, None))

    def test_source_requires_explicit_registered_identity(self):
        with self.assertRaisesRegex(ValueError, 'source_registry_required_before_voice'):
            source_binding(self.plan, None)
        self.plan.scenes[0].layout['hybrid']['source_id'] = 'unknown'
        with self.assertRaisesRegex(ValueError, 'requested_source_missing'):
            source_binding(self.plan, self.root)

    def test_binding_detects_metadata_and_image_changes(self):
        first = source_binding(self.plan, self.root)
        self.assertEqual(first, source_binding(self.plan, self.root))
        self.record['meaning_limit'] = 'Changed scope'
        self.write_catalog()
        self.assertNotEqual(first, source_binding(self.plan, self.root))
        Image.new('RGB', (32, 24), '#ffffff').save(self.root / 'source.png')
        with self.assertRaisesRegex(ValueError, 'source_hash_changed'):
            source_binding(self.plan, self.root)

    def test_path_escape_rejected(self):
        self.record['file'] = '../outside.png'
        self.write_catalog()
        with self.assertRaisesRegex(ValueError, 'source_path_outside_registry_or_missing'):
            source_binding(self.plan, self.root)

    def test_preparation_preserves_source_and_provenance(self):
        result = prepare_source(self.root, 'record-1', self.root / 'prepared.png')
        self.assertEqual(self.record['sha256'], result['original_sha256'])
        self.assertEqual(result['prepared_by'], 'trusted_source_registry')
        with Image.open(self.root / 'prepared.png') as prepared, Image.open(self.root / 'source.png') as original:
            self.assertEqual(prepared.tobytes(), original.tobytes())

    def test_original_fairytale_uses_existing_style_id(self):
        self.assertEqual(engine_image_style('family_fairytale'), 'disney_animation')
        self.assertEqual(engine_image_style('cinematic_realism'), 'cinematic_realism')


if __name__ == '__main__':
    unittest.main()
