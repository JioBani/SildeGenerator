import tempfile
import asyncio
import json
import subprocess
import unittest
from pathlib import Path
from types import SimpleNamespace
from app.planner import deterministic_plan
from app.render_pipeline import _input_hash, ProgressiveRenderer
from app.engine.harness_loader import HarnessRegistry
from app.engine.process_runner import ProcessRunner


class RenderContractCacheTests(unittest.TestCase):
    def test_direction_changes_invalidate_reuse(self):
        with tempfile.TemporaryDirectory() as directory:
            asset = Path(directory) / 'asset'
            asset.write_bytes(b'unchanged-media')
            scene = deterministic_plan('원문을 보여줍니다.', 'Simple illustration.').scenes[0]
            scene.image_path = scene.audio_path = str(asset)
            scene.duration_seconds = 3
            settings = SimpleNamespace(fps=30, width=1920, height=1080, crossfade_seconds=.3, ffmpeg_preset='fast')
            harness = SimpleNamespace(snapshot=SimpleNamespace(as_dict=lambda: {'version': 'test'}), config={})
            original = _input_hash([scene], settings, harness)
            self.assertEqual(original, _input_hash([scene.model_copy(deep=True)], settings, harness))
            self.assertNotEqual(original, _input_hash([scene], SimpleNamespace(**vars(settings), subtitles_enabled=False), harness))
            self.assertNotEqual(original, _input_hash([scene], SimpleNamespace(**{**vars(settings), 'width': 1080, 'height': 1920}), harness))
            for field, value in [('narration', '수정 자막'), ('layout', {'camera': {'mode': 'push'}}),
                                 ('transition', 'cut' if scene.transition != 'cut' else 'dissolve'),
                                 ('rhythm', 'revised rhythm')]:
                revised = scene.model_copy(deep=True)
                setattr(revised, field, value)
                self.assertNotEqual(original, _input_hash([revised], settings, harness), field)


class SchedulerIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_cinematic_boundaries_reach_actual_scheduler(self):
        from unittest.mock import AsyncMock
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            plan = deterministic_plan('첫 장면입니다. 두 번째 장면입니다. 세 번째 장면입니다.', 'Simple illustration.')
            for scene, rgb, transition in zip(plan.scenes, [b'\xff\x00\x00', b'\x00\xff\x00', b'\x00\x00\xff'], ['cut', 'dissolve', 'cut']):
                image = work / (scene.id + '.ppm')
                image.write_bytes(b'P6\n320 180\n255\n' + rgb * (320 * 180))
                scene.image_path = scene.audio_path = str(image)
                scene.duration_seconds = 3
                scene.transition = transition
                scene.layout = {'camera': {'mode': 'hold'}}
            harnesses = Path(__file__).resolve().parents[2] / 'harnesses'
            if not harnesses.exists():
                harnesses = Path('/app/harnesses')
            harness = HarnessRegistry(harnesses).load('cinematic-slide')
            renderer = ProgressiveRenderer.__new__(ProgressiveRenderer)
            renderer.settings = SimpleNamespace(fps=10, width=320, height=180, crossfade_seconds=.3,
                ffmpeg_preset='ultrafast', render_segment_scenes=1)
            renderer.pool = SimpleNamespace(execute=AsyncMock())
            renderer.redis = SimpleNamespace(zrem=AsyncMock())
            renderer._acquire = AsyncMock()
            renderer.process = ProcessRunner()
            outputs = await renderer.render_ready_segments('00000000-0000-0000-0000-000000000001',
                plan.scenes, [asyncio.sleep(0) for _ in plan.scenes], work, harness)
            self.assertEqual(len(outputs), 2)
            durations = [float(json.loads(subprocess.check_output(['ffprobe', '-v', 'error',
                '-show_format', '-of', 'json', str(path)]))['format']['duration']) for path in outputs]
            self.assertAlmostEqual(durations[0], 3, delta=.12)
            self.assertAlmostEqual(durations[1], 6, delta=.12)
            self.assertEqual(renderer._acquire.await_count, 2)
            await renderer.render_ready_segments('00000000-0000-0000-0000-000000000001',
                plan.scenes, [asyncio.sleep(0) for _ in plan.scenes], work, harness)
            self.assertEqual(renderer._acquire.await_count, 2, 'unchanged contract should reuse both segments')
            plan.scenes[1].layout['camera'] = {'mode': 'push', 'strength': .02}
            await renderer.render_ready_segments('00000000-0000-0000-0000-000000000001',
                plan.scenes, [asyncio.sleep(0) for _ in plan.scenes], work, harness)
            self.assertEqual(renderer._acquire.await_count, 3, 'only modified segment should render again')
