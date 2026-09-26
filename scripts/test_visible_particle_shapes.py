import unittest
from PIL import Image,ImageDraw
from measure_visible_particle_shapes import shapes


class VisibleShapesTest(unittest.TestCase):
    def test_touching_pair_retained(self):
        im=Image.new('RGB',(640,360),'#900000');d=ImageDraw.Draw(im)
        d.ellipse((100,180,114,194),fill='#fff0bd');d.ellipse((113,180,127,194),fill='#fff0bd')
        self.assertEqual(len(shapes(im)),2)

    def test_yellow_is_not_light_particle(self):
        im=Image.new('RGB',(640,360),'#900000')
        ImageDraw.Draw(im).ellipse((100,180,114,194),fill='#ffdd00')
        self.assertEqual(shapes(im),[])

    def test_color_preserved(self):
        im=Image.new('RGB',(640,360),'#900000')
        ImageDraw.Draw(im).ellipse((100,180,114,194),fill='#cbbb77')
        self.assertEqual(shapes(im)[0]['fill'],'#cbbb77')


if __name__=='__main__':unittest.main()
