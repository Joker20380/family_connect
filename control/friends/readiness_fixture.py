"""Disposable contract authority; never accepts existing state or production keys."""
import base64
from contextlib import contextmanager
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time

from cryptography import x509
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat
from cryptography.x509.oid import NameOID

from control.friends.access import Access
from control.friends.restricted import DOMAIN, iso, migrate, utc
from device_identity.device import DeviceIdentity


def create(directory):
    if any(directory.iterdir()):
        raise ValueError('Fixture requires a new empty directory')
    now = int(time.time())
    access = Access(directory / 'access.db')
    access.initialize()
    migrate(access)
    identities = []
    for _ in range(2):
        identity = DeviceIdentity.generate()
        invitation = access.invite()
        challenge = access.challenge(identity.public_identity, identity.wireguard_public_key, 'activate', invitation)
        access.complete(identity.prove_transport_key(challenge['challenge']), 'activate')
        identities.append(identity)
    owner, non_owner = identities
    issuer = Ed25519PrivateKey.generate()
    anchor = Ed25519PrivateKey.generate()
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'disposable contract issuer')])
    authority = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
                 .public_key(issuer.public_key()).serial_number(x509.random_serial_number())
                 .not_valid_before(utc(now - 10)).not_valid_after(utc(now + 86400))
                 .add_extension(x509.BasicConstraints(ca=True, path_length=0), True)
                 .add_extension(x509.KeyUsage(False, False, False, False, False, True, True, False, False), True)
                 .add_extension(x509.SubjectKeyIdentifier.from_public_key(issuer.public_key()), False)
                 .sign(issuer, None))
    family, gateway = 'a' * 32, 'b' * 32
    payload = json.dumps(dict(version=1, sequence=1, family=family, gateway=gateway,
                             authority=authority.public_bytes(Encoding.PEM).decode(), minimum_revision=1,
                             issued_at=now - 10, expires_at=now + 86400)).encode()
    envelope = dict(payload=base64.b64encode(payload).decode(),
                    signature=base64.b64encode(anchor.sign(DOMAIN + payload)).decode())
    crl = (x509.CertificateRevocationListBuilder().issuer_name(name)
           .last_update(utc(now - 1)).next_update(utc(now + 899))
           .add_extension(x509.CRLNumber(1), False).sign(issuer, None))
    directory_value = dict(version=1, family=family, issued_at=iso(now - 1), expires_at=iso(now + 3299),
                           seeds=[dict(transport='telemost-webrtc', gateway=gateway,
                                       join_url='https://telemost.yandex.ru/j/test-only')])
    with access.db() as database:
        database.execute('INSERT INTO restricted_grants VALUES (?,?,?,?,0)',
                         (owner.reference, family, 1, now + 86400))
        database.execute('CREATE TABLE restricted_crl_sequence (singleton INTEGER PRIMARY KEY, sequence INTEGER NOT NULL)')
        database.execute('INSERT INTO restricted_crl_sequence VALUES (1,1)')
    values = {'issuer.json': json.dumps(envelope).encode(),
              'issuer.key': issuer.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()),
              'anchor.pub': base64.b64encode(anchor.public_key().public_bytes_raw()),
              'admission.json': json.dumps(dict(devices=[owner.reference])).encode(),
              'revocations.pem': crl.public_bytes(Encoding.PEM),
              'directory.json': json.dumps(directory_value).encode()}
    for filename, raw in values.items():
        descriptor = os.open(directory / filename, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(raw)
    public = lambda identity: dict(public_identity=identity.public_identity,
                                   wireguard_public_key=identity.wireguard_public_key)
    return dict(owner=owner, anchor=values['anchor.pub'].decode(),
                identities=dict(canary=public(owner), non_canary=[public(non_owner)]))


@contextmanager
def listener(artifact, *, port=0):
    with tempfile.TemporaryDirectory(prefix='fc-readiness-contract-') as temporary:
        directory = Path(temporary)
        fixture = create(directory)
        with socket.socket() as reservation:
            reservation.bind(('127.0.0.1', port))
            selected = reservation.getsockname()[1]
        environment = dict(PATH=os.defpath, HOME=temporary, PYTHONDONTWRITEBYTECODE='1',
                           FC_FRIENDS_RESTRICTED_DIR=temporary)
        process = subprocess.Popen([sys.executable, '-I', str(artifact), '--root', temporary,
                                    '--port', str(selected)], cwd=temporary, env=environment,
                                   stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError('Fixture exited')
                try:
                    with socket.create_connection(('127.0.0.1', selected), timeout=.2):
                        break
                except OSError:
                    time.sleep(.1)
            else:
                raise TimeoutError('Fixture startup')
            yield dict(fixture, directory=directory, process=process,
                       origin='http://127.0.0.1:' + str(selected))
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
