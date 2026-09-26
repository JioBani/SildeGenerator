import unittest
from PIL import Image,ImageDraw
from measure_micro_transition import bounds


class PanelTest(unittest.TestCase):
    def test_panel(self):
        im=Image.new('RGB',(640,360),'#760000');ImageDraw.Draw(im).rectangle((160,0,639,359),fill='#247a70')
        self.assertEqual(bounds(im),[160,640])
    def test_prop_rejected(self):
        im=Image.new('RGB',(640,360),'white');ImageDraw.Draw(im).rectangle((200,100,300,200),fill='#247a70')
        self.assertIsNone(bounds(im))
    def test_disjoint_not_joined(self):
        im=Image.new('RGB',(640,360),'white');d=ImageDraw.Draw(im)
        d.rectangle((0,0,49,359),fill='#247a70');d.rectangle((400,0,639,359),fill='#247a70')
        self.assertEqual(bounds(im),[400,640])
    def test_vertical_exit(self):
        im=Image.new('RGB',(640,360),'#760000');ImageDraw.Draw(im).rectangle((0,120,639,359),fill='#247a70')
        self.assertEqual(bounds(im,axis=1),[120,360])


if __name__=='__main__':unittest.main()
