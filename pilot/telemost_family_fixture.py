"""Disposable 5N.3 issuer; never accepts a production DB, identity or signing key."""
import argparse
import base64
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import sqlite3
import time

from cryptography import x509
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID

from control.product.store import ProductStore, EnrollmentRejected
from device_identity.device import DeviceIdentity

PROTOCOL = 'family-connect-5n3-test-v1'


def signing_key(device):
    key = Ed25519PrivateKey.from_private_bytes(device._identity.get_private_key()[32:])
    assert key.public_key().public_bytes_raw() == base64.b64decode(device.public_identity)[32:]
    return key


class FixtureIssuer:
    def __init__(self, directory):
        self.directory = directory
        directory.mkdir(mode=0o700)
        self.store = ProductStore(directory / 'test-only.db')
        self.store.migrate()
        self.now = datetime.now(timezone.utc).replace(microsecond=0)
        self.authority = DeviceIdentity.generate()
        self.key = signing_key(self.authority)
        name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'DISPOSABLE 5N.3 TEST AUTHORITY')])
        self.ca = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
                   .public_key(self.key.public_key()).serial_number(x509.random_serial_number())
                   .not_valid_before(self.now - timedelta(minutes=1))
                   .not_valid_after(self.now + timedelta(hours=2))
                   .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
                   .add_extension(x509.KeyUsage(False, False, False, False, False, True, True, False, False), critical=True)
                   .add_extension(x509.SubjectKeyIdentifier.from_public_key(self.key.public_key()), critical=False)
                   .sign(self.key, None))
        self.issued = {}

    def family(self):
        return self.store.create_entitlement(expires_at=int(time.time()) + 3600, device_limit=5)

    def enroll(self, family):
        invitation = self.store.create_invitation(family['entitlement_id'], expires_at=int(time.time()) + 1800)
        identity = DeviceIdentity.generate()
        challenge = self.store.challenge(invitation_token=invitation['invitation_token'],
                                         public_identity=identity.public_identity,
                                         wireguard_public_key=identity.wireguard_public_key)
        proof = identity.prove_transport_key(challenge['challenge'])
        self.store.enroll(proof)
        try:
            self.store.enroll(proof)
        except EnrollmentRejected:
            pass
        else:
            raise RuntimeError('existing enrollment accepted replay')
        return identity

    def issue(self, identity, role):
        if role not in {'device', 'gateway'}:
            raise ValueError('invalid test role')
        authorization = self.store.authorization(identity.reference)
        with sqlite3.connect(self.store.path) as database:
            family = database.execute('SELECT family_id FROM entitlements WHERE id=?',
                                      (authorization['entitlement_id'],)).fetchone()[0]
            public = database.execute('SELECT public_identity FROM devices WHERE identity=?',
                                      (identity.reference,)).fetchone()[0]
        if public != identity.public_identity:
            raise ValueError('identity does not match authority')
        subject = x509.Name([
            x509.NameAttribute(NameOID.SERIAL_NUMBER, identity.reference),
            *[x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, value)
              for value in ('protocol=' + PROTOCOL, 'family=' + family, 'role=' + role,
                            'revision=' + str(authorization['entitlement_revision']))],
        ])
        usage = ExtendedKeyUsageOID.SERVER_AUTH if role == 'gateway' else ExtendedKeyUsageOID.CLIENT_AUTH
        certificate = (x509.CertificateBuilder().subject_name(subject).issuer_name(self.ca.subject)
                       .public_key(signing_key(identity).public_key()).serial_number(x509.random_serial_number())
                       .not_valid_before(self.now - timedelta(minutes=1))
                       .not_valid_after(datetime.fromtimestamp(authorization['expires_at'], timezone.utc))
                       .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
                       .add_extension(x509.ExtendedKeyUsage([usage]), critical=True)
                       .add_extension(x509.SubjectAlternativeName([
                           x509.DNSName('gateway.family-connect.test'),
                           x509.UniformResourceIdentifier('urn:family-connect:identity:' + base64.b64decode(public).hex())
                       ]), critical=False)
                       .sign(self.key, None))
        self.issued[identity.reference] = certificate
        return certificate

    def revocations(self):
        builder = (x509.CertificateRevocationListBuilder().issuer_name(self.ca.subject)
                   .last_update(self.now).next_update(self.now + timedelta(hours=1))
                   .add_extension(x509.CRLNumber(2), critical=False)
                   .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(self.key.public_key()), critical=False))
        for reference, certificate in self.issued.items():
            try:
                self.store.authorization(reference)
            except EnrollmentRejected:
                builder = builder.add_revoked_certificate(x509.RevokedCertificateBuilder()
                    .serial_number(certificate.serial_number).revocation_date(self.now).build())
        return builder.sign(self.key, None)


def generate(directory):
    issuer = FixtureIssuer(directory)
    family = issuer.family()
    gateway = issuer.enroll(family)
    identities = {'valid': issuer.enroll(family), 'gateway': gateway,
                  'revoked': issuer.enroll(family), 'wrong-family': issuer.enroll(issuer.family())}
    certificates = {name: issuer.issue(identity, 'gateway' if name == 'gateway' else 'device')
                    for name, identity in identities.items()}
    foreign = FixtureIssuer(directory / 'foreign-test-only')
    identities['unknown'] = foreign.enroll(foreign.family())
    certificates['unknown'] = foreign.issue(identities['unknown'], 'device')
    issuer.store.revoke_device(identities['revoked'].reference)
    for identity in (identities['revoked'], DeviceIdentity.generate()):
        try:
            issuer.issue(identity, 'device')
        except EnrollmentRejected:
            pass
        else:
            raise RuntimeError('issuer failed closed admission')
    revocations = issuer.revocations().public_bytes(Encoding.PEM).decode()
    for name, identity in identities.items():
        profile = dict(certificate=certificates[name].public_bytes(Encoding.PEM).decode(),
                       private_key=signing_key(identity).private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()).decode(),
                       authority=issuer.ca.public_bytes(Encoding.PEM).decode(), revocations=revocations,
                       family=family['family_id'], gateway=gateway.reference, minimum_revision=1, minimum_crl=2)
        path = directory / (name + '.json')
        with open(path, 'x', opener=lambda filename, flags: os.open(filename, flags, 0o600)) as output:
            json.dump(profile, output)
    print('DISPOSABLE_FIXTURES_READY; enrollment_replay/unknown/revoked_issuer=REJECTED')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    generate(args.out)


if __name__ == '__main__':
    main()
