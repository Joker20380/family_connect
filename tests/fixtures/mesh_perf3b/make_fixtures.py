import base64
import importlib.util
import json
import os
from pathlib import Path
import sys
import time

from cryptography import x509
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption

os.umask(0o077)
root = Path(__file__).resolve().parents[3]
out = root / 'state-client-build/mesh-perf-3b' / (sys.argv[1] if len(sys.argv) > 1 else 'fixtures')
out.mkdir()
sys.path.insert(0, str(root / 'state-client-build/mesh-perf-3b/api'))
spec = importlib.util.spec_from_file_location('baseline_fixtures', root / 'tests/test_friends_restricted.py')
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)
from device_identity.device import DeviceIdentity
from control.friends.restricted import utc, iso

now = int(time.time())
service, device, _ = fixtures.configured(out, now, directory_lifetime=10800)
trust, authority, crl, crl_pem, crl_number = service._trust(now)
gateway = DeviceIdentity.generate()
identities = {'valid': device, 'other': DeviceIdentity.generate(), 'gateway': gateway,
              'revoked': DeviceIdentity.generate(), 'wrong-family': DeviceIdentity.generate()}
certificates = {}
for name, identity in identities.items():
    row = dict(public=identity.public_identity, device=identity.reference, revision=1,
               family='c' * 32 if name == 'wrong-family' else trust['family'])
    certificates[name] = service._issue(row, authority, now, now + 3600, 'gateway' if name == 'gateway' else 'device')
revoked = (x509.RevokedCertificateBuilder().serial_number(certificates['revoked'].serial_number)
           .revocation_date(utc(now - 1)).build())
crl = (x509.CertificateRevocationListBuilder().issuer_name(authority.subject).last_update(utc(now-1))
       .next_update(utc(now+3600)).add_extension(x509.CRLNumber(2), False).add_revoked_certificate(revoked)
       .sign(service.signing_key, None))
for name, identity in identities.items():
    key = Ed25519PrivateKey.from_private_bytes(identity._identity.get_private_key()[32:])
    value = dict(authority=trust['authority'], certificate=certificates[name].public_bytes(Encoding.PEM).decode(),
                 private_key=key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()).decode(),
                 revocations=crl.public_bytes(Encoding.PEM).decode(), family=trust['family'],
                 gateway=gateway.reference, minimum_revision=1, minimum_crl=2)
    (out / (name + '.json')).write_text(json.dumps(value))
unknown_dir = out / 'unknown-family'
unknown_dir.mkdir()
unknown_service, unknown, _ = fixtures.configured(unknown_dir, now)
unknown_response = unknown_service.fetch(fixtures.proof(unknown_service, unknown))
unknown_trust, *_ = unknown_service._trust(now)
key = Ed25519PrivateKey.from_private_bytes(unknown._identity.get_private_key()[32:])
unknown_profile = dict(value, authority=unknown_trust['authority'], certificate=unknown_response['certificate'],
                       private_key=key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()).decode(),
                       revocations=unknown_response['revocations'], minimum_crl=1)
(out / 'unknown.json').write_text(json.dumps(unknown_profile))
guard = dict(operation='local-fixture', family=trust['family'], device=device.reference,
             public_key=base64.b64decode(device.public_identity)[32:].hex(), not_before=iso(now - 10), not_after=iso(now + 3600))
(out / 'owner.json').write_text(json.dumps(guard))
first = service.fetch(fixtures.proof(service, device))
canary = json.loads(json.dumps(first))
canary['directory']['issued_at'] = iso(now)
canary['directory']['seeds'][0]['join_url'] = 'https://telemost.yandex.ru/j/disposable-canary'
returned = json.loads(json.dumps(first))
returned['directory']['issued_at'] = iso(now + 1)
returned['directory']['seeds'][0]['join_url'] = 'https://telemost.yandex.ru/j/disposable-return'
for name, response in [('production', first), ('canary', canary), ('returned', returned)]:
    (out / (name + '-delivery.json')).write_text(json.dumps(dict(response=response,
        public=device.public_identity,
        anchor=base64.b64encode(service.anchor).decode(), now=now + 2)))
(out / 'roundtrip.json').write_text(json.dumps([first, canary, returned]))
print('Disposable local issuer/device fixtures created; no production inputs')
