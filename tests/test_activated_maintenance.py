import base64
import importlib.util
import json
import os
from pathlib import Path
import sys

import pytest
from cryptography import x509
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

from control.friends.restricted import DOMAIN, PROTOCOL, activated_grant, delegation, iso, utc
from device_identity.device import DeviceIdentity
from test_friends_restricted import configured, proof
from test_restricted_activation_policy import activate


MAINTENANCE = Path(__file__).resolve().parents[1] / 'deploy/friends/restricted/maintenance'
sys.path.insert(0, str(MAINTENANCE))
from credential_renewal import DAY, Rejected, Validator, atomic, canonical, digest, evaluate, parse
from expired_recovery import historical, sign as recovery_sign
from grant_cutover import GrantDatabase
from maintenance_policy import MaintenanceAuthorization
from node import dispatch
from production_controller import ProductionController
from production_node import ProductionNode


def pem_key(key):
    return key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()).decode()


class Barrier:
    def __init__(self, role, live, clock, family, gateway):
        self.role, self.live, self.clock = role, live, clock
        self.family, self.gateway = family, gateway
        self.quiet, self.starts = False, 0

    def stopped(self):
        return self.quiet

    def quiesce(self):
        self.quiet = True

    def resume(self, *, commit_decided, equality_verified):
        assert commit_decided and equality_verified
        if not self.quiet:
            return
        self.quiet = False
        self.starts += 1
        if self.role == 'NL':
            now = self.clock()
            atomic(self.live / 'directory.json', canonical(dict(version=1, family=self.family,
                issued_at=iso(now), expires_at=iso(now + 3599), seeds=[dict(transport='telemost-webrtc',
                join_url='https://telemost.yandex.ru/j/test-' + str(self.starts), gateway=self.gateway)])))


class Rpc:
    def __init__(self, node):
        self.node = node

    def call(self, action, operation_id, payload=None):
        return dispatch(self.node, dict(schema=1, role=self.node.role, action=action, operation_id=operation_id,
            expected_source_sha256='test-source', payload=payload))


class Cluster:
    def __init__(self, root, *, authority_days=90, grants=False):
        self.now = 1800000000
        self.clock = lambda: self.now
        self.service, self.device, _ = configured(root, self.now, delivery_lifetime=14400)
        self.service.all_activated = True
        self.service.access.clock = self.clock
        self.root_key = Ed25519PrivateKey.generate()
        self.service.anchor = self.root_key.public_key().public_bytes_raw()
        signer = self.service.signing_key
        name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'test-family')])
        issuer = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(signer.public_key())
            .serial_number(x509.random_serial_number()).not_valid_before(utc(self.now - 5))
            .not_valid_after(utc(self.now - 5 + authority_days * DAY))
            .add_extension(x509.BasicConstraints(ca=True, path_length=0), True)
            .add_extension(x509.KeyUsage(False, False, False, False, False, True, True, False, False), True)
            .add_extension(x509.SubjectKeyIdentifier.from_public_key(signer.public_key()), False).sign(signer, None))
        gateway_identity = DeviceIdentity.generate()
        gateway_public = base64.b64decode(gateway_identity.public_identity)
        gateway_key = Ed25519PrivateKey.from_private_bytes(gateway_identity._identity.get_private_key()[32:])
        self.family, self.gateway = 'a' * 32, gateway_identity.reference
        trust = dict(version=1, sequence=1, family=self.family, gateway=self.gateway,
            authority=issuer.public_bytes(Encoding.PEM).decode(), minimum_revision=1,
            issued_at=self.now - 5, expires_at=self.now - 5 + authority_days * DAY)
        payload = canonical(trust)
        self.service.manifest = dict(payload=base64.b64encode(payload).decode(),
            signature=base64.b64encode(self.root_key.sign(DOMAIN + payload)).decode())
        subject = x509.Name([x509.NameAttribute(NameOID.SERIAL_NUMBER, self.gateway)] +
            [x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, claim) for claim in
             ('protocol=' + PROTOCOL, 'family=' + self.family, 'role=gateway', 'revision=1')])
        leaf = (x509.CertificateBuilder().subject_name(subject).issuer_name(issuer.subject)
            .public_key(gateway_key.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(utc(self.now - 5)).not_valid_after(utc(self.now + 14395))
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), True)
            .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), False)
            .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(signer.public_key()), False)
            .add_extension(x509.SubjectAlternativeName([x509.UniformResourceIdentifier(
                'urn:family-connect:identity:' + gateway_public.hex())]), False).sign(signer, None))
        crl = (x509.CertificateRevocationListBuilder().issuer_name(issuer.subject)
            .last_update(utc(self.now - 5)).next_update(utc(self.now + 14395))
            .add_extension(x509.CRLNumber(1), False).sign(signer, None))
        seed = canonical(dict(version=1, family=self.family, issued_at=iso(self.now - 1),
            expires_at=iso(self.now + 3599), seeds=[dict(transport='telemost-webrtc',
            join_url='https://telemost.yandex.ru/j/test-initial', gateway=self.gateway)]))
        self.validator = Validator(self.service.anchor, delegation, all_activated=True)
        self.nodes = {}
        with self.service.access.db() as database:
            if not grants:
                database.execute('DELETE FROM restricted_grants')
            database.execute('CREATE TABLE restricted_crl_sequence (singleton INTEGER PRIMARY KEY CHECK(singleton=1), sequence INTEGER NOT NULL)')
            database.execute('INSERT INTO restricted_crl_sequence VALUES (1,1)')
        database_path = root / 'access.db'
        database_path.chmod(0o600)
        for role in ('RU', 'NL'):
            live, state = root / (role + '-live'), root / (role + '-state')
            live.mkdir(mode=0o700)
            state.mkdir(mode=0o700)
            atomic(live / 'directory.json', seed)
            database = None
            if role == 'RU':
                atomic(live / 'issuer.json', canonical(self.service.manifest))
                atomic(live / 'issuer.key', pem_key(signer).encode())
                atomic(live / 'revocations.pem', crl.public_bytes(Encoding.PEM))
                database = GrantDatabase(database_path, lambda connection, device, now:
                    activated_grant(connection, device, self.family, 1), all_activated=True,
                    family=self.family, minimum_revision=1)
            else:
                atomic(live / 'gateway.json', canonical(dict(authority=trust['authority'],
                    certificate=leaf.public_bytes(Encoding.PEM).decode(), revocations=crl.public_bytes(Encoding.PEM).decode(),
                    private_key=pem_key(gateway_key), family=self.family, gateway=self.gateway,
                    minimum_revision=1, minimum_crl=1)))
            barrier = Barrier(role, live, self.clock, self.family, self.gateway)
            self.nodes[role] = ProductionNode(role, live, state, self.validator, database=database,
                barrier=barrier, clock=self.clock, profile_uid=os.geteuid())
        coordinator = root / 'coordinator'
        coordinator.mkdir(mode=0o700)
        self.controller = ProductionController(coordinator, {role: Rpc(node) for role, node in self.nodes.items()},
            self.validator, clock=self.clock)
        self.service.crl_source = lambda: (self.nodes['RU'].live / 'revocations.pem').read_bytes()
        self.service.seed_source = lambda: (self.nodes['RU'].live / 'directory.json').read_bytes()

    def snapshot(self):
        return self.controller.read('test-snapshot-operation')[0]

    def scheduled(self, suffix='first'):
        return self.controller.run('test-renewal-operation-' + suffix, scheduled=True, approved_leaf_crl_schedule=True)


@pytest.fixture
def cluster(tmp_path):
    return Cluster(tmp_path)


@pytest.mark.parametrize('advance', [12000, 14400, 20000])
def test_automatic_renewal_including_missed_expiry(cluster, advance):
    before = cluster.snapshot()
    cluster.now += advance
    if advance >= 14395:
        with pytest.raises(Rejected):
            cluster.validator.validate(canonical(before), cluster.now)
    decision = evaluate(cluster.validator.validate(canonical(before), cluster.now, expired_leaf_predecessor=True),
                        cluster.now, all_activated=True)
    assert decision['due'] == ['crl', 'leaf']
    assert 'grant' not in decision['headroom']
    result = cluster.scheduled()
    assert result['result'] == 'COMMITTED', result
    assert cluster.snapshot()['grants'] == []
    assert cluster.validator.validate(canonical(cluster.snapshot()), cluster.now)
    assert all(not node.barrier.stopped() for node in cluster.nodes.values())
    newcomer = activate(cluster.service)
    assert cluster.service.fetch(proof(cluster.service, newcomer))['device'] == newcomer.reference


def test_new_activation_after_checkpoint_and_four_hours(cluster):
    cluster.now += 12000
    assert cluster.scheduled()['result'] == 'COMMITTED'
    newcomer = activate(cluster.service)
    cluster.service.fetch(proof(cluster.service, newcomer))
    cluster.now += 15000
    assert cluster.scheduled('second')['result'] == 'COMMITTED'
    assert cluster.service.fetch(proof(cluster.service, newcomer))['device'] == newcomer.reference
    assert cluster.snapshot()['grants'] == []


@pytest.mark.parametrize('table', ['devices', 'invites'])
def test_automatic_revocation_without_legacy_grant(cluster, table):
    response = cluster.service.fetch(proof(cluster.service, cluster.device))
    serial = x509.load_pem_x509_certificate(response['certificate'].encode()).serial_number
    with cluster.service.access.db() as database:
        database.execute('UPDATE ' + table + ' SET revoked=1 WHERE device=?', (cluster.device.reference,))
    result = cluster.scheduled()
    assert result['result'] == 'COMMITTED', result
    crl = x509.load_pem_x509_crl(cluster.service.crl_source())
    assert crl.get_revoked_certificate_by_serial_number(serial) is not None
    with pytest.raises(ValueError):
        cluster.service.challenge(cluster.device.public_identity, cluster.device.wireguard_public_key)


def test_expired_legacy_entitlement_is_not_renewed(tmp_path):
    cluster = Cluster(tmp_path, grants=True)
    with cluster.service.access.db() as database:
        database.execute('UPDATE restricted_grants SET expires=?', (cluster.now - 1,))
    before = cluster.snapshot()['grants']
    cluster.now += 12000
    assert cluster.scheduled()['result'] == 'COMMITTED'
    assert cluster.snapshot()['grants'] == before
    assert cluster.service.fetch(proof(cluster.service, cluster.device))['device'] == cluster.device.reference


def test_mixed_policy_nodes_rejected_before_mutation(cluster):
    cluster.nodes['NL'].validator = Validator(cluster.service.anchor, delegation)
    with pytest.raises(Rejected, match='ADMISSION_MODE_MISMATCH'):
        cluster.scheduled()
    assert all(node.barrier.starts == 0 and not node.barrier.stopped() for node in cluster.nodes.values())


def test_expired_recovery_with_empty_grants_and_new_activations(cluster):
    cluster.now += 12000
    assert cluster.scheduled()['result'] == 'COMMITTED'
    newcomer = activate(cluster.service)
    cluster.service.fetch(proof(cluster.service, newcomer))
    cluster.now += 90 * DAY
    operation = 'test-offline-expired-recovery'
    request = cluster.controller.recovery_request(operation, [])
    bundle = recovery_sign(request, cluster.validator, cluster.root_key, cluster.now)
    current = {role: node.inspect() for role, node in cluster.nodes.items()}
    approval = MaintenanceAuthorization(operation, digest(canonical(current)), cluster.now, cluster.now + 900)
    result = cluster.controller.run_expired(operation, bundle, approval=approval)
    assert result['result'] == 'COMMITTED', result
    cluster.service.manifest = json.loads((cluster.nodes['RU'].live / 'issuer.json').read_bytes())
    assert cluster.service.fetch(proof(cluster.service, newcomer))['device'] == newcomer.reference
    assert cluster.snapshot()['grants'] == []


@pytest.mark.parametrize('role,stage', [('RU', 'stage-revocations.pem'), ('NL', 'stage-gateway.json'),
                                     ('RU', 'after-rename-revocations.pem'), ('NL', 'after-rename-gateway.json')])
def test_failure_before_commit_never_resumes_mixed_material(cluster, role, stage):
    before = cluster.snapshot()
    cluster.now += 12000
    def fail(current):
        if current == stage:
            cluster.nodes[role].fault = lambda ignored: None
            raise OSError('injected')
    cluster.nodes[role].fault = fail
    result = cluster.scheduled()
    assert result['result'] in ('ABORTED', 'RECOVERY_REQUIRED'), result
    assert cluster.snapshot() == before
    if result['result'] == 'RECOVERY_REQUIRED':
        assert all(node.barrier.stopped() for node in cluster.nodes.values())


@pytest.mark.parametrize('field', ['authority', 'crl', 'certificate'])
def test_bad_signatures_and_future_material_fail_closed(cluster, field):
    snapshot = cluster.snapshot()
    if field == 'authority':
        snapshot[field]['signature'] = base64.b64encode(bytes(64)).decode()
    else:
        snapshot[field] = snapshot[field].replace('\n', '\nA', 1)
    with pytest.raises(Rejected):
        cluster.validator.validate(canonical(snapshot), cluster.now, expired_leaf_predecessor=True)
    with pytest.raises(Rejected):
        cluster.validator.validate(canonical(cluster.snapshot()), cluster.now - 3600, expired_leaf_predecessor=True)


def test_ninety_day_authority_requires_explicit_mode(cluster):
    snapshot = cluster.snapshot()
    assert historical(canonical(snapshot), cluster.service.anchor, all_activated=True)
    with pytest.raises(Rejected):
        historical(canonical(snapshot), cluster.service.anchor)
    with pytest.raises(Rejected, match='AUTHORITY_VALIDITY'):
        Validator(cluster.service.anchor, delegation).validate(canonical(snapshot), cluster.now)


def test_offline_same_key_migration_from_daily_authority(tmp_path):
    cluster = Cluster(tmp_path, authority_days=1, grants=True)
    cluster.now += 20 * 3600
    operation = 'test-offline-authority-migration'
    request = cluster.nodes['RU'].authority_request(operation)
    specification = importlib.util.spec_from_file_location('bridge_offline_signer',
        MAINTENANCE.parent / 'offline/sign_authority.py')
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    bundle = module.sign(request, cluster.service.anchor, cluster.root_key.private_bytes_raw(),
                         cluster.validator, cluster.now)
    current = {role: node.inspect() for role, node in cluster.nodes.items()}
    approval = MaintenanceAuthorization(operation, digest(canonical(current)), cluster.now, cluster.now + 900)
    result = cluster.controller.run(operation, approval=approval, authority_handoff=bundle)
    assert result['result'] == 'COMMITTED', result
    trust, _ = delegation(cluster.snapshot()['authority'], cluster.service.anchor, cluster.now)
    assert trust['expires_at'] - trust['issued_at'] == 90 * DAY
    assert cluster.snapshot()['grants'][0]['revision'] == 1


@pytest.mark.parametrize('stage', ['RU_PROMOTED', 'NL_PROMOTED', 'COMMIT_DECIDED', 'NL_RESUMED', 'RU_RESUMED'])
def test_interrupted_controller_reconciles_before_resume(cluster, stage):
    cluster.now += 12000
    def interrupt(current):
        if current == stage:
            raise KeyboardInterrupt()
    cluster.controller.fault = interrupt
    with pytest.raises(KeyboardInterrupt):
        cluster.scheduled()
    cluster.controller.fault = lambda ignored: None
    result = cluster.scheduled('resume')
    expected = 'COMMITTED' if stage in ('COMMIT_DECIDED', 'NL_RESUMED', 'RU_RESUMED') else 'ABORTED'
    assert result['result'] == expected, result
    cluster.validator.validate(canonical(cluster.snapshot()), cluster.now)
    assert all(not node.barrier.stopped() for node in cluster.nodes.values())
