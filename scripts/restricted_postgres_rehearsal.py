"""Disposable issuer/receipt DB rehearsal with ephemeral synthetic authority only."""
import argparse
import base64
from copy import copy
import json
from pathlib import Path
import signal

from cryptography import x509
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.x509.oid import NameOID

from control.friends import readiness_receipts, support_ids
from control.friends.access import Access
from control.friends.paid_postgres import initialize_synthetic_paid
from control.friends.restricted import DOMAIN, RestrictedReadiness, iso, utc
from control.friends.restricted_admin import grant
from control.friends.restricted_admin_postgres import initialize_synthetic_restricted_admin
from control.friends.restricted_postgres import initialize_synthetic_restricted
from control.friends.support_postgres import initialize_synthetic_support
from device_identity.device import DeviceIdentity
from scripts.control_ha_rehearsal import private_file, require
from scripts.enrollment_postgres_rehearsal import Rehearsal
from scripts.paid_postgres_rehearsal import PaidRehearsal, apply, snapshot, require_current_restore
from scripts.referral_postgres_rehearsal import NOW, proof, refused


def initialize(repository):
    initialize_synthetic_restricted_admin(repository)
    initialize_synthetic_paid(repository)
    initialize_synthetic_support(repository)
    initialize_synthetic_restricted(repository)


def synthetic_service(access):
    device = DeviceIdentity.generate()
    access.complete(proof(access, device, 'activate', access.invite()), 'activate')
    signer, root = Ed25519PrivateKey.generate(), Ed25519PrivateKey.generate()
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'HA synthetic issuer')])
    authority = (x509.CertificateBuilder().subject_name(subject).issuer_name(subject).public_key(signer.public_key())
        .serial_number(1).not_valid_before(utc(NOW - 10)).not_valid_after(utc(NOW + 86400))
        .add_extension(x509.BasicConstraints(ca=True, path_length=0), True)
        .add_extension(x509.KeyUsage(False, False, False, False, False, True, True, False, False), True)
        .add_extension(x509.SubjectKeyIdentifier.from_public_key(signer.public_key()), False).sign(signer, None))
    payload = json.dumps(dict(version=1, sequence=1, family='a' * 32, gateway='b' * 32,
        authority=authority.public_bytes(Encoding.PEM).decode(), minimum_revision=1, issued_at=NOW - 10, expires_at=NOW + 86400)).encode()
    manifest = dict(payload=base64.b64encode(payload).decode(), signature=base64.b64encode(root.sign(DOMAIN + payload)).decode())
    crl = (x509.CertificateRevocationListBuilder().issuer_name(subject).last_update(utc(NOW - 1)).next_update(utc(NOW + 3599))
           .add_extension(x509.CRLNumber(1), False).sign(signer, None).public_bytes(Encoding.PEM))
    directory = json.dumps(dict(version=1, family='a' * 32, issued_at=iso(NOW - 1), expires_at=iso(NOW + 3599),
        seeds=[dict(transport='telemost-webrtc', join_url='https://telemost.yandex.ru/j/test-only', gateway='b' * 32)])).encode()
    grant(access, device.reference, 'a' * 32, NOW + 86400)
    return RestrictedReadiness(access, manifest=manifest, anchor=root.public_key().public_bytes_raw(), signing_key=signer,
                              seed_source=lambda: directory, crl_source=lambda: crl), device


def issue_proof(service, device, correlation=None):
    value = service.challenge(device.public_identity, device.wireguard_public_key, request_id=correlation)
    return device.prove_transport_key(value['challenge'])


def receipt(response, correlation='a' * 32, fetch_id='b' * 32):
    return dict(version=1, type='READINESS_IMPORT_RESULT', correlation_id=correlation, challenge_id=correlation,
        fetch_id=fetch_id, result='READY', provisioning='PRESENT_VALID', bootstrap='PRESENT_VALID', orchestrator_usable=True,
        revision=response['revision'], minimum_crl=response['minimum_crl'], expires_at=response['expires_at'],
        observed_at=NOW, phase='import', app_version='0.1.18-beta126', version_code=126, failure_reason='NONE')


def ack_proof(service, device, payload):
    value = readiness_receipts.ack_challenge(service, dict(public_identity=device.public_identity,
        wireguard_public_key=device.wireguard_public_key, receipt=payload))
    return device.prove_transport_key(value['challenge'])


class RestrictedRehearsal(PaidRehearsal):
    CONTRACT_FILES = ('tests/test_enrollment_repository.py', 'tests/test_restricted_repository.py')

    def restricted_recovery(self):
        repository = self.repository()
        repository.initialize_synthetic()
        initialize(repository)
        access = Access(None, clock=lambda: NOW, enrollment_repository=repository)
        service, device = synthetic_service(access)
        support = support_ids.request(access, dict(proof=proof(access, device, 'support'), platform='android',
            app_version='0.1.18-beta126', version_code=126))['device_support_id']
        with repository.transaction() as transaction:
            apply(transaction.paid(), support, paid_until=NOW + 600)
            audit = transaction.restricted_admin().begin_audit(NOW, support, 0, 1)
            transaction.restricted_admin().finish_audit(audit, 'APPLIED')
        other = DeviceIdentity.generate()
        access.complete(proof(access, other, 'activate', access.invite()), 'activate')
        grant(access, other.reference, 'a' * 32, NOW + 3600)
        old_backup = self.dump(repository, 'before-issuance.dump')
        consumed = issue_proof(service, device, 'a' * 32)
        response = service.fetch(consumed, request_id='b' * 32)
        payload = receipt(response)
        consumed_ack = dict(proof=ack_proof(service, device, payload), receipt=payload)
        readiness_receipts.acknowledge(service, consumed_ack)
        pending = issue_proof(service, device, 'c' * 32)
        second = service.fetch(issue_proof(service, device, 'e' * 32), request_id='f' * 32)
        pending_payload = receipt(second, 'e' * 32, 'f' * 32)
        pending_ack = dict(proof=ack_proof(service, device, pending_payload), receipt=pending_payload)
        denied = issue_proof(service, other)
        service.fetch(issue_proof(service, other))
        with repository.transaction() as transaction:
            transaction.restricted_admin().revoke_grant(other.reference)
        access.revoke_device(other.reference)
        committed = snapshot(repository)
        unfinished = repository.connect()
        try:
            repository.configure(unfinished)
            unfinished.execute('DELETE FROM restricted_certificates')
            unfinished.execute('UPDATE restricted_readiness_results SET ack=NULL,ack_at=NULL')
            unfinished.execute('UPDATE challenges SET used=1 WHERE used=0')
            require(self.owned(), 'REHEARSAL_CONTAINER_MISSING')
            self.docker('kill', '--signal', 'KILL', self.container)
        finally:
            unfinished.close()
        self.docker('start', self.container)
        self.refresh_port()
        repository.port = self.port
        self.wait_ready()
        require_current_restore(committed, snapshot(repository))
        backup = self.dump(repository, 'current-issuance.dump')
        with Rehearsal(self.root / 'stale-restore') as target:
            stale = self.restore(target, repository, old_backup)
            try:
                require_current_restore(committed, snapshot(stale))
            except ValueError as error:
                require(str(error) == 'RESTORE_WOULD_LOSE_OR_CHANGE_ACKNOWLEDGED_STATE', 'UNEXPECTED_RESTORE_ERROR')
            else:
                raise RuntimeError('Stale issuance restore accepted')
        with Rehearsal(self.root / 'current-restore') as target:
            restored = self.restore(target, repository, backup)
            require_current_restore(committed, snapshot(restored))
            recovered = copy(service)
            recovered.access = Access(None, clock=lambda: NOW, enrollment_repository=restored)
            refused(lambda: recovered.fetch(consumed))
            refused(lambda: recovered.fetch(denied))
            refused(lambda: readiness_receipts.acknowledge(recovered, consumed_ack))
            require(readiness_receipts.readback(recovered, 'a' * 32, device.reference)['receipt'] == payload, 'ACK_LOST')
            with restored.transaction() as transaction:
                require(apply(transaction.paid(), support, paid_until=NOW + 600)['duplicate'], 'PAYMENT_REPLAYED')
            require_current_restore(committed, snapshot(restored))
            refreshed = recovered.fetch(pending, request_id='d' * 32)
            require(refreshed['certificate'] == response['certificate'], 'CERTIFICATE_REISSUED')
            require(refreshed['expires_at'] <= NOW + 600, 'PAID_BOUND_EXTENDED')
            refused(lambda: recovered.fetch(pending))
            readiness_receipts.acknowledge(recovered, pending_ack)
            refused(lambda: readiness_receipts.acknowledge(recovered, pending_ack))
            require(readiness_receipts.readback(recovered, 'e' * 32, device.reference)['receipt'] == pending_payload, 'PENDING_ACK_LOST')
        return {table: len(records) for table, records in committed.items()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workdir', required=True, type=Path)
    args = parser.parse_args()
    with RestrictedRehearsal(args.workdir) as rehearsal:
        tests = rehearsal.contracts()
        restored = rehearsal.restricted_recovery()
        result = dict(schema=1, result='ISOLATED_RESTRICTED_POSTGRES_PASS', contracts=tests,
            postgres=rehearsal.manifest['version'], synthetic_only=True, crash_recovery='PASS',
            current_restore='EXACT_ALL_LAB_TABLES', stale_restore='REFUSED', restored_rows=restored,
            consumed_proofs='REFUSED', pending_fetch_and_ack='CONSUMED_ONCE', certificate_reuse='PASS',
            paid_bound='PRESERVED', production_writes=0, authority_keys='EPHEMERAL_RETAINED_NOT_RESTORED',
            field_crl_publication='NOT_MIGRATED', replication='NOT_IMPLEMENTED', reverse_migration='NOT_IMPLEMENTED')
    result['owned_container_cleanup'] = 'PASS'
    private_file(args.workdir / 'receipt.json', json.dumps(result, indent=2).encode())
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    def terminate(signum, frame):
        raise SystemExit(128 + signum)

    signal.signal(signal.SIGTERM, terminate)
    main()
