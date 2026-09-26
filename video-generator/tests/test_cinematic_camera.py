import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

PATH = Path(__file__).resolve().parents[2] / 'harnesses/cinematic-slide/src/cinematic_slide/effects/camera.py'
spec = importlib.util.spec_from_file_location('cinematic_camera', PATH)
camera = importlib.util.module_from_spec(spec)
spec.loader.exec_module(camera)


class CameraTests(unittest.TestCase):
    def test_default_is_hold(self):
        self.assertEqual(camera.camera_filter(SimpleNamespace(layout={}), 150, .045)[0], '1')

    def test_matched_group_is_identical_across_segment_lengths(self):
        shot = SimpleNamespace(layout={'continuity_group': 'same-room', 'camera': {'mode': 'hold'}})
        self.assertEqual(camera.camera_filter(shot, 150, .045), camera.camera_filter(shot, 900, .045))

    def test_explicit_focus_and_move(self):
        shot = SimpleNamespace(layout={'camera': {'mode': 'push', 'focus': [.3, .4], 'strength': .02}})
        z, x, y = camera.camera_filter(shot, 150, .045)
        self.assertIn('0.02', z)
        self.assertIn('on/149', z)
        self.assertTrue(x.endswith('*0.3'))
        self.assertTrue(y.endswith('*0.4'))

    def test_invalid_contract_fails(self):
        for layout in [
            {'camera': {'mode': 'orbit'}}, {'camera': {'strength': float('nan')}},
            {'camera': {'strength': .5}}, {'camera': {'focus': [True, .5]}},
            {'camera': {'focus': [-1, .5]}}, {'camera': []},
            {'continuity_group': 'same', 'camera': {'mode': 'pull'}},
        ]:
            with self.subTest(layout=layout), self.assertRaises(ValueError):
                camera.camera_filter(SimpleNamespace(layout=layout), 150, .045)
