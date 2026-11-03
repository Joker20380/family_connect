import base64
import importlib.util
import json
from pathlib import Path
import socket
import struct
import subprocess

import pytest

from pilot import fleet_canary as canary

SPEC = importlib.util.spec_from_file_location('isolated_canary_runner', Path(__file__).parents[1] / 'scripts/test_fleet_canary.py')
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


def configuration():
    return dict(origin='172.25.0.2', gateway='172.26.0.3', egress='172.25.0.3', certificate='fixture public certificate')


def test_disposable_material_has_no_production_identity_or_direct_tcp_fallback():
    spec = configuration()
    server_awg, server_tcp, client = canary.material(spec)
    next_awg, next_tcp, next_client = canary.material(spec)
    assert server_awg != next_awg and server_tcp != next_tcp and client != next_client
    assert 'PrivateKey' in client['awg'] and 'Endpoint = 172.26.0.3:51823' in client['awg']
    assert 'AllowedIPs = 172.25.0.2/32' in client['awg']
    assert b'AllowedIPs = 10.254.253.2/32' in server_awg
    assert client['tcp']['outbounds'][0]['protocol'] == 'vless' and len(client['tcp']['outbounds']) == 1
    assert client['tcp']['inbounds'][0]['listen'] == '127.0.0.1'
    server_settings = server_tcp['inbounds'][0]['streamSettings']['realitySettings']
    assert server_settings['dest'] == '172.25.0.2:443'
    assert server_settings['privateKey'] not in json.dumps(client)
    assert server_tcp['dns'] == dict(servers=['172.25.0.2'], queryStrategy='UseIPv4')
    assert server_tcp['outbounds'][0]['settings']['domainStrategy'] == 'UseIPv4'
    assert len(base64.b64decode(client['server_public'])) == 32


@pytest.mark.parametrize('value', ['185.10.158.212', '185.10.158.196', '185.251.89.19',
    '186.246.51.201', '127.0.0.1', '169.254.1.1', '0.0.0.0', '224.0.0.1', '::1', 'example.com'])
def test_inner_fixture_rejects_public_or_nonfixture_destinations(value):
    with pytest.raises(ValueError):
        canary.private_address(value)


def test_material_rejects_same_host_or_extra_fields():
    spec = configuration()
    with pytest.raises(ValueError):
        canary.material(dict(spec, gateway=spec['origin']))
    with pytest.raises(ValueError):
        canary.material(dict(spec, private_key='unacceptable imported identity'))


def test_secret_custody_is_exclusive_and_private(tmp_path, monkeypatch):
    monkeypatch.setattr(canary, 'ROOT', tmp_path)
    canary.secret('fixture', b'private fixture')
    assert (tmp_path / 'fixture').stat().st_mode & 0o777 == 0o600
    with pytest.raises(FileExistsError):
        canary.secret('fixture', b'other')
    (tmp_path / 'link').symlink_to(tmp_path / 'fixture')
    with pytest.raises(FileExistsError):
        canary.secret('link', b'other')
    assert (tmp_path / 'fixture').read_bytes() == b'private fixture'


def question(domain=canary.DOMAIN, kind=1):
    labels = b''.join(bytes([len(label)]) + label.encode() for label in domain.split('.')) + b'\0'
    return struct.pack('!HHHHHH', 123, 0x100, 1, 0, 0, 0) + labels + struct.pack('!HH', kind, 1)


def test_dns_fixture_only_answers_its_exact_ipv4_name():
    response = canary.dns_response(question(), '172.25.0.2')
    assert response[:2] == question()[:2] and response[6:8] == b'\0\1'
    assert response[-4:] == socket.inet_aton('172.25.0.2')
    for raw in (question('unrelated.test'), question(kind=28)):
        assert canary.dns_response(raw, '172.25.0.2')[6:8] == b'\0\0'
    for raw in (b'', b'\0' * 16, question()[:15]):
        with pytest.raises((ValueError, IndexError)):
            canary.dns_response(raw, '172.25.0.2')


@pytest.mark.parametrize('change', ['peer', 'nonce', 'invalid-json', 'status'])
def test_https_requires_nonce_exact_egress_and_success(monkeypatch, change):
    value = dict(path='/canary/nonce', peer='172.25.0.3')
    if change in ('peer', 'nonce'):
        value['peer' if change == 'peer' else 'path'] = 'wrong'
    raw = b'invalid' if change == 'invalid-json' else json.dumps(value).encode()
    def run(arguments, **options):
        assert '--cacert' in arguments and '--insecure' not in arguments
        assert arguments[arguments.index('--proxy') + 1] == ''
        assert '--max-time' in arguments and '--connect-timeout' in arguments
        return subprocess.CompletedProcess(arguments, int(change == 'status'), stdout=raw)
    monkeypatch.setattr(canary, 'run', run)
    with pytest.raises(ValueError):
        canary.curl([], 'nonce', True, '172.25.0.3')


def test_negative_control_cannot_pass_on_direct_success(monkeypatch):
    monkeypatch.setattr(canary, 'run', lambda args, **kwargs: subprocess.CompletedProcess(args, 0, stdout=b''))
    with pytest.raises(ValueError):
        canary.curl([], 'nonce', False, '172.25.0.3')


def test_gateway_uses_json_configs_and_multiline_scoped_nft_rules(tmp_path, monkeypatch):
    monkeypatch.setattr(canary, 'ROOT', tmp_path)
    monkeypatch.setattr(canary, 'launch', lambda *args: None)
    monkeypatch.setattr(canary, 'wait_for', lambda *args: None)
    calls = []
    def run(command, **options):
        calls.append(command)
        if command[:2] == ['/native/xray', 'run']:
            assert command[-1].endswith('.json')
            assert json.loads(Path(command[-1]).read_text())['inbounds']
        if command[0] == 'nft':
            assert options['data'] == (b'table ip fc_canary {\n chain postrouting {\n '
                b'type nat hook postrouting priority srcnat;\n '
                b'ip saddr 10.254.253.0/30 ip daddr 172.25.0.2 masquerade\n }\n}\n')
        return subprocess.CompletedProcess(command, 0, stdout=b'')
    monkeypatch.setattr(canary, 'run', run)
    canary.prepare_gateway(configuration())
    assert sum(command[0] == 'nft' for command in calls) == 1


def isolated_info():
    return dict(Config=dict(Labels={runner.LABEL: 'run'}), HostConfig=dict(Privileged=False, PidMode='',
        IpcMode='private', Binds=None, PortBindings={}, ReadonlyRootfs=True, CapDrop=['ALL'],
        CapAdd=['NET_ADMIN', 'NET_BIND_SERVICE'], SecurityOpt=['no-new-privileges:true'],
        Devices=[dict(PathOnHost='/dev/net/tun', PathInContainer='/dev/net/tun', CgroupPermissions='rwm')]), Mounts=[dict(Type='tmpfs')],
        NetworkSettings=dict(Networks={'entry': {}, 'egress': {}}))


@pytest.mark.parametrize('key,value', [('Privileged', True), ('PidMode', 'host'), ('IpcMode', 'host'),
    ('Binds', ['/home:/host']), ('PortBindings', {'443/tcp': 443}), ('ReadonlyRootfs', False),
    ('CapDrop', []), ('CapAdd', ['SYS_ADMIN']), ('SecurityOpt', []),
    ('Devices', [dict(PathOnHost='/dev/sda', PathInContainer='/dev/sda', CgroupPermissions='rwm')])])
def test_host_namespace_mount_or_excess_privilege_rejected(key, value):
    info = isolated_info()
    runner.verify_container(info, 'run', ['entry', 'egress'], 'gateway')
    info['HostConfig'][key] = value
    with pytest.raises(RuntimeError):
        runner.verify_container(info, 'run', ['entry', 'egress'], 'gateway')


def test_wrong_label_network_or_volume_rejected():
    for section, key, value in [('Config', 'Labels', {runner.LABEL: 'other'}),
        ('NetworkSettings', 'Networks', {'host': {}})]:
        info = isolated_info()
        info[section][key] = value
        with pytest.raises(RuntimeError):
            runner.verify_container(info, 'run', ['entry', 'egress'], 'gateway')
    info = isolated_info()
    info['Mounts'] = [dict(Type='bind')]
    with pytest.raises(RuntimeError):
        runner.verify_container(info, 'run', ['entry', 'egress'], 'gateway')


def test_docker_canonical_capability_names_keep_the_same_exact_budget():
    info = isolated_info()
    info['HostConfig']['CapAdd'] = ['CAP_NET_ADMIN', 'CAP_NET_BIND_SERVICE']
    runner.verify_container(info, 'run', ['entry', 'egress'], 'gateway')
    info['HostConfig']['CapAdd'].append('CAP_SYS_ADMIN')
    with pytest.raises(RuntimeError):
        runner.verify_container(info, 'run', ['entry', 'egress'], 'gateway')


@pytest.mark.parametrize('failure', [None, 'ownership', 'discovery', 'removal'])
def test_cleanup_is_label_scoped_and_never_false_passes(failure):
    remaining = {'container': ['container-id'], 'network': ['network-id']}
    removed = []
    def run(command, **kwargs):
        output, status = b'', 0
        if command[:3] == ['docker', 'ps', '-aq'] or command[:4] == ['docker', 'network', 'ls', '-q']:
            kind = 'container' if command[1] == 'ps' else 'network'
            assert command[-1] == 'label=' + runner.LABEL + '=run'
            if failure == 'discovery':
                raise subprocess.TimeoutExpired(command, 60)
            output = '\n'.join(remaining[kind]).encode()
        elif command[2] == 'inspect':
            labels = {runner.LABEL: 'other' if failure == 'ownership' else 'run'}
            output = json.dumps([dict(Config=dict(Labels=labels)) if command[1] == 'container' else dict(Labels=labels)]).encode()
        else:
            kind = 'container' if command[1] == 'rm' else 'network'
            assert command[-1] in remaining[kind]
            removed.append(kind)
            if failure == 'removal':
                status = 1
            else:
                remaining[kind].remove(command[-1])
        return subprocess.CompletedProcess(command, status, stdout=output)
    failures = runner.cleanup('run', run)
    assert bool(failures) is bool(failure)
    if failure in ('ownership', 'discovery'):
        assert not removed
    if failure is None:
        assert removed == ['container', 'network']


def test_failed_execution_records_cleanup_without_overwriting_receipts(tmp_path):
    report = tmp_path / 'receipt.json'
    def run(command, **kwargs):
        if command[1:3] == ['image', 'inspect']:
            raise RuntimeError('private error must not leak')
        return subprocess.CompletedProcess(command, 0, stdout=b'')
    result = runner.execute(report, run)
    assert result['result'] == 'FAIL' and result['cleanup'] == 'PASS'
    assert result['production_node_acceptance'] == 'NOT_RUN'
    assert 'private error' not in report.read_text()
    assert report.stat().st_mode & 0o777 == 0o600
    with pytest.raises(FileExistsError):
        runner.execute(report, run)
