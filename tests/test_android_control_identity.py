"""Native enrollment proof fixture, using only the existing public test keys."""
import base64
import json
from pathlib import Path

import RNS
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from device_identity.device import DeviceIdentity, verify_transport_key_proof


def test_android_enrollment_proof_matches_reference():
    vectors = Path(__file__).parent / 'vectors'
    keys = json.loads((vectors / 'control-v1/TEST-ONLY-identity.json').read_text())
    assert keys['test_only'] is True
    device = DeviceIdentity(
        RNS.Identity.from_bytes(base64.b64decode(keys['rns_private_b64'], validate=True)),
        X25519PrivateKey.from_private_bytes(base64.b64decode(keys['wg_private_b64'], validate=True)))
    proof = json.loads((vectors / 'control-identity-v1/identity-binding-proof.json').read_text())
    challenge = base64.b64encode(bytes(32)).decode()
    assert device.prove_transport_key(challenge) == proof
    verify_transport_key_proof(proof, expected_challenge=challenge)
