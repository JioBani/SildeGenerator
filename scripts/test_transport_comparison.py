import unittest
from build_transport_comparison import scene


class ComparisonTests(unittest.TestCase):
    def test_cpu_has_two_finished_four_waiting(self):
        s=scene('CPU',3.508934,'unused.png')
        events=[o.get('performance_states',[]) for o in s.object_states]
        self.assertEqual(sum(bool(e) for e in events),2)
        self.assertLess(events[0][-1]['time'],events[1][0]['time'])
        self.assertTrue(all(p['time']<=s.duration_seconds for m in s.motion for p in m['points']))

    def test_gpu_has_six_simultaneous_calculations(self):
        s=scene('GPU',475/30-10.422131,'unused.png')
        self.assertEqual(len(s.object_states),6)
        self.assertEqual({o['performance_states'][0]['time'] for o in s.object_states},{1.0})
        self.assertEqual({o['performance_states'][1]['time'] for o in s.object_states},{2.5})
        self.assertEqual([o['performance_states'][1]['label'] for o in s.object_states],
                         ['3','6','9','12','15','18'])

    def test_example_holds_result_before_comparison(self):
        s=scene('DEMO',6.913197,'unused.png')
        self.assertEqual(len(s.object_states),1)
        self.assertGreater(s.duration_seconds-s.motion[0]['points'][-1]['time'],1.8)


if __name__=='__main__':unittest.main()
