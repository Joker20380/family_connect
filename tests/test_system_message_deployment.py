import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]


def test_external_publisher_compose_preserves_web_secret_boundary():
    if shutil.which('docker') is None:
        pytest.skip('Compose validation requires the Docker CLI, not a running daemon')
    environment = dict(os.environ, FC_PANEL_IMAGE='fc-panel:synthetic-qualified',
        FC_PUBLISHER_UID='1000', FC_PUBLISHER_GID='1000', FC_SYSTEM_PUBLISHER_TOKEN_FILE='/private/synthetic.token',
        FC_SYSTEM_PUBLISHER_ORIGIN='https://synthetic.invalid', DJANGO_SECRET_KEY='synthetic-only-test-key',
        POSTGRES_PASSWORD='synthetic-only-test-password')
    result = subprocess.run(['docker', 'compose', '--env-file', '/dev/null', '-f', str(ROOT / 'control_plane/compose.yaml'),
                             '-f', str(ROOT / 'deploy/system-messages/compose.publisher.yaml'),
                             'config', '--format', 'json'], env=environment, capture_output=True, check=True, timeout=10)
    services = json.loads(result.stdout)['services']
    publisher = services['system_publisher']
    console = services['console']
    assert publisher['image'] == console['image'] == 'fc-panel:synthetic-qualified'
    assert 'seed_demo' not in ' '.join(console['command'])
    assert 'migrate --noinput' in ' '.join(console['command'])
    assert 'collectstatic --noinput' in ' '.join(console['command'])
    assert publisher['user'] == '1000:1000' and publisher['read_only'] and publisher['init']
    assert publisher['restart'] == console['restart'] == services['postgres']['restart'] == 'unless-stopped'
    assert publisher['cap_drop'] == ['ALL'] and publisher['pids_limit'] == 64
    assert 'no-new-privileges:true' in publisher['security_opt']
    assert len(publisher['volumes']) == 1
    mount = dict(publisher['volumes'][0])
    assert mount.pop('bind').get('create_host_path', False) is False
    assert mount == dict(type='bind', source='/private/synthetic.token',
        target='/run/secrets/system-publisher.token', read_only=True)
    assert 'create_host_path: false' in (ROOT / 'deploy/system-messages/compose.publisher.yaml').read_text()
    assert 'synthetic.token' not in json.dumps(console)
    assert 'system-publisher.token' not in json.dumps(console)
    assert 'FC_SYSTEM_PUBLISHER_ORIGIN' not in console['environment']
    assert publisher['logging']['options'] == {'max-size': '2m', 'max-file': '2'}
    assert '--limit 1' in publisher['command'][2] and 'sleep 10' in publisher['command'][2]
    assert set(publisher['networks']) == {'local_only', 'loopback_ui'}
