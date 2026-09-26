import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from reference_learning import assess_experiment


class QualityTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        (self.root/'candidate').write_bytes(b'video')
        (self.root/'measurement').write_text(json.dumps({'error':.01}),encoding='utf-8')
        def evidence(name):return {'path':name,'sha256':hashlib.sha256((self.root/name).read_bytes()).hexdigest()}
        self.case={'id':'test','candidate':evidence('candidate'),'best_version':'approved-old',
                   'checks':[{'id':'position','evidence':evidence('measurement'),'field':'error','op':'lte','expected':.25}],
                   'next_action':'Human visual comparison'}

    def test_numbers_cannot_approve_quality(self):
        r=assess_experiment(self.case,self.root)
        self.assertTrue(r['technical_pass'])
        self.assertEqual(r['decision'],'HUMAN_QUALITY_REVIEW_REQUIRED')
        self.assertFalse(r['production_authorized'])
        self.assertFalse(r['replace_best'])
        self.assertEqual(len(r['quality_review_questions']),7)

    def test_known_regression_preserves_best(self):
        self.case['known_regressions']=['identity changed']
        r=assess_experiment(self.case,self.root)
        self.assertEqual(r['decision'],'REWORK_PRESERVE_BEST')
        self.assertEqual(r['best_version'],'approved-old')

    def test_stale_artifact_blocks(self):
        (self.root/'candidate').write_bytes(b'changed')
        self.assertEqual(assess_experiment(self.case,self.root)['decision'],'EVIDENCE_INVALID')

    def test_stale_measurement_blocks(self):
        (self.root/'measurement').write_text('{}')
        self.assertEqual(assess_experiment(self.case,self.root)['decision'],'EVIDENCE_INVALID')

    def test_no_checks_does_not_pass(self):
        self.case['checks']=[]
        self.assertFalse(assess_experiment(self.case,self.root)['technical_pass'])


if __name__=='__main__':unittest.main()
