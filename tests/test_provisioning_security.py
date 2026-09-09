import base64
import json

import pytest
import RNS

from device_identity.device import DeviceIdentity
from provisioning.envelope import DOMAIN, ProvisioningRejected, ProvisioningVerifier, issue
from provisioning.models import NetworkProvisioningState


@pytest.fixture
def setup():
    device = DeviceIdentity.generate()
    signer = RNS.Identity()
    data = dict(schema_version=1, revision=20, recipient=device.reference,
                issued_at=1000, expires_at=2000, entitlement_id='family-1',
                entitlement_revision=3, wireguard_public_key=device.wireguard_public_key,
                addresses=['10.77.0.4/32'], dns=['1.1.1.1'], gateways=[dict(
                    gateway_id='ru-1', provider_id='provider-1', region='RU',
                    transport='wireguard', endpoint='198.51.100.1', port=51820,
                    public_key=DeviceIdentity.generate().wireguard_public_key)])
    state = NetworkProvisioningState.model_validate_json(json.dumps(data))
    verifier = ProvisioningVerifier(trusted_signer_public=signer.get_public_key(),
                                    device_identity=device._identity,
                                    wireguard_public_key=device.wireguard_public_key)
    return device, signer, data, state, verifier


def encrypted(data, device, signer):
    ciphertext = device._identity.encrypt(json.dumps(data).encode())
    return json.dumps(dict(ciphertext=base64.b64encode(ciphertext).decode(),
                           signature=base64.b64encode(signer.sign(DOMAIN + ciphertext)).decode())).encode()


def test_signed_encrypted_round_trip_uses_reference_reticulum(setup):
    device, signer, _, state, verifier = setup
    wire = issue(state, recipient_public=base64.b64decode(device.public_identity), signing_identity=signer)
    assert b'family-1' not in wire and b'198.51.100.1' not in wire
    verified = verifier.verify(wire, now=1500, minimum_revision=19)
    assert verified.state == state
    assert 'family-1' not in repr(verified)


@pytest.mark.parametrize('mutation', ['recipient', 'wg_key', 'expired', 'future',
                                    'schema', 'bool_schema', 'private_key', 'duplicate_gateway'])
def test_signed_but_invalid_states_rejected(setup, mutation):
    device, signer, data, _, verifier = setup
    if mutation == 'recipient':
        data['recipient'] = DeviceIdentity.generate().reference
    elif mutation == 'wg_key':
        data['wireguard_public_key'] = DeviceIdentity.generate().wireguard_public_key
    elif mutation == 'expired':
        data['expires_at'] = 1500
    elif mutation == 'future':
        data['issued_at'] = 1501
    elif mutation == 'schema':
        data['schema_version'] = 2
    elif mutation == 'bool_schema':
        data['schema_version'] = True
    elif mutation == 'private_key':
        data['private_key'] = 'not allowed'
    else:
        data['gateways'] *= 2
    with pytest.raises(ProvisioningRejected):
        verifier.verify(encrypted(data, device, signer), now=1500, minimum_revision=19)


@pytest.mark.parametrize('floor', [20, 21])
def test_replay_and_downgrade_rejected(setup, floor):
    device, signer, data, _, verifier = setup
    with pytest.raises(ProvisioningRejected, match='replay or downgrade'):
        verifier.verify(encrypted(data, device, signer), now=1500, minimum_revision=floor)


def test_stale_entitlement_rejected(setup):
    device, signer, data, _, verifier = setup
    with pytest.raises(ProvisioningRejected, match='stale entitlement'):
        verifier.verify(encrypted(data, device, signer), now=1500, minimum_revision=19,
                        minimum_entitlement_revision=4)


def test_untrusted_signer_and_wrong_decryption_key_rejected(setup):
    device, signer, data, _, verifier = setup
    for recipient, issuer in [(device, RNS.Identity()), (DeviceIdentity.generate(), signer)]:
        with pytest.raises(ProvisioningRejected):
            verifier.verify(encrypted(data, recipient, issuer), now=1500, minimum_revision=19)


@pytest.mark.parametrize('wire', [b'{}', b'[]', b'x' * 65537,
                                   b'{"ciphertext":"","signature":"","signature":""}'])
def test_malformed_envelope_rejected(setup, wire):
    verifier = setup[-1]
    with pytest.raises(ProvisioningRejected):
        verifier.verify(wire, now=1500, minimum_revision=19)


def test_ciphertext_tampering_rejected(setup):
    device, signer, data, _, verifier = setup
    wire = json.loads(encrypted(data, device, signer))
    raw = bytearray(base64.b64decode(wire['ciphertext']))
    raw[-1] ^= 1
    wire['ciphertext'] = base64.b64encode(raw).decode()
    with pytest.raises(ProvisioningRejected):
        verifier.verify(json.dumps(wire).encode(), now=1500, minimum_revision=19)


def test_provider_candidates_and_revision_update(setup):
    device, signer, data, _, verifier = setup
    data['revision'] = 21
    alternative = {**data['gateways'][0], 'gateway_id': 'ru-2', 'provider_id': 'provider-2',
                   'endpoint': '203.0.113.2'}
    data['gateways'].append(alternative)
    state = verifier.verify(encrypted(data, device, signer), now=1500, minimum_revision=20).state
    assert state.revision == 21
    assert {g.provider_id for g in state.gateways} == {'provider-1', 'provider-2'}
    with pytest.raises(ValueError):
        state.revision = 19
