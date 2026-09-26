import unittest
import cv2
import numpy as np
from measure_blood_particle_flow import displacement


class FlowTests(unittest.TestCase):
    def test_known_translation(self):
        image = np.zeros((100, 150, 3), dtype=np.uint8)
        for x in range(20, 130, 20):
            cv2.rectangle(image, (x, 30), (x+9, 41), (120, 160, 200), -1)
        moved = cv2.warpAffine(image, np.float32([[1,0,3],[0,1,-2]]), (150,100))
        found = displacement(image, moved, np.ones((100,150),dtype=np.uint8)*255)
        self.assertIsNotNone(found)
        self.assertAlmostEqual(found['dx'], 3, delta=.1)
        self.assertAlmostEqual(found['dy'], -2, delta=.1)

    def test_blank_is_missing_not_stationary(self):
        image = np.zeros((100,150,3),dtype=np.uint8)
        self.assertIsNone(displacement(image,image,np.ones((100,150),dtype=np.uint8)*255))


if __name__ == '__main__':
    unittest.main()
