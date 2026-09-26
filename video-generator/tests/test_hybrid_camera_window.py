import importlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from PIL import Image, ImageChops, ImageDraw, ImageStat
from app.engine.harness_loader import HarnessRegistry
from test_hybrid_story import ROOT, route


class CameraWindowTests(unittest.TestCase):
    def test_hold_does_not_create_a_move_and_short_move_fails(self):
        from hybrid_story.effects.camera import camera_window
        hold = SimpleNamespace(layout={"camera": {"mode": "hold"}})
        self.assertIsNone(camera_window(hold, 6, .035))
        push = SimpleNamespace(layout={"camera": {"mode": "push", "focus": [.35, .6],
                                                   "strength": .06}})
        with self.assertRaisesRegex(ValueError, "1_8s_travel"):
            camera_window(push, 2, .035)
        window = camera_window(push, 6, .035)
        self.assertAlmostEqual(6, sum(window[k] for k in
                               ("lead_seconds", "travel_seconds", "settle_seconds")))
        self.assertEqual("sine.inOut", window["ease"])
        self.assertEqual([.35, .6], window["focus"])

    @unittest.skipUnless(Path('/app/hyperframes-runtime/node_modules/.bin/hyperframes').exists(),
                         'Pinned runtime required')
    def test_rendered_camera_starts_and_settles(self):
        HarnessRegistry(ROOT / "harnesses").load("hybrid-story")
        renderer = importlib.import_module("hybrid_story.hybrid_renderer")
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            image = Image.new("RGB", (1280, 720), "#203339")
            draw = ImageDraw.Draw(image)
            draw.rectangle((140, 120, 450, 610), fill="#ec9952")
            draw.ellipse((760, 120, 1160, 560), fill="#65c8c2")
            asset = root / "cinematic.png"
            image.save(asset)
            item = SimpleNamespace(id="camera-scene", duration_seconds=6, image_path=str(asset),
                layout={"hybrid": route("cinematic"),
                        "camera": {"mode": "push", "focus": [.35, .6], "strength": .06}})
            project = root / "project"
            renderer.compile_project([item], project, SimpleNamespace(width=1280, height=720, fps=24))
            data = json.loads((project / "program.json").read_text())
            self.assertEqual("sine.inOut", data[0]["camera_window"]["ease"])
            self.assertAlmostEqual(5.1, data[0]["camera_window"]["lead_seconds"] +
                data[0]["camera_window"]["travel_seconds"])
            subprocess.run(['/app/hyperframes-runtime/node_modules/.bin/hyperframes', 'snapshot',
                str(project), '--at=0.1,0.3,1,3,5.3,5.8', '--no-end', '--describe=false'],
                check=True, capture_output=True, timeout=90)
            frames = sorted((project / "snapshots").glob("frame-*.png"))
            self.assertEqual(6, len(frames))
            pictures = []
            for frame in frames:
                with Image.open(frame) as rendered:
                    pictures.append(rendered.convert("RGB").crop((100, 100, 1180, 640)))
            def difference(a, b):
                return max(ImageStat.Stat(ImageChops.difference(pictures[a],pictures[b])).mean)
            self.assertLess(difference(0, 1), .02)
            self.assertGreater(difference(1, 2), .2)
            self.assertGreater(difference(2, 3), .2)
            self.assertLess(difference(4, 5), .02)


if __name__ == '__main__':
    unittest.main()
