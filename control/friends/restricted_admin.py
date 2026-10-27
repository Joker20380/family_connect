"""Local operator grant and CRL publication; same Friends DB, no new identities."""
import argparse
import os
from pathlib import Path
import secrets
import base64
import hashlib
import hmac

from cryptography import x509
from cryptography.hazmat.primitives.serialization import Encoding

from .access import Access
from .readiness_receipts import CLOCK_SKEW_SECONDS
from .restricted import MAX_TEST_LIFETIME, from_env, migrate, delegation, utc


def grant(access, device, family, expires, minimum_revision=1):
    with access.db() as database:
        row = database.execute('SELECT d.revoked, i.revoked AS invite_revoked FROM devices d '
                               'JOIN invites i ON d.device=i.device WHERE d.device=?', (device,)).fetchone()
        if row is None or row['revoked'] or row['invite_revoked'] or expires <= access.clock():
            raise ValueError('grant rejected')
        old = database.execute('SELECT revision FROM restricted_grants WHERE device=?', (device,)).fetchone()
        database.execute('INSERT INTO restricted_grants VALUES (?,?,?,?,0) ON CONFLICT(device) DO UPDATE SET '
                         'family=excluded.family, revision=excluded.revision, expires=excluded.expires, revoked=0',
                         (device, family, max(old['revision'] + 1 if old else 1, minimum_revision), expires))


def build_crl_payload(service, database, previous_crl, previous_sequence, now, lifetime, *, receipt_key=None):
    if type(lifetime) is not int or not 900 <= lifetime <= MAX_TEST_LIFETIME:
        raise ValueError('invalid CRL lifetime')
    if type(previous_sequence) is not int or previous_sequence < 0:
        raise ValueError('invalid CRL sequence')
    if receipt_key is not None and (type(receipt_key) is not bytes or len(receipt_key) != 32):
        raise ValueError('invalid receipt key')
    trust, authority = delegation(service.manifest, service.anchor, now)
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
    builder = (x509.CertificateRevocationListBuilder().issuer_name(authority.subject).last_update(utc(issued))
               .next_update(utc(expires)).add_extension(x509.CRLNumber(number), critical=False))
    serials = []
    rows = database.execute('SELECT c.* FROM restricted_certificates c WHERE c.expires>? ORDER BY c.serial', (now,)).fetchall()
    for certificate in rows:
        try:
            row = service._grant(database, certificate['device'], now)
            valid = row['revision'] == certificate['revision'] and row['family'] == trust['family'] and row['revision'] >= trust['minimum_revision']
        except ValueError:
            valid = False
        if not valid:
            serial = int(certificate['serial'])
            serials.append(serial)
            builder = builder.add_revoked_certificate(x509.RevokedCertificateBuilder()
                .serial_number(serial).revocation_date(utc(now)).build())
    raw = builder.sign(service.signing_key, None).public_bytes(Encoding.PEM)
    return raw, dict(previous_number=previous_number, generated_number=number, this_update=issued,
                     next_update=expires, revoked_serials=tuple(serials), safe_serial_tokens=tuple(
                         hmac.new(receipt_key, str(serial).encode(), hashlib.sha256).hexdigest()[:12]
                         for serial in serials) if receipt_key is not None else ())


def publish_crl(service, path, *, lifetime=900):
    now = int(service.access.clock())
    with service.access.db() as database:
        try:
            previous = service.crl_source()
        except FileNotFoundError:
            previous = None
        exists = database.execute("SELECT 1 FROM sqlite_master WHERE name='restricted_crl_sequence'").fetchone()
        row = database.execute('SELECT sequence FROM restricted_crl_sequence WHERE singleton=1').fetchone() if exists else None
        raw, metadata = build_crl_payload(service, database, previous, row[0] if row else 0, now, lifetime)
        number = metadata['generated_number']
        database.execute('CREATE TABLE IF NOT EXISTS restricted_crl_sequence (singleton INTEGER PRIMARY KEY CHECK(singleton=1), sequence INTEGER NOT NULL)')
        database.execute('INSERT INTO restricted_crl_sequence VALUES (1,?) ON CONFLICT(singleton) DO UPDATE SET sequence=excluded.sequence', (number,))
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
    parser.add_argument('action', choices=['migrate', 'grant', 'publish-crl', 'gateway-certificate'])
    parser.add_argument('--device')
    parser.add_argument('--expires', type=int)
    parser.add_argument('--public-identity')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    access = Access(args.db)
    if args.action == 'migrate':
        migrate(access)
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
