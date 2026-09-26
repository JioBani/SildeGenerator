"""Exercise the pinned composition loader, not only a standalone browser seek."""
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

CLI = Path("/app/hyperframes-runtime/node_modules/.bin/hyperframes")


@unittest.skipUnless(CLI.exists(), "Pinned HyperFrames Docker runtime required")
class HybridPixelRegression(unittest.TestCase):
    def test_real_composition_mount_and_late_diagram_state(self):
        HarnessRegistry(ROOT / "harnesses").load("hybrid-story")
        renderer = importlib.import_module("hybrid_story.hybrid_renderer")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fixture = Image.new("RGB", (1280, 720), "#246060")
            ImageDraw.Draw(fixture).rectangle((640, 0, 1280, 720), fill="#e09b43")
            asset = root / "fixture.png"
            fixture.save(asset)
            scenes = [SimpleNamespace(id="scene-001", duration_seconds=2, image_path=str(asset),
                layout={"hybrid": route("cinematic")}),
                SimpleNamespace(id="scene-002", duration_seconds=4, image_path=str(asset),
                layout={"hybrid": route("diagram")})]
            project = root / "project"
            renderer.compile_project(scenes, project, SimpleNamespace(width=1280, height=720, fps=24))
            subprocess.run([str(CLI), "snapshot", str(project), "--at=1,2.3,5.8", "--no-end", "--describe=false"],
                check=True, timeout=90, capture_output=True)
            snapshots = sorted((project / "snapshots").glob("frame-*.png"))
            self.assertEqual(3, len(snapshots))
            with Image.open(snapshots[0]) as cinematic:
                self.assertEqual((1280, 720), cinematic.size)
                left, right = cinematic.convert("RGB").getpixel((200, 300)), cinematic.convert("RGB").getpixel((1000, 300))
                self.assertLess(sum(abs(a-b) for a,b in zip(left, (36, 96, 96))), 12)
                self.assertLess(sum(abs(a-b) for a,b in zip(right, (224, 155, 67))), 12)
            with Image.open(snapshots[1]) as early, Image.open(snapshots[2]) as late:
                # Bottom node state changes must execute, not just edge reveals.
                region = (180, 380, 1100, 460)
                delta = ImageChops.difference(early.convert("RGB").crop(region), late.convert("RGB").crop(region))
                self.assertGreater(max(ImageStat.Stat(delta).mean), .5)
            self.assertEqual(["cinematic", "diagram"], [p["route"] for p in json.loads((project / "program.json").read_text())])


if __name__ == "__main__":
    unittest.main()
