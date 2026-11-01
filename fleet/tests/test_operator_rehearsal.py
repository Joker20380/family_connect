import copy
from types import SimpleNamespace

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey

from fleet.acceptance import STEPS, verify
from fleet.contracts import FleetError, canonical
from fleet.material_factory import generate, raw_public
from fleet.operator_harness import mesh_result, run
from fleet.rehearsal_cli import COMMANDS, parser
from fleet.role_config import SNI, awg_config, mesh_config, publisher_config, tcp_config


@pytest.mark.parametrize('action',[action for action in COMMANDS if action!='prepare'])
def test_operator_commands_require_explicit_permit_and_pin(action):
    with pytest.raises(SystemExit):
        parser().parse_args([action])


@pytest.mark.parametrize('flag',['--force','--skip-health','--insecure','--live','--shell'])
def test_no_generic_live_bypass(flag):
    with pytest.raises(SystemExit):
        parser().parse_args(['stage',flag])


def test_fresh_material_factory_and_role_contracts():
    private=Ed25519PrivateKey.generate()
    public=raw_public(X25519PrivateKey.generate())+raw_public(private)
    publisher=canonical(dict(scope='DISPOSABLE_FLEET_REHEARSAL',token='synthetic-token-not-a-provider-credential'))
    slots,clients=generate('fleet-rehearsal-test',public,private,publisher,issued_at=1000,expires_at=1300)
    assert awg_config(slots['awg-material'])[1]['port']==51827
    assert b'4443' in tcp_config(slots['tcp-material'])
    assert publisher_config(slots['publisher-material']).startswith(b'YANDEX_')
    profile,binding=mesh_config(slots['mesh-material'],instance_id='fleet-rehearsal-test',now=1001,permit_expires_at=1300)
    assert binding['expires_at']==1300
    other,unused=generate('fleet-rehearsal-test',public,private,publisher,issued_at=1000,expires_at=1300)
    assert other['awg-material']!=slots['awg-material'] and other['tcp-material']!=slots['tcp-material']
    assert clients['mesh-profile.json'] not in slots.values()
    assert SNI=='www.cloudflare.com'
    from fleet.contracts import load
    rejected=load(slots['tcp-material'])
    rejected.update(sni='www.microsoft.com',destination='www.microsoft.com:443')
    with pytest.raises(FleetError,match='tcp_scope_or_destination'):tcp_config(canonical(rejected))


def test_mesh_safe_result_requires_all_native_evidence():
    events=[dict(event='family_auth',accepted=True),dict(event='mux_result',status='PASS'),
            dict(event='fleet_probe_egress',passed=True,expected_rehearsal_egress=True)]
    events += [dict(event='mux_https',passed=True) for index in range(4)]
    events += [dict(event='mux_dns',passed=True) for index in range(3)]
    raw=b'\n'.join(canonical(event) for event in events)
    assert all(value=='PASS' for value in mesh_result(raw).values())
    for index in range(len(events)):
        with pytest.raises(FleetError):
            mesh_result(b'\n'.join(canonical(event) for position,event in enumerate(events) if position!=index))


def test_mesh_uses_authenticated_broker_not_diagnostic_bootstrap(tmp_path,monkeypatch):
    import base64
    from device_identity import friends
    from fleet import operator_harness as module
    from fleet.contracts import digest
    private=Ed25519PrivateKey.generate()
    public=raw_public(X25519PrivateKey.generate())+raw_public(private)
    publisher=canonical(dict(scope='DISPOSABLE_FLEET_REHEARSAL',token='synthetic-token'))
    unused,clients=generate('fleet-rehearsal-test',public,private,publisher,issued_at=1000,expires_at=1300)
    monkeypatch.setattr(friends,'load_friends_identity',lambda directory,create:SimpleNamespace(public_identity=base64.b64encode(public)))
    monkeypatch.setattr(module,'PROBE_IDENTITY_SHA256',digest(public))
    monkeypatch.setattr(module,'read_private',lambda filename:clients['mesh-profile.json'])
    harness=object.__new__(module.Harness)
    harness.config={'probe_identity':str(tmp_path/'identity'),'mesh_profile':str(tmp_path/'profile.json')}
    harness.probe=tmp_path/'operator-probe'
    harness.target='8.8.8.8'
    calls=[]
    def command(argv,**options):
        calls.append((argv,options))
        return SimpleNamespace(stdout=b'bound-native-output')
    monkeypatch.setattr(module,'command',command)
    monkeypatch.setattr(module,'mesh_result',lambda raw:raw)
    assert harness.mesh(tmp_path)==b'bound-native-output'
    assert calls==[([str(harness.probe),'-family-config',harness.config['mesh_profile'],
        '-broker-url','https://8.8.8.8:18444','-mux-config',str(tmp_path/'mux.json'),'-duration','180s'],
        dict(timeout=200,env=dict(PATH=module.os.environ.get('PATH','/usr/bin:/bin'),HOME=str(tmp_path),FC_REHEARSAL_TARGET_IPV4='8.8.8.8')))]
    assert not (tmp_path/'bootstrap.json').exists()
    assert clients['mesh-profile.json'] not in canonical(calls)


def test_synthetic_operator_harness_signs_only_after_probes_and_cleanup():
    key=Ed25519PrivateKey.generate()
    challenge=dict(instance_id='fleet-rehearsal-test',bundle_id='gw-'+'a'*32,operation_id='verification-one',
        verification_nonce='b'*64,ipv4='8.8.8.8',local_health_sha256='c'*64,started_at=1000,expires_at=1300)
    calls=[]
    harness=SimpleNamespace(challenge=challenge)
    for role,steps in STEPS.items():
        def probe(directory,role=role,steps=steps):
            calls.append(role)
            return {step:'PASS' for step in steps}
        setattr(harness,role,probe)
    receipt=run(harness,key,now=lambda:1001)
    assert calls==['awg','tcp','mesh']
    assert verify(receipt,key.public_key(),challenge,now=1002)
    harness.tcp=lambda directory:(_ for unused in ()).throw(FleetError('fixture_failure'))
    failed=run(harness,key,now=lambda:1001)
    assert failed['body']['cleanup']=='FAIL'
    with pytest.raises(FleetError):
        verify(failed,key.public_key(),challenge,now=1002)


@pytest.mark.parametrize('occupied',[False,True])
def test_awg_policy_precedes_main_table_and_cleans_exact_owned_rule(tmp_path,monkeypatch,occupied):
    import base64
    from fleet import operator_harness as module
    public=base64.b64encode(b'a'*32).decode()
    private=base64.b64encode(b'b'*32).decode()
    calls=[]
    process=SimpleNamespace(active=False)
    harness=object.__new__(module.Harness)
    harness.config={'awg_peer':'unused'}
    harness.native=tmp_path
    harness.target='8.8.8.8'
    harness.challenge={'started_at':1000}
    harness.web=lambda prefix:calls.append(['web',*prefix])
    monkeypatch.setattr(module,'read_private',lambda path:canonical(dict(scope='DISPOSABLE_FLEET_REHEARSAL',server_public_key=public,peer_private_key=private)))
    def command(argv,**options):
        calls.append(argv)
        output=b'';result=0
        if argv==['ip','link','show','dev','fcrhp0']:result=0 if process.active else 1
        elif argv==['ip','rule','show']:output=b'0: from all lookup local\n32766: from all lookup main\n'+(b'12027: from all lookup 7\n' if occupied else b'')
        elif argv[0]=='dig':output=b'93.184.216.34\n'
        elif argv[-1]=='latest-handshakes':output=(public+'\t1001\n').encode()
        return SimpleNamespace(returncode=result,stdout=output)
    def start(*arguments,**options):process.active=True;return process
    monkeypatch.setattr(module,'command',command)
    monkeypatch.setattr(module.subprocess,'Popen',start)
    monkeypatch.setattr(module,'stop_process',lambda value:setattr(value,'active',False))
    if occupied:
        with pytest.raises(FleetError,match='operator_awg_route_busy'):harness.awg(tmp_path)
        assert not any('add' in argv for argv in calls)
        return
    assert all(value=='PASS' for value in harness.awg(tmp_path).values())
    added=next(argv for argv in calls if argv[:3]==['ip','rule','add'])
    removed=next(argv for argv in calls if argv[:3]==['ip','rule','del'])
    assert 0<int(added[4])<32766 and added[3:]==removed[3:]
    assert added[-2:]==['table','50027'] and not (tmp_path/'awg.conf').exists()


@pytest.mark.parametrize('mode',['awg','tcp','private-dns'])
def test_web_dns_follows_transport_and_preserves_tls_validation(monkeypatch,mode):
    from fleet import operator_harness as module
    harness=object.__new__(module.Harness)
    harness.target='8.8.8.8'
    calls=[]
    def command(argv,**options):
        calls.append(argv)
        response=(b'10.0.0.1\n' if mode=='private-dns' else b'alias.example.\n1.1.1.1\n') if argv[0]=='dig' else b'ip=8.8.8.8\n'
        return SimpleNamespace(stdout=response,returncode=0)
    monkeypatch.setattr(module,'command',command)
    prefix=['--socks5-hostname','127.0.0.1:19728'] if mode=='tcp' else ['--interface','10.203.217.2']
    if mode=='private-dns':
        with pytest.raises(FleetError,match='operator_awg_https_dns'):harness.web(prefix)
        assert not any(argv[0]=='curl' for argv in calls)
        return
    harness.web(prefix)
    if mode=='awg':
        assert [argv[:4] for argv in calls if argv[0]=='dig']==[['dig','-b','10.203.217.2','@9.9.9.9']]*2
        assert all('--resolve' in argv for argv in calls if argv[0]=='curl')
    else:assert all(argv[0]=='curl' and '--socks5-hostname' in argv and '--resolve' not in argv for argv in calls)
    assert all('--insecure' not in argv and '-k' not in argv for argv in calls)
