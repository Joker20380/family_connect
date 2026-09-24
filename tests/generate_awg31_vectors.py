"""PUBLIC TEST ONLY. Generate a new immutable AWG 3.1 corpus; never read keys."""
import base64
import copy
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import RNS
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from device_identity.device import DeviceIdentity
from provisioning.configuration import AUDIENCE, DOMAIN


def generate(output):
    output.mkdir(parents=True, exist_ok=False)
    def seed(label):
        return hashlib.sha256(('PUBLIC TEST ONLY FC AWG31 '+label).encode()).digest()
    def b64(raw):return base64.b64encode(raw).decode()
    def encode(value):return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()
    device = DeviceIdentity(RNS.Identity.from_bytes(seed('rx')+seed('re')),
                            X25519PrivateKey.from_private_bytes(seed('wg')))
    signer = Ed25519PrivateKey.from_private_bytes(seed('issuer'))
    anchor = signer.public_key().public_bytes_raw()
    manifest = dict(schema_version=1, test_only=True, suite='family-connect-control-awg31-v1',
                    files={}, configurations=[])
    def put(name, raw):
        (output/name).write_bytes(raw)
        manifest['files'][name] = dict(size=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    put('TEST-ONLY-identity.json', encode(dict(test_only=True, warning='PUBLIC TEST KEYS: NEVER DEPLOY',
        rns_private_b64=b64(seed('rx')+seed('re')), wg_private_b64=b64(seed('wg')),
        public_identity_b64=device.public_identity, wireguard_public_key=device.wireguard_public_key,
        device_reference=device.reference, anchor_b64=b64(anchor))))
    peer = X25519PrivateKey.from_private_bytes(seed('peer')).public_key().public_bytes_raw()
    config = ('[Interface]\nPrivateKey = LOCAL_DEVICE_KEY\nAddress = 10.83.0.2/32\nDNS = 1.1.1.1\n'
        'Jc = 4\nJmin = 40\nJmax = 100\nS1 = 32\nS2 = 32\nS3 = 32\nS4 = 32\n'
        'H1 = 1\nH2 = 2\nH3 = 3\nH4 = 4\nHeaderProtectionKey = '+b64(seed('header'))+'\n'
        'ContentPaddingAddition = 0-64\nRandomTrailers = true\nDisableCookies = false\n'
        '[Peer]\nPublicKey = '+b64(peer)+'\nEndpoint = 198.51.100.1:51820\nAllowedIPs = 0.0.0.0/0, ::/0\n')
    payload = dict(schema_version=2, config_id='awg31-fixture', revision=1, issued_at=1000,
        expires_at=2000, recipient=device.reference, audience=AUDIENCE,
        wireguard_public_key=device.wireguard_public_key, min_client_version='0.2.13',
        previous_config_hash=None, signer_key_id=hashlib.sha256(anchor).hexdigest(),
        gateways=[dict(gateway_id='dynamic-node-47', endpoint='198.51.100.1', port=51820)],
        transport_profiles=[dict(profile_id='protected-udp', gateway_id='dynamic-node-47',
                                transport='amneziawg', transport_version='3.1', config=config)])
    for name in ('valid', 'missing-protection', 'invalid-padding', 'gateway-mismatch',
                 'downgrade-label', 'expired', 'older-client', 'tampered'):
        value = copy.deepcopy(payload)
        profile = value['transport_profiles'][0]
        error = 'ACCEPT'
        now, version = 1000, '0.2.13'
        if name == 'missing-protection':
            profile['config'] = config.replace('DisableCookies = false\n', '')
            error = 'STRUCTURE'
        elif name == 'invalid-padding':
            profile['config'] = config.replace('0-64', '64-0')
            error = 'STRUCTURE'
        elif name == 'gateway-mismatch':
            value['gateways'][0]['port'] = 443
            error = 'STRUCTURE'
        elif name == 'downgrade-label':
            profile['transport_version'] = '2.0'
            error = 'STRUCTURE'
        elif name == 'expired':now, error = 2000, 'LEASE'
        elif name == 'older-client':version, error = '0.2.10', 'CLIENT_VERSION'
        ciphertext = device._identity.encrypt(encode(value))
        signature = signer.sign(DOMAIN+ciphertext)
        if name == 'tampered':
            signature = bytes([signature[0]^1])+signature[1:]
            error = 'SIGNATURE'
        raw = encode(dict(ciphertext=b64(ciphertext), signature=b64(signature)))
        put(name+'.envelope', raw)
        manifest['configurations'].append(dict(id=name, input=name+'.envelope', now=now,
            client_version=version, expected=error,
            legacy_expected=error if name in ('tampered', 'downgrade-label') else 'UNSUPPORTED_TRANSPORT_VERSION',
            payload=value if error == 'ACCEPT' else None))
    (output/'manifest.json').write_bytes(encode(manifest))
    return manifest


if __name__ == '__main__':
    generate(Path(sys.argv[1]))
