"""Validate resolved test topology without starting Docker or reading app secrets."""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
result = subprocess.run(['docker', 'compose', '-p', 'astra-genre-test', '-f',
                         str(ROOT / 'docker-compose.genre-test.yml'), 'config', '--format', 'json'],
                        check=True, capture_output=True, text=True, cwd=ROOT)
config = json.loads(result.stdout)
assert config['name'] == 'astra-genre-test'
assert config['networks']['isolated'].get('internal')
assert set(config['networks']) == {'isolated', 'local_ui'}
for name, service in config['services'].items():
    assert service.get('restart') == 'no', name
    assert not service.get('secrets') and not service.get('env_file'), name
    expected_networks = {'isolated', 'local_ui'} if name in {'api', 'web'} else {'isolated'}
    assert service.get('network_mode') == 'none' or set(service['networks']) == expected_networks, name
    assert all(v['type'] == 'volume' for v in service.get('volumes', [])), name
    assert all(p['host_ip'] == '127.0.0.1' for p in service.get('ports', [])), name
runner = config['services']['runner']['environment']
assert (runner['RUNNER_MODE'], runner['IMAGE_PROVIDER'], runner['VOICE_PROVIDER']) == ('mock', 'mock', 'mock')
assert runner['RUNNER_ENV_FILE'] == '/nonexistent-test-settings'
assert not any('API_KEY' in k or 'TOKEN' in k for k in runner)
assert all(v['name'].startswith('astra-genre-test_') for v in config['volumes'].values())
print('PASS: isolated test volumes, internal network, mock providers, no host credential mounts, no auto-restart')
