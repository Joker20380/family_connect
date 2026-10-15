import copy
import json
from pathlib import Path

import pytest

from configure import BASE_SOURCE_MAP, project


@pytest.mark.parametrize('role', ['RU', 'NL'])
def test_config_projection_changes_only_source_identity(role):
    manifest = json.loads((Path(__file__).with_name('source-manifest.json')).read_bytes())
    node = dict(schema=1, role=role, live='/fixture/live', state='/fixture/state', database='/fixture/database',
        anchor='/fixture/anchor', anchor_sha256='a'*64, api_archive='/fixture/api', api_sha256='b'*64,
        source_files=manifest['base_management_sources'], source_sha256=BASE_SOURCE_MAP)
    controller = dict(schema=1, node_config='/fixture/node.json', coordinator_state='/fixture/coordinator',
        nl_source_sha256=BASE_SOURCE_MAP, ssh=dict(key='/fixture/ssh', known_hosts='/fixture/hosts'),
        approved_leaf_crl_schedule=True) if role == 'RU' else None
    before = copy.deepcopy(node)
    successor, coordinator = project(node, controller)
    assert node == before
    assert {name for name in node if node[name] != successor[name]} == {'source_files', 'source_sha256'}
    if controller:
        assert {name for name in controller if controller[name] != coordinator[name]} == {'nl_source_sha256'}
    assert project(successor, coordinator) == (successor, coordinator)
    node['source_sha256'] = 'c'*64
    with pytest.raises(AssertionError):
        project(node, controller)


def test_config_unknown_scope_rejected():
    with pytest.raises(AssertionError):
        project(dict(schema=1, role='OTHER'))
