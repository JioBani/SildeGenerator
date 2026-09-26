import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from app.rendered_review import inspect_render, inspect_for_contract, spatial_variation


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required")
class RenderedReviewTests(unittest.TestCase):
    def make_video(self, folder, source, *, audio=True):
        path = Path(folder) / "fixture.mp4"
        args = ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", source]
        if audio:
            args += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono"]
        args += ["-t", "2", "-c:v", "libx264", "-pix_fmt", "yuv420p"]
        if audio:
            args += ["-c:a", "aac"]
        subprocess.run([*args, str(path)], check=True, timeout=30)
        return path

    def scene(self, id="scene-001", seconds=2, **direction):
        return SimpleNamespace(id=id, duration_seconds=seconds, narration="A test picture.",
                               layout={"direction": direction})

    def test_black_picture_and_missing_audio_are_not_passed(self):
        with tempfile.TemporaryDirectory() as folder:
            path = self.make_video(folder, "color=black:s=128x72:r=12", audio=False)
            review = inspect_render(path, [self.scene()], width=128, height=72, fps=12)
            self.assertIn("audio_stream_missing", review["findings"])
            self.assertIn("scene-001:near_uniform_picture", review["findings"])

    def test_tinted_blank_is_not_content_and_gate_is_opt_in(self):
        self.assertEqual(0, spatial_variation(bytes([244, 247, 247]) * 64))
        with tempfile.TemporaryDirectory() as folder:
            path = self.make_video(folder, "color=0xf4f7f7:s=128x72:r=12")
            args = dict(width=128, height=72, fps=12)
            self.assertIsNone(inspect_for_contract(path, [self.scene()], None, **args))
            with self.assertRaisesRegex(ValueError, "unsupported"):
                inspect_for_contract(path, [self.scene()], {"rendered_observation_gate": "invented"}, **args)
            review = inspect_for_contract(path, [self.scene()], {"rendered_observation_gate": "rendered-observations-0.2"}, **args)
            self.assertEqual("REVISE", review["status"])
            self.assertIn("scene-001:near_uniform_picture", review["findings"])

    def test_real_frames_detect_repetition_except_declared_callback(self):
        with tempfile.TemporaryDirectory() as folder:
            path = self.make_video(folder, "testsrc=size=128x72:rate=12,select=eq(n\\,0),loop=-1:1,setpts=N/(12*TB)")
            scenes = [self.scene(seconds=1), self.scene("scene-002", 1)]
            review = inspect_render(path, scenes, width=128, height=72, fps=12)
            self.assertIn("scene-002:near_duplicate_picture:1", review["findings"])
            scenes[1].layout["direction"] = {"repeat_of_scene_number": 1}
            accepted = inspect_render(path, scenes, width=128, height=72, fps=12)
            self.assertEqual("PIXEL_CHECKS_PASS", accepted["status"])
            self.assertNotEqual(review["plan_sha256"], accepted["plan_sha256"])
            self.assertEqual(review["video_sha256"], accepted["video_sha256"])
            self.assertIn("emotion", accepted["not_evaluated"])
            self.assertIsNone(accepted["human_approval"])

    def test_dimensions_and_timeline_checked_against_real_output(self):
        with tempfile.TemporaryDirectory() as folder:
            path = self.make_video(folder, "testsrc2=size=128x72:rate=12")
            review = inspect_render(path, [self.scene(seconds=1)], width=1920, height=1080, fps=24)
            self.assertIn("dimensions_mismatch", review["findings"])
            self.assertIn("fps_mismatch", review["findings"])
            self.assertIn("narration_timeline_mismatch", review["findings"])

    def test_static_picture_cannot_claim_executed_diagram_change(self):
        with tempfile.TemporaryDirectory() as folder:
            path = self.make_video(folder, "testsrc=size=128x72:rate=12,select=eq(n\\,0),loop=-1:1,setpts=N/(12*TB)")
            scene = self.scene()
            scene.layout["hybrid"] = {"route": "diagram", "diagram": {"nodes": [{"before": "open", "after": "closed"}], "edges": []}}
            review = inspect_render(path, [scene], width=128, height=72, fps=12)
            self.assertIn("scene-001:declared_diagram_change_not_visible", review["findings"])

    def test_snapshot_pair_is_not_exempt_from_frozen_picture_detection(self):
        with tempfile.TemporaryDirectory() as folder:
            path=self.make_video(folder,"testsrc=size=128x72:rate=12,select=eq(n\\,0),loop=-1:1,setpts=N/(12*TB)")
            scene=self.scene()
            scene.layout['hybrid']={'route':'diagram','diagram':{'nodes':[],'edges':[],
                'snapshot_pair':{'before':{'value':80},'after':{'value':35}}}}
            review=inspect_render(path,[scene],width=128,height=72,fps=12)
            self.assertIn('scene-001:declared_diagram_change_not_visible',review['findings'])


if __name__ == "__main__":
    unittest.main()
