import unittest

from report_bulge_layer_diagnostics import compare_support


class SupportComparisonTests(unittest.TestCase):
    def test_measures_both_edges(self):
        result = compare_support([[320, 172, 201]], [[320, 172, 195]])
        self.assertEqual(result['columns'][0]['max_edge_error'], 6)

    def test_missing_is_not_zero_error(self):
        result = compare_support([[320, 172, 201]], [])
        self.assertEqual(result['missing_columns'], [320])
        self.assertEqual(result['matched_columns'], 0)

    def test_column_order_is_not_identity(self):
        result = compare_support([[310, 1, 5], [320, 2, 6]], [[320, 2, 6], [310, 1, 5]])
        self.assertEqual([c['max_edge_error'] for c in result['columns']], [0, 0])


if __name__ == '__main__':
    unittest.main()
