import unittest
from PIL import Image, ImageDraw
from measure_reference_balloon import measure


class MeasurementTest(unittest.TestCase):
    def test_disconnected_lining_is_excluded(self):
        im = Image.new('RGB', (640, 360), (240, 140, 100))
        draw = ImageDraw.Draw(im)
        for y0, y1 in [(115, 125), (160, 199), (235, 245)]:
            draw.rectangle((300, y0, 340, y1), fill=(200, 20, 15))
        self.assertEqual(measure(im), 40)

    def test_no_balloon_is_zero(self):
        self.assertEqual(measure(Image.new('RGB', (640, 360), (240, 140, 100))), 0)

    def test_wrong_resolution_rejected(self):
        with self.assertRaises(ValueError):
            measure(Image.new('RGB', (1920, 1080)))


if __name__ == '__main__':
    unittest.main()
