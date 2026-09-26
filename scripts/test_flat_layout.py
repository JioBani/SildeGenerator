import tempfile
import unittest
from pathlib import Path
from PIL import Image, ImageDraw
from measure_flat_layout import bounds


class LayoutTest(unittest.TestCase):
    def test_known_foreground(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'image.png'
            image = Image.new('RGB', (640, 360), (251, 208, 82))
            ImageDraw.Draw(image).rectangle((100, 20, 299, 319), fill=(3, 60, 90))
            image.save(path)
            self.assertEqual(bounds(path)['bbox'], (100, 20, 300, 320))

    def test_empty_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'image.png'
            Image.new('RGB', (640, 360), (251, 208, 82)).save(path)
            with self.assertRaises(ValueError):
                bounds(path)


if __name__ == '__main__':
    unittest.main()
