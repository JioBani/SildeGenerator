import unittest
from PIL import Image,ImageDraw
from track_deposit_particles import detect,associate


class ParticleTest(unittest.TestCase):
    def test_circle_and_yellow_rejection(self):
        im=Image.new('RGB',(640,360),'#900000');d=ImageDraw.Draw(im)
        d.ellipse((100,180,114,194),fill='#fff0bd')
        d.ellipse((200,180,214,194),fill='#ffdd00')
        self.assertEqual(len(detect(im)),1)

    def test_unique_motion(self):
        self.assertEqual(associate([{'x':10,'y':10}],[{'x':15,'y':11}]),{0:0})

    def test_ambiguous_merge_breaks(self):
        self.assertEqual(associate([{'x':10,'y':10},{'x':20,'y':10}],[{'x':15,'y':10}]),{})

    def test_missing_frame_not_bridged(self):
        self.assertEqual(associate([],[{'x':15,'y':10}]),{})


if __name__=='__main__':unittest.main()
