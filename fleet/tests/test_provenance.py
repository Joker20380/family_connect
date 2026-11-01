import copy
from pathlib import Path

import pytest

from fleet.contracts import FleetError, canonical, digest, load
from fleet.provenance import check_inputs, validate


def inventory():
    return load((Path(__file__).parents[1]/'inventory/deployable-gateway-v1.json').read_bytes())


def test_native_inventory_exact_source_bindings():
    value = validate(inventory())
    assert {item['id'] for item in value['artifacts']} == {'awg-engine','awg-tools','tcp-xray','mesh-gateway'}
    assert all(item['source_commit'] and item['receipt'] and item['license'] for item in value['artifacts'])
    assert value['artifacts'][-1]['source_commit'] == 'c9c0a4de55f455e0788e7b519383c0cb0743fc96'
    assert 'pending' in value['disabled_roles']['monitoring']


@pytest.mark.parametrize('field,value',[('sha256',None),('source_commit','observed'),('source_inventory_sha256',''),
    ('receipt','../private'),('architecture','aarch64'),('path','/opt/private'),('argv',['sh','-c','touch /bad']),
    ('unit','unrelated.service'),('health','sh /bad')])
def test_unbound_artifacts_rejected(field, value):
    data = inventory()
    data['artifacts'][0][field] = value
    with pytest.raises(FleetError):
        validate(data)


def test_observation_is_not_deployable():
    observed = load((Path(__file__).parents[1]/'inventory/role-audit.json').read_bytes())
    with pytest.raises(FleetError):
        validate(observed)


def test_exact_input_inventory_and_tamper(tmp_path):
    data = inventory()
    data['artifacts'] = data['artifacts'][:1]
    artifact = data['artifacts'][0]
    content = b'not a real binary - bound fixture content'
    source = dict(source_commit=artifact['source_commit'])
    artifact.update(size=len(content),sha256=digest(content),source_inventory_sha256=digest(canonical(source)))
    binary = tmp_path/artifact['path']
    binary.parent.mkdir()
    binary.write_bytes(content)
    sources = {artifact['id']:source}
    assert check_inputs(data,tmp_path,sources) == {artifact['id']:digest(content)}
    with pytest.raises(FleetError):
        check_inputs(data,tmp_path,{artifact['id']:dict(source,changed=True)})
    binary.write_bytes(content+b'changed')
    with pytest.raises(FleetError):
        check_inputs(data,tmp_path,sources)
