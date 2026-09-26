import unittest
from build_blood_transport import integrate


class TransportTests(unittest.TestCase):
    def test_unequal_intervals(self):
        rows=[{'start':10,'end':10.1,'measurement':{'dx':2}},
              {'start':10.1,'end':10.3,'measurement':{'dx':7}}]
        result=integrate(rows)
        self.assertEqual(result[-1][1],9)
        self.assertAlmostEqual(result[-1][0],.3)

    def test_missing_rejected(self):
        with self.assertRaises(ValueError):
            integrate([{'start':0,'end':1,'measurement':None}])

    def test_gap_rejected(self):
        with self.assertRaises(ValueError):
            integrate([{'start':0,'end':1,'measurement':{'dx':2}},
                       {'start':2,'end':3,'measurement':{'dx':2}}])


if __name__=='__main__':
    unittest.main()
