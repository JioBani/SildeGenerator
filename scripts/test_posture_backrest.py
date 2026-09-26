import unittest
import cv2
import numpy as np
from measure_posture_backrest import orientation


class BackrestTests(unittest.TestCase):
    def test_known_slope(self):
        a = np.full((360,640,3), [255,208,78], np.uint8)
        cv2.line(a,(70,120),(240,218),(33,140,108),7)
        self.assertAlmostEqual(orientation(a)['angle_degrees'],30,delta=.6)

    def test_horizontal(self):
        a = np.full((360,640,3), [255,208,78], np.uint8)
        cv2.line(a,(70,220),(240,220),(33,140,108),7)
        self.assertAlmostEqual(orientation(a)['angle_degrees'],0,delta=.1)

    def test_absent(self):
        self.assertIsNone(orientation(np.full((360,640,3), [255,208,78], np.uint8)))


if __name__ == '__main__': unittest.main()
