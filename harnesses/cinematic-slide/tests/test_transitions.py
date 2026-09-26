import unittest
import asyncio
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from types import SimpleNamespace
from cinematic_slide.effects.media import video_filter, render_segment, write_subtitles
from cinematic_slide.effects.transitions import boundary_fades, transition_kind
from cinematic_slide.plugin import ClassicSlideHarness


class TransitionTests(unittest.TestCase):
    def test_segment_planning_retains_dissolve_chain(self):
        shots = self.shots()
        self.assertEqual(ClassicSlideHarness().plan_segments(shots, 1, {}), [(0, 1), (1, 3)])
        self.assertEqual(ClassicSlideHarness().plan_segments(shots, 2, {}), [(0, 3)])
        self.assertEqual(ClassicSlideHarness().plan_segments(shots, 1, {'crossfade_seconds': 0}), [(0, 1), (1, 2), (2, 3)])

    def shots(self):
        return [SimpleNamespace(id=str(i), transition=t, duration_seconds=3, layout={})
                for i, t in enumerate(['cut', 'dissolve', 'cut'])]

    def test_mixed_boundaries_preserve_narration_timeline(self):
        shots = self.shots()
        self.assertEqual(boundary_fades(shots, .3), [0, .3])
        filters, _ = video_filter(shots, Path('captions.ass'),
            SimpleNamespace(width=1920, height=1080, fps=30, crossfade_seconds=.3), {}, 'fade')
        self.assertIn('[v0][v1]concat=n=2:v=1:a=0,fps=30,settb=1/30[x1]', filters)
        self.assertIn('[x1][v2]xfade=transition=fade:duration=0.300000:offset=6.000000', filters)
        self.assertEqual(filters.count('trim=duration=3.300000'), 1)

    def test_unsupported_transition_fails_preflight(self):
        scene = self.shots()[0]
        scene.transition = 'match'
        self.assertTrue(any('transition_contract' in f for f in ClassicSlideHarness().validate_plan([scene], {})))
        with self.assertRaises(ValueError):
            transition_kind(scene)

    def test_zero_fade_and_invalid_duration(self):
        self.assertEqual(boundary_fades(self.shots(), 0), [0, 0])
        for value in [-1, float('nan'), float('inf')]:
            with self.assertRaises(ValueError):
                boundary_fades(self.shots(), value)

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'FFmpeg required')
    def test_real_render_mixed_boundaries(self):
        class Process:
            async def run(self, command):
                result = subprocess.run(command, capture_output=True, timeout=60)
                if result.returncode:
                    raise RuntimeError(result.stderr.decode(errors='replace'))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shots = self.shots()
            for scene, color in zip(shots, [bytes([255, 0, 0]), bytes([0, 255, 0]), bytes([0, 0, 255])]):
                asset = root / (scene.id + '.ppm')
                asset.write_bytes(b'P6\n320 180\n255\n' + color * (320 * 180))
                scene.image_path = str(asset)
                scene.narration = ''
            settings = SimpleNamespace(width=320, height=180, fps=10, crossfade_seconds=.3, ffmpeg_preset='ultrafast')
            captions, output = root / 'captions.ass', root / 'result.mp4'
            write_subtitles(shots, captions, settings, {})
            asyncio.run(render_segment(shots, captions, output, settings, {}, Process()))
            info = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_format', '-of', 'json', str(output)]))
            self.assertAlmostEqual(float(info['format']['duration']), 9, delta=.12)
            def pixel(time):
                value = subprocess.check_output(['ffmpeg', '-v', 'error', '-ss', str(time), '-i', str(output),
                    '-vf', 'scale=1:1', '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'])
                return list(value[:3])
            self.assertGreater(pixel(2.8)[0], 220)
            self.assertGreater(pixel(3.1)[1], 220)
            middle = pixel(6.1)
            self.assertGreater(middle[1], 30)
            self.assertGreater(middle[2], 30)
            self.assertGreater(pixel(6.5)[2], 220)
