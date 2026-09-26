import unittest
import numpy as np
from measure_blood_context_transition import teal_fraction, sustained_onset


class ContextTransitionTests(unittest.TestCase):
    def test_color_discrimination(self):
        for color in ([180, 30, 15], [255, 210, 40], [240, 230, 180]):
            self.assertEqual(teal_fraction(np.full((4, 4, 3), color)), 0)
        self.assertEqual(teal_fraction(np.full((4, 4, 3), [25, 150, 130])), 1)

    def test_flash_is_not_sustained(self):
        rows = [{'source_second': i, 'teal_fraction': v}
                for i, v in enumerate([0, .4, 0, .2, .3, .2])]
        self.assertEqual(sustained_onset(rows), 3)

    def test_no_event(self):
        self.assertIsNone(sustained_onset([]))
        self.assertIsNone(sustained_onset([{'source_second': 1, 'teal_fraction': 1}]))


if __name__ == '__main__':
    unittest.main()
