import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from reference_curriculum import AXES, build_reference, intervals, resolve, seconds


class CurriculumTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root/'source.mp4').write_bytes(b'source fixture')
        (self.root/'candidate.mp4').write_bytes(b'candidate fixture')
        self.source_hash = hashlib.sha256(b'source fixture').hexdigest()
        self.artifact_hash = hashlib.sha256(b'candidate fixture').hexdigest()
        self.write('overview.json', {'probe': {'format': {'duration': '10.5'}},
                                    'segments': [{'start': 0, 'end': 10}], 'per_second': []})
        self.ref = {'id': 'fixture', 'label': 'Fixture', 'source': 'source.mp4', 'overview': 'overview.json',
                    'motion': [], 'studies': [], 'approved_reviews': [], 'transfer_review': None}

    def write(self, filename, value):
        (self.root/filename).write_text(json.dumps(value), encoding='utf-8')

    def review(self):
        return {'decision': 'PASS', 'reviewer_type': 'human', 'reviewer': 'fixture-reviewer',
                'source_sha256': self.source_hash, 'artifact': 'candidate.mp4',
                'artifact_sha256': self.artifact_hash, 'axes': dict.fromkeys(AXES, 'PASS'),
                'source_windows': [[0, 10.5]]}

    def test_overlap_is_not_double_counted(self):
        self.assertEqual(seconds([[0, 4], [2, 6], [6, 10]], 10), 10)

    def test_bad_ranges_rejected(self):
        for pair in [[-1, 2], [2, 1], [0, 11], [0, float('inf')]]:
            with self.assertRaises(ValueError):
                intervals([pair], 10)

    def test_path_escape_rejected(self):
        with self.assertRaises(ValueError):
            resolve(self.root, '../outside.json')

    def test_tail_preserved(self):
        result = build_reference(self.ref, self.root)
        self.assertEqual(result['tasks'][-1]['source_end'], 10.5)
        self.assertEqual(sum(t['source_end']-t['source_start'] for t in result['tasks']), 10.5)

    def test_sample_is_not_approval(self):
        self.ref['studies'] = [{'file': 'candidate.mp4', 'source_windows': [[0, 10.5]]}]
        result = build_reference(self.ref, self.root)
        self.assertEqual(result['partial_study_seconds'], 10.5)
        self.assertEqual(result['approved_seconds'], 0)
        self.assertEqual(result['status'], 'IN_PROGRESS')

    def test_model_review_cannot_promote(self):
        review = self.review()
        review['reviewer_type'] = 'model'
        self.write('review.json', review)
        self.ref['approved_reviews'] = ['review.json']
        self.assertFalse(build_reference(self.ref, self.root)['quality_approved'])

    def test_rejected_semantics_excluded(self):
        self.ref['studies'] = [{'file':'candidate.mp4','source_windows':[[0,10.5]],'status':'REJECTED_SEMANTICS'}]
        self.assertEqual(build_reference(self.ref,self.root)['partial_study_seconds'],0)

    def test_stale_artifact_cannot_promote(self):
        self.write('review.json', self.review())
        self.ref['approved_reviews'] = ['review.json']
        (self.root/'candidate.mp4').write_bytes(b'changed')
        self.assertEqual(build_reference(self.ref, self.root)['approved_seconds'], 0)

    def test_audio_review_required(self):
        review = self.review()
        del review['axes']['audio']
        self.write('review.json', review)
        self.ref['approved_reviews'] = ['review.json']
        self.assertFalse(build_reference(self.ref, self.root)['quality_approved'])

    def test_completion_requires_transfer(self):
        self.write('review.json', self.review())
        self.ref['approved_reviews'] = ['review.json']
        self.assertEqual(build_reference(self.ref, self.root)['status'], 'IN_PROGRESS')
        transfer = self.review()
        (self.root/'transfer.mp4').write_bytes(b'different transfer fixture')
        (self.root/'new-script.txt').write_text('A new non-medical script', encoding='utf-8')
        transfer.update({'different_script': True, 'script': 'new-script.txt',
                         'script_sha256': hashlib.sha256((self.root/'new-script.txt').read_bytes()).hexdigest(),
                         'artifact': 'transfer.mp4', 'artifact_sha256': hashlib.sha256(b'different transfer fixture').hexdigest()})
        self.write('transfer.json', transfer)
        self.ref['transfer_review'] = 'transfer.json'
        self.assertEqual(build_reference(self.ref, self.root)['status'], 'COMPLETE')

    def test_same_artifact_is_not_a_transfer(self):
        review = self.review()
        self.write('review.json', review)
        self.ref['approved_reviews'] = ['review.json']
        (self.root/'script.txt').write_bytes(b'new script')
        review.update({'different_script': True, 'script': 'script.txt', 'script_sha256': hashlib.sha256(b'new script').hexdigest()})
        self.write('transfer.json', review)
        self.ref['transfer_review'] = 'transfer.json'
        self.assertFalse(build_reference(self.ref, self.root)['transfer_passed'])

    def test_missing_source_stays_unknown(self):
        self.ref['source'] = None
        self.assertEqual(build_reference(self.ref, self.root)['status'], 'SOURCE_NOT_REGISTERED')


if __name__ == '__main__':
    unittest.main()
