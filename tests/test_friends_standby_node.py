import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
from types import SimpleNamespace

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey

from clients.desktop.profile_config import parse, parse_tcp

SOURCE = Path(__file__).parents[1] / 'deploy/friends/standby-node.py'


@pytest.fixture
def node(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location('standby_node', SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, 'STATE', tmp_path / 'state')
    monkeypatch.setattr(module, 'ROOT', tmp_path / 'app')
    monkeypatch.setattr(module, 'SYSCTL', tmp_path / 'sysctl.conf')
    return module


def test_material_has_fresh_server_keys_and_no_users(node):
    first = node.material('1.1.1.1')
    second = node.material('1.1.1.1')
    assert all(first[index] != second[index] for index in range(3))
    awg, tcp, template = first
    assert '[Peer]' not in awg.decode()
    config = json.loads(tcp)
    assert config['inbounds'][0]['settings']['clients'] == []
    key = config['inbounds'][0]['streamSettings']['realitySettings']['privateKey']
    public = X25519PrivateKey.from_private_bytes(base64.urlsafe_b64decode(key + '=')).public_key()
    assert base64.urlsafe_b64encode(public.public_bytes(serialization.Encoding.Raw,
        serialization.PublicFormat.Raw)).decode().rstrip('=') == template['tcp']['public_key']
    assert key not in json.dumps(template)
    awg_key = awg.decode().split('PrivateKey = ')[1].splitlines()[0]
    assert awg_key not in json.dumps(template)
    assert awg_key not in tcp.decode()
    assert b'ListenPort = 51823' in awg
    assert config['inbounds'][0]['port'] == 443
    assert config['inbounds'][1]['listen'] == '127.0.0.1'
    assert config['inbounds'][1]['port'] == 18085


def test_templates_use_existing_desktop_contract(node):
    _, _, template = node.material('1.1.1.1')
    tcp = dict(template['tcp'], id='11111111-1111-4111-8111-111111111111')
    assert parse_tcp(json.dumps(tcp)) == tcp
    key = base64.b64encode(bytes([7]) * 32).decode()
    awg = template['awg'].replace('LOCAL_DEVICE_KEY', key).replace('ASSIGNED_ADDRESS', '10.83.0.2/32')
    assert parse(awg, allow_awg=True, allow_awg31=True)


def test_units_have_no_material_and_bound_argv(node):
    units = node.units()
    assert set(units) == set(node.UNITS)
    for name, raw in units.items():
        assert b'PrivateKey' not in raw and b'Environment=' not in raw
        assert b'StartLimitBurst=5' in raw and b'NoNewPrivileges=true' in raw
        assert b'ExecStart=/opt/apps/' in raw or b'ExecStart=/usr/bin/python3 /opt/apps/' in raw
        assert b'StandardOutput=null' in raw and b'StandardError=null' in raw
    assert b'User=fc-friends' in units[node.UNITS[0]]
    assert b'CapabilityBoundingSet=CAP_NET_BIND_SERVICE' in units[node.UNITS[0]]
    assert b'User=root' in units[node.UNITS[1]]


@pytest.fixture
def manifest(node, tmp_path, monkeypatch):
    files = {}
    for name in (*node.NATIVE, 'awg-gateway.py', 'standby-node.py'):
        raw = ('fixture-' + name).encode()
        (tmp_path / name).write_bytes(raw)
        files[name] = hashlib.sha256(raw).hexdigest()
    monkeypatch.setattr(node, 'NATIVE', {name: files[name] for name in node.NATIVE})
    return dict(schema=1, target='1.1.1.1', operation_id='standby-fixture-0001',
                source_commit='1' * 40, files=files)


def test_exact_source_and_native_manifest(node, manifest, tmp_path):
    node.manifest_check(manifest, tmp_path, manifest['target'])


@pytest.mark.parametrize('host', ['185.251.89.19', '185.10.158.212', '186.246.45.246',
                                  '186.246.51.201', '127.0.0.1', '10.0.0.1', '::1', '-oProxyCommand=bad'])
def test_existing_production_or_unsafe_target_rejected(node, manifest, tmp_path, host):
    manifest['target'] = host
    with pytest.raises(ValueError):
        node.manifest_check(manifest, tmp_path, host)


@pytest.mark.parametrize('change', ['target', 'operation', 'native', 'source', 'extra', 'traversal'])
def test_manifest_mutation_rejected(node, manifest, tmp_path, change):
    if change == 'target':
        manifest['target'] = '8.8.8.8'
    elif change == 'operation':
        manifest['operation_id'] = '../bad'
    elif change == 'native':
        (tmp_path / 'awg').write_bytes(b'changed')
        manifest['files']['awg'] = hashlib.sha256(b'changed').hexdigest()
    elif change == 'source':
        (tmp_path / 'awg-gateway.py').write_bytes(b'changed')
    elif change == 'extra':
        manifest['files']['new'] = '1' * 64
    else:
        manifest['files']['../bad'] = manifest['files'].pop('xray')
    with pytest.raises(ValueError):
        node.manifest_check(manifest, tmp_path, '1.1.1.1')


@pytest.mark.parametrize('kind', ['symlink', 'hardlink', 'parent'])
def test_file_alias_rejected(node, tmp_path, kind):
    original = tmp_path / 'original'
    original.write_bytes(b'private')
    target = tmp_path / 'target'
    if kind == 'symlink':
        target.symlink_to(original)
    elif kind == 'hardlink':
        os.link(original, target)
    else:
        target.symlink_to(tmp_path, target_is_directory=True)
        target = target / 'original'
    with pytest.raises(ValueError):
        node.regular(target)


def test_private_write_modes_and_no_overwrite(node, tmp_path):
    target = tmp_path / 'secret'
    node.write(target, b'secret', gid=os.getegid())
    assert stat.S_IMODE(target.stat().st_mode) == 0o600
    assert target.read_bytes() == b'secret'
    with pytest.raises(FileExistsError):
        node.write(target, b'new', gid=os.getegid())
    assert target.read_bytes() == b'secret'


def test_application_root_does_not_inherit_private_umask(node, monkeypatch):
    directories = {}
    class Directory:
        def __init__(self, name, parent=None):
            self.name = name
            self.parents = () if parent is None else (parent, *parent.parents)
        def exists(self):
            return self.name in directories
        def mkdir(self, mode):
            directories[self.name] = mode & ~0o077
        def chmod(self, mode):
            directories[self.name] = mode
        def is_symlink(self):
            return False
        def is_dir(self):
            return self.exists()
        def stat(self):
            return SimpleNamespace(st_uid=0, st_mode=directories[self.name])
    parent = Directory('/opt')
    directories['/opt'] = 0o755
    root = Directory('/opt/apps/family_connect', Directory('/opt/apps', parent))
    monkeypatch.setattr(node, 'ROOT', root)
    node.application_root()
    assert directories == {'/opt': 0o755, '/opt/apps': 0o755, '/opt/apps/family_connect': 0o755}
    directories['/opt/apps'] = 0o700
    with pytest.raises(ValueError):
        node.application_root()
    assert directories['/opt/apps'] == 0o700


def test_prepare_interruption_never_blindly_restarts(node, manifest, tmp_path):
    node.STATE.mkdir()
    (node.STATE / 'intent.json').write_bytes(node.canonical(manifest))
    with pytest.raises(ValueError):
        node.prepare(manifest, tmp_path)
    assert not node.ROOT.exists()


@pytest.mark.parametrize('phase', ['start-intent', 'admitted'])
def test_start_fences_replay_and_admitted_node(node, phase):
    node.STATE.mkdir()
    (node.STATE / 'prepared.json').write_bytes(b'{}')
    (node.STATE / phase).write_bytes(b'')
    with pytest.raises(ValueError):
        node.start()
    assert not node.SYSCTL.exists()


def test_stop_does_not_mutate_admitted_node(node, monkeypatch):
    node.STATE.mkdir()
    (node.STATE / 'intent.json').write_bytes(b'{}')
    (node.STATE / 'admitted').write_bytes(b'')
    monkeypatch.setattr(node, 'command', lambda *args, **kwargs: pytest.fail('unexpected mutation'))
    with pytest.raises(ValueError):
        node.stop()


def test_command_suppresses_private_failure(node, monkeypatch):
    monkeypatch.setattr(node.subprocess, 'run', lambda *args, **kwargs:
                        SimpleNamespace(returncode=1, stdout=b'private', stderr=b'secret'))
    with pytest.raises(ValueError, match='^standby node precondition rejected$'):
        node.command(['/bin/false'])


def test_command_has_no_shell_or_unbounded_timeout(node, monkeypatch):
    observed = []
    def run(argv, **kwargs):
        observed.append((argv, kwargs))
        return SimpleNamespace(returncode=0, stdout=b'ok')
    monkeypatch.setattr(node.subprocess, 'run', run)
    assert node.command(['fixed']) == b'ok'
    assert observed == [(['fixed'], {'capture_output': True, 'timeout': 90})]


def test_start_failure_stops_owned_services(node, monkeypatch):
    node.STATE.mkdir()
    (node.STATE / 'prepared.json').write_bytes(b'{}')
    calls = []
    monkeypatch.setattr(node, 'write', lambda path, *args, **kwargs: calls.append(path.name))
    monkeypatch.setattr(node, 'command', lambda *args, **kwargs: node.require(False))
    monkeypatch.setattr(node, 'stop', lambda: calls.append('STOP'))
    with pytest.raises(ValueError):
        node.start()
    assert calls == ['start-intent', 'sysctl.conf', 'STOP']


@pytest.fixture
def probe():
    spec = importlib.util.spec_from_file_location('standby_probe', SOURCE.parents[2] / 'scripts/accept_friends_standby.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def probe_input(node):
    return dict(target='1.1.1.1', private_key=base64.b64encode(bytes([7]) * 32).decode(),
                tcp_id='11111111-1111-4111-8111-111111111111', template=node.material('1.1.1.1')[2])


def test_external_probe_uses_same_strict_client_parser(node, probe, probe_input):
    awg, tcp = probe.configuration(probe_input)
    assert b'DNS =' not in awg and b'Address =' not in awg
    assert b'Endpoint = 1.1.1.1:51823' in awg
    config = json.loads(tcp)
    assert config['inbounds'][0]['listen'] == '127.0.0.1'
    assert config['outbounds'][0]['settings']['vnext'][0]['port'] == 443
    assert probe.NATIVE == node.NATIVE


@pytest.mark.parametrize('change', ['host', 'old_nl', 'private_key', 'tcp_id', 'hook', 'extra'])
def test_external_probe_rejects_unbound_or_injected_input(probe, probe_input, change):
    if change == 'host':
        probe_input['target'] = '8.8.8.8'
    elif change == 'old_nl':
        probe_input['target'] = '185.10.158.212'
    elif change == 'hook':
        probe_input['template']['awg'] += 'PostUp = arbitrary\n'
    else:
        probe_input[change] = 'invalid'
    with pytest.raises(ValueError):
        probe.configuration(probe_input)


@pytest.mark.parametrize('host', ['0.0.0.0', '*', '[::]'])
def test_listener_wildcard_spellings_keep_exact_process_binding(host):
    from scripts.friends_standby_health import listener_owners
    line = 'tcp LISTEN 0 4096 ' + host + ':443 *:* users:(("xray",pid=123,fd=4))'
    assert listener_owners(line, 'tcp', 443, {'123'}, {'0.0.0.0', '*', '[::]'}) == [host]
    with pytest.raises(ValueError):
        listener_owners(line, 'tcp', 443, {'999'}, {'0.0.0.0', '*', '[::]'})


@pytest.mark.parametrize('line', ['', 'tcp LISTEN 0 4096 *:443 *:*',
    'tcp LISTEN 0 4096 127.0.0.1:443 *:* users:(("xray",pid=123,fd=4))',
    'tcp LISTEN 0 4096 *:4443 *:* users:(("xray",pid=123,fd=4))'])
def test_listener_missing_owner_wrong_scope_or_port_rejected(line):
    from scripts.friends_standby_health import listener_owners
    with pytest.raises(ValueError):
        listener_owners(line, 'tcp', 443, {'123'}, {'0.0.0.0', '*', '[::]'})


def test_absent_health_fences_admission():
    from scripts.friends_standby_health import require_ready
    with pytest.raises((KeyError, ValueError)):
        require_ready({}, {}, {}, target='1.1.1.1', now=1000)


@pytest.mark.parametrize('change', ['valid', 'stale', 'future', 'failed', 'host', 'restart', 'cleanup'])
def test_admission_requires_fresh_complete_independent_observations(change):
    from scripts.friends_standby_health import require_ready
    units = {name: dict(ActiveState='active', NRestarts='0', UnitFileState='enabled') for name in (
        'family-connect-friends-awg.service', 'family-connect-friends-tcp.service')}
    health = dict(result='LOCAL_ORDINARY_HEALTH_PASS', target='1.1.1.1', observed_at=1000, units=units,
                  native_hashes='PASS', forwarding_nat='PASS', awg_address='PASS', listener_ownership='PASS')
    external = dict(target='1.1.1.1', exit=0, external=dict(awg='HANDSHAKE_DNS_HTTPS_EGRESS_PASS',
                    tcp='AUTH_DNS_HTTPS_EGRESS_PASS', operator_cleanup='PASS'),
                    cleanup=dict(receipt=dict(result='TARGET_CLEANUP_PASS')))
    registration = dict(probe=dict(result='PINNED_RU_TO_NEW_NL_REGISTRATION_PASS'),
                        cleanup=dict(result='REGISTRATION_PROBE_CLEANUP_PASS'))
    if change == 'stale':
        health['observed_at'] = 879
    elif change == 'future':
        health['observed_at'] = 1001
    elif change == 'failed':
        health['listener_ownership'] = 'FAIL'
    elif change == 'host':
        external['target'] = '8.8.8.8'
    elif change == 'restart':
        units['family-connect-friends-awg.service']['NRestarts'] = '1'
    elif change == 'cleanup':
        registration['cleanup']['result'] = 'FAIL'
    if change == 'valid':
        require_ready(health, external, registration, target='1.1.1.1', now=1000)
    else:
        with pytest.raises(ValueError):
            require_ready(health, external, registration, target='1.1.1.1', now=1000)
