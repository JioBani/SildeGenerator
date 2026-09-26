import unittest
import cv2
import numpy as np
from measure_posture_alignment import measure


class AlignmentTests(unittest.TestCase):
    def image(self):
        a = np.full((360, 640, 3), [30, 180, 162], np.uint8)
        a[:, 322:] = [255, 208, 78]
        a[60:340, 100:170] = [0, 60, 85]
        a[60:340, 400:480] = [0, 60, 85]
        return a

    def test_known_centers_and_split(self):
        a = self.image()
        for x in [140, 440]:
            for y in [100, 115, 130]:
                cv2.circle(a, (x, y), 2, (255, 248, 230), -1)
        r = measure(a)
        self.assertEqual(r['divider_x'], 322)
        self.assertEqual([len(r['left']), len(r['right'])], [3, 3])
        self.assertEqual(r['left'][0]['x'], 140)

    def test_bright_background_distractor_rejected(self):
        a = self.image()
        cv2.circle(a, (280, 120), 3, (255, 248, 230), -1)
        self.assertEqual(measure(a)['points'], [])

    def test_dense_marker_neighbors_are_not_rejected(self):
        a = self.image()
        for y in range(95, 293, 6):
            cv2.circle(a, (140, y), 2, (255, 248, 230), -1)
        self.assertEqual(len(measure(a)['points']), 33)

    def test_absent_divider_is_not_guessed(self):
        a = self.image(); a[:, 322:] = [30, 180, 162]
        self.assertIsNone(measure(a)['divider_x'])

    def test_divider_near_right_edge(self):
        a = self.image(); a[:, 322:] = [30, 180, 162]
        a[:, 610:] = [255, 208, 78]
        self.assertEqual(measure(a)['divider_x'], 610)

    def test_wrong_resolution_rejected(self):
        with self.assertRaises(ValueError):
            measure(np.zeros((720, 1280, 3), np.uint8))


if __name__ == '__main__':
    unittest.main()
