import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from resume_concept_probe import checked_resume
from app.concept_planning import concept_context
from app.harness_sdk.concept_design import concept_extension, digest
from app.harness_sdk.semantic_beats import RelatedScriptAnalysis
from app.tracking import sha256_file
from test_concept_planning import batch, reports
from test_semantic_planning import SCRIPT, analysis_payload, contract
import hashlib


class ConceptResumeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name); self.probe=self.root/'probe'; self.review=self.root/'review'
        (self.probe/'work').mkdir(parents=True); self.review.mkdir()
        self.contract=contract('semantic-beats-0.2',film=True)
        self.contract['concept_selection']=concept_extension()
        data=analysis_payload(); data['version']='semantic-beats-0.2'
        for beat in data['beats']: beat.pop('cause_beat_numbers'); beat['relations']=[]
        analysis=RelatedScriptAnalysis.model_validate(data)
        script_hash=hashlib.sha256(SCRIPT.encode()).hexdigest()
        self.analysis_path=self.probe/'work/semantic-analysis-1.json'
        self.candidates_path=self.probe/'work/concept-candidates.json'
        self.write(self.analysis_path,dict(status='STRUCTURAL_PASS',analysis=data,script_sha256=script_hash,attempt=1))
        self.write(self.candidates_path,dict(batch=batch().model_dump(mode='json'),script_sha256=script_hash))
        self.write(self.review/'input-evidence.json',dict(candidates_sha256=sha256_file(self.candidates_path),analysis_sha256=sha256_file(self.analysis_path)))
        for order,report in zip(('abc','cba'),reports()):
            report.update(script_sha256=script_hash,context_sha256=digest(concept_context(analysis,self.contract,'cinematic_realism')),
                          model='gpt-5.6-terra',evaluator_version='concept-review-0.4')
            self.write(self.review/f'concept-review-{order}.json',report)

    def write(self,path,value): path.write_text(json.dumps(value),encoding='utf-8')
    def run_check(self): return checked_resume(SCRIPT,self.probe,self.review,self.contract)

    def test_reuses_only_bound_evidence_and_remaining_budget(self):
        analysis,concept,budget,comparison,paths=self.run_check()
        self.assertEqual(2,budget); self.assertEqual(5,len(paths))
        self.assertEqual(SCRIPT,''.join(b.literal_content for b in analysis.beats))
        self.assertEqual('candidate-0',concept.design.concept_id)

    def test_changed_candidate_analysis_or_review_policy_is_rejected(self):
        original=self.candidates_path.read_bytes()
        self.candidates_path.write_bytes(original+b' ')
        with self.assertRaisesRegex(ValueError,'input_changed'): self.run_check()
        self.candidates_path.write_bytes(original)
        path=self.review/'concept-review-abc.json'; report=json.loads(path.read_text())
        report['context_sha256']='old-policy'; self.write(path,report)
        with self.assertRaisesRegex(ValueError,'policy_changed'): self.run_check()

    def test_unpassed_preference_is_not_trusted_from_receipt(self):
        path=self.review/'concept-review-abc.json'; report=json.loads(path.read_text())
        report['verdict']['candidates'][0]['executable']='FAIL'
        report['verdict']['candidates'][0]['repair_target']='Fix unsupported request'
        self.write(path,report)
        with self.assertRaisesRegex(ValueError,'invalid_review'): self.run_check()

    def test_stale_numeric_analysis_is_checked_again(self):
        value=json.loads(self.analysis_path.read_text())
        value['analysis']['beats'][1]['grammar']='cumulative_change'
        self.write(self.analysis_path,value)
        with self.assertRaisesRegex(ValueError,'numeric_grammar'): self.run_check()
