import json
import os
from pathlib import Path
import runpy
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]


class DirectorBenchmarkTests(unittest.TestCase):
    def test_prepare_never_opens_http_and_records_same_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            script = root / 'input.txt'
            script.write_text('두 밤하늘을 비교합니다. 인물이 이동합니다.', encoding='utf-8')
            output = root / 'prepared'
            argv = ['prepare_director_benchmark.py', str(script), str(output)]
            with patch.dict(os.environ), patch.object(sys, 'argv', argv), \
                 patch('httpx.AsyncClient', side_effect=AssertionError('network forbidden')):
                runpy.run_path(str(ROOT / 'scripts/prepare_director_benchmark.py'), run_name='__main__')
            reviews = [json.loads(p.read_text(encoding='utf-8')) for p in output.glob('*/review.json')]
            self.assertEqual(len(reviews), 2)
            self.assertEqual(len({r['source_sha256'] for r in reviews}), 1)
            self.assertEqual(len({r['prompt_sha256'] for r in reviews}), 2)
            for review in reviews:
                self.assertEqual(review['status'], 'PREPARED_NOT_EXECUTED')
                self.assertEqual(review['planning_requests_attempted'], 0)
                self.assertEqual((review['image_tasks'], review['voice_tasks'], review['render_jobs']), (0, 0, 0))
                self.assertEqual(review['effort'], 'low')
            prompt = (output / 'research_pilot' / 'director-input.txt').read_text(encoding='utf-8')
            self.assertIn('source_unit_count 합', prompt)
            self.assertIn('범위를 벗어난 번호나 누락된 대상을 런타임이 보정', prompt)
            self.assertIn('runtime/research-risk-questions.json', prompt)
            baseline = (output / 'baseline' / 'director-input.txt').read_text(encoding='utf-8')
            self.assertNotIn('runtime/research-risk-questions.json', baseline)
            self.assertEqual({r['harness']['id'] for r in reviews}, {'astra-motion'})

    def test_live_batch_rejected_before_any_network(self):
        with patch.dict(os.environ), patch.object(sys, 'argv', [
            'prepare_director_benchmark.py', 'absent.txt', 'absent-output', '--execute-subscription']), \
             patch('httpx.AsyncClient', side_effect=AssertionError('network forbidden')):
            with self.assertRaises(SystemExit) as stopped:
                runpy.run_path(str(ROOT / 'scripts/prepare_director_benchmark.py'), run_name='__main__')
            self.assertEqual(stopped.exception.code, 2)

    def test_remote_subscription_bridge_is_rejected_before_any_network(self):
        with patch.dict(os.environ), patch.object(sys, 'argv', [
            'prepare_director_benchmark.py', 'absent.txt', 'absent-output',
            '--variant', 'baseline', '--execute-subscription',
            '--subscription-base-url', 'https://example.com']), \
             patch('httpx.AsyncClient', side_effect=AssertionError('network forbidden')):
            with self.assertRaises(SystemExit) as stopped:
                runpy.run_path(str(ROOT / 'scripts/prepare_director_benchmark.py'), run_name='__main__')
            self.assertEqual(stopped.exception.code, 2)
