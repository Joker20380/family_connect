from pathlib import Path
from types import SimpleNamespace

import pytest

from fleet import probe
from fleet.preflight import accept


@pytest.fixture
def host(monkeypatch):
    files = {'/etc/os-release': 'ID=ubuntu\nVERSION_ID="24.04"', '/proc/meminfo': 'MemTotal: 2000000 kB',
             '/proc/1/comm': 'systemd\n', '/sys/module/apparmor/parameters/enabled': 'Y\n'}
    monkeypatch.setattr(Path, 'read_text', lambda self: files[str(self)])
    monkeypatch.setattr(Path, 'exists', lambda self: str(self) in files or str(self) == '/dev/net/tun')
    monkeypatch.setattr(Path, 'stat', lambda self: SimpleNamespace(st_mode=0o20600))
    monkeypatch.setattr(probe.platform, 'machine', lambda: 'x86_64')
    monkeypatch.setattr(probe.platform, 'release', lambda: '6.8.0-147-generic')
    monkeypatch.setattr(probe.os, 'cpu_count', lambda: 2)
    monkeypatch.setattr(probe.shutil, 'disk_usage', lambda path: SimpleNamespace(free=24*1024**3))
    monkeypatch.setattr(probe.socket, 'getaddrinfo', lambda *args: [])
    class Response:
        status = 200
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
    monkeypatch.setattr(probe.urllib.request, 'urlopen', lambda *args, **kwargs: Response())
    def command(argv, *, successful=False):
        if argv[0] == 'ip':
            return '[{"addr_info":[{"local":"8.8.8.8"}]}]'
        if argv[0] == 'ss':
            return 'tcp LISTEN 0 128 0.0.0.0:4443 0.0.0.0:*'
        if argv[0] == 'timedatectl':
            return 'yes'
        if argv[0] == 'iptables':
            return 'iptables v1.8.10 (nf_tables)'
        if argv[0] == 'aa-status':
            return True
        raise AssertionError(argv)
    monkeypatch.setattr(probe, 'command', command)
    return dict(ipv4='8.8.8.8', ipv6=None, ports=[])


def test_empty_port_set_allows_post_enrollment_preflight(host):
    report = probe.collect(host)
    assert report['ports_available'] is True
    assert accept(report, dict(instance_id='fleet-rehearsal-test', ipv4='8.8.8.8', ipv6=None)) == report


def test_requested_occupied_port_still_rejected(host):
    report = probe.collect(dict(host, ports=[4443]))
    assert report['ports_available'] is False
    with pytest.raises(ValueError, match='host_capability'):
        accept(report, dict(instance_id='fleet-rehearsal-test', ipv4='8.8.8.8', ipv6=None))


@pytest.mark.parametrize('ports', [None, '4443', [True], [0], [65536], ['22'], list(range(1, 34))])
def test_invalid_ports_remain_rejected(host, ports):
    with pytest.raises(ValueError):
        probe.collect(dict(host, ports=ports))


def test_diagnostics_are_opt_in_and_bound_to_selected_paths(host, monkeypatch):
    calls = []
    def observe(bundle, instance):
        calls.append((bundle, instance))
        return dict(remote_writes=0)
    monkeypatch.setattr(probe, 'observations', observe)
    assert 'diagnostics' not in probe.collect(host)
    request = dict(host, bundle_id='gw-'+'a'*32, instance_id='fleet-rehearsal-test')
    assert probe.collect(request)['diagnostics'] == dict(remote_writes=0)
    assert calls == [(request['bundle_id'], request['instance_id'])]


@pytest.mark.parametrize('field,value', [('bundle_id','../outside'),('bundle_id',None),
    ('instance_id','../outside'),('instance_id','production')])
def test_diagnostic_path_injection_rejected_before_observation(host, monkeypatch, field, value):
    monkeypatch.setattr(probe, 'observations', lambda *args: pytest.fail('unexpected observation'))
    request = dict(host, bundle_id='gw-'+'a'*32, instance_id='fleet-rehearsal-test')
    request[field] = value
    with pytest.raises(ValueError, match='probe_diagnostic_binding'):
        probe.collect(request)


def test_observations_do_not_read_secret_contents_or_emit_arbitrary_service_data(monkeypatch):
    monkeypatch.setattr(Path,'lstat',lambda self: SimpleNamespace(st_mode=0o100640,st_uid=0,st_gid=996,st_nlink=1))
    monkeypatch.setattr(Path,'read_bytes',lambda self: pytest.fail('secret content read'))
    monkeypatch.setattr(Path,'read_text',lambda self: pytest.fail('secret content read'))
    monkeypatch.setattr(probe.os,'listxattr',lambda *args,**kwargs: ['private-attribute'])
    def deny_open(*args,**kwargs):
        raise PermissionError()
    monkeypatch.setattr(probe.os,'open',deny_open)
    monkeypatch.setattr(probe,'command',lambda argv: 'ActiveState=failed\nNRestarts=3\nEnvironment=SECRET\nResult=unsafe/value\n')
    result=probe.observations('gw-'+'a'*32,'fleet-rehearsal-test')
    assert result['remote_writes']==0
    assert result['services']['mesh']==dict(ActiveState='failed',NRestarts='3')
    assert result['files']['profile/gateway.json']['extended_attribute_count']==1
    assert 'SECRET' not in str(result) and 'private-attribute' not in str(result)
