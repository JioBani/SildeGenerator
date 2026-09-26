import unittest
from PIL import Image,ImageDraw
from measure_deposit_structure import columns


class ColumnTest(unittest.TestCase):
    def test_separate_columns(self):
        im=Image.new('RGB',(640,360),'#a41100');d=ImageDraw.Draw(im)
        d.rectangle((250,230,260,260),fill='#bb8b00');d.rectangle((265,225,277,263),fill='#bb8b00')
        self.assertEqual(columns(im),[{'x':250,'y':230,'width':11,'height':31},{'x':265,'y':225,'width':13,'height':39}])

    def test_yellow_region_is_not_column(self):
        im=Image.new('RGB',(640,360),'#a41100')
        ImageDraw.Draw(im).rectangle((250,230,260,260),fill='#ffdc00')
        self.assertEqual(columns(im),[])


if __name__=='__main__':unittest.main()
