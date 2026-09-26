import unittest
import numpy as np
from scripts.measure_blood_bulge import measure, lumen_support


class BulgeTests(unittest.TestCase):
    def test_dimmed_bands_and_fluid(self):
        image=np.zeros((360,640,3),np.uint8)
        image[120:129]=(34,44,162)
        image[240:249]=(34,44,162)
        image[165:211]=(26,45,164)
        self.assertEqual(measure(image)['upper'][26],[270,120,128])
        self.assertEqual(lumen_support(image)[26],[270,165,210])

    def test_fluid_envelope_with_internal_occlusion(self):
        image=np.zeros((360,640,3),np.uint8)
        image[165:211]=(40,70,253)
        image[181:195]=(2,4,140)
        self.assertEqual(lumen_support(image)[26],[270,165,210])

    def test_no_fluid_support(self):
        self.assertEqual(lumen_support(np.zeros((360,640,3),np.uint8)),[])

    def test_known_bands(self):
        image=np.zeros((360,640,3),np.uint8)
        image[120:129]=(60,90,230)
        image[240:249]=(60,90,230)
        result=measure(image)
        self.assertEqual(result['upper'][26],[270,120,128])
        self.assertEqual(result['lower'][26],[270,240,248])

    def test_cream_not_wall(self):
        image=np.full((360,640,3),(200,230,245),np.uint8)
        self.assertEqual(measure(image),{'upper':[],'lower':[]})

    def test_disconnected_particle_is_not_band_extent(self):
        image=np.zeros((360,640,3),np.uint8)
        image[210:213,266:275]=(60,90,230)
        image[240:249]=(60,90,230)
        self.assertEqual(measure(image)['lower'][26],[270,240,248])

    def test_tied_bands_unresolved(self):
        image=np.zeros((360,640,3),np.uint8)
        image[220:229]=(60,90,230)
        image[240:249]=(60,90,230)
        self.assertEqual(measure(image)['lower'],[])

    def test_bad_resolution(self):
        with self.assertRaises(ValueError):
            measure(np.zeros((180,320,3),np.uint8))


if __name__=='__main__':
    unittest.main()
