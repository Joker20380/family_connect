"""Experimental v1 envelope using reference RNS encryption/signature APIs.

No RNS link or HTTP trust is assumed. Signatures cover the exact encrypted bytes
and domain separator; signed plaintext carries recipient, revision and lease.
This format is not yet a frozen public protocol or deployed production service.
"""
import base64
import json
from dataclasses import dataclass

import RNS

from .models import NetworkProvisioningState

DOMAIN = b'family-connect/provisioning-envelope/v1\x00'
MAX_ENVELOPE_BYTES = 65536


class ProvisioningRejected(ValueError):
    pass


def public_identity(raw):
    if type(raw) is not bytes or len(raw) != 64:
        raise ProvisioningRejected('invalid public identity')
    result = RNS.Identity(create_keys=False)
    result.load_public_key(raw)
    return result


def issue(state: NetworkProvisioningState, *, recipient_public: bytes, signing_identity) -> bytes:
    recipient = public_identity(recipient_public)
    if recipient.hash.hex() != state.recipient:
        raise ProvisioningRejected('wrong provisioning recipient')
    ciphertext = recipient.encrypt(state.model_dump_json().encode())
    signature = signing_identity.sign(DOMAIN + ciphertext)
    return json.dumps(dict(ciphertext=base64.b64encode(ciphertext).decode(),
                           signature=base64.b64encode(signature).decode()),
                      separators=(',', ':')).encode()


def _unique_fields(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ProvisioningRejected('duplicate envelope field')
        result[key] = value
    return result


@dataclass(frozen=True, slots=True, repr=False)
class VerifiedProvisioningState:
    """In-process type boundary, not protection against malicious local code."""
    state: NetworkProvisioningState


class ProvisioningVerifier:
    def __init__(self, *, trusted_signer_public: bytes, device_identity,
                 wireguard_public_key: str):
        self._signer = public_identity(trusted_signer_public)
        self._device = device_identity
        self._wg_public = wireguard_public_key

    def verify(self, envelope: bytes, *, now: int, minimum_revision: int,
               minimum_entitlement_revision: int = 1) -> VerifiedProvisioningState:
        # Floors must come from trusted local persistence, never delivery hints.
        if (type(now) is not int or now < 0 or type(minimum_revision) is not int
                or minimum_revision < 0 or type(minimum_entitlement_revision) is not int
                or minimum_entitlement_revision < 1):
            raise ProvisioningRejected('invalid verification context')
        if type(envelope) is not bytes or len(envelope) > MAX_ENVELOPE_BYTES:
            raise ProvisioningRejected('invalid envelope size')
        try:
            outer = json.loads(envelope, object_pairs_hook=_unique_fields)
            if type(outer) is not dict or set(outer) != {'ciphertext', 'signature'}:
                raise ValueError()
            ciphertext = base64.b64decode(outer['ciphertext'], validate=True)
            signature = base64.b64decode(outer['signature'], validate=True)
            if len(signature) != 64 or not self._signer.validate(signature, DOMAIN + ciphertext):
                raise ValueError()
            plaintext = self._device.decrypt(ciphertext)
            if plaintext is None:
                raise ValueError()
            # Reject duplicate fields before typed validation, including nested objects.
            json.loads(plaintext, object_pairs_hook=_unique_fields)
            state = NetworkProvisioningState.model_validate_json(plaintext)
        except (ValueError, TypeError, KeyError, UnicodeError, RecursionError):
            raise ProvisioningRejected('invalid provisioning envelope') from None
        if state.recipient != self._device.hash.hex() or state.wireguard_public_key != self._wg_public:
            raise ProvisioningRejected('provisioning device mismatch')
        if not state.issued_at <= now < state.expires_at:
            raise ProvisioningRejected('provisioning outside authorization lease')
        if state.revision <= minimum_revision:
            raise ProvisioningRejected('provisioning replay or downgrade')
        if state.entitlement_revision < minimum_entitlement_revision:
            raise ProvisioningRejected('stale entitlement revision')
        return VerifiedProvisioningState(state)
