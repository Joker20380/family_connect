import base64
import json
import os
from pathlib import Path
import sqlite3
import sys

import pytest

from control.fleet_gateway import FenceRejected, FencedGateway, receipt
from control.fleet_process import ProcessFailed, run
from control.fleet_ssh import SSHGateway, request
from control.fleet_wg import WGBackends, WGPeerBackend
from scripts.fleet_agent import AgentConfig, build, protected
from test_fleet_gateway import system, removal
from test_fleet_store import state
from test_fleet import inventory


FAKE_WG = '''
import json,os,sys
from pathlib import Path
p=Path(__file__).with_suffix('.json')
s=json.loads(p.read_text());a=sys.argv[1:];s['calls'].append(a)
if a[0]=='show':
    if a[2]=='public-key':print(s['server_public'])
    elif a[2]=='listen-port':print(s['port'])
    elif a[2]=='allowed-ips':
        for k,v in s['peers'].items():print(k+'\\t'+v)
    else:sys.exit(7)
elif a[0]=='set':
    # A real subprocess must inherit the gateway effects lock.
    inherited=False
    for fd in Path('/proc/self/fd').iterdir():
        try:inherited |= os.readlink(fd).endswith('/.effects.lock')
        except OSError:pass
    if not inherited:sys.exit(8)
    if not s.get('ignore_mutation'):
        if a[4]=='remove':s['peers'].pop(a[3],None)
        else:s['peers'][a[3]]=a[5]
else:sys.exit(9)
p.write_text(json.dumps(s))
'''


@pytest.fixture
def real_backend(system, tmp_path):
    store, old, _, command, clock = system
    binary = tmp_path/'wg-fixture'
    binary.write_text(f'#!{sys.executable}\n'+FAKE_WG); binary.chmod(0o700)
    data = binary.with_suffix('.json')
    server_key = base64.b64encode(bytes([42])*32).decode()
    other_key = base64.b64encode(bytes([43])*32).decode()
    data.write_text(json.dumps(dict(server_public=server_key, port=51820,
                                   peers={other_key:'10.99.0.2/32'}, calls=[])))
    backend = WGPeerBackend(binary=str(binary), interface='fcfixture', server_public=server_key, port=51820)
    agent = FencedGateway(tmp_path/'native-journal', old.gateway,
        WGBackends({('amneziawg','3.1'): backend}), clock=lambda:clock[0])
    agent.initialize()
    return agent, backend, command, data


def change(path, **values):
    state = json.loads(path.read_text()); state.update(values); path.write_text(json.dumps(state))


def test_wg_subprocess_lifecycle_preserves_other_peers_and_inherits_lock(real_backend):
    agent, _, command, data = real_backend
    baseline = json.loads(data.read_text())['peers']
    assert agent.execute(command) == receipt(command)
    assert json.loads(data.read_text())['peers'] == {**baseline, command.wg:command.address}
    agent.execute(command)
    agent.execute(removal(command)); agent.execute(removal(command))
    result = json.loads(data.read_text())
    assert result['peers'] == baseline
    assert [a[4] for a in result['calls'] if a[0]=='set'] == ['allowed-ips','remove']
    assert not any(a[-1] in ('dump','private-key') for a in result['calls'])


def test_preflight_refuses_even_matching_unmanaged_key(real_backend):
    agent, _, command, data = real_backend
    change(data, peers={command.wg:command.address})
    with pytest.raises(FenceRejected, match='unmanaged-live-key'):
        agent.execute(command)
    with sqlite3.connect(agent.files.path/'gateway.db') as db:
        assert db.execute('SELECT COUNT(*) FROM commands').fetchone()[0] == 0
    assert not any(a[0]=='set' for a in json.loads(data.read_text())['calls'])


@pytest.mark.parametrize('scope', ['host','subnet'])
def test_overlapping_unmanaged_route_is_never_reassigned(real_backend, scope):
    import ipaddress
    agent, _, command, data = real_backend
    other_key = base64.b64encode(bytes([43])*32).decode()
    route = command.address if scope=='host' else str(ipaddress.ip_network(command.address.replace('/32','/24'), strict=False))
    change(data, peers={other_key:route})
    with pytest.raises(FenceRejected, match='live-address-owned'):
        agent.execute(command)
    assert not any(a[0]=='set' for a in json.loads(data.read_text())['calls'])


@pytest.mark.parametrize('values', [dict(server_public=base64.b64encode(bytes([9])*32).decode()), dict(port=9999)])
def test_wrong_interface_pin_never_mutates(real_backend, values):
    agent, _, command, data = real_backend
    change(data, **values)
    with pytest.raises(FenceRejected, match='interface-pin'):
        agent.execute(command)
    assert not any(a[0]=='set' for a in json.loads(data.read_text())['calls'])


def test_success_exit_without_live_peer_is_not_ready(real_backend):
    agent, _, command, data = real_backend
    change(data, ignore_mutation=True)
    with pytest.raises(FenceRejected, match='peer-not-confirmed'):
        agent.execute(command)
    change(data, ignore_mutation=False)
    agent.execute(command)  # Pending intent can retry; preflight must not reclaim it.
    change(data, ignore_mutation=True)
    with pytest.raises(FenceRejected, match='removal-not-confirmed'):
        agent.execute(removal(command))
    change(data, ignore_mutation=False)
    agent.execute(removal(command))


def test_recovery_refuses_changed_binding_instead_of_overwriting(real_backend):
    agent, _, command, data = real_backend
    agent.execute(command)
    change(data, peers={command.wg:'10.99.0.2/32'})
    with pytest.raises(FenceRejected, match='live-binding-changed'):
        agent.recover()
    assert json.loads(data.read_text())['peers'] == {command.wg:'10.99.0.2/32'}


def test_process_input_and_output_are_bounded():
    data = b'x'*6000
    assert run([sys.executable,'-c','import sys;sys.stdout.buffer.write(sys.stdin.buffer.read())'],
               payload=data, output_limit=6000) == data
    with pytest.raises(ProcessFailed, match='process-output'):
        run([sys.executable,'-c','print("x"*100000)'], output_limit=100)
    with pytest.raises(ValueError):
        run([sys.executable], payload=b'x'*8193)


@pytest.mark.parametrize('code', ['import time;time.sleep(10)',
    'import os,time;os.close(1);time.sleep(10)'])
def test_timeout_kills_and_reaps_child(code):
    with pytest.raises(ProcessFailed, match='process-timeout'):
        run([sys.executable,'-c',code], timeout=.15)


def test_process_failure_never_exposes_stderr():
    with pytest.raises(ProcessFailed) as error:
        run([sys.executable,'-c','import sys;print("TEST-SENSITIVE",file=sys.stderr);sys.exit(7)'])
    assert str(error.value) == 'process-exit'


def ssh(tmp_path, **values):
    key, hosts = tmp_path/'key', tmp_path/'known_hosts'
    for path in (key,hosts):
        path.write_text('TEST ONLY'); path.chmod(0o600)
    return SSHGateway(host='185.251.89.19',key=key,known_hosts=hosts,**values)


def test_ssh_is_pinned_and_sends_data_only_on_stdin(system,tmp_path,monkeypatch):
    _, _, _, command, _ = system
    adapter=ssh(tmp_path)
    calls=[]
    def execute(argv,**kwargs):
        calls.append((argv,kwargs));return json.dumps(receipt(command)).encode()
    monkeypatch.setattr('control.fleet_ssh.run',execute)
    assert adapter.execute(command)==receipt(command)
    argv,kw=calls[0]
    assert argv[-2:]==['fc-fleet@185.251.89.19','fleet-v1']
    assert argv[:4]==['/usr/bin/ssh','-F','/dev/null','-T']
    for option in ('StrictHostKeyChecking=yes','IdentityAgent=none','ClearAllForwardings=yes','ProxyCommand=none'):
        assert option in argv
    assert command.wg not in argv and command.lease_id not in argv
    assert kw['payload']==command.canonical().encode() and kw['output_limit']==4096


@pytest.mark.parametrize('kind', ['bool','duplicate','wrong','error'])
def test_ssh_refuses_bad_receipt(system,tmp_path,monkeypatch,kind):
    _, _, _, command, _ = system
    answer=receipt(command)
    if kind=='bool':answer['generation']=True
    if kind=='wrong':answer['digest']='0'*64
    if kind=='error':answer={'error':'unavailable'}
    raw=json.dumps(answer).encode()
    if kind=='duplicate':raw=raw[:-1]+b',"generation":1}'
    monkeypatch.setattr('control.fleet_ssh.run',lambda *a,**kw:raw)
    with pytest.raises(ValueError):ssh(tmp_path).execute(command)


@pytest.mark.parametrize('values', [dict(user='root;id'),dict(user='-x'),dict(port=True),dict(port=0)])
def test_ssh_rejects_invalid_destination(tmp_path,values):
    with pytest.raises(ValueError):ssh(tmp_path,**values)


def test_ssh_rejects_unsafe_key_file(tmp_path):
    ssh(tmp_path)
    (tmp_path/'key').chmod(0o644)
    with pytest.raises(ValueError):
        SSHGateway(host='185.251.89.19',key=tmp_path/'key',known_hosts=tmp_path/'known_hosts')


def test_request_limits_duplicates_and_command_validation(system):
    _,agent,_,command,_=system
    raw=command.canonical().encode()
    for invalid in (b'x'*4097,raw[:-1]+b',"generation":1}',raw.replace(b'"generation":1',b'"generation":true')):
        with pytest.raises(ValueError):request(invalid,agent)
    assert request(raw,agent)==receipt(command)


def test_agent_config_requires_complete_matching_bindings(system,tmp_path):
    _,agent,_,_,_=system
    spec=dict(schema_version=1,gateway=agent.gateway.model_dump(mode='json'),state_directory=str(tmp_path/'new'),
        bindings=[dict(transport='amneziawg',version='3.1',binary='/usr/bin/awg',interface='fcfleet',
                       server_public=base64.b64encode(bytes([42])*32).decode(),port=51820)])
    assert isinstance(build(AgentConfig.model_validate_json(json.dumps(spec))),FencedGateway)
    spec['bindings'][0]['port']=9999
    with pytest.raises(ValueError):build(AgentConfig.model_validate_json(json.dumps(spec)))
    with pytest.raises(ValueError):protected(tmp_path)
