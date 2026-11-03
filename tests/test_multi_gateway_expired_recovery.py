import base64
import copy
import importlib.util
import json

import pytest
from cryptography import x509
from cryptography.hazmat.primitives.serialization import Encoding

from test_multi_gateway_renewal import fleet, profiles, inspected, approve, assert_committed, change_leaf
from test_activated_maintenance import DAY, MAINTENANCE, ProductionController, Rejected, Rpc, atomic, canonical, digest, proof
from expired_recovery import DOMAIN, sign, verify, projection


def expired_request(fleet):
    fleet.now += 12000
    assert fleet.scheduled('expired-checkpoint')['result'] == 'COMMITTED'
    fleet.now += 90*DAY
    operation = 'test-fleet-expired-authority-recovery'
    request = fleet.controller.recovery_request(operation,[])
    assert request['schema'] == 4 and request['gateway_ids'] == fleet.identities
    assert set(request['expected']) == {'RU','NL','NL2'}
    return operation,request


def signed(fleet,request):
    return sign(request,fleet.validator,fleet.root_key,fleet.now)


def test_expired_fleet_recovers_both_identities_with_one_shared_crl(fleet):
    operation,request = expired_request(fleet)
    before = profiles(fleet)
    database = fleet.nodes['RU'].database.snapshot()
    assert fleet.controller.recovery_request(operation,[]) == request
    bundle = signed(fleet,request)
    authorization = verify(bundle,fleet.validator,operation,fleet.now)
    assert authorization.secondary.predecessor.trust['gateway'] == fleet.identities['NL2']
    result = fleet.controller.run_expired(operation,bundle,approval=approve(fleet,operation))
    assert result['result'] == 'COMMITTED',result
    assert_committed(fleet,before)
    current = profiles(fleet)
    assert current['NL']['authority'] == current['NL2']['authority'] != before['NL']['authority']
    assert current['NL']['minimum_crl'] == current['NL2']['minimum_crl'] == 3
    after_database = fleet.nodes['RU'].database.snapshot()
    assert {name:value for name,value in after_database.items() if name != 'restricted_crl_sequence'} == {
        name:value for name,value in database.items() if name != 'restricted_crl_sequence'}
    checkpoint = fleet.controller.recovery_checkpoint()
    assert 'secondary_snapshot_sha256' in checkpoint
    for node in fleet.nodes.values():
        assert node.recovery_evidence(checkpoint)['current'] == node.inspect()
    before_replay = inspected(fleet)
    assert fleet.controller.run_expired(operation,bundle)['idempotent'] is True
    assert inspected(fleet) == before_replay
    fleet.service.manifest = json.loads((fleet.nodes['RU'].live/'issuer.json').read_bytes())
    assert fleet.service.fetch(proof(fleet.service,fleet.device))['device'] == fleet.device.reference
    fleet.now += 15000
    assert fleet.scheduled('after-expired-recovery')['result'] == 'COMMITTED'


@pytest.mark.parametrize('state',[*['RECOVERY_STEP_'+str(index) for index in range(1,14)],
                                 'COMMIT_DECIDED','DECISION_REPLICATED','NL_RESUMED','NL2_RESUMED','RU_RESUMED','CLEANING'])
def test_interrupted_expired_recovery_requires_explicit_three_node_rollforward(fleet,state):
    operation,request = expired_request(fleet)
    before = profiles(fleet)
    bundle = signed(fleet,request)
    def interrupt(current):
        if current == state:
            raise KeyboardInterrupt()
    fleet.controller.fault = interrupt
    with pytest.raises(KeyboardInterrupt):
        fleet.controller.run_expired(operation,bundle,approval=approve(fleet,operation))
    fleet.controller.fault = lambda current: None
    with pytest.raises(Rejected,match='OPERATOR_RECOVERY_REQUIRED'):
        fleet.scheduled('unsafe-automatic-retry')
    with pytest.raises(Rejected,match='RECOVERY_EXPLICIT_RESUME_REQUIRED'):
        fleet.controller.run_expired(operation,bundle)
    result = fleet.controller.run_expired(operation,bundle,resume=True)
    assert result['result'] == 'COMMITTED',result
    assert_committed(fleet,before)


@pytest.mark.parametrize('defect',['secondary_missing','membership','expected_missing','expected_slot',
    'checkpoint_missing','predecessor_digest','crl_floor','scope','clone','successor_family','different_ca'])
def test_offline_recovery_signer_rejects_misbound_fleet_requests(fleet,defect):
    operation,request = expired_request(fleet)
    damaged = copy.deepcopy(request)
    if defect == 'secondary_missing':
        del damaged['secondary']
    elif defect == 'membership':
        damaged['gateway_ids']['NL2'] = damaged['gateway_ids']['NL']
    elif defect == 'expected_missing':
        del damaged['expected']['NL2']
    elif defect == 'expected_slot':
        damaged['expected']['NL2']['gateway_slot'] = 'NL'
    elif defect == 'checkpoint_missing':
        del damaged['checkpoint']['secondary_snapshot_sha256']
    elif defect == 'predecessor_digest':
        damaged['secondary']['predecessor_sha256'] = 'e'*64
    elif defect == 'crl_floor':
        damaged['secondary']['floors']['crl'] += 1
    elif defect == 'scope':
        damaged['grant_scope'] = ['e'*32]
    elif defect == 'clone':
        damaged['secondary']['predecessor'] = damaged['predecessor']
        damaged['secondary']['predecessor_sha256'] = damaged['predecessor_sha256']
    elif defect == 'successor_family':
        damaged['secondary']['successor_payload']['family'] = 'e'*32
    else:
        certificate = x509.load_pem_x509_certificate(damaged['successor_payload']['authority'].encode())
        builder = (x509.CertificateBuilder().subject_name(certificate.subject).issuer_name(certificate.issuer)
            .public_key(certificate.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(certificate.not_valid_before_utc).not_valid_after(certificate.not_valid_after_utc))
        for extension in certificate.extensions:
            builder = builder.add_extension(extension.value,extension.critical)
        damaged['secondary']['successor_payload']['authority'] = builder.sign(
            fleet.service.signing_key,None).public_bytes(Encoding.PEM).decode()
    before = inspected(fleet)
    with pytest.raises(Rejected):
        signed(fleet,damaged)
    assert inspected(fleet) == before
    assert all(not node.barrier.stopped() for node in fleet.nodes.values())


def test_pair_only_recovery_signature_cannot_recover_a_fleet(fleet):
    operation,request = expired_request(fleet)
    bundle = signed(fleet,projection(request,'NL'))
    before = inspected(fleet)
    with pytest.raises(Rejected,match='GATEWAY_SET_BINDING'):
        fleet.controller.run_expired(operation,bundle,approval=approve(fleet,operation))
    assert inspected(fleet) == before
    assert all(not (node.state/'owner.json').exists() for node in fleet.nodes.values())


@pytest.mark.parametrize('defect',['signature','missing_secondary','swapped_authority','wrong_operation','expired','approval'])
def test_recovery_bundle_rejection_never_stops_or_changes_nodes(fleet,defect):
    operation,request = expired_request(fleet)
    bundle = signed(fleet,request)
    if defect in ('signature','missing_secondary','swapped_authority'):
        envelope = json.loads(bundle)
        value = json.loads(base64.b64decode(envelope['payload']))
        if defect == 'signature':
            envelope['signature'] = base64.b64encode(b'\0'*64).decode()
        else:
            if defect == 'missing_secondary':
                del value['secondary_authority']
            else:
                value['secondary_authority'] = value['authority']
            payload = canonical(value)
            envelope = dict(payload=base64.b64encode(payload).decode(),
                signature=base64.b64encode(fleet.root_key.sign(DOMAIN+payload)).decode())
        bundle = canonical(envelope)
    elif defect == 'wrong_operation':
        operation += '-wrong'
    elif defect == 'expired':
        fleet.now += DAY
    before = inspected(fleet)
    with pytest.raises(Rejected):
        fleet.controller.run_expired(operation,bundle,approval=None if defect == 'approval' else approve(fleet,operation))
    assert inspected(fleet) == before
    assert all(not (node.state/'owner.json').exists() and not node.barrier.stopped() for node in fleet.nodes.values())


@pytest.mark.parametrize('slot',['RU','NL','NL2'])
@pytest.mark.parametrize('defect',['checkpoint','live_state'])
def test_changed_checkpoint_or_profile_invalidates_offline_recovery(fleet,slot,defect):
    operation,request = expired_request(fleet)
    bundle = signed(fleet,request)
    node = fleet.nodes[slot]
    if defect == 'checkpoint':
        path = node.state/'archive'/request['checkpoint']['operation_id']/'plan.json'
        value = json.loads(path.read_bytes())
        value['secondary']['nl_profile_sha256'] = 'e'*64
    else:
        path = node.live/('issuer.json' if slot == 'RU' else 'gateway.json')
        value = json.loads(path.read_bytes())
        atomic(path,json.dumps(value,indent=2).encode())
    if defect == 'checkpoint':
        atomic(path,canonical(value))
    before = inspected(fleet)
    with pytest.raises(Rejected,match='RECOVERY_CHECKPOINT_UNCONFIRMED'):
        fleet.controller.run_expired(operation,bundle,approval=approve(fleet,operation))
    assert inspected(fleet) == before
    assert all(not (node.state/'owner.json').exists() for node in fleet.nodes.values())


@pytest.mark.parametrize('action',['acquire','quiesce','stage','promote','readback','resume','public-directory'])
def test_secondary_transport_failure_requires_explicit_recovery(fleet,action):
    operation,request = expired_request(fleet)
    bundle = signed(fleet,request)
    before = profiles(fleet)
    original = fleet.controller.nodes['NL2']
    class Unreachable:
        def call(self,current,*args):
            if current == action:
                raise Rejected('SECONDARY_DISCONNECTED')
            return original.call(current,*args)
    fleet.controller.nodes['NL2'] = Unreachable()
    result = fleet.controller.run_expired(operation,bundle,approval=approve(fleet,operation))
    assert result['result'] == 'PUBLICATION_INCOMPLETE',result
    assert fleet.nodes['RU'].barrier.stopped() and fleet.nodes['NL'].barrier.stopped()
    assert fleet.nodes['NL2'].barrier.stopped() == (action != 'acquire')
    if action == 'acquire':
        assert not (fleet.nodes['NL2'].state/'owner.json').exists()
        assert profiles(fleet)['NL2'] == before['NL2']
    fleet.controller.nodes['NL2'] = original
    with pytest.raises(Rejected,match='RECOVERY_EXPLICIT_RESUME_REQUIRED'):
        fleet.controller.run_expired(operation,bundle)
    assert fleet.controller.run_expired(operation,bundle,resume=True)['result'] == 'COMMITTED'
    assert_committed(fleet,before)


def test_wrong_secondary_readback_keeps_expired_recovery_fenced(fleet):
    operation,request = expired_request(fleet)
    bundle = signed(fleet,request)
    original = fleet.controller.nodes['NL2']
    class WrongReceipt:
        def call(self,action,*args):
            result = original.call(action,*args)
            return dict(result,plan_sha256='e'*64) if action == 'readback' else result
    fleet.controller.nodes['NL2'] = WrongReceipt()
    result = fleet.controller.run_expired(operation,bundle,approval=approve(fleet,operation))
    assert result['result'] == 'PUBLICATION_INCOMPLETE' and result['first_cause'] == 'RU_NL_MISMATCH'
    record = json.loads((fleet.controller.root/'transaction.json').read_bytes())
    assert record['commit_decided'] is False
    assert all(node.barrier.stopped() for node in fleet.nodes.values())
    fleet.controller.nodes['NL2'] = original
    assert fleet.controller.run_expired(operation,bundle,resume=True)['result'] == 'COMMITTED'


@pytest.mark.parametrize('state',['RECOVERY_STEP_7','RECOVERY_STEP_10','RECOVERY_STEP_13'])
def test_expired_approval_cannot_resume_partial_fleet_publication(fleet,state):
    operation,request = expired_request(fleet)
    bundle = signed(fleet,request)
    def interrupt(current):
        if current == state:
            raise KeyboardInterrupt()
    fleet.controller.fault = interrupt
    with pytest.raises(KeyboardInterrupt):
        fleet.controller.run_expired(operation,bundle,approval=approve(fleet,operation))
    fleet.controller.fault = lambda current: None
    before = inspected(fleet)
    fleet.now += DAY
    result = fleet.controller.run_expired(operation,bundle,resume=True)
    assert result['result'] == 'PUBLICATION_INCOMPLETE' and result['first_cause'] == 'RECOVERY_APPROVAL_EXPIRED',result
    assert inspected(fleet) == before
    assert all(node.barrier.stopped() for node in fleet.nodes.values())


@pytest.mark.parametrize('resume',[False,True])
def test_runtime_recovery_and_offline_fd_signer_cover_all_three_nodes(fleet,tmp_path,monkeypatch,capsys,resume):
    import runtime_controller as runtime
    operation,request = expired_request(fleet)
    config = dict(schema=2,node_config='synthetic-node.json',coordinator_state=str(fleet.controller.root),
        nl_source_sha256='a'*64,ssh={'test_slot':'NL'},approved_leaf_crl_schedule=True,
        secondary=dict(source_sha256='b'*64,ssh={'test_slot':'NL2'}))
    config_path,scope_path,request_path = (tmp_path/name for name in ('controller.json','scope.json','request.json'))
    atomic(config_path,canonical(config))
    atomic(scope_path,canonical([]))
    routes = []
    def transport(role,source,*,forced):
        slot = forced['test_slot']
        assert role == 'NL' and source == ('a'*64 if slot == 'NL' else 'b'*64)
        routes.append(slot)
        return Rpc(fleet.nodes[slot])
    monkeypatch.setattr(runtime,'construct',lambda path: (fleet.nodes['RU'],'c'*64))
    monkeypatch.setattr(runtime,'SshNode',transport)
    monkeypatch.setattr(runtime,'ProductionController',lambda root,nodes,validator:
        ProductionController(root,nodes,validator,clock=fleet.clock))
    monkeypatch.setattr(runtime.time,'time',lambda: fleet.clock())
    monkeypatch.setattr(runtime.resource,'setrlimit',lambda *args: None)
    monkeypatch.setattr(runtime.os,'umask',lambda *args: None)
    arguments = ['runtime_controller.py','--config',str(config_path),'--operation',operation]
    monkeypatch.setattr(runtime.sys,'argv',arguments+['--mode','expired-request','--grant-scope',str(scope_path),
        '--request-output',str(request_path)])
    runtime.main()
    assert json.loads(capsys.readouterr().out)['result'] == 'RECOVERY_REQUESTED'
    assert json.loads(request_path.read_bytes()) == request
    specification = importlib.util.spec_from_file_location('fleet_recovery_signer',MAINTENANCE.parent/'offline/sign_authority.py')
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    anchor_path,bundle_path,key_path = (tmp_path/name for name in ('anchor','bundle.json','synthetic-root.key'))
    atomic(anchor_path,base64.b64encode(fleet.service.anchor))
    atomic(key_path,fleet.root_key.private_bytes_raw())
    with key_path.open('rb') as key:
        monkeypatch.setattr(runtime.sys,'argv',['sign_authority.py','--request',str(request_path),'--anchor',str(anchor_path),
            '--root-key-fd',str(key.fileno()),'--output',str(bundle_path),'--confirm-authority-renewal',
            '--expired-recovery','--all-activated'])
        module.main()
    receipt = json.loads(capsys.readouterr().out)
    assert receipt['result'] == 'SIGNED_OFFLINE' and receipt['root_key_exported'] is False
    bundle = bundle_path.read_bytes()
    assert receipt['bundle_sha256'] == digest(bundle)
    assert verify(bundle,fleet.validator,operation,fleet.now).secondary is not None
    before = profiles(fleet)
    if resume:
        def interrupt(current):
            if current == 'RECOVERY_STEP_12':
                raise KeyboardInterrupt()
        fleet.controller.fault = interrupt
        with pytest.raises(KeyboardInterrupt):
            fleet.controller.run_expired(operation,bundle,approval=approve(fleet,operation))
    monkeypatch.setattr(runtime.sys,'argv',arguments+['--mode','expired-resume' if resume else 'expired-apply',
        '--authority-bundle',str(bundle_path),'--approve-maintenance-outage'])
    runtime.main()
    assert json.loads(capsys.readouterr().out)['result'] == 'COMMITTED'
    assert routes == ['NL','NL2','NL','NL2']
    assert_committed(fleet,before)


def test_expired_recovery_accepts_last_checkpoint_with_unchanged_secondary_profile(fleet):
    change_leaf(fleet,'NL',expires=fleet.now+500)
    assert fleet.scheduled('primary-only-checkpoint')['result'] == 'COMMITTED'
    checkpoint = fleet.controller.recovery_checkpoint()
    location = fleet.nodes['NL2'].state/'archive'/checkpoint['operation_id']
    assert json.loads((location/'files.json').read_bytes()) == {}
    fleet.now += 90*DAY
    operation = 'test-unchanged-secondary-expired'
    request = fleet.controller.recovery_request(operation,[])
    assert fleet.controller.run_expired(operation,signed(fleet,request),approval=approve(fleet,operation))['result'] == 'COMMITTED'


def test_expired_recovery_preserves_revoked_client_and_crl_entries(fleet):
    response = fleet.service.fetch(proof(fleet.service,fleet.device))
    serial = x509.load_pem_x509_certificate(response['certificate'].encode()).serial_number
    with fleet.service.access.db() as database:
        database.execute('UPDATE devices SET revoked=1 WHERE device=?',(fleet.device.reference,))
    assert fleet.scheduled('revocation-checkpoint')['result'] == 'COMMITTED'
    for profile in profiles(fleet).values():
        assert x509.load_pem_x509_crl(profile['revocations'].encode()).get_revoked_certificate_by_serial_number(serial) is not None
    operation,request = expired_request(fleet)
    before = fleet.nodes['RU'].database.snapshot()
    result = fleet.controller.run_expired(operation,signed(fleet,request),approval=approve(fleet,operation))
    assert result['result'] == 'COMMITTED',result
    assert fleet.nodes['RU'].database.snapshot()['devices'] == before['devices']
    for profile in profiles(fleet).values():
        assert x509.load_pem_x509_crl(profile['revocations'].encode()).get_revoked_certificate_by_serial_number(serial) is not None


def test_expired_recovery_preserves_independent_delegation_sequences(fleet):
    path = fleet.nodes['RU'].live/'gateways'/'nl-amsterdam-2'/'issuer.json'
    envelope = json.loads(path.read_bytes())
    trust = json.loads(base64.b64decode(envelope['payload']))
    trust['sequence'] = 7
    payload = canonical(trust)
    from control.friends.restricted import DOMAIN as ISSUER_DOMAIN
    atomic(path,canonical(dict(payload=base64.b64encode(payload).decode(),
        signature=base64.b64encode(fleet.root_key.sign(ISSUER_DOMAIN+payload)).decode())))
    operation,request = expired_request(fleet)
    assert request['floors']['authority'] == 1 and request['secondary']['floors']['authority'] == 7
    assert request['successor_payload']['sequence'] == 2 and request['secondary']['successor_payload']['sequence'] == 8
    result = fleet.controller.run_expired(operation,signed(fleet,request),approval=approve(fleet,operation))
    assert result['result'] == 'COMMITTED',result
