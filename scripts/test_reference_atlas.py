import copy
import json
from pathlib import Path
import unittest
from compile_reference_atlas import scene_record, validate


class AtlasTests(unittest.TestCase):
    def setUp(self):
        self.atlas = json.loads((Path(__file__).resolve().parents[1]/'docs/reference-director-atlas.json').read_text(encoding='utf-8'))

    def test_full_duration_partitioning(self):
        validate(self.atlas)

    def test_gap_rejected(self):
        self.atlas['references'][0]['partitions'][1]['range'][0] += 1
        with self.assertRaises(ValueError):
            validate(self.atlas)

    def test_tail_rejected(self):
        self.atlas['references'][0]['partitions'].pop()
        with self.assertRaises(ValueError):
            validate(self.atlas)

    def test_no_implicit_approval(self):
        for ref in self.atlas['references']:
            for i, part in enumerate(ref['partitions']):
                record = scene_record(ref, part, i, self.atlas['designs'][ref['design']])
                self.assertFalse(record['render_authorized'])
                self.assertFalse(record['production_promotion'])
                self.assertIsNone(record['motion']['measured_trajectory'])
                self.assertEqual(record['boundary_status'], 'ANALYSIS_PARTITION_NOT_VERIFIED_CUT')

    def test_duplicate_reference_rejected(self):
        self.atlas['references'].append(copy.deepcopy(self.atlas['references'][0]))
        with self.assertRaises(ValueError):
            validate(self.atlas)


if __name__ == '__main__':
    unittest.main()
