import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from app.subtitle_timing import cues_from_alignment

HARNESS_ROOT = Path(__file__).resolve().parents[2] / "harnesses"
if not HARNESS_ROOT.exists():
    HARNESS_ROOT = Path("/app/harnesses")
sys.path.insert(0, str(HARNESS_ROOT / "classic-slide" / "src"))
sys.path.insert(0, str(HARNESS_ROOT / "cinematic-slide" / "src"))


class SubtitleTimingTests(unittest.TestCase):
    def test_uses_real_character_times_and_keeps_sentence_text(self):
        text = "첫 문장입니다. 다음 문장입니다."
        characters = list(text)
        alignment = {
            "characters": characters,
            "character_start_times_seconds": [index * .1 for index in range(len(characters))],
            "character_end_times_seconds": [(index + 1) * .1 for index in range(len(characters))],
        }
        cues = cues_from_alignment(text, alignment, 5, max_chars=12)
        self.assertGreaterEqual(len(cues), 2)
        self.assertEqual("".join(cue["text"].replace(" ", "") for cue in cues), text.replace(" ", ""))
        self.assertAlmostEqual(cues[0]["start"], 0)
        self.assertTrue(all(cue["source"] == "elevenlabs_alignment" for cue in cues))

    def test_rejects_mismatched_transcript_instead_of_guessing(self):
        alignment = {"characters": list("다른 문장"), "character_start_times_seconds": [0] * 5,
                     "character_end_times_seconds": [1] * 5}
        self.assertEqual(cues_from_alignment("원래 문장", alignment, 3), [])

    def test_both_harnesses_write_cue_times(self):
        from classic_slide.effects.media import write_subtitles as classic
        from cinematic_slide.effects.media import write_subtitles as cinematic
        scene = SimpleNamespace(duration_seconds=4, narration="첫 문장. 다음 문장.", layout={
            "subtitle_cues": [{"text": "첫 문장.", "start": .2, "end": 1.3},
                              {"text": "다음 문장.", "start": 1.7, "end": 3.8}],
        })
        settings = SimpleNamespace(width=1080, height=1920)
        with tempfile.TemporaryDirectory() as directory:
            for build in (classic, cinematic):
                path = Path(directory) / (build.__module__.split(".")[0] + ".ass")
                build([scene], path, settings, {})
                output = path.read_text(encoding="utf-8-sig")
                self.assertIn("0:00:00.20,0:00:01.30", output)
                self.assertIn("0:00:01.70,0:00:03.80", output)
                self.assertEqual(output.count("Dialogue: 0,"), 2)


if __name__ == "__main__":
    unittest.main()
