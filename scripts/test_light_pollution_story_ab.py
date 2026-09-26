from __future__ import annotations

import unittest

from scripts.build_light_pollution_story_ab import ASSETS, EXPERIMENT, VOICE, page, sha256


class StoryAbTests(unittest.TestCase):
    def test_variants_share_context_and_narration(self):
        flat = page("A", 9.41619)
        layered = page("B", 9.41619)
        self.assertIn('data-duration="9.416190"', flat)
        self.assertIn('data-duration="9.416190"', layered)
        self.assertIn('class="light"', flat)
        self.assertIn('class="light"', layered)
        self.assertNotIn('person-head-notice.png', flat)
        self.assertIn('person-head-notice.png', layered)
        self.assertTrue(VOICE.is_file())

    def test_project_assets_and_video_records_exist(self):
        for name in ("person-full.png", "person-body.png", "person-head-neutral.png", "person-head-notice.png"):
            self.assertTrue((ASSETS / name).is_file())
        for variant in ("A", "B"):
            video = EXPERIMENT / variant / "comparison.mp4"
            self.assertTrue(video.is_file())
            self.assertEqual(len(sha256(video)), 64)


if __name__ == "__main__":
    unittest.main()
