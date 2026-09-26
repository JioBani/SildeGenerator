import unittest
from scripts.assemble_reference_study import validate


class CoverageTests(unittest.TestCase):
    def test_contiguous(self):
        validate([{'source_window': [60,90]}, {'source_window': [90,106]}, {'source_window': [106,120]}])

    def test_gap_overlap_reordering(self):
        for window in [[91,106], [89,106], [50,60], [90,90]]:
            with self.subTest(window=window), self.assertRaises(ValueError):
                validate([{'source_window': [60,90]}, {'source_window': window}])

    def test_empty(self):
        with self.assertRaises(ValueError):
            validate([])


if __name__ == '__main__':
    unittest.main()
