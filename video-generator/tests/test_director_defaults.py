import os
import subprocess
import sys
import unittest
from pathlib import Path


class DirectorDefaultsTests(unittest.TestCase):
    def test_fresh_config_uses_low_effort_without_loading_secret_file(self):
        env = {key: os.environ[key] for key in ('SYSTEMROOT', 'PATH') if key in os.environ}
        env['RUNNER_ENV_FILE'] = str(Path(__file__).with_name('nonexistent-settings.fixture'))
        result = subprocess.check_output([sys.executable, '-c',
            "from app.config import settings; assert settings.codex_model == 'gpt-5.6-terra'; "
            "assert settings.codex_reasoning_effort == 'low'; print('PASS')"],
            cwd=Path(__file__).resolve().parents[1], env=env, text=True)
        self.assertEqual(result.strip(), 'PASS')
