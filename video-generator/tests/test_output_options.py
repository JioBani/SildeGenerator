import sys
import asyncio
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from app.config import Settings, output_settings
from app.media import validate_video


HARNESS_ROOT = Path(__file__).resolve().parents[2] / "harnesses"
if not HARNESS_ROOT.exists():
    HARNESS_ROOT = Path("/app/harnesses")
sys.path.insert(0, str(HARNESS_ROOT / "classic-slide" / "src"))
sys.path.insert(0, str(HARNESS_ROOT / "cinematic-slide" / "src"))


class OutputOptionsTests(unittest.TestCase):
    def test_job_settings_do_not_mutate_global_defaults(self):
        base = Settings(width=1920, height=1080)
        portrait = output_settings(base, "9:16", False)
        self.assertEqual((portrait.width, portrait.height), (1080, 1920))
        self.assertFalse(portrait.subtitles_enabled)
        self.assertEqual((base.width, base.height), (1920, 1080))
        with self.assertRaises(ValueError):
            output_settings(base, "4:3", True)

    def test_both_slide_harnesses_obey_subtitle_toggle(self):
        from classic_slide.effects.media import video_filter as classic_filter
        from cinematic_slide.effects.media import video_filter as cinematic_filter
        scene = SimpleNamespace(duration_seconds=3.0, layout={})
        settings = SimpleNamespace(width=1080, height=1920, fps=24, crossfade_seconds=.35, subtitles_enabled=False)
        for build in (classic_filter, cinematic_filter):
            graph, _ = build([scene], Path("/tmp/test.ass"), settings, {}, "fade")
            self.assertIn("1080x1920", graph)
            self.assertIn("null[video]", graph)
            self.assertNotIn("subtitles=", graph)
            settings.subtitles_enabled = True
            graph, _ = build([scene], Path("/tmp/test.ass"), settings, {}, "fade")
            self.assertIn("subtitles=", graph)
            settings.subtitles_enabled = False

    def test_video_qc_rejects_all_black_render(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            settings = Settings(width=320, height=180, fps=24)
            for color, should_pass in (("black", False), ("red", True)):
                path = base / f"{color}.mp4"
                subprocess.run([
                    "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                    "-f", "lavfi", "-i", f"color=c={color}:s=320x180:r=24:d=2",
                    "-f", "lavfi", "-i", "sine=frequency=440:duration=2",
                    "-c:v", "libx264", "-c:a", "aac", "-shortest", str(path),
                ], check=True)
                if should_pass:
                    self.assertEqual(len(asyncio.run(validate_video(path, settings))["sample_brightness"]), 3)
                else:
                    with self.assertRaisesRegex(ValueError, "black"):
                        asyncio.run(validate_video(path, settings))


if __name__ == "__main__":
    unittest.main()
