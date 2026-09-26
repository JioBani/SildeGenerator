import unittest
from types import SimpleNamespace
from app.engine.harness_segments import segment_ranges


class SegmentRangesTests(unittest.TestCase):
    def test_legacy_partition(self):
        harness = SimpleNamespace(instance=object(), config={})
        self.assertEqual(segment_ranges(harness, list(range(5)), 2), [(0, 2), (2, 4), (4, 5)])
        self.assertEqual(segment_ranges(harness, [], 2), [])

    def test_invalid_partitions_cannot_drop_duplicate_or_reorder_scenes(self):
        for ranges in [[(0, 2)], [(0, 2), (1, 3)], [(1, 3)], [(0, 4)], [(0, True)], 'invalid']:
            harness = SimpleNamespace(instance=SimpleNamespace(plan_segments=lambda *args: ranges), config={})
            with self.assertRaises((ValueError, TypeError)):
                segment_ranges(harness, list(range(3)), 2)

    def test_optional_partition_can_extend_soft_size(self):
        harness = SimpleNamespace(instance=SimpleNamespace(plan_segments=lambda *args: [(0, 4), (4, 5)]), config={})
        self.assertEqual(segment_ranges(harness, list(range(5)), 2), [(0, 4), (4, 5)])
