import unittest
from PIL import Image,ImageDraw
from measure_deposit_growth import envelope


class DepositTest(unittest.TestCase):
    def test_envelope(self):
        im=Image.new('RGB',(640,360),'#550000')
        ImageDraw.Draw(im).rectangle((250,250,350,270),fill='#ffdb00')
        self.assertEqual(envelope(im)['bounds'],[250,250,351,271])

    def test_cream_cells_and_top_arrow_excluded(self):
        im=Image.new('RGB',(640,360),'#550000');d=ImageDraw.Draw(im)
        d.ellipse((280,240,295,255),fill='#fff0bd')
        d.line((313,60,313,105),fill='#ffdb00',width=3)
        self.assertIsNone(envelope(im))

    def test_holes_do_not_mean_envelope_shrank(self):
        im=Image.new('RGB',(640,360),'#550000');d=ImageDraw.Draw(im)
        d.rectangle((250,250,350,270),fill='#ffdb00');before=envelope(im)
        d.rectangle((260,253,340,267),fill='#886000');after=envelope(im)
        self.assertEqual(before['bounds'],after['bounds'])
        self.assertLess(after['colored_pixels'],before['colored_pixels'])

    def test_clipped_growth_rejected(self):
        im=Image.new('RGB',(640,360),'#550000')
        ImageDraw.Draw(im).rectangle((70,250,320,270),fill='#ffdb00')
        with self.assertRaises(ValueError):envelope(im)


if __name__=='__main__':unittest.main()
