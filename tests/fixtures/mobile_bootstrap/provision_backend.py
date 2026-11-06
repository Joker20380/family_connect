"""Disposable real Friends authority for the bounded provisioning integration test."""
import base64
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
from http.server import ThreadingHTTPServer

from cryptography import x509
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID

from control.friends.access import Access
from control.friends import paid_beta
from control.friends.restricted import DOMAIN, PROTOCOL, from_env, migrate, utc
from control.friends.bootstrap_locator import issue
from device_identity.device import DeviceIdentity


def save(root, name, raw):
    with os.fdopen(os.open(root / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'wb') as output:
        output.write(raw)


def prepare(root):
    if any(root.iterdir()):
        raise ValueError('Requires empty disposable directory')
    access = Access(root / 'access.db')
    access.initialize()
    migrate(access)
    device, gateway = DeviceIdentity.generate(), DeviceIdentity.generate()
    invitation = access.invite()
    challenge = access.challenge(device.public_identity, device.wireguard_public_key, 'activate', invitation)
    access.complete(device.prove_transport_key(challenge['challenge']), 'activate')
    now = int(time.time())
    signer, anchor = Ed25519PrivateKey.generate(), Ed25519PrivateKey.generate()
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'isolated provisioning issuer')])
    authority = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(signer.public_key())
                 .serial_number(1).not_valid_before(utc(now - 10)).not_valid_after(utc(now + 3600))
                 .add_extension(x509.BasicConstraints(ca=True, path_length=0), True)
                 .add_extension(x509.KeyUsage(False, False, False, False, False, True, True, False, False), True)
                 .add_extension(x509.SubjectKeyIdentifier.from_public_key(signer.public_key()), False).sign(signer, None))
    family = 'a' * 32
    public = base64.b64decode(gateway.public_identity)
    gateway_key = Ed25519PrivateKey.from_private_bytes(gateway._identity.get_private_key()[32:])
    subject = x509.Name([x509.NameAttribute(NameOID.SERIAL_NUMBER, gateway.reference)] +
                        [x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, claim) for claim in
                         (f'protocol={PROTOCOL}', f'family={family}', 'role=gateway', 'revision=1')])
    server = (x509.CertificateBuilder().subject_name(subject).issuer_name(name).public_key(gateway_key.public_key())
              .serial_number(2).not_valid_before(utc(now - 1)).not_valid_after(utc(now + 600))
              .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), False)
              .add_extension(x509.SubjectAlternativeName([x509.DNSName('gateway.family-connect.test'),
                             x509.UniformResourceIdentifier('urn:family-connect:identity:' + public.hex())]), False)
              .sign(signer, None))
    payload = json.dumps(dict(version=1, sequence=1, family=family, gateway=gateway.reference,
                             authority=authority.public_bytes(Encoding.PEM).decode(), minimum_revision=1,
                             issued_at=now - 10, expires_at=now + 3600)).encode()
    manifest = dict(payload=base64.b64encode(payload).decode(), signature=base64.b64encode(anchor.sign(DOMAIN + payload)).decode())
    crl = (x509.CertificateRevocationListBuilder().issuer_name(name).last_update(utc(now - 1)).next_update(utc(now + 599))
           .add_extension(x509.CRLNumber(1), False).sign(signer, None)).public_bytes(Encoding.PEM).decode()
    profile = dict(certificate=server.public_bytes(Encoding.PEM).decode(),
                   private_key=gateway_key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()).decode(),
                   authority=authority.public_bytes(Encoding.PEM).decode(), revocations=crl, family=family,
                   gateway=gateway.reference, minimum_revision=1, minimum_crl=1)
    with access.db() as database:
        database.execute('INSERT INTO restricted_grants VALUES (?,?,?,?,0)', (device.reference, family, 1, now + 3600))
        database.execute('CREATE TABLE restricted_crl_sequence (singleton INTEGER PRIMARY KEY, sequence INTEGER NOT NULL)')
        database.execute('INSERT INTO restricted_crl_sequence VALUES (1,1)')
    values = {'issuer.json': json.dumps(manifest).encode(), 'issuer.key': signer.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()),
              'anchor.pub': base64.b64encode(anchor.public_key().public_bytes_raw()), 'admission.json': json.dumps(dict(devices=[device.reference])).encode(),
              'revocations.pem': crl.encode(), 'gateway.json': json.dumps(profile).encode(),
              'identity.private': device._identity.get_private_key(), 'wireguard.public': device.wireguard_public_key.encode(),
              'identity96.private': device._identity.get_private_key() + device._wireguard_key.private_bytes_raw()}
    for filename, raw in values.items():
        save(root, filename, raw)
    impostor = (x509.CertificateBuilder().subject_name(subject).issuer_name(name).public_key(gateway_key.public_key())
                .serial_number(3).not_valid_before(utc(now - 1)).not_valid_after(utc(now + 600))
                .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), False)
                .add_extension(x509.SubjectAlternativeName([x509.DNSName('gateway.family-connect.test')]), False).sign(signer, None))
    save(root, 'other-server.pem', impostor.public_bytes(Encoding.PEM))
    admission = [device.reference]
    negatives = {}
    for case in ('unactivated', 'revoked', 'subscription_expired'):
        candidate = DeviceIdentity.generate()
        negatives[case] = dict(public_identity=candidate.public_identity, wireguard_public_key=candidate.wireguard_public_key)
        if case == 'unactivated':
            continue
        invitation = access.invite()
        challenge = access.challenge(candidate.public_identity, candidate.wireguard_public_key, 'activate', invitation)
        access.complete(candidate.prove_transport_key(challenge['challenge']), 'activate')
        admission.append(candidate.reference)
        with access.db() as database:
            database.execute('INSERT INTO restricted_grants VALUES (?,?,?,?,0)', (candidate.reference, family, 1, now + 3600))
        if case == 'revoked':
            access.revoke_device(candidate.reference)
        else:
            with access.db() as database:
                database.execute('UPDATE device_support SET platform=?,app_version=?,version_code=108,last_seen=? WHERE device=?',
                                 ('android', paid_beta.PAID_ANDROID_VERSION, now, candidate.reference))
                support = database.execute('SELECT support_id FROM device_support WHERE device=?', (candidate.reference,)).fetchone()[0]
            with paid_beta.connection(access.path, write=True) as database:
                paid_beta.apply_event(database, support, 'payment', 'synthetic-payment-001', 'synthetic-confirmation', now=now,
                                      period_start=now, paid_until=now + 600, apk_sha256=paid_beta.PAID_ANDROID_APK_SHA256)
                paid_beta.apply_event(database, support, 'expire', 'synthetic-expire-001', 'synthetic-confirmation', now=now)
    (root / 'admission.json').write_text(json.dumps(dict(devices=admission)))
    save(root, 'negative-devices.json', json.dumps(negatives).encode())
    save(root, 'wrong-purpose.json', json.dumps(access.challenge(device.public_identity, device.wireguard_public_key, 'status')).encode())


def main():
    root = Path(sys.argv[2]).resolve()
    os.environ['FC_FRIENDS_RESTRICTED_DIR'] = str(root)
    if sys.argv[1] == 'inspect':
        with Access(root / 'access.db').db() as database:
            print(database.execute('SELECT count(*) FROM restricted_certificates').fetchone()[0])
        return
    if sys.argv[1] == 'issue':
        service = from_env(Access(root / 'access.db'))
        profile = json.loads((root / 'gateway.json').read_bytes())
        raw = issue(service, (root / 'provision-seed.json').read_bytes(), profile['certificate'], 1)
        save(root, 'locator.json', raw)
        return
    prepare(root)
    module_path = Path(__file__).resolve().parents[3] / 'deploy/friends/access-api.py'
    spec = importlib.util.spec_from_file_location('isolated_friends', module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ROOT, module.access = root, Access(root / 'access.db')
    with ThreadingHTTPServer(('127.0.0.1', 0), module.Handler) as server:
        print(json.dumps(dict(address='127.0.0.1:' + str(server.server_port))), flush=True)
        server.serve_forever()


if __name__ == '__main__':
    main()
