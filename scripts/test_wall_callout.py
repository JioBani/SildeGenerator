import unittest
from PIL import Image, ImageDraw
from measure_wall_callout import measure


class CalloutTest(unittest.TestCase):
    def test_tip_and_wall(self):
        im = Image.new('RGB', (640, 360), '#420000')
        d = ImageDraw.Draw(im)
        d.line((313, 62, 313, 105), fill='#ffdd55', width=3)
        d.rectangle((290, 110, 330, 115), fill='#dd7044')
        self.assertEqual(measure(im), {'tip': [313.0, 105], 'wall_y': 110, 'gap': 5})

    def test_absent_is_not_zero(self):
        self.assertIsNone(measure(Image.new('RGB', (640, 360), '#420000')))

    def test_cream_text_is_not_arrow(self):
        im = Image.new('RGB', (640, 360), '#420000')
        d = ImageDraw.Draw(im)
        d.rectangle((285, 140, 330, 155), fill='#ffbf95')
        self.assertIsNone(measure(im))

    def test_missing_wall_not_approved(self):
        im = Image.new('RGB', (640, 360), '#420000')
        ImageDraw.Draw(im).line((313, 62, 313, 105), fill='#ffdd55', width=3)
        self.assertIsNone(measure(im)['gap'])

    def test_wrong_size(self):
        with self.assertRaises(ValueError):
            measure(Image.new('RGB', (1920, 1080)))


if __name__ == '__main__':
    unittest.main()
