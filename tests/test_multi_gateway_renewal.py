import base64
import json
import os

import pytest
from cryptography import x509
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

from control.friends.restricted import DOMAIN, PROTOCOL, utc
from device_identity.device import DeviceIdentity
from test_activated_maintenance import (
    Barrier, Cluster, ProductionController, ProductionNode, Rejected, Rpc, atomic, canonical, pem_key, proof,
)


@pytest.fixture
def fleet(tmp_path):
    cluster = Cluster(tmp_path)
    primary = cluster.nodes['NL'].public_gateway()
    secondary = DeviceIdentity.generate()
    public = base64.b64decode(secondary.public_identity)
    key = Ed25519PrivateKey.from_private_bytes(secondary._identity.get_private_key()[32:])
    issuer = x509.load_pem_x509_certificate(primary['authority'].encode())
    subject = x509.Name([x509.NameAttribute(NameOID.SERIAL_NUMBER, secondary.reference)] + [
        x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, claim) for claim in
        ('protocol='+PROTOCOL,'family='+cluster.family,'role=gateway','revision=1')])
    leaf = (x509.CertificateBuilder().subject_name(subject).issuer_name(issuer.subject)
        .public_key(key.public_key()).serial_number(x509.random_serial_number())
        .not_valid_before(utc(cluster.now-5)).not_valid_after(utc(cluster.now+14395))
        .add_extension(x509.BasicConstraints(ca=False,path_length=None),True)
        .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]),False)
        .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(cluster.service.signing_key.public_key()),False)
        .add_extension(x509.SubjectAlternativeName([x509.UniformResourceIdentifier(
            'urn:family-connect:identity:'+public.hex())]),False).sign(cluster.service.signing_key,None))
    trust = json.loads(base64.b64decode(cluster.service.manifest['payload']))
    trust['gateway'] = secondary.reference
    payload = canonical(trust)
    folder = cluster.nodes['RU'].live/'gateways'/'nl-amsterdam-2'
    folder.mkdir(parents=True,mode=0o700)
    folder.parent.chmod(0o700)
    atomic(folder/'issuer.json',canonical(dict(payload=base64.b64encode(payload).decode(),
        signature=base64.b64encode(cluster.root_key.sign(DOMAIN+payload)).decode())))
    directory = json.loads((cluster.nodes['NL'].live/'directory.json').read_bytes())
    directory['seeds'][0].update(gateway=secondary.reference,join_url='https://telemost.yandex.ru/j/second')
    atomic(folder/'directory.json',canonical(directory))
    cluster.identities = dict(NL=cluster.gateway,NL2=secondary.reference)
    for slot,node in list(cluster.nodes.items()):
        cluster.nodes[slot] = ProductionNode(node.role,node.live,node.state,cluster.validator,
            database=node.database,barrier=node.barrier,clock=cluster.clock,profile_uid=os.geteuid(),
            gateway_ids=cluster.identities,gateway_slot=slot)
    live,state = tmp_path/'NL2-live',tmp_path/'NL2-state'
    live.mkdir(mode=0o700)
    state.mkdir(mode=0o700)
    profile = dict(primary,certificate=leaf.public_bytes(Encoding.PEM).decode(),gateway=secondary.reference,
                   private_key=pem_key(key))
    profile.pop('profile_sha256')
    atomic(live/'gateway.json',canonical(profile))
    atomic(live/'directory.json',canonical(directory))
    cluster.nodes['NL2'] = ProductionNode('NL',live,state,cluster.validator,clock=cluster.clock,
        barrier=Barrier('NL',live,cluster.clock,cluster.family,secondary.reference),profile_uid=os.geteuid(),
        gateway_ids=cluster.identities,gateway_slot='NL2')
    cluster.controller = ProductionController(tmp_path/'coordinator',
        {slot:Rpc(node) for slot,node in cluster.nodes.items()},cluster.validator,clock=cluster.clock)
    return cluster


def profiles(fleet):
    return {slot:json.loads((fleet.nodes[slot].live/'gateway.json').read_bytes()) for slot in ('NL','NL2')}


def inspected(fleet):
    return {slot:node.inspect() for slot,node in fleet.nodes.items()}


def change_leaf(fleet,slot,*,expires=None,subject=None,extensions=None):
    profile = profiles(fleet)[slot]
    leaf = x509.load_pem_x509_certificate(profile['certificate'].encode())
    builder = (x509.CertificateBuilder().subject_name(leaf.subject if subject is None else subject)
        .issuer_name(leaf.issuer).public_key(leaf.public_key()).serial_number(leaf.serial_number)
        .not_valid_before(leaf.not_valid_before_utc)
        .not_valid_after(leaf.not_valid_after_utc if expires is None else utc(expires)))
    for extension in (leaf.extensions if extensions is None else extensions):
        builder = builder.add_extension(extension.value,extension.critical)
    profile['certificate'] = builder.sign(fleet.service.signing_key,None).public_bytes(Encoding.PEM).decode()
    atomic(fleet.nodes[slot].live/'gateway.json',canonical(profile))


def assert_committed(fleet, before):
    after = profiles(fleet)
    assert after['NL']['revocations'] == after['NL2']['revocations'] == fleet.service.crl_source().decode()
    assert after['NL']['minimum_crl'] == after['NL2']['minimum_crl']
    assert after['NL']['certificate'] != after['NL2']['certificate']
    for slot in ('NL','NL2'):
        assert after[slot]['private_key'] == before[slot]['private_key']
        assert after[slot]['gateway'] == before[slot]['gateway']
        assert after[slot]['certificate'] != before[slot]['certificate']
        destination = fleet.nodes['RU'].directory_destination(slot)
        assert destination.read_bytes() == (fleet.nodes[slot].live/'directory.json').read_bytes()
    assert all(not node.barrier.stopped() for node in fleet.nodes.values())
    fleet.snapshot()


def test_healthy_fleet_noop_has_no_remote_writes(fleet):
    before = inspected(fleet)
    result = fleet.scheduled()
    assert result['result'] == 'NOOP'
    assert result['remote_writes'] == result['restarts'] == result['files_changed'] == 0
    assert inspected(fleet) == before


@pytest.mark.parametrize('advance',[12000,14400,20000])
def test_shared_renewal_preserves_two_gateway_identities(fleet,advance):
    before = profiles(fleet)
    fleet.now += advance
    result = fleet.scheduled()
    assert result['result'] == 'COMMITTED',result
    assert_committed(fleet,before)
    crl = x509.load_pem_x509_crl(fleet.service.crl_source())
    assert crl.extensions.get_extension_for_class(x509.CRLNumber).value.crl_number == 2
    record = json.loads((fleet.controller.root/'transaction.json').read_bytes())
    assert set(record['reconciliation']) == {'RU','NL','NL2'}
    assert record['reconciliation']['RU'] == record['reconciliation']['NL'] == record['reconciliation']['NL2']


def test_revocation_reaches_both_gateways_with_one_crl_sequence(fleet):
    response = fleet.service.fetch(proof(fleet.service,fleet.device))
    serial = x509.load_pem_x509_certificate(response['certificate'].encode()).serial_number
    with fleet.service.access.db() as database:
        database.execute('UPDATE devices SET revoked=1 WHERE device=?',(fleet.device.reference,))
    result = fleet.scheduled()
    assert result['result'] == 'COMMITTED',result
    for profile in profiles(fleet).values():
        crl = x509.load_pem_x509_crl(profile['revocations'].encode())
        assert crl.get_revoked_certificate_by_serial_number(serial) is not None
        assert profile['minimum_crl'] == 2


def test_legacy_writer_cannot_omit_configured_second_gateway(fleet):
    controller = ProductionController(fleet.controller.root,
        {slot:Rpc(fleet.nodes[slot]) for slot in ('RU','NL')},fleet.validator,clock=fleet.clock)
    before = inspected(fleet)
    fleet.now += 12000
    with pytest.raises(Rejected,match='GATEWAY_SET_REQUIRED'):
        controller.run('test-legacy-writer-rejected',scheduled=True,approved_leaf_crl_schedule=True)
    assert inspected(fleet) == before
    assert not (controller.root/'transaction.json').exists()


@pytest.mark.parametrize('stage',[
    'RU_ACQUIRED','NL_ACQUIRED','NL2_ACQUIRED','RU_QUIESCED','NL_QUIESCED','NL2_QUIESCED',
    'PREPARED','RU_STAGED','NL_STAGED','NL2_STAGED','RU_PROMOTED','NL_PROMOTED','NL2_PROMOTED',
    'COMMIT_DECIDED','DECISION_REPLICATED','NL_RESUMED','NL2_RESUMED','RU_RESUMED','CLEANING',
])
def test_controller_restart_cannot_commit_only_one_gateway(fleet,stage):
    before = profiles(fleet)
    fleet.now += 12000
    visited = []
    def interrupt(state):
        visited.append(state)
        if state == stage:
            raise KeyboardInterrupt()
    fleet.controller.fault = interrupt
    with pytest.raises(KeyboardInterrupt):
        fleet.scheduled()
    fleet.controller.fault = lambda state: None
    assert stage in visited
    result = fleet.scheduled('restart')
    if stage in ('COMMIT_DECIDED','DECISION_REPLICATED','NL_RESUMED','NL2_RESUMED','RU_RESUMED','CLEANING'):
        assert result['result'] == 'COMMITTED',result
        assert_committed(fleet,before)
    else:
        assert result['result'] == 'ABORTED',result
        assert profiles(fleet) == before
        assert all(not node.barrier.stopped() for node in fleet.nodes.values())


def test_secondary_transport_failure_does_not_acquire_any_node(fleet):
    before = inspected(fleet)
    class Unreachable:
        def call(self,*args):
            raise Rejected('SECONDARY_UNAVAILABLE')
    fleet.controller.nodes['NL2'] = Unreachable()
    fleet.now += 12000
    with pytest.raises(Rejected,match='SECONDARY_UNAVAILABLE'):
        fleet.scheduled()
    assert inspected(fleet) == before
    assert not (fleet.controller.root/'transaction.json').exists()


def test_only_secondary_leaf_due_is_renewed_without_extra_crl(fleet):
    change_leaf(fleet,'NL2',expires=fleet.now+1000)
    before = profiles(fleet)
    result = fleet.scheduled()
    assert result['result'] == 'COMMITTED',result
    after = profiles(fleet)
    assert after['NL'] == before['NL']
    assert after['NL2']['certificate'] != before['NL2']['certificate']
    assert after['NL2']['private_key'] == before['NL2']['private_key']
    assert after['NL2']['revocations'] == before['NL2']['revocations']
    assert after['NL2']['minimum_crl'] == 1


@pytest.mark.parametrize('slot',['NL','NL2'])
@pytest.mark.parametrize('defect',['floor_ahead','floor_bool','gateway','family','revision','leaf_role','leaf_identity'])
def test_each_gateway_is_bound_before_any_remote_write(fleet,slot,defect):
    if defect in ('leaf_role','leaf_identity'):
        leaf = x509.load_pem_x509_certificate(profiles(fleet)[slot]['certificate'].encode())
        if defect == 'leaf_role':
            subject = x509.Name([x509.NameAttribute(attribute.oid,
                'role=client' if attribute.value == 'role=gateway' else attribute.value) for attribute in leaf.subject])
            change_leaf(fleet,slot,subject=subject)
        else:
            extensions = [extension for extension in leaf.extensions if not isinstance(extension.value,x509.SubjectAlternativeName)]
            extensions.append(x509.Extension(x509.oid.ExtensionOID.SUBJECT_ALTERNATIVE_NAME,False,
                x509.SubjectAlternativeName([x509.UniformResourceIdentifier('urn:family-connect:identity:'+'ab'*64)])))
            change_leaf(fleet,slot,extensions=extensions)
    else:
        profile = profiles(fleet)[slot]
        field,value = {'floor_ahead':('minimum_crl',2),'floor_bool':('minimum_crl',True),
            'gateway':('gateway','e'*32),'family':('family','e'*32),'revision':('minimum_revision',2)}[defect]
        profile[field] = value
        atomic(fleet.nodes[slot].live/'gateway.json',canonical(profile))
    before = inspected(fleet)
    with pytest.raises((Rejected,ValueError)):
        fleet.scheduled()
    assert inspected(fleet) == before
    assert not (fleet.controller.root/'transaction.json').exists()


@pytest.mark.parametrize('stage',['RU_STAGED','NL2_STAGED','NL2_PROMOTED'])
def test_secondary_expired_rollback_is_durable_and_never_resumes(fleet,stage):
    change_leaf(fleet,'NL2',expires=fleet.now+1000)
    before = inspected(fleet)
    def interrupt(state):
        if state == stage:
            raise KeyboardInterrupt()
    fleet.controller.fault = interrupt
    with pytest.raises(KeyboardInterrupt):
        fleet.scheduled()
    fleet.controller.fault = lambda state: None
    fleet.now += 1001
    result = fleet.scheduled('restart')
    assert result['result'] == 'ROLLED_BACK_READERS_STOPPED',result
    assert inspected(fleet) == before
    assert all(node.barrier.stopped() and node.barrier.starts == 0 for node in fleet.nodes.values())
    record = json.loads((fleet.controller.root/'transaction.json').read_bytes())
    assert fleet.controller.recover(record)['result'] == 'ROLLED_BACK_READERS_STOPPED'
    assert all(node.barrier.stopped() for node in fleet.nodes.values())


@pytest.mark.parametrize('action',['stage','promote','readback','commit-decision','resume','public-directory','cleanup'])
def test_secondary_failed_rpc_is_reconciled_without_partial_ru_resume(fleet,action):
    before = profiles(fleet)
    original = fleet.controller.nodes['NL2']
    failed = []
    class FailOnce:
        def call(self,called,*args):
            if called == action and not failed:
                failed.append(called)
                raise Rejected('SECONDARY_TEST_FAILURE')
            return original.call(called,*args)
    fleet.controller.nodes['NL2'] = FailOnce()
    fleet.now += 12000
    result = fleet.scheduled()
    assert failed == [action]
    if action == 'cleanup':
        assert result['result'] == 'CLEANUP_REQUIRED'
        result = fleet.scheduled('retry')
    if action in ('stage','promote','readback'):
        assert result['result'] == 'ABORTED',result
        assert profiles(fleet) == before
    else:
        assert result['result'] == 'COMMITTED',result
        assert_committed(fleet,before)
    assert all(not node.barrier.stopped() for node in fleet.nodes.values())


def test_unreachable_secondary_after_commit_fences_ru_until_reconnected(fleet):
    before = profiles(fleet)
    original = fleet.controller.nodes['NL2']
    failed = []
    class UnreachableAfterCommit:
        def call(self,action,*args):
            if action == 'resume' or failed:
                failed.append(action)
                raise Rejected('SECONDARY_DISCONNECTED')
            return original.call(action,*args)
    fleet.controller.nodes['NL2'] = UnreachableAfterCommit()
    fleet.now += 12000
    result = fleet.scheduled()
    assert result['result'] == 'RECOVERY_REQUIRED',result
    assert fleet.nodes['RU'].barrier.stopped() and fleet.nodes['RU'].barrier.starts == 0
    assert fleet.nodes['NL'].barrier.stopped()
    assert fleet.nodes['NL2'].barrier.stopped()
    fleet.controller.nodes['NL2'] = original
    assert fleet.scheduled('reconnected')['result'] == 'COMMITTED'
    assert_committed(fleet,before)


def test_mismatched_secondary_receipt_cannot_commit(fleet):
    before = profiles(fleet)
    original = fleet.controller.nodes['NL2']
    class WrongReceipt:
        def call(self,action,*args):
            result = original.call(action,*args)
            return dict(result,plan_sha256='e'*64) if action == 'readback' else result
    fleet.controller.nodes['NL2'] = WrongReceipt()
    fleet.now += 12000
    result = fleet.scheduled()
    assert result['result'] == 'ABORTED' and result['first_cause'] == 'RU_NL_MISMATCH',result
    assert profiles(fleet) == before
    record = json.loads((fleet.controller.root/'transaction.json').read_bytes())
    assert record['commit_decided'] is False


def test_incomplete_directory_receipt_cannot_resume_ru(fleet):
    def interrupt(state):
        if state == 'DECISION_REPLICATED':
            raise KeyboardInterrupt()
    fleet.controller.fault = interrupt
    fleet.now += 12000
    with pytest.raises(KeyboardInterrupt):
        fleet.scheduled()
    operation = 'test-renewal-operation-first'
    primary = fleet.nodes['NL']
    primary.resume(operation)
    fleet.nodes['RU'].publish_directory(operation,dict(primary.public_directory(operation),gateway_slot='NL'))
    with pytest.raises(Rejected,match='DIRECTORY_RECONCILIATION_FAILED'):
        fleet.nodes['RU'].resume(operation)
    assert fleet.nodes['RU'].barrier.stopped() and fleet.nodes['RU'].barrier.starts == 0


@pytest.mark.parametrize('operation',['authority-request','authority-handoff','expired-request','expired-apply'])
def test_unsupported_authority_recovery_is_explicitly_fenced_without_writes(fleet,operation):
    before = inspected(fleet)
    with pytest.raises(Rejected,match='FLEET_AUTHORITY_HANDOFF_REQUIRED'):
        if operation == 'authority-request':
            fleet.nodes['RU'].authority_request('test-fleet-authority-request')
        elif operation == 'authority-handoff':
            fleet.controller.run('test-fleet-authority-request',authority_handoff=b'unsupported')
        elif operation == 'expired-request':
            fleet.controller.recovery_request('test-fleet-authority-request',[])
        else:
            fleet.controller.run_expired('test-fleet-authority-request',b'unsupported')
    assert inspected(fleet) == before
    assert not (fleet.controller.root/'transaction.json').exists()
    assert not (fleet.controller.root/'recovery-requests').exists()


@pytest.mark.parametrize('mode',['evaluate','scheduled'])
@pytest.mark.parametrize('defect',[None,'legacy_schema','missing_secondary','unknown_secondary'])
def test_runtime_opt_in_uses_one_coordinator_and_two_pinned_nl_routes(fleet,tmp_path,monkeypatch,capsys,mode,defect):
    import runtime_controller as runtime
    config = dict(schema=2,node_config='synthetic-node.json',coordinator_state=str(fleet.controller.root),
        nl_source_sha256='a'*64,ssh={'test_slot':'NL'},approved_leaf_crl_schedule=True,
        secondary=dict(source_sha256='b'*64,ssh={'test_slot':'NL2'}))
    if defect == 'legacy_schema':
        config['schema'] = 1
    elif defect == 'missing_secondary':
        del config['secondary']
    elif defect == 'unknown_secondary':
        config['secondary']['fallback'] = 'NL'
    path = tmp_path/'controller.json'
    atomic(path,canonical(config))
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
    monkeypatch.setattr(runtime.resource,'setrlimit',lambda *args: None)
    monkeypatch.setattr(runtime.os,'umask',lambda *args: None)
    monkeypatch.setattr(runtime.sys,'argv',['runtime_controller.py','--config',str(path),'--mode',mode,
        '--operation','test-fleet-runtime-controller'])
    before = inspected(fleet)
    if mode == 'scheduled':
        fleet.now += 12000
    if defect:
        with pytest.raises(SystemExit) as failure:
            runtime.main()
        assert failure.value.code == 1
        result = json.loads(capsys.readouterr().out)
        assert result['result'] == 'FAIL_CLOSED' and result['cause'] == 'CONTROLLER_CONFIG'
        assert inspected(fleet) == before
    else:
        runtime.main()
        result = json.loads(capsys.readouterr().out)
        assert result['result'] == ('NOOP' if mode == 'evaluate' else 'COMMITTED'),result
        assert routes == ['NL','NL2']
