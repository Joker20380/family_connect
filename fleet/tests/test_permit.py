import copy

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from fleet.contracts import FleetError
from fleet.permit import ACTIONS, EXCLUDED, SCOPE, replay_binding, sign, validate, verify


@pytest.fixture
def authority():
    key = Ed25519PrivateKey.generate()
    body = dict(schema=1, scope=SCOPE, permit_id='rehearsal-one', instance_id='fleet-rehearsal-001',
        logical_gateway='fleet-rehearsal', ipv4='8.8.8.8', ssh_fingerprint='SHA256:'+'A'*43,
        provider='test-provider', region='test-region', bundle_a='gw-'+'a'*32, bundle_b='gw-'+'b'*32,
        allowed_actions=list(ACTIONS), issued_at=1000, expires_at=15400, catalog_publication=False,
        production_identity_import=False, user_operations=False, paid_operations=False,
        agent_sha256='c'*64, bundle_signer_sha256='d'*64)
    permit = sign(body, key, now=1000)
    arguments = dict(host=body['ipv4'], fingerprint=body['ssh_fingerprint'], bundle_id=body['bundle_a'],
        action='preflight', agent_sha256=body['agent_sha256'], bundle_signer_sha256=body['bundle_signer_sha256'], now=1001)
    return key, permit, arguments


def test_signed_permit_and_operation_idempotency(authority):
    key, permit, arguments = authority
    assert len(verify(permit, key.public_key(), **arguments)) == 64
    request = dict(operation_id='test-001', action='stage', bundle_id=arguments['bundle_id'], parameters={})
    binding = replay_binding(None, permit, request)
    assert replay_binding(binding, permit, request) == binding
    for changed in (dict(request, parameters={'revision': 2}), dict(request, action='retire')):
        with pytest.raises(FleetError, match='replay_changed'):
            replay_binding(binding, permit, changed)
    other = copy.deepcopy(permit)
    other['body']['permit_id'] = 'rehearsal-two'
    with pytest.raises(FleetError, match='replay_changed'):
        replay_binding(binding, other, request)


@pytest.mark.parametrize('field,value', [('host','1.1.1.1'), ('fingerprint','SHA256:'+'B'*43),
    ('bundle_id','gw-'+'e'*32), ('agent_sha256','e'*64), ('bundle_signer_sha256','e'*64),
    ('action','catalog'), ('action','paid'), ('action','enroll-user'), ('action','shell'),
    ('now',999), ('now',15400)])
def test_permit_bindings(authority, field, value):
    key, permit, arguments = authority
    arguments[field] = value
    with pytest.raises(FleetError):
        verify(permit, key.public_key(), **arguments)


@pytest.mark.parametrize('address', sorted(EXCLUDED) + ['127.0.0.1','10.1.2.3','::1','1.2.3.999'])
def test_production_and_nonpublic_hosts(authority, address):
    key, permit, arguments = authority
    permit['body']['ipv4'] = address
    with pytest.raises(FleetError):
        sign(permit['body'], key, now=1000)


@pytest.mark.parametrize('field,value', [('instance_id','nl-trainhosting-001'), ('logical_gateway','nl'),
    ('scope','production'), ('catalog_publication',True), ('production_identity_import',True),
    ('user_operations',True), ('paid_operations',True), ('expires_at',15401),
    ('allowed_actions',['preflight','shell']), ('allowed_actions',['stage','stage'])])
def test_forbidden_permits(authority, field, value):
    key, permit, arguments = authority
    permit['body'][field] = value
    with pytest.raises(FleetError):
        validate(permit['body'], now=1000)


def test_signature_and_unknown_fields(authority):
    key, permit, arguments = authority
    with pytest.raises(FleetError, match='signature'):
        verify(permit, Ed25519PrivateKey.generate().public_key(), **arguments)
    permit['body']['region'] = 'changed'
    with pytest.raises(FleetError, match='signature'):
        verify(permit, key.public_key(), **arguments)
    permit['body']['force_live'] = True
    with pytest.raises(FleetError):
        validate(permit['body'], now=1000)
