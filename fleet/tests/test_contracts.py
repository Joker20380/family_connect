import copy

import pytest

from fleet.contracts import FleetError, inventory, load, transition, validate


def instance():
    return dict(instance_id='nl-test-001', logical_gateway='nl', provider='synthetic', region='test',
        ipv4='192.0.2.10', ipv6=None, os_family='ubuntu', os_version='24.04', architecture='x86_64',
        state='DISCOVERED', desired_bundle='test-v1', actual_bundle=None, enrollment_state='NEW',
        health_state='UNKNOWN', deployment_identity=None, roles=['awg'], created_at='2026-11-01T00:00:00Z',
        activated_at=None, drained_at=None, quarantined_at=None)


def sample():
    return dict(schema=1, logical_gateways=[dict(id='nl', country='NL', transports=['awg'],
        desired_state='ACTIVE', active_instance=None, fallback_instances=[], catalog_generation=4)],
        instances=[instance()], artifacts=[dict(bundle_id='test-v1', source_commit='a'*40,
        manifest_sha256='b'*64, archive_sha256='c'*64, signature='A'*86+'==', supported_os=['ubuntu-24.04'],
        architectures=['x86_64'], roles=['awg'], created_at='2026-11-01T00:00:00Z')])


def test_inventory():
    assert inventory(sample())


@pytest.mark.parametrize('field,value', [('ipv4','bad'), ('state','PROVISIONING'), ('roles',['password']),
    ('unknown','x'), ('activated_at','yesterday'), ('desired_bundle',None)])
def test_strict_instance(field, value):
    item = instance()
    item[field] = value
    with pytest.raises(FleetError):validate('instance', item)


@pytest.mark.parametrize('mutation', [
    lambda data: data['instances'].append(copy.deepcopy(data['instances'][0])),
    lambda data: data.update(artifacts=[]),
    lambda data: data['instances'][0].update(state='ACTIVE'),
    lambda data: data.update(secret='no'),
])
def test_inventory_rejects(mutation):
    data = sample()
    mutation(data)
    with pytest.raises(FleetError):inventory(data)


def test_transition():
    assert transition('DISCOVERED','PREFLIGHTED') == 'PREFLIGHTED'
    for previous,target in [('STAGED','ACTIVE'), ('RETIRED','ACTIVE'), ('STAGED','VERIFIED')]:
        with pytest.raises(FleetError):transition(previous,target)
    assert transition('STAGED','VERIFIED',health_pass=True) == 'VERIFIED'


def test_duplicate_json():
    with pytest.raises(FleetError):load('{"schema":1,"schema":1}')
