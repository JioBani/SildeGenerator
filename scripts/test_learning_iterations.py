import unittest
from reference_learning import iteration_checkpoint


def attempt(identity, failures):
    return {'id':identity,'hypothesis':'Longer hold improves readability',
            'changed_variables':['hold_duration'],'observation':'Not yet readable',
            'next_action':'Inspect text density','unresolved_failures':failures}


class IterationTests(unittest.TestCase):
    def test_three_repeated_failures_require_cause_review(self):
        result=iteration_checkpoint([attempt(str(i),['readability','readability']) for i in range(3)])
        self.assertEqual(result['status'],'CAUSE_REVIEW_REQUIRED')
        self.assertEqual(result['repeated_failure_families'],['readability'])
        self.assertFalse(result['automatic_retry_authorized'])

    def test_resolved_failure_breaks_streak(self):
        result=iteration_checkpoint([attempt('1',['a']),attempt('2',[]),attempt('3',['a'])])
        self.assertEqual(result['status'],'NEXT_EXPERIMENT_REVIEW')

    def test_missing_history_is_not_success(self):
        self.assertEqual(iteration_checkpoint([])['status'],'RECORD_INCOMPLETE')

    def test_missing_observation_is_reported(self):
        row=attempt('1',[])
        del row['observation']
        self.assertIn('1:observation',iteration_checkpoint([row])['missing_records'])

    def test_duplicate_id_rejected(self):
        with self.assertRaises(ValueError):iteration_checkpoint([attempt('1',[]),attempt('1',[])])

    def test_invalid_family_rejected(self):
        with self.assertRaises(ValueError):iteration_checkpoint([attempt('1','readability')])


if __name__=='__main__':unittest.main()
