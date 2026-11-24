import json
import subprocess
import sys

import pytest

from scripts import control_ha_recovery_systemd as recovery


def test_closed_resource_and_namespace_policy():
    arguments = recovery.command('/opt/apps/family_connect/ha-recovery/20261124-host-01', '20261124-run-01')
    assert arguments[:5] == ['/usr/bin/systemd-run', '--quiet', '--wait', '--pipe', '--collect']
    assert '--unit=fc-ha-recovery-20261124-run-01' in arguments
    for prop in ('DynamicUser=yes', 'PrivateNetwork=yes', 'PrivateUsers=yes', 'CapabilityBoundingSet=',
                 'ProtectSystem=strict', 'MemoryMax=512M', 'MemorySwapMax=0', 'CPUQuota=25%',
                 'RuntimeMaxSec=600', 'KillMode=control-group', 'RestrictAddressFamilies=AF_UNIX'):
        assert prop in arguments
    binds = [value for value in arguments if value.startswith('Bind')]
    assert len(binds) == 4 and all(value.startswith('BindReadOnlyPaths=') for value in binds)
    assert not any('.key' in value or '/home/' in value or 'docker.sock' in value for value in binds)
    assert arguments[-2:] == ['fc-ha-offline', recovery.INPUT]
    compile(recovery.INPUT, '<bounded-stdin>', 'exec')


@pytest.mark.parametrize('root', [
    '/opt/apps/family_connect', '/opt/apps/family_connect/ha-recovery/../friends-state',
    '/opt/apps/family_connect/ha-recovery/run', '/opt/apps/family_connect/ha-recovery/a:bcd123',
    '/opt/apps/family_connect/ha-recovery/abcd1234/child',
    '/opt/apps/family_connect/ha-recovery//abcd1234',
    '/opt/apps/family_connect/ha-recovery/abcd1234\n', '/tmp/abcdefgh',
])
def test_path_scope_rejected(root):
    with pytest.raises(ValueError, match='RECOVERY_SCOPE'):
        recovery.command(root, 'abcdefgh')


@pytest.mark.parametrize('operation', ['live', '../abcdefgh', 'abcdefgh.service', 'abcdefgh\n', 'x' * 65])
def test_cannot_select_live_unit(operation):
    with pytest.raises(ValueError, match='RECOVERY_SCOPE'):
        recovery.command('/opt/apps/family_connect/ha-recovery/abcdefgh', operation)


def test_secret_input_not_in_argv():
    arguments = recovery.command('/opt/apps/family_connect/ha-recovery/abcdefgh', 'abcdefgh')
    assert 'sys.stdin.buffer.read(65537)' in arguments[-1]
    assert 'interfaces==[\'lo\']' in arguments[-1]
    assert '/tmp/fc-custody' in arguments[-1]
    assert 'socket.if_nameindex' not in arguments[-1]
    assert 'control_ha_recovery_probe /tmp/fc-custody' in arguments[-3]


def test_input_refuses_root_before_any_write():
    source = 'import os; os.getuid=lambda:0\n' + recovery.INPUT
    result = subprocess.run([sys.executable, '-I', '-c', source], input=json.dumps({}),
                            text=True, capture_output=True, timeout=5)
    assert result.returncode != 0 and 'AssertionError' in result.stderr
