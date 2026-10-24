import json
import os
from pathlib import Path
import subprocess
import time
import uuid

import pytest

ROOT = Path(__file__).resolve().parents[3]
pytestmark = pytest.mark.skipif(os.environ.get('FC_TEST_USER_SYSTEMD') != '1', reason='requires explicit isolated user-systemd test')


def wait_file(path):
    deadline = time.monotonic() + 15
    while not path.exists() and time.monotonic() < deadline:
        time.sleep(0.1)
    assert path.exists(), 'bounded service-manager checkpoint timed out: ' + path.name
    return path.read_text()


@pytest.mark.parametrize('contract', ['', 'auto'])
def test_actual_systemd_restores_memory_and_honors_revocation_after_sigkill(tmp_path, contract):
    unit = 'fc-parity-intent-' + uuid.uuid4().hex[:12] + '.service'
    fixture = str(ROOT / 'tests/desktop_mesh_intent_peer.py')
    command = ['systemd-run', '--user', '--collect', '--unit=' + unit,
        '--property=Type=notify', '--property=NotifyAccess=main', '--property=FileDescriptorStoreMax=1',
        '--property=FileDescriptorStorePreserve=restart', '--property=Restart=on-failure', '--property=RestartSec=1',
        '--property=StartLimitIntervalSec=60', '--property=StartLimitBurst=4', '--property=RuntimeMaxSec=65',
        '--property=TimeoutStopSec=3', '--property=KillMode=control-group', '--property=CPUQuota=25%',
        '--property=LimitCORE=0', '--property=UMask=0077',
        '/usr/bin/python3', '-I', fixture, str(tmp_path), unit] + ([contract] if contract else [])
    try:
        subprocess.run(command, check=True, capture_output=True, timeout=10)
        first = json.loads(wait_file(tmp_path / 'stage1.json'))
        assert first == dict(run=1, recovered=False, desired=True, descriptors=1, recoveries=0)
        subprocess.run(['systemctl', '--user', 'kill', '--kill-whom=main', '--signal=KILL', unit], check=True, timeout=5)
        second = json.loads(wait_file(tmp_path / 'stage2.json'))
        assert second == dict(run=2, recovered=True, desired=True, descriptors=1, recoveries=1)
        (tmp_path / 'revoke').touch()
        assert wait_file(tmp_path / 'revoked') == 'committed'
        subprocess.run(['systemctl', '--user', 'kill', '--kill-whom=main', '--signal=KILL', unit], check=True, timeout=5)
        third = json.loads(wait_file(tmp_path / 'stage3.json'))
        assert third == dict(run=3, recovered=False, desired=False, descriptors=0, recoveries=1)
        record = json.loads((tmp_path / 'intent.json').read_text())
        assert set(record) == {'schema', 'uid', 'generation', 'desired', 'recoveries'}
        assert not record['desired']
    finally:
        subprocess.run(['systemctl', '--user', 'stop', unit], capture_output=True, timeout=10)
