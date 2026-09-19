from __future__ import annotations

import unittest

from app.config import Settings
from app.planner import _compose_prompt, compile_source_units
from app.voice_broker import VoiceTaskBroker, voice_settings_hash


class ParallelPipelineContractTests(unittest.TestCase):
    def test_runtime_defaults_are_safe_first_phase_values(self) -> None:
        configured = Settings()
        self.assertEqual(configured.fps, 24)
        self.assertEqual(configured.voice_task_concurrency, 2)
        self.assertEqual(configured.ffmpeg_task_concurrency, 1)
        self.assertEqual(configured.image_task_concurrency, 4)

    def test_voice_reuse_hash_covers_narration_and_all_settings(self) -> None:
        snapshot = {
            "voice_id": "voice-a", "model": "eleven_flash_v2_5", "stability": .6,
            "similarity_boost": .6, "speed": .7, "style": .15, "language": "ko",
            "seed": 20260919, "output_format": "mp3_44100_128",
        }
        first = voice_settings_hash("같은 문장", snapshot)
        self.assertEqual(first, voice_settings_hash("같은 문장", dict(reversed(list(snapshot.items())))))
        self.assertNotEqual(first, voice_settings_hash("다른 문장", snapshot))
        self.assertNotEqual(first, voice_settings_hash("같은 문장", {**snapshot, "speed": .8}))

    def test_voice_retry_policy_only_retries_transient_failures(self) -> None:
        self.assertTrue(VoiceTaskBroker._classify(RuntimeError("provider returned 429"))[0])
        self.assertTrue(VoiceTaskBroker._classify(RuntimeError("provider returned 503"))[0])
        self.assertFalse(VoiceTaskBroker._classify(ValueError("invalid audio"))[0])

    def test_continuity_off_omits_long_selection_documents(self) -> None:
        prompts = {
            "director/system.md": "director",
            "narrative/story-intent.md": "{{SOURCE_UNITS}}",
            "narrative/analyze-sequences.md": "sequences",
            "narrative/analyze-scene-groups.md": "groups",
            "narrative/analyze-scenes.md": "scenes",
            "keycut/select-keycuts.md": "keycuts",
            "style/common.md": "{{IMAGE_STYLE}}",
            "style/presets/editorial-illustration.md": "EDITORIAL",
            "continuity/select-assets.md": "LONG_SELECT",
            "continuity/assign-scene-references.md": "LONG_ASSIGN",
            "continuity/disabled.md": "SHORT_DISABLED",
            "image/system.md": "image",
            "image/build-image-prompt.md": "{{SCENE_JSON}}",
            "image/style-guide.md": "STYLE_BIBLE",
        }
        units = compile_source_units("대본")
        disabled = _compose_prompt(prompts, "대본", units, False, "editorial_illustration")
        enabled = _compose_prompt(prompts, "대본", units, True, "editorial_illustration")
        self.assertIn("SHORT_DISABLED", disabled)
        self.assertIn("STYLE_BIBLE", disabled)
        self.assertNotIn("LONG_SELECT", disabled)
        self.assertNotIn("LONG_ASSIGN", disabled)
        self.assertIn("LONG_SELECT", enabled)
        self.assertIn("LONG_ASSIGN", enabled)


if __name__ == "__main__":
    unittest.main()
