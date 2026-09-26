import copy
import hashlib
import tempfile
import unittest
from pathlib import Path
from compile_reference_atlas import attach_semantics


class SemanticEvidenceTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        (self.root/'frame.png').write_bytes(b'test image evidence')
        self.scenes=[{'source_window':[204,216],'object_states':['uniformed_guard'],'render_authorized':False}]
        self.item={'id':'example','source_sha256':'source','scene_window':[204,216],'observed_at':207,
          'required_scene_state':'uniformed_guard','evidence':[{'file':'frame.png','sha256':hashlib.sha256(b'test image evidence').hexdigest()}],
          'discriminating_cues':['tunic','buttons'],'visible_identity':'guard','rejected_hypothesis':'anatomy',
          'story_function_hypothesis':'unverified','transfer_limits':'check context'}
    def test_valid_evidence_not_approval(self):
        attach_semantics(self.scenes,[self.item],'source',self.root)
        item=self.scenes[0]['semantic_observations'][0]
        self.assertFalse(self.scenes[0]['render_authorized']);self.assertFalse(item['production_promotion']);self.assertIsNone(item['narration_claim'])
    def test_source_mismatch(self):
        with self.assertRaises(ValueError):attach_semantics(self.scenes,[self.item],'other',self.root)
    def test_scope_mismatch(self):
        self.item['scene_window']=[192,204]
        with self.assertRaises(ValueError):attach_semantics(self.scenes,[self.item],'source',self.root)
    def test_stale_image(self):
        (self.root/'frame.png').write_bytes(b'replaced')
        with self.assertRaises(ValueError):attach_semantics(self.scenes,[self.item],'source',self.root)
    def test_wrong_scene_state(self):
        self.scenes[0]['object_states']=['internal_overlay']
        with self.assertRaises(ValueError):attach_semantics(self.scenes,[self.item],'source',self.root)
    def test_timestamp_outside_scene(self):
        self.item['observed_at']=216
        with self.assertRaises(ValueError):attach_semantics(self.scenes,[self.item],'source',self.root)


if __name__=='__main__':unittest.main()
