import unittest
from PIL import Image, ImageDraw
from measure_pressure_walls import profile


class ProfileTest(unittest.TestCase):
    def test_line(self):
        im = Image.new('RGB', (640, 360), '#640000')
        ImageDraw.Draw(im).rectangle((0, 105, 639, 109), fill='#ffe8c2')
        self.assertTrue(all(y == 107 for x,y in profile(im,70,140)))

    def test_missing_rejected(self):
        with self.assertRaises(ValueError):
            profile(Image.new('RGB',(640,360),'black'),70,140)

    def test_ambiguous_rejected(self):
        im = Image.new('RGB',(640,360),'black')
        d = ImageDraw.Draw(im)
        d.line((0,90,639,90),fill='#ffe8c2',width=3)
        d.line((0,120,639,120),fill='#ffe8c2',width=3)
        with self.assertRaises(ValueError):
            profile(im,70,140)


if __name__ == '__main__':
    unittest.main()
