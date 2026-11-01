import http.client
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from fleet.acceptance import sign
from fleet.contracts import FleetError, canonical, digest
from fleet.materials import public_hex
from fleet.monitoring import server
from fleet.rehearsal_cli import execute_known
from fleet.tests.test_permit import authority
from fleet.tests.test_rehearsal_state import active, external, request, state
from fleet.tests.test_role_runtime import runtime


def test_distinct_post_start_challenges_and_negative_upgrade(state):
    active(state)
    state.execute(request(state,'stage','-b',bundle='b'))
    state.execute(request(state,'upgrade','-b',bundle='b'))
    first=state.status()['verification']['verification_nonce']
    receipt=external(state)
    receipt['body']['roles']['tcp']['authentication']='FAIL'
    receipt=sign(receipt['body'],state.runtime.test_signer,now=1001)
    operation=request(state,'complete-verification','-negative',bundle='b')
    operation['parameters']={'receipt':receipt}
    result=state.execute(operation)
    assert result['result']=='FAIL' and result['rollback']=='PASS'
    assert state.status()['state']=='ACTIVE'
    assert state.runtime.current==state.permit['body']['bundle_a']
    state.execute(request(state,'upgrade','-again',bundle='b'))
    assert state.status()['verification']['verification_nonce']!=first


def test_node_identity_cannot_sign_acceptance(state):
    state.execute(request(state,'stage'))
    state.execute(request(state,'start-verification'))
    node_key=Ed25519PrivateKey.generate()
    receipt=external(state)
    receipt['body']['signer']=digest(bytes.fromhex(public_hex(node_key.public_key())))
    receipt=sign(receipt['body'],node_key,now=1001)
    operation=request(state,'complete-verification')
    operation['parameters']={'receipt':receipt}
    assert state.execute(operation)['result']=='FAIL'
    assert state.status()['state']=='AWAITING_EXTERNAL_ACCEPTANCE'


def test_status_and_observed_interrupted_recovery(state):
    operation=request(state,'stage')
    receipt=state.execute(operation)
    receipt['result']='RUNNING'
    (state.directory/'stage.json').write_bytes(canonical(receipt))
    status=state.execute(request(state,'status'))
    assert status['operations'][0]['result']=='RUNNING'
    with pytest.raises(FleetError,match='interrupted_operation'):
        state.execute(request(state,'stage','-blind'))
    recovery=request(state,'drain','-recover')
    recovery['parameters']=dict(recover_operation_id='stage',recover_binding=receipt['binding'])
    assert state.execute(recovery)['result']=='PASS'
    assert state.runtime.stopped and state.status()['state']=='DRAINING'
    assert state.execute(request(state,'status'))['operations'][-1]['result']!='RUNNING'


@pytest.mark.parametrize('action',['enroll','deliver-materials','start-verification','complete-verification','status','retire'])
def test_unknown_remote_outcome_never_blind_retry(action):
    calls=[]
    def execute(action, operation_id, parameters=None):
        calls.append(action)
        raise FleetError('remote_transport_failure')
    result=execute_known(SimpleNamespace(execute=execute),action,'operation-one')
    assert result['result']=='UNKNOWN' and result['recovery']=='READ_JOURNAL_DO_NOT_RETRY'
    assert calls==([action] if action=='status' else [action,'status'])


def test_retire_before_activation_preserves_foreign_network_resources(runtime):
    runtime.executor.table=b'foreign ownership sentinel'
    runtime.sysctl.write_bytes(b'foreign sysctl sentinel')
    runtime.retire()
    assert runtime.executor.table==b'foreign ownership sentinel'
    assert runtime.sysctl.read_bytes()==b'foreign sysctl sentinel'


def test_foreign_same_named_unit_is_not_stopped(runtime):
    path=runtime.root/'etc/systemd/system/fc-rehearsal-mesh.service'
    path.write_bytes(b'foreign service sentinel')
    with pytest.raises(FleetError):
        runtime.stop()
    assert not any(argv[:2]==['systemctl','stop'] for argv,data in runtime.executor.calls)


def test_monitor_is_loopback_readonly_and_no_external_client(monkeypatch):
    from fleet import monitoring
    monkeypatch.setattr(monitoring,'observe',lambda metadata:dict(instance_id='fixture',bundle_id='fixture',load=[0,0,0]))
    listener=server({},port=0)
    thread=threading.Thread(target=listener.serve_forever,daemon=True)
    thread.start()
    try:
        assert listener.server_address[0]=='127.0.0.1'
        connection=http.client.HTTPConnection(*listener.server_address,timeout=5)
        connection.request('GET','/status')
        response=connection.getresponse()
        assert response.status==200 and b'fixture' in response.read()
        connection.request('POST','/status',body=b'mutation')
        response=connection.getresponse()
        assert response.status==501
        response.read()
        connection.close()
    finally:
        listener.shutdown()
        thread.join()
        listener.server_close()


def test_bundle_templates_match_exact_renderer():
    from fleet.rehearsal_templates import SYSCTL, nftables, units
    root=Path(__file__).parents[1]/'templates/rehearsal'
    for name,content in units('gw-'+'a'*32,'fleet-rehearsal-template',14400,1893456000).items():
        template=(root/(name+'.in')).read_bytes()
        for old,new in ((b'{{BUNDLE_ID}}',('gw-'+'a'*32).encode()),(b'{{INSTANCE_ID}}',b'fleet-rehearsal-template'),
                        (b'{{LIFETIME_SECONDS}}',b'14400'),(b'{{EXPIRY_UTC}}',b'2030-01-01 00:00:00 UTC')):
            template=template.replace(old,new)
        assert template==content
    assert (root/'nftables.nft.in').read_bytes().replace(b'{{UPLINK}}',b'eth0')==nftables('eth0')
    assert (root/'sysctl.conf.in').read_bytes()==SYSCTL


@pytest.mark.parametrize('path,mode',[('publisher.env',0o640),('tcp.json',0o600),('profile/gateway.json',0o644)])
def test_config_exact_modes_are_health_preconditions(runtime,path,mode):
    target=runtime.manifest['bundle_id']
    runtime.stage(target)
    runtime.configure(target)
    (runtime.configuration/target/path).chmod(mode)
    with pytest.raises(FleetError):
        runtime.verify_configuration(target)


def test_readonly_release_directory_is_a_health_precondition(runtime):
    target=runtime.manifest['bundle_id']
    runtime.stage(target)
    (runtime.releases/target/'bin').chmod(0o755)
    with pytest.raises(FleetError,match='release_directory_mode'):
        runtime.verify_release(target)


def test_evidence_projection_never_persists_raw_extra_fields(authority):
    from fleet.evidence import project, verify
    key,permit,unused=authority
    source=dict(result='PASS',state_after='ACTIVE',elapsed_seconds=1.25,token='fixture-private-token',
                private_key='fixture-private-key',join_url='https://private.invalid/fixture')
    receipt=project('completion',source,permit,key,operation_id='operation-one',bundle_id=permit['body']['bundle_a'],issued_at=1001)
    body=verify(receipt,key.public_key())
    assert body['duration_ms']==1250 and body['source_receipt_sha256']==digest(canonical(source))
    assert b'fixture-private' not in canonical(receipt) and b'private.invalid' not in canonical(receipt)
    assert b'8.8.8.8' not in canonical(receipt)
