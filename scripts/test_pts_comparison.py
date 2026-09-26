import unittest
from render_pts_comparison import presented_index


class PtsComparisonTests(unittest.TestCase):
    def test_no_future_frame(self):
        self.assertEqual(presented_index([106, 106.04, 106.08], 106.033), 0)

    def test_exact_boundary(self):
        self.assertEqual(presented_index([106, 106.04, 106.08], 106.04), 1)

    def test_no_early_clamping(self):
        with self.assertRaises(ValueError):
            presented_index([106.02, 106.06], 106)

    def test_irregular_pts(self):
        self.assertEqual(presented_index([0, .041, .1, .17], .169), 2)


if __name__ == '__main__':
    unittest.main()
