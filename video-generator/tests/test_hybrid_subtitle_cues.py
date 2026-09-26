import importlib
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from app.engine.harness_loader import HarnessRegistry

ROOT = Path(__file__).resolve().parents[2]


class HybridSubtitleCueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        HarnessRegistry(ROOT / 'harnesses').load('hybrid-story')
        cls.media = importlib.import_module('hybrid_story.effects.media')

    def write(self, cues):
        scene = SimpleNamespace(id='probe', duration_seconds=4, narration='첫 문장. 다음 문장.',
                                layout={'subtitle_cues': cues})
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'captions.ass'
            self.media.write_subtitles([scene], output,
                SimpleNamespace(width=1280, height=720), {})
            return output.read_text(encoding='utf-8-sig')

    def test_measured_cues_render_separately(self):
        text = self.write([{'text': '첫 문장.', 'start': 0, 'end': 1.5},
                           {'text': '다음 문장.', 'start': 1.5, 'end': 4}])
        self.assertEqual(text.count('Dialogue: 0,'), 2)

    def test_overlap_and_out_of_bounds_fail(self):
        for cues in ([{'text': '첫 문장.', 'start': 0, 'end': 2},
                      {'text': '다음 문장.', 'start': 1.8, 'end': 4}],
                     [{'text': '첫 문장.', 'start': 0, 'end': 4.1}]):
            with self.subTest(cues=cues), self.assertRaisesRegex(ValueError, 'subtitle_cue_outside_scene_or_overlap'):
                self.write(cues)

    def test_overlong_cue_fails_before_render(self):
        with self.assertRaisesRegex(ValueError, 'subtitle_cue_exceeds_two_lines'):
            self.write([{'text': '긴 자막 문장이 화면을 가리지 않도록 충분히 긴 문장을 여러 번 반복합니다. ' * 3,
                         'start': 0, 'end': 4}])


if __name__ == '__main__':
    unittest.main()
