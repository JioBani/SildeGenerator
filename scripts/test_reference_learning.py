import hashlib
import tempfile
import unittest
from pathlib import Path
from reference_learning import packet, retrieve


class LearningTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        (self.root/'evidence').write_bytes(b'verified')
        self.case={'id':'one','scene_functions':['flow'],'conditions':['transport'],
                   'counterexamples':['intentional overlap'],'failure':'duplicate positions',
                   'correction':'spacing','required_effects':['object_path'],'next_experiment':'new script',
                   'evidence':[{'path':'evidence','sha256':hashlib.sha256(b'verified').hexdigest()}]}

    def report(self):return packet({'cases':[self.case]},self.root,{'reveal'})

    def test_missing_capability_explicit(self):
        c=self.report()['cases'][0]
        self.assertEqual(c['missing_compiler_effects'],['object_path'])
        self.assertFalse(c['production_authorized'])

    def test_stale_evidence_not_retrieved(self):
        (self.root/'evidence').write_bytes(b'changed')
        self.assertEqual(retrieve(self.report(),'flow'),[])

    def test_scope_filters(self):
        self.assertEqual(len(retrieve(self.report(),'flow')),1)
        self.assertEqual(retrieve(self.report(),'emotion'),[])

    def test_forged_approval_cannot_authorize(self):
        self.case['production_authorized']=True
        self.assertFalse(self.report()['cases'][0]['production_authorized'])

    def test_path_escape_rejected(self):
        self.case['evidence'][0]['path']='../outside'
        with self.assertRaises(ValueError):self.report()


if __name__=='__main__':unittest.main()
