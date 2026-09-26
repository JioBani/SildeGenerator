import unittest
from PIL import Image, ImageDraw
from measure_wall_geometry import boundaries


class GeometryTest(unittest.TestCase):
    def test_outer_edges(self):
        im=Image.new('RGB',(640,360),'#400500');d=ImageDraw.Draw(im)
        d.rectangle((0,100,639,120),fill='#ef603b')
        d.rectangle((0,250,639,270),fill='#ef603b')
        d.rectangle((270,40,350,53),fill='#ef603b')
        upper,lower=boundaries(im)
        self.assertTrue(all(y==100 for x,y in upper))
        self.assertTrue(all(y==270 for x,y in lower))

    def test_missing_rejected(self):
        with self.assertRaises(ValueError):boundaries(Image.new('RGB',(640,360),'black'))

    def test_texture_gaps_closed_but_broad_bulge_preserved(self):
        im=Image.new('RGB',(640,360),'#400500');d=ImageDraw.Draw(im)
        d.rectangle((0,100,639,120),fill='#ef603b')
        d.rectangle((200,70,320,120),fill='#ef603b')
        d.rectangle((0,250,639,270),fill='#ef603b')
        for x in range(10,640,16):
            d.rectangle((x,100,x+7,110),fill='#400500')
        upper,_=boundaries(im)
        self.assertTrue(all(y==100 for x,y in upper if x<180 or x>340))
        self.assertTrue(all(y==70 for x,y in upper if 220<x<300))

    def test_yellow_arrow_not_wall(self):
        im=Image.new('RGB',(640,360),'black')
        ImageDraw.Draw(im).rectangle((0,100,639,120),fill='#ffdd55')
        with self.assertRaises(ValueError):boundaries(im)


if __name__=='__main__':unittest.main()
