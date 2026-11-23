"""Local operator grant and CRL publication; same Friends DB, no new identities."""
import argparse
import os
from pathlib import Path
import secrets
import base64
import hashlib
import hmac
import json
import re

from cryptography import x509
from cryptography.hazmat.primitives.serialization import Encoding

from .access import Access, SQLiteEnrollment
from .readiness_receipts import CLOCK_SKEW_SECONDS
from .restricted import MAX_TEST_LIFETIME, from_env, migrate, delegation, utc


MAX_INTEGER = 2**63 - 1
CRL_LIMIT = 2**53
CRL_PURPOSE = 'family-connect/ha-crl-synthetic/v1/db-only'


class CRLTransaction:
    def __init__(self, enrollment):
        self.enrollment = enrollment
        self.database = enrollment.database
        self.placeholder = enrollment.placeholder

    def exists(self, table):
        return self.database.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                                     (table,)).fetchone() is not None

    def sequence(self):
        if not self.exists('restricted_crl_sequence'):
            return 0
        rows = self.database.execute('SELECT singleton,sequence FROM restricted_crl_sequence').fetchall()
        if len(rows) != 1 or rows[0]['singleton'] != 1 or not 0 <= rows[0]['sequence'] < CRL_LIMIT:
            raise ValueError('invalid CRL sequence state')
        return rows[0]['sequence']

    def reserve(self, number):
        if type(number) is not int or not self.sequence() < number < CRL_LIMIT:
            raise ValueError('invalid CRL sequence advance')
        self.database.execute('CREATE TABLE IF NOT EXISTS restricted_crl_sequence '
            '(singleton INTEGER PRIMARY KEY CHECK(singleton=1), sequence INTEGER NOT NULL)')
        self.database.execute('INSERT INTO restricted_crl_sequence VALUES (1,' + self.placeholder +
            ') ON CONFLICT(singleton) DO UPDATE SET sequence=excluded.sequence', (number,))

    def certificates(self, now):
        return self.database.execute('SELECT * FROM restricted_certificates WHERE expires>' + self.placeholder +
                                     ' ORDER BY serial', (now,)).fetchall()

    def require_outbox(self):
        rows = self.database.execute('SELECT version,purpose FROM ha_crl_schema').fetchall()
        if [dict(row) for row in rows] != [dict(version=1, purpose=CRL_PURPOSE)]:
            raise RuntimeError('CRL rehearsal schema mismatch')

    def publication(self, operation_id):
        return self.database.execute('SELECT * FROM restricted_crl_publications WHERE operation_id=' +
                                     self.placeholder, (operation_id,)).fetchone()

    def latest(self):
        return self.database.execute('SELECT * FROM restricted_crl_publications ORDER BY sequence DESC LIMIT 1').fetchone()

    def record(self, operation_id, request_hash, raw, metadata):
        self.database.execute('INSERT INTO restricted_crl_publications'
            '(operation_id,request_sha256,sequence,payload,payload_sha256,issued_at,expires_at,local_receipt) VALUES (' +
            ','.join([self.placeholder] * 7) + ',0)', (operation_id, request_hash, metadata['generated_number'],
            raw.decode(), hashlib.sha256(raw).hexdigest(), metadata['this_update'], metadata['next_update']))

    def acknowledge(self, operation_id):
        self.database.execute('UPDATE restricted_crl_publications SET local_receipt=1 WHERE operation_id=' +
                              self.placeholder, (operation_id,))


def crl_transaction(database):
    return database if isinstance(database, CRLTransaction) else SQLiteEnrollment(database).crl()


def require_local_crl(access):
    if access.path is None:
        raise NotImplementedError('Legacy SQLite writers require fenced CRL file publication')
    with access.read_enrollment() as enrollment:
        transaction = enrollment.crl()
        if transaction.exists('ha_crl_schema') or transaction.exists('restricted_crl_publications'):
            raise NotImplementedError('CRL outbox requires fenced file publication')


class RestrictedAdminTransaction:
    def __init__(self, enrollment):
        self.database = enrollment.database
        self.placeholder = enrollment.placeholder

    def grant_row(self, device):
        return self.database.execute('SELECT * FROM restricted_grants WHERE device=' + self.placeholder,
                                     (device,)).fetchone()

    def grant(self, device, family, expires, minimum_revision, now):
        if (type(family) is not str or not family or type(expires) is not int
                or not 0 <= expires <= MAX_INTEGER or expires <= now
                or type(minimum_revision) is not int or not 1 <= minimum_revision <= MAX_INTEGER):
            raise ValueError('grant rejected')
        row = self.database.execute('SELECT d.revoked, i.revoked AS invite_revoked FROM devices d '
            'JOIN invites i ON d.device=i.device WHERE d.device=' + self.placeholder, (device,)).fetchone()
        if row is None or row['revoked'] or row['invite_revoked']:
            raise ValueError('grant rejected')
        old = self.grant_row(device)
        revision = max(old['revision'] + 1 if old else 1, minimum_revision)
        if revision > MAX_INTEGER:
            raise ValueError('grant revision exhausted')
        self.database.execute('INSERT INTO restricted_grants(device,family,revision,expires,revoked) VALUES (' +
            ','.join([self.placeholder] * 4) + ',0) ON CONFLICT(device) DO UPDATE SET '
            'family=excluded.family, revision=excluded.revision, expires=excluded.expires, revoked=0',
            (device, family, revision, expires))

    def revoke_grant(self, device):
        old = self.grant_row(device)
        if old is not None and not old['revoked'] and old['revision'] >= MAX_INTEGER:
            raise ValueError('grant revision exhausted')
        self.database.execute('UPDATE restricted_grants SET revoked=1,revision=revision+1 WHERE device=' +
                              self.placeholder + ' AND revoked=0', (device,))

    def begin_audit(self, timestamp, support, previous_state, new_state):
        if (type(timestamp) is not int or not 0 <= timestamp <= MAX_INTEGER
                or type(previous_state) is not int or previous_state not in (0, 1)
                or type(new_state) is not int or new_state not in (0, 1)
                or self.database.execute('SELECT 1 FROM device_support WHERE support_id=' + self.placeholder,
                                         (support,)).fetchone() is None):
            raise ValueError('audit rejected')
        statement = ('INSERT INTO field_support_audit(timestamp,support_id,previous_state,new_state,outcome) VALUES (' +
                     ','.join([self.placeholder] * 4) + ",'PENDING')")
        return self.insert_audit(statement, (timestamp, support, previous_state, new_state))

    def insert_audit(self, statement, values):
        return self.database.execute(statement, values).lastrowid

    def finish_audit(self, audit_id, outcome):
        if type(audit_id) is not int or not 1 <= audit_id <= MAX_INTEGER or outcome not in ('APPLIED', 'INCOMPLETE'):
            raise ValueError('audit completion rejected')
        allowed = "('PENDING','APPLIED')" if outcome == 'APPLIED' else "('PENDING','APPLIED','INCOMPLETE')"
        cursor = self.database.execute('UPDATE field_support_audit SET outcome=' + self.placeholder +
            ' WHERE id=' + self.placeholder + ' AND outcome IN ' + allowed, (outcome, audit_id))
        if cursor.rowcount != 1:
            raise ValueError('audit completion rejected')


def grant(access, device, family, expires, minimum_revision=1):
    with access.enrollment() as transaction:
        transaction.restricted_admin().grant(device, family, expires, minimum_revision, access.clock())


def build_crl_payload(service, database, previous_crl, previous_sequence, now, lifetime, *, receipt_key=None):
    database = crl_transaction(database)
    if type(lifetime) is not int or not 900 <= lifetime <= MAX_TEST_LIFETIME:
        raise ValueError('invalid CRL lifetime')
    if type(previous_sequence) is not int or not 0 <= previous_sequence < CRL_LIMIT - 1:
        raise ValueError('invalid CRL sequence')
    if receipt_key is not None and (type(receipt_key) is not bytes or len(receipt_key) != 32):
        raise ValueError('invalid receipt key')
    trust, authority = delegation(service.manifest, service.anchor, now)
    if service.signing_key.public_key().public_bytes_raw() != authority.public_key().public_bytes_raw():
        raise ValueError('CRL signing key mismatch')
    previous_number = 0
    issued = max(now - CLOCK_SKEW_SECONDS, trust['issued_at'], int(authority.not_valid_before_utc.timestamp()))
    if previous_crl is not None:
        previous = x509.load_pem_x509_crl(previous_crl)
        if (not previous.is_signature_valid(authority.public_key()) or previous.issuer != authority.subject
                or previous.last_update_utc > utc(now)):
            raise ValueError('CRL continuity rejected')
        previous_number = previous.extensions.get_extension_for_class(x509.CRLNumber).value.crl_number
        issued = max(issued, int(previous.last_update_utc.timestamp()))
    number = max(previous_number, previous_sequence) + 1
    expires = min(issued + lifetime, trust['expires_at'])
    if not 0 < number < CRL_LIMIT or expires <= now:
        raise ValueError('CRL sequence or validity exhausted')
    builder = (x509.CertificateRevocationListBuilder().issuer_name(authority.subject).last_update(utc(issued))
               .next_update(utc(expires)).add_extension(x509.CRLNumber(number), critical=False))
    serials = []
    rows = database.certificates(now)
    for certificate in rows:
        try:
            row = service._grant(database.enrollment.restricted(), certificate['device'], now)
            valid = row['revision'] == certificate['revision'] and row['family'] == trust['family'] and row['revision'] >= trust['minimum_revision']
        except ValueError:
            valid = False
        if not valid:
            serial = int(certificate['serial'])
            serials.append(serial)
            builder = builder.add_revoked_certificate(x509.RevokedCertificateBuilder()
                .serial_number(serial).revocation_date(utc(now)).build())
    raw = builder.sign(service.signing_key, None).public_bytes(Encoding.PEM)
    if len(raw) > 16384:
        raise ValueError('CRL payload exceeds reader bound')
    return raw, dict(previous_number=previous_number, generated_number=number, this_update=issued,
                     next_update=expires, revoked_serials=tuple(serials), safe_serial_tokens=tuple(
                         hmac.new(receipt_key, str(serial).encode(), hashlib.sha256).hexdigest()[:12]
                         for serial in serials) if receipt_key is not None else ())


def prepare_crl(service, operation_id, previous_crl, *, lifetime=900):
    if (type(operation_id) is not str or re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{7,95}', operation_id) is None
            or type(previous_crl) is not bytes or not 0 < len(previous_crl) <= 16384):
        raise ValueError('invalid CRL preparation')
    request = json.dumps(dict(previous=hashlib.sha256(previous_crl).hexdigest(), lifetime=lifetime,
        manifest=service.manifest, anchor=service.anchor.hex()), sort_keys=True, separators=(',', ':'), allow_nan=False)
    request_hash = hashlib.sha256(request.encode()).hexdigest()
    with service.access.enrollment() as enrollment:
        transaction = enrollment.crl()
        transaction.require_outbox()
        previous = transaction.publication(operation_id)
        if previous is not None:
            if previous['request_sha256'] != request_hash:
                raise ValueError('CRL operation conflict')
            return dict(previous)
        latest = transaction.latest()
        if (transaction.sequence() != (latest['sequence'] if latest else 0)
                or latest is not None and latest['payload'].encode() != previous_crl):
            raise ValueError('CRL predecessor mismatch')
        now = int(service.access.clock())
        raw, metadata = build_crl_payload(service, transaction, previous_crl, transaction.sequence(), now, lifetime)
        if not now <= int(service.access.clock()) < metadata['next_update']:
            raise ValueError('CRL preparation clock changed')
        transaction.reserve(metadata['generated_number'])
        transaction.record(operation_id, request_hash, raw, metadata)
        return dict(transaction.publication(operation_id))


def checked_crl_candidate(transaction, operation_id, now):
    transaction.require_outbox()
    record, latest = transaction.publication(operation_id), transaction.latest()
    if (record is None or latest is None or record['sequence'] != latest['sequence']
            or record['sequence'] != transaction.sequence() or not record['issued_at'] <= now < record['expires_at']
            or hashlib.sha256(record['payload'].encode()).hexdigest() != record['payload_sha256']):
        raise ValueError('CRL candidate is stale or inconsistent')
    return dict(record)


def pending_crl(access, operation_id):
    with access.read_enrollment() as enrollment:
        return checked_crl_candidate(enrollment.crl(), operation_id, int(access.clock()))


def acknowledge_crl(access, operation_id, payload_sha256):
    with access.enrollment() as enrollment:
        transaction = enrollment.crl()
        record = checked_crl_candidate(transaction, operation_id, int(access.clock()))
        if record['payload_sha256'] != payload_sha256:
            raise ValueError('CRL receipt mismatch')
        transaction.acknowledge(operation_id)
        return dict(transaction.publication(operation_id))


def publish_crl(service, path, *, lifetime=900):
    require_local_crl(service.access)
    with service.access.enrollment() as enrollment:
        database = enrollment.crl()
        if database.exists('ha_crl_schema') or database.exists('restricted_crl_publications'):
            raise NotImplementedError('CRL outbox requires fenced file publication')
        now = int(service.access.clock())
        try:
            previous = service.crl_source()
        except FileNotFoundError:
            previous = None
        raw, metadata = build_crl_payload(service, database, previous, database.sequence(), now, lifetime)
        number = metadata['generated_number']
        database.reserve(number)
        pending = path.with_name(path.name + '.' + secrets.token_hex(8))
        descriptor = os.open(pending, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        try:
            with os.fdopen(descriptor, 'wb') as output:
                output.write(raw)
                output.flush()
                os.fsync(output.fileno())
            os.replace(pending, path)
            folder = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(folder)
            finally:
                os.close(folder)
        finally:
            if pending.exists():
                pending.unlink()
    return number


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', type=Path, required=True)
    parser.add_argument('action', choices=['migrate', 'grant', 'revoke-device', 'publish-crl', 'gateway-certificate'])
    parser.add_argument('--device')
    parser.add_argument('--expires', type=int)
    parser.add_argument('--public-identity')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    access = Access(args.db)
    if args.action == 'migrate':
        migrate(access)
    elif args.action == 'revoke-device':
        access.revoke_device(args.device)
    else:
        service = from_env(access)
        if args.action in ('grant', 'gateway-certificate'):
            trust, _ = delegation(service.manifest, service.anchor, int(access.clock()))
            if args.expires is None or not int(access.clock()) < args.expires <= trust['expires_at']:
                raise ValueError('invalid grant expiry')
            if args.action == 'grant':
                grant(access, args.device, trust['family'], args.expires, trust['minimum_revision'])
            else:
                public = base64.b64decode(args.public_identity, validate=True)
                if len(public) != 64 or hashlib.sha256(public).hexdigest()[:32] != trust['gateway'] or args.output is None:
                    raise ValueError('gateway binding rejected')
                authority = x509.load_pem_x509_certificate(trust['authority'].encode())
                if service.signing_key.public_key().public_bytes_raw() != authority.public_key().public_bytes_raw():
                    raise ValueError('issuer rejected')
                certificate = service._issue(dict(public=args.public_identity, device=trust['gateway'], family=trust['family'],
                                                  revision=trust['minimum_revision']), authority, int(access.clock()), args.expires, 'gateway')
                descriptor = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
                with os.fdopen(descriptor, 'wb') as output:
                    output.write(certificate.public_bytes(Encoding.PEM))
                    output.flush()
                    os.fsync(output.fileno())
        else:
            publish_crl(service, Path(os.environ['FC_FRIENDS_RESTRICTED_DIR']) / 'revocations.pem')
    print('Restricted operator operation complete')


if __name__ == '__main__':
    main()
