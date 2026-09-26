import hashlib
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from app.asset_origin import record_generated_origin


class AssetOriginTests(unittest.TestCase):
    def test_runtime_overrides_planner_claim_and_preserves_other_layout(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / 'fixture.png'
            image.write_bytes(b'fixture-one')
            for provider, expected in [('mock', 'mock'), ('oauth', 'generated'), ('future', 'unknown')]:
                scene = SimpleNamespace(layout={'genre_id': 'documentary', 'asset_origin': 'archive',
                                                'asset_provenance': {'archive_verified': True}})
                record = record_generated_origin(scene, image, provider=provider, task_id='task-1')
                self.assertEqual(scene.layout['asset_origin'], expected)
                self.assertEqual(scene.layout['genre_id'], 'documentary')
                self.assertFalse(record['archive_verified'])
                self.assertEqual(record['sha256'], hashlib.sha256(b'fixture-one').hexdigest())

    def test_changed_image_refreshes_hash_and_missing_file_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / 'fixture.png'
            image.write_bytes(b'one')
            scene = SimpleNamespace(layout={})
            first = record_generated_origin(scene, image, provider='mock', task_id='one')
            image.write_bytes(b'two')
            second = record_generated_origin(scene, image, provider='mock', task_id='two')
            self.assertNotEqual(first['sha256'], second['sha256'])
            self.assertEqual(second['image_task_id'], 'two')
            with self.assertRaises(FileNotFoundError):
                record_generated_origin(scene, Path(directory) / 'absent', provider='mock', task_id='absent')
