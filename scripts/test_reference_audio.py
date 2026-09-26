import unittest
import numpy as np
from analyze_reference_audio import envelope, quiet_intervals, summarize


class AudioEvidenceTest(unittest.TestCase):
    def test_antiphase_not_cancelled(self):
        rows=envelope(np.tile([.5,-.5],(320,1)))
        self.assertAlmostEqual(rows[0]['rms_dbfs'],-6.021,places=3)

    def test_silence(self):
        rows=envelope(np.zeros((3200,2)))
        self.assertEqual(quiet_intervals(rows),[[0,.2]])

    def test_short_tail_exact_duration(self):
        rows=envelope(np.zeros((321,2)))
        self.assertEqual(rows[-1]['end'],321/16000)
        self.assertEqual(quiet_intervals(rows),[])

    def test_partition_overlap_not_double_count(self):
        rows=envelope(np.zeros((3200,2)))
        parts=summarize(rows,[{'range':[0,.11],'function':'a'},{'range':[.11,.2],'function':'b'}])
        self.assertAlmostEqual(sum(p['low_energy_seconds'] for p in parts),.2)

    def test_nonfinite_rejected(self):
        with self.assertRaises(ValueError):envelope([[float('nan'),0]])


if __name__=='__main__':unittest.main()
