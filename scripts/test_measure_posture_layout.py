import unittest

import numpy as np

from scripts.measure_posture_layout import bounds


class LayoutBoundsTests(unittest.TestCase):
    def test_known_foreground_and_noise(self):
        image = np.full((360, 640, 3), (78, 208, 255), dtype=np.uint8)
        image[50:210, 100:250] = (102, 73, 0)
        image[300, 600] = 0
        self.assertEqual(bounds(image), [100, 50, 250, 210])

    def test_wrong_scene_rejected(self):
        with self.assertRaisesRegex(ValueError, 'yellow'):
            bounds(np.zeros((360, 640, 3), dtype=np.uint8))

    def test_empty_field_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Insufficient'):
            bounds(np.full((360, 640, 3), (78, 208, 255), dtype=np.uint8))


if __name__ == '__main__':
    unittest.main()
