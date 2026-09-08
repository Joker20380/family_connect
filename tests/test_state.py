import base64
import copy

import pytest
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from control.app import sign_state, verify_state


def fixture():
    key = Ed25519PrivateKey.generate()
    pub = key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    state = {"version": 1, "epoch": 4, "issued_at": 100, "expires_at": 200,
             "nodes": [{"role": "relay", "internet_exit": False}]}
    return key, pub, state


def test_state_signature_expiry_and_rollback():
    key, pub, state = fixture()
    envelope = sign_state(state, key)
    assert verify_state(envelope, pub, now=150, minimum_epoch=4) == state
    for now, epoch in [(99, 4), (200, 4), (150, 5)]:
        with pytest.raises(ValueError):
            verify_state(envelope, pub, now=now, minimum_epoch=epoch)
    modified = copy.deepcopy(envelope)
    modified["payload"] = base64.b64encode(b'{}').decode()
    with pytest.raises(InvalidSignature):
        verify_state(modified, pub, now=150)


def test_relay_exit_rejected_even_if_signed():
    key, pub, state = fixture()
    state["nodes"][0]["internet_exit"] = True
    with pytest.raises(ValueError, match="relay cannot"):
        verify_state(sign_state(state, key), pub, now=150)


def test_other_root_not_trusted():
    key, pub, state = fixture()
    with pytest.raises(InvalidSignature):
        verify_state(sign_state(state, Ed25519PrivateKey.generate()), pub, now=150)
