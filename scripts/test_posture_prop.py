import unittest
import numpy as np
from measure_posture_prop import detect, fit_visible_fragment


class PropTests(unittest.TestCase):
    def image(self):
        return np.full((360, 640, 3), [250, 207, 78], dtype=np.uint8)

    def test_single_prop(self):
        a = self.image(); a[150:164, 200:270] = [25, 185, 145]
        self.assertEqual(detect(a)['resolved']['bounds'], [200, 150, 270, 164])

    def test_ambiguous_is_not_linked(self):
        a = self.image(); a[150:164, 200:270] = [25, 185, 145]
        a[220:234, 400:470] = [25, 185, 145]
        self.assertIsNone(detect(a)['resolved'])

    def test_background_is_not_prop(self):
        a = np.full((360, 640, 3), [33, 135, 107], dtype=np.uint8)
        self.assertIsNone(detect(a)['resolved'])

    def test_fragment_requires_continuity(self):
        rows = [{'source_second': i*.04, 'resolved': {'center': [i, i*i]}} for i in range(8)]
        self.assertLess(fit_visible_fragment(rows, 0, 1)['maximum_center_residual_pixels'], 1e-8)
        rows[3]['resolved'] = None
        self.assertEqual(fit_visible_fragment(rows, 0, 1)['status'], 'UNRESOLVED')

    def test_fragment_rejects_time_gap(self):
        rows = [{'source_second': i*.1, 'resolved': {'center': [i, i*i]}} for i in range(8)]
        self.assertEqual(fit_visible_fragment(rows, 0, 1)['status'], 'UNRESOLVED')


if __name__ == '__main__':
    unittest.main()
