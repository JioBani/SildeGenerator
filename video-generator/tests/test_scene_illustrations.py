from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from PIL import Image

from app.config import Settings, production_settings
from app.models import RenderRequest
from app.main import _configure_render_harness
from app.engine.harness_loader import LoadedHarness
from app.providers.scene_illustrations import IllustratedSceneImageProvider, classify_environment


class SceneIllustrationTests(unittest.TestCase):
    def test_environment_and_aspect_ratio(self):
        self.assertEqual(classify_environment("배가 바다를 건넙니다"), "water")
        self.assertEqual(classify_environment("숲의 나무 사이를 걷습니다"), "forest")
        self.assertEqual(classify_environment("새로운 시작"), "meadow")
        with TemporaryDirectory() as directory:
            provider = IllustratedSceneImageProvider()
            first = Path(directory) / "sea.png"
            second = Path(directory) / "forest.png"
            report = provider.render("배가 바다를 건넙니다", "cute_character", 1080, 1920, first)
            provider.render("숲의 나무 사이를 걷습니다", "cute_character", 1080, 1920, second)
            with Image.open(first) as image:
                self.assertEqual(image.size, (1080, 1920))
            self.assertEqual(report["source_dimensions"], "720x1280")
            self.assertNotEqual(first.read_bytes(), second.read_bytes())

    def test_route_is_pinned_and_rejects_mismatched_style(self):
        profile = {"id": "local_illustration", "version": "0.5.0", "imageStyle": "cute_character"}
        base = Settings(runner_mode="live", image_provider="oauth")
        selected = production_settings(base, "classic-slide", None, profile)
        self.assertEqual((selected.runner_mode, selected.image_provider), ("local", "local_illustration"))
        self.assertEqual((base.runner_mode, base.image_provider), ("live", "oauth"))
        common = {"job_id": "00000000-0000-4000-8000-000000000001", "scenario": "바다를 건넙니다.",
                  "harness_id": "classic-slide", "continuity_enabled": False,
                  "slide_visual_profile": profile}
        RenderRequest(**common, image_style="cute_character")
        with self.assertRaises(ValueError):
            RenderRequest(**common, image_style="fantasy_anime")

    def test_local_slides_do_not_animate_still_images_or_change_shared_defaults(self):
        harness = LoadedHarness(None, None, None, Path("."), {"zoom_strength": 0.045})
        request = RenderRequest(
            job_id="00000000-0000-4000-8000-000000000002",
            scenario="바다를 건넙니다.",
            image_style="cute_character",
            slide_visual_profile={"id": "local_illustration", "version": "0.5.0", "imageStyle": "cute_character"},
        )
        configured = _configure_render_harness(harness, request)
        self.assertEqual(configured.config["zoom_strength"], 0.0)
        self.assertEqual(harness.config["zoom_strength"], 0.045)
        ordinary = request.model_copy(update={"slide_visual_profile": None})
        self.assertIs(_configure_render_harness(harness, ordinary), harness)


if __name__ == "__main__":
    unittest.main()
