import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from review_voice_cues import caption_cues, align_quantity_events


class ReviewVoiceCueTests(unittest.TestCase):
    def test_comparison_and_accumulation_follow_voice_not_old_template(self):
        for grammar in ('quantitative_comparison','cumulative_change'):
            node=dict(id='a',source_quote='10 liters',quantity=10,reveal_at=.1,change_at=.2)
            diagram=dict(grammar=grammar,nodes=[node])
            result=align_quantity_events(diagram,'Day one: 10 liters.',[dict(start=9,length=2,seconds=3)],10)
            self.assertEqual(.3,node['change_at'])
            self.assertEqual(10,node['quantity'])
            self.assertEqual(3,result[0]['seconds'])

    def test_ambiguous_or_missing_word_event_is_not_guessed(self):
        node=dict(id='a',source_quote='10',quantity=10,reveal_at=.1,change_at=.2)
        diagram=dict(grammar='cumulative_change',nodes=[node])
        with self.assertRaisesRegex(ValueError,'ambiguous'):
            align_quantity_events(diagram,'10 then 10',[],10)
        with self.assertRaisesRegex(ValueError,'missing'):
            align_quantity_events(diagram,'10',[],10)

    def test_preserves_text_and_actual_boundaries(self):
        text="First small sentence. Second small sentence."
        words=[dict(start=0,seconds=.1),dict(start=6,seconds=.5),dict(start=12,seconds=1),dict(start=22,seconds=3),dict(start=29,seconds=3.5),dict(start=35,seconds=4)]
        cues=caption_cues(text,words,6)
        self.assertEqual(2,len(cues))
        self.assertEqual(3,cues[0]["end"])
        self.assertEqual(6,cues[-1]["end"])
        self.assertEqual(text," ".join(c["text"] for c in cues))

    def test_mismatched_audio_clock_fails(self):
        with self.assertRaisesRegex(ValueError,"alignment"):
            caption_cues("test",[dict(start=0,seconds=20)],15)

    def test_reversed_timing_fails(self):
        with self.assertRaisesRegex(ValueError,"unordered"):
            caption_cues("test text",[dict(start=0,seconds=2),dict(start=5,seconds=1)],3)
