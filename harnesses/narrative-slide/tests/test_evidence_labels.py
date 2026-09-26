import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from cinematic_slide.effects.media import write_subtitles


class EvidenceLabelsTests(unittest.TestCase):
    def render(self, layouts):
        scenes = [SimpleNamespace(narration='원문입니다.', duration_seconds=2, layout=layout) for layout in layouts]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'captions.ass'
            write_subtitles(scenes, output, SimpleNamespace(width=1920, height=1080), {})
            return output.read_text(encoding='utf-8-sig')

    def test_generated_and_unknown_have_exact_shot_boundaries(self):
        text = self.render([{'genre_id': 'history', 'asset_origin': 'generated'}, {'genre_id': 'documentary'}])
        self.assertIn('Dialogue: 1,0:00:00.00,0:00:02.00,Evidence,,0,0,0,,AI 재현 삽화', text)
        self.assertIn('Dialogue: 1,0:00:02.00,0:00:04.00,Evidence,,0,0,0,,출처 미확인', text)
        self.assertEqual(text.count('원문입니다.'), 2)

    def test_planner_archival_claim_does_not_approve_provenance(self):
        text = self.render([{'genre_id': 'documentary', 'asset_origin': 'archive', 'verified': True}])
        self.assertIn('출처 미확인', text)

    def test_other_genres_do_not_receive_evidence_overlay(self):
        for genre in [None, 'cartoon', 'knowledge', 'tutorial']:
            self.assertNotIn('Dialogue: 1', self.render([{'genre_id': genre}]))


if __name__ == '__main__':
    unittest.main()
