"""Bounded Friends issuance; existing identity, offline-root delegated Family issuer."""
import base64
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import re
import secrets
import os
import stat
import time
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

from device_identity.device import verify_transport_key_proof
from provisioning.friends_catalog import fields, key, parse, require
from .access import Rejected, CHALLENGE_TTL

DOMAIN = b'family-connect/restricted-issuer/v1\0'
PROTOCOL = 'family-connect-5n3-test-v1'
MAX_RESPONSE = 65536


def bounded_file(path, limit, private=False):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as source:
        info = os.fstat(source.fileno())
        require(stat.S_ISREG(info.st_mode) and not stat.S_IMODE(info.st_mode) & 0o022)
        require(not private or stat.S_IMODE(info.st_mode) == 0o600)
        raw = source.read(limit + 1)
    require(0 < len(raw) <= limit)
    return raw


def from_env(access):
    root = Path(os.environ['FC_FRIENDS_RESTRICTED_DIR'])
    require(root.is_absolute())
    anchor = base64.b64decode(bounded_file(root / 'anchor.pub', 128).strip(), validate=True)
    require(len(anchor) == 32)
    policy = parse(bounded_file(root / 'admission.json', 16384))
    fields(policy, 'devices')
    require(type(policy['devices']) is list and len(policy['devices']) <= 256)
    require(all(type(device) is str and (device == '*' or re.fullmatch('[0-9a-f]{32}', device)) for device in policy['devices']))
    return RestrictedReadiness(access, manifest=parse(bounded_file(root / 'issuer.json', 16384)),
                              anchor=anchor, signing_key=load_pem_private_key(bounded_file(root / 'issuer.key', 4096, True), None),
                              seed_source=lambda: bounded_file(root / 'directory.json', 8192),
                              crl_source=lambda: bounded_file(root / 'revocations.pem', 16384), eligible_devices=policy['devices'])


def request(access, action, value):
    try:
        service = from_env(access)
        if action == 'challenge':
            fields(value, 'public_identity wireguard_public_key')
            return service.challenge(**value)
        require(action == 'fetch')
        return service.fetch(value)
    except Rejected:
        raise
    except Exception:
        raise RuntimeError('restricted readiness unavailable') from None


def timestamp(value):
    return timestamp_ns(value) // 1_000_000_000


def timestamp_ns(value):
    require(type(value) is str)
    match = re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]'
                         r'(?:\.([0-9]{1,9}))?(?:Z|[+-](?:[01][0-9]|2[0-3]):[0-5][0-9])', value)
    require(match is not None)
    instant = datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone(timezone.utc)
    seconds = int(instant.replace(microsecond=0).timestamp())
    return seconds * 1_000_000_000 + int((match.group(1) or '').ljust(9, '0'))


def utc(value):
    return datetime.fromtimestamp(value, timezone.utc)


def iso(value):
    return utc(value).isoformat().replace('+00:00', 'Z')


def delegation(envelope, anchor, now):
    fields(envelope, 'payload signature')
    payload = base64.b64decode(envelope['payload'], validate=True)
    require(len(payload) <= 8192)
    Ed25519PublicKey.from_public_bytes(anchor).verify(key(envelope['signature'], 64), DOMAIN + payload)
    value = parse(payload)
    fields(value, 'version sequence family gateway authority minimum_revision issued_at expires_at')
    require(type(value['version']) is int and value['version'] == 1)
    require(type(value['sequence']) is int and 0 < value['sequence'] < 2**53)
    require(type(value['minimum_revision']) is int and 0 < value['minimum_revision'] < 2**31)
    require(all(type(value[name]) is str and re.fullmatch('[0-9a-f]{32}', value[name]) for name in ('family', 'gateway')))
    require(type(value['issued_at']) is int and type(value['expires_at']) is int)
    require(value['issued_at'] <= now < value['expires_at'])
    authority = x509.load_pem_x509_certificate(value['authority'].encode())
    require(value['authority'] == authority.public_bytes(Encoding.PEM).decode())
    require(isinstance(authority.public_key(), Ed25519PublicKey))
    authority.verify_directly_issued_by(authority)
    require(authority.extensions.get_extension_for_class(x509.BasicConstraints).value.ca)
    usage = authority.extensions.get_extension_for_class(x509.KeyUsage).value
    require(usage.key_cert_sign and usage.crl_sign)
    require(authority.not_valid_before_utc <= utc(now) < authority.not_valid_after_utc)
    require(value['expires_at'] <= int(authority.not_valid_after_utc.timestamp()))
    return value, authority


class DirectoryValidationError(ValueError):
    def __init__(self, stage, predicate, field):
        self.stage, self.predicate, self.field = stage, predicate, field
        super().__init__(f'directory_validation_failed: stage={stage} predicate={predicate} field={field}')


def directory_require(ok, stage, predicate, field):
    if not ok:
        raise DirectoryValidationError(stage, predicate, field)


def clock_nanoseconds(clock):
    if clock is time.time:
        return time.time_ns()
    return int(Decimal(str(clock())) * 1_000_000_000)


def directory(raw, family, gateway, now=None, *, now_ns=None):
    directory_require(type(raw) is bytes and 0 < len(raw) <= 8192, 'parse', 'invalid_size', 'directory')
    try:
        value = parse(raw)
    except (ValueError, UnicodeError, RecursionError):
        raise DirectoryValidationError('parse', 'invalid_json', 'directory') from None
    directory_require(type(value) is dict and set(value) == {'version', 'family', 'issued_at', 'expires_at', 'seeds'},
                      'structure', 'invalid_fields', 'directory')
    directory_require(type(value['version']) is int and value['version'] == 1, 'structure', 'invalid_version', 'version')
    directory_require(value['family'] == family, 'binding', 'invalid_family_binding', 'family')
    instants = {}
    for field in ('issued_at', 'expires_at'):
        try:
            instants[field] = timestamp_ns(value[field])
        except (ValueError, TypeError, OverflowError):
            raise DirectoryValidationError('parse', 'invalid_timestamp', field) from None
    directory_require(now is None or (type(now) is int and now_ns is None), 'clock', 'invalid_clock', 'now')
    if now_ns is None:
        now_ns = time.time_ns() if now is None else now * 1_000_000_000
    directory_require(type(now_ns) is int, 'clock', 'invalid_clock', 'now')
    issued, expires = instants['issued_at'], instants['expires_at']
    directory_require(issued <= now_ns, 'time', 'issued_in_future', 'issued_at')
    directory_require(now_ns < expires, 'time', 'expired', 'expires_at')
    directory_require(0 < expires - issued <= 3600 * 1_000_000_000, 'time', 'invalid_lifetime', 'expires_at')
    directory_require(type(value['seeds']) is list and 1 <= len(value['seeds']) <= 4,
                      'structure', 'invalid_seed_count', 'seeds')
    seen = set()
    for seed in value['seeds']:
        directory_require(type(seed) is dict and set(seed) == {'transport', 'join_url', 'gateway'},
                          'structure', 'invalid_seed_fields', 'seeds')
        directory_require(seed['transport'] == 'telemost-webrtc', 'seed', 'invalid_transport', 'seeds.transport')
        directory_require(seed['gateway'] == gateway, 'binding', 'invalid_gateway_binding', 'seeds.gateway')
        directory_require(type(seed['join_url']) is str and re.fullmatch(r'https://telemost\.yandex\.ru/j/[A-Za-z0-9_-]{1,128}', seed['join_url']),
                          'seed', 'invalid_join_url', 'seeds.join_url')
        directory_require(seed['join_url'] not in seen, 'seed', 'duplicate_seed', 'seeds.join_url')
        seen.add(seed['join_url'])
    for field, instant in (('issued_at', issued), ('expires_at', expires)):
        seconds, nanos = divmod(instant, 1_000_000_000)
        fraction = f'.{nanos:09d}'.rstrip('0') if nanos else ''
        value[field] = iso(seconds)[:-1] + fraction + 'Z'
    return value


def migrate(access):
    require(access.path.is_file())
    with access.db() as database:
        existing = {row[0] for row in database.execute('SELECT name FROM sqlite_master WHERE type="table"')}
        require({'devices', 'invites', 'challenges'} <= existing)
        database.execute('CREATE TABLE IF NOT EXISTS restricted_grants ('
                         'device TEXT PRIMARY KEY REFERENCES devices(device), family TEXT NOT NULL, '
                         'revision INTEGER NOT NULL, expires INTEGER, revoked INTEGER NOT NULL DEFAULT 0)')
        database.execute('CREATE TABLE IF NOT EXISTS restricted_challenges ('
                         'nonce TEXT PRIMARY KEY, revision INTEGER NOT NULL, family TEXT NOT NULL, '
                         'expires INTEGER NOT NULL)')
        database.execute('CREATE TABLE IF NOT EXISTS restricted_certificates ('
                         'device TEXT NOT NULL, revision INTEGER NOT NULL, serial TEXT PRIMARY KEY, '
                         'expires INTEGER NOT NULL, certificate TEXT NOT NULL)')


class RestrictedReadiness:
    def __init__(self, access, *, manifest, anchor, signing_key, seed_source, crl_source, eligible_devices=None):
        self.access, self.manifest, self.anchor = access, manifest, anchor
        self.signing_key, self.seed_source, self.crl_source = signing_key, seed_source, crl_source
        self.eligible_devices = None if eligible_devices is None else frozenset(eligible_devices)

    def _enroll(self, database, device, public, wg, trust, now):
        if database.execute('SELECT 1 FROM restricted_grants WHERE device=?', (device,)).fetchone():
            return
        if self.eligible_devices is None or (device not in self.eligible_devices and '*' not in self.eligible_devices):
            raise Rejected()
        row = database.execute('SELECT d.*, i.revoked AS invite_revoked FROM devices d '
                               'JOIN invites i ON d.device=i.device WHERE d.device=?', (device,)).fetchone()
        if row is None or row['revoked'] or row['invite_revoked'] or row['public'] != public or row['wg'] != wg:
            raise Rejected()
        database.execute('INSERT INTO restricted_grants VALUES (?,?,?,?,0)', (device, trust['family'], trust['minimum_revision'], None))

    def _trust(self, now):
        trust, authority = delegation(self.manifest, self.anchor, now)
        require(isinstance(self.signing_key, Ed25519PrivateKey))
        require(self.signing_key.public_key().public_bytes_raw() == authority.public_key().public_bytes_raw())
        raw = self.crl_source()
        require(type(raw) is bytes and 0 < len(raw) <= 16384)
        crl = x509.load_pem_x509_crl(raw)
        require(raw == crl.public_bytes(Encoding.PEM))
        require(crl.is_signature_valid(authority.public_key()))
        require(crl.issuer == authority.subject)
        require(crl.last_update_utc <= utc(now) < crl.next_update_utc)
        require((crl.next_update_utc - crl.last_update_utc).total_seconds() <= 3600)
        number = crl.extensions.get_extension_for_class(x509.CRLNumber).value.crl_number
        require(0 < number < 2**53)
        return trust, authority, crl, raw.decode(), number

    def _grant(self, database, device, now):
        if self.eligible_devices is not None and device not in self.eligible_devices and '*' not in self.eligible_devices:
            raise Rejected()
        row = database.execute('SELECT d.*, g.family, g.revision, g.expires, g.revoked AS grant_revoked '
                               'FROM devices d JOIN restricted_grants g ON d.device=g.device '
                               'WHERE d.device=?', (device,)).fetchone()
        invite = database.execute('SELECT revoked FROM invites WHERE device=?', (device,)).fetchone()
        if row is None or row['revoked'] or row['grant_revoked'] or (row['expires'] is not None and row['expires'] <= now) or invite is None or invite['revoked']:
            raise Rejected()
        return row

    def challenge(self, public_identity, wireguard_public_key):
        device = self.access.binding(public_identity, wireguard_public_key)
        now = int(self.access.clock())
        trust, _, _, _, _ = self._trust(now)
        with self.access.db() as database:
            self._enroll(database, device, public_identity, wireguard_public_key, trust, now)
            row = self._grant(database, device, now)
            if row['family'] != trust['family'] or row['revision'] < trust['minimum_revision'] or row['public'] != public_identity or row['wg'] != wireguard_public_key:
                raise Rejected()
            database.execute('DELETE FROM restricted_challenges WHERE expires<=?', (now,))
            database.execute('DELETE FROM challenges WHERE expires<=?', (now,))
            if database.execute('SELECT COUNT(*) FROM challenges WHERE device=? AND used=0', (device,)).fetchone()[0] >= 8:
                raise RuntimeError('restricted readiness busy')
            nonce = base64.b64encode(secrets.token_bytes(32)).decode()
            digest = hashlib.sha256(nonce.encode()).hexdigest()
            expiry = min(now + CHALLENGE_TTL, row['expires'] if row['expires'] is not None else trust['expires_at'], trust['expires_at'])
            database.execute('INSERT INTO challenges VALUES (?,?,?,?,?,?,?,0)',
                             (digest, device, public_identity, wireguard_public_key, 'restricted', None, expiry))
            database.execute('INSERT INTO restricted_challenges VALUES (?,?,?,?)',
                             (digest, row['revision'], row['family'], expiry))
        return dict(challenge=nonce, expires_at=expiry, audience='family-connect/enrollment/v1')

    def fetch(self, proof):
        device = verify_transport_key_proof(proof, expected_challenge=proof['challenge'])
        digest = hashlib.sha256(proof['challenge'].encode()).hexdigest()
        now = int(self.access.clock())
        trust, authority, crl, crl_pem, crl_number = self._trust(now)
        seeds = directory(self.seed_source(), trust['family'], trust['gateway'], now_ns=clock_nanoseconds(self.access.clock))
        with self.access.db() as database:
            now = int(self.access.clock())
            require(trust['issued_at'] <= now < trust['expires_at'] and crl.last_update_utc <= utc(now) < crl.next_update_utc)
            directory(json.dumps(seeds).encode(), trust['family'], trust['gateway'], now_ns=clock_nanoseconds(self.access.clock))
            row = self._grant(database, device, now)
            challenge = database.execute('SELECT c.*, r.revision, r.family FROM challenges c '
                                         'JOIN restricted_challenges r ON c.nonce=r.nonce WHERE c.nonce=?', (digest,)).fetchone()
            if (challenge is None or challenge['used'] or challenge['expires'] <= now or challenge['purpose'] != 'restricted'
                    or challenge['device'] != device or challenge['public'] != proof['public_identity']
                    or challenge['wg'] != proof['wireguard_public_key'] or row['public'] != proof['public_identity']
                    or row['wg'] != proof['wireguard_public_key'] or row['family'] != trust['family']
                    or row['revision'] < trust['minimum_revision']
                    or challenge['family'] != row['family'] or challenge['revision'] != row['revision']):
                raise Rejected()
            expires = min(now + 3600, row['expires'] if row['expires'] is not None else trust['expires_at'], trust['expires_at'], int(crl.next_update_utc.timestamp()))
            database.execute('DELETE FROM restricted_certificates WHERE expires<=?', (now,))
            current = database.execute('SELECT serial FROM restricted_certificates WHERE device=? AND revision=?',
                                       (device, row['revision'])).fetchall()
            if any(crl.get_revoked_certificate_by_serial_number(int(record['serial'])) is not None for record in current):
                raise Rejected()
            previous = database.execute('SELECT * FROM restricted_certificates WHERE device=? AND revision=? '
                                        'AND expires>? ORDER BY expires DESC LIMIT 1', (device, row['revision'], now + 300)).fetchone()
            if previous is None:
                certificate = self._issue(row, authority, now, expires)
                pem = certificate.public_bytes(Encoding.PEM).decode()
                database.execute('INSERT INTO restricted_certificates VALUES (?,?,?,?,?)',
                                 (device, row['revision'], str(certificate.serial_number), expires, pem))
            else:
                pem = previous['certificate']
                certificate = x509.load_pem_x509_certificate(pem.encode())
                certificate.verify_directly_issued_by(authority)
                pem = certificate.public_bytes(Encoding.PEM).decode()
            if crl.get_revoked_certificate_by_serial_number(certificate.serial_number) is not None:
                raise Rejected()
            result = dict(version=1, device=device, challenge=proof['challenge'], issued_at=now,
                          expires_at=min(expires, int(certificate.not_valid_after_utc.timestamp()), timestamp(seeds['expires_at'])),
                          revision=row['revision'], issuer=self.manifest, certificate=pem,
                          revocations=crl_pem, minimum_crl=crl_number, directory=seeds)
            encoded = json.dumps(result, separators=(',', ':')).encode()
            require(len(encoded) <= MAX_RESPONSE)
            database.execute('UPDATE challenges SET used=1 WHERE nonce=?', (digest,))
            return result

    def _issue(self, row, authority, now, expires, role='device'):
        require(role in ('device', 'gateway'))
        public = key(row['public'], 64)
        subject = x509.Name([x509.NameAttribute(NameOID.SERIAL_NUMBER, row['device']), *[
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, value) for value in (
                'protocol=' + PROTOCOL, 'family=' + row['family'], 'role=' + role, 'revision=' + str(row['revision']))]])
        return (x509.CertificateBuilder().subject_name(subject).issuer_name(authority.subject)
                .public_key(Ed25519PublicKey.from_public_bytes(public[32:])).serial_number(x509.random_serial_number())
                .not_valid_before(utc(now)).not_valid_after(utc(expires))
                .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
                .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH if role == 'gateway' else ExtendedKeyUsageOID.CLIENT_AUTH]), critical=True)
                .add_extension(x509.SubjectAlternativeName([x509.UniformResourceIdentifier(
                    'urn:family-connect:identity:' + public.hex()), x509.DNSName('gateway.family-connect.test')]), critical=False).sign(self.signing_key, None))
