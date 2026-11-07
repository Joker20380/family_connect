import json
import subprocess
import sys
import zipfile

import pytest

from scripts import package_paid_transport as kit
from scripts.package_friends_http import build as build_http


def test_closed_overlay_modules_and_tamper(tmp_path, monkeypatch):
    baseline_dir = tmp_path/'http'
    build_http(baseline_dir)
    baseline = baseline_dir/'friends-http.pyz'
    with zipfile.ZipFile(baseline) as package:
        inputs = {name: package.read(name) for name in package.namelist()}
    inputs['friends_http.py'] = inputs['friends_http.py'].replace(kit.API_INSERT, b'')
    inputs['control/friends/paid_beta.py'] = inputs['control/friends/paid_beta.py'].replace(kit.PAID_INSERT, b'')
    inputs.pop('control/friends/transport_membership.py', None)
    inputs.pop('control/friends/transport_policy.py', None)
    baseline.unlink()
    kit.archive(baseline, inputs)
    gateway = tmp_path/'observed-gateway.py'
    gateway.write_bytes(b'synthetic observed gateway fixture\n')
    monkeypatch.setattr(kit, 'BASELINE', kit.sha(baseline.read_bytes()))
    monkeypatch.setattr(kit, 'GATEWAY', kit.sha(gateway.read_bytes()))
    output = tmp_path/'kit'
    receipt = kit.build(baseline, gateway, output)
    changed = {name for name, digest in receipt['http_after'].items() if receipt['http_before'].get(name) != digest}
    assert changed == {'friends_http.py', 'control/friends/transport_policy.py', 'control/friends/transport_reconcile.py',
                       'control/friends/transport_membership.py', 'control/friends/paid_beta.py'}
    with zipfile.ZipFile(output/'paid-operator.pyz') as operator, zipfile.ZipFile(output/'friends-http.pyz') as http:
        for name in ('paid_beta','transport_policy','transport_membership'):
            assert operator.read('control/friends/'+name+'.py') == http.read('control/friends/'+name+'.py')
    assert not receipt['production_enabled']
    code = '''import json,sys
sys.path.insert(0,sys.argv[1])
from control.friends import transport_policy,transport_gateway
assert transport_policy.__loader__.archive == transport_gateway.__loader__.archive == sys.argv[1]
print(json.dumps(dict(profile=transport_policy.PROFILE,lease=transport_policy.LEASE_SECONDS)))
'''
    process = subprocess.run([sys.executable, '-I', '-B', '-c', code, str(output/'paid-transport.pyz')],
                             cwd=tmp_path, capture_output=True, text=True, check=True)
    assert json.loads(process.stdout) == dict(profile='paid-transports-v2', lease=120)
    original = gateway.read_bytes()
    gateway.write_bytes(original+b'tampered')
    with pytest.raises(ValueError, match='OBSERVED_SERVING_INPUTS_REQUIRED'):
        kit.build(baseline, gateway, tmp_path/'bad')
    gateway.write_bytes(original)
    with zipfile.ZipFile(baseline, 'a') as package:
        package.writestr('unreviewed.py', b'bad')
    with pytest.raises(ValueError, match='OBSERVED_SERVING_INPUTS_REQUIRED'):
        kit.build(baseline, gateway, tmp_path/'bad')


def test_unrelated_http_changes_are_rejected(tmp_path, monkeypatch):
    baseline = tmp_path/'baseline.pyz'
    original = (kit.ROOT/'deploy/friends/access-api.py').read_bytes().replace(kit.API_INSERT, b'')
    kit.archive(baseline, {'friends_http.py': original+b'\nchanged\n'})
    gateway = tmp_path/'gateway'
    gateway.write_bytes(b'fixture')
    monkeypatch.setattr(kit, 'BASELINE', kit.sha(baseline.read_bytes()))
    monkeypatch.setattr(kit, 'GATEWAY', kit.sha(gateway.read_bytes()))
    with pytest.raises(ValueError, match='UNRELATED_HTTP_DELTA'):
        kit.build(baseline, gateway, tmp_path/'bad')


def test_lifetime_fences_and_disabled_default():
    root = kit.ROOT/'deploy/friends/paid-transport'
    watcher = (root/'family-connect-paid-watch.service').read_text()
    dependency = (root/'paid-dependency.conf').read_text()
    assert 'Type=notify' in watcher and 'WatchdogSec=12' in watcher
    assert 'KillMode=control-group' in watcher and 'TimeoutStopSec=5' in watcher
    assert 'BindsTo=family-connect-paid-watch.service' in dependency
    assert 'After=family-connect-paid-watch.service' in dependency
    assert 'KillMode=control-group' in dependency and 'TimeoutStopSec=5' in dependency
    assert 'paid-preflight' in (root/'paid-tcp-preflight.conf').read_text()
    assert 'TimeoutStartSec=40' in (root/'family-connect-paid-reconcile.service.in').read_text()
    assert 'TimeoutStopSec=5' in (root/'family-connect-paid-reconcile.service.in').read_text()
    assert 'OnUnitInactiveSec=30' in (root/'family-connect-paid-reconcile.timer').read_text()


def test_exact_v2_node_forward_package_and_inventory(tmp_path):
    from scripts import package_transport_node_recovery as recovery
    commit = '2077c271d43d3bbe09f76e70934947bcc3fb51c6'
    def historical(path):
        return subprocess.check_output(['git', '-C', str(kit.ROOT), 'show', commit+':'+path])
    inputs = {name: historical(name) for name in kit.MODULES}
    inputs.update({'control/': b'', 'control/friends/': b'', 'control/friends/__init__.py': b''})
    node = tmp_path/'v2.pyz'
    gateway = tmp_path/'v2.py'
    kit.archive(node, inputs)
    gateway.write_bytes(historical('deploy/friends/awg-gateway.py'))
    assert kit.sha(node.read_bytes()) == recovery.PREVIOUS_NODE
    assert kit.sha(gateway.read_bytes()) == recovery.PREVIOUS_GATEWAY
    output = tmp_path/'recovery'
    receipt = recovery.build(node, gateway, output)
    assert {name for name, digest in receipt['archives']['paid-transport.pyz'].items() if receipt['before'][name] != digest} == {'control/friends/transport_gateway.py'}
    assert not any(name in receipt['files'] for name in ('friends-http.pyz','paid-operator.pyz','paid-reconcile.pyz'))
    assert 'ExecStartPre=+' in (output/'paid-tcp-preflight.conf').read_text()
    code = 'import sys;sys.path.insert(0,sys.argv[1]);from control.friends.transport_gateway import Operation,OPERATION_SECONDS;assert OPERATION_SECONDS==8;assert Operation().remaining()>0'
    subprocess.run([sys.executable,'-I','-B','-c',code,str(output/'paid-transport.pyz')],check=True,cwd=tmp_path)
    gateway.write_bytes(gateway.read_bytes()+b'\n')
    with pytest.raises(ValueError,match='EXACT_INSTALLED_V2_REQUIRED'):
        recovery.build(node,gateway,tmp_path/'bad')
