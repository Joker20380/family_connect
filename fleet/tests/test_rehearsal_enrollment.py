import time

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from fleet.contracts import FleetError
from fleet.enrollment import EnrollmentStore, proof_payload, verify_receipt
from fleet.remote import public_hex


def test_rehearsal_one_use_node_proof_and_scope(tmp_path):
    authority = Ed25519PrivateKey.generate()
    node = Ed25519PrivateKey.generate()
    public = public_hex(node.public_key())
    binding = dict(instance_id='fleet-rehearsal-001', logical_gateway='fleet-rehearsal',
        bundle_id='gw-'+'a'*32, provider='fixture', region='fixture', ipv4='8.8.8.8', roles=['awg','tcp','mesh'])
    store = EnrollmentStore(tmp_path/'rehearsal.sqlite', authority, scope='rehearsal')
    token, challenge = store.issue(binding)
    signature = node.sign(proof_payload(binding, challenge['challenge'], public, 'rehearsal'))
    receipt = store.enroll(token, binding, public, signature)
    assert verify_receipt(receipt, authority.public_key(), binding, 'rehearsal')
    assert token.encode() not in (tmp_path/'rehearsal.sqlite').read_bytes()
    with pytest.raises(FleetError):
        store.enroll(token, binding, public, signature)
    with pytest.raises(FleetError):
        verify_receipt(receipt, authority.public_key(), binding)
    with pytest.raises(FleetError):
        EnrollmentStore(tmp_path/'rehearsal.sqlite', authority)
    with pytest.raises(FleetError):
        store.issue(dict(binding, logical_gateway='nl'))


def test_synthetic_proof_cannot_enroll_rehearsal(tmp_path):
    authority = Ed25519PrivateKey.generate()
    node = Ed25519PrivateKey.generate()
    public = public_hex(node.public_key())
    binding = dict(instance_id='fleet-rehearsal-001', logical_gateway='fleet-rehearsal',
        bundle_id='gw-'+'a'*32, provider='fixture', region='fixture', ipv4='8.8.8.8', roles=['awg'])
    store = EnrollmentStore(tmp_path/'rehearsal.sqlite', authority, scope='rehearsal')
    token, challenge = store.issue(binding)
    with pytest.raises(FleetError, match='possession'):
        store.enroll(token, binding, public, node.sign(proof_payload(binding, challenge['challenge'], public)))
