from copy import deepcopy
from pathlib import Path
import os
import shutil

import pytest

from scripts import control_ha_forward_sources as sources
from scripts.control_ha_import import ImportRejected, digest, encoded
from scripts.control_ha_recovery_bundle import parse
from scripts.package_credential_renewal import MODULES

ANCHOR = b'a' * 32
GATEWAYS = {'NL': '1' * 32, 'NL2': '2' * 32}


def materials_for(anchor, gateway_ids):
    directory = Path(__file__).resolve().parents[1] / 'deploy/friends/restricted/maintenance'
    files = {name: (directory / name).read_bytes() for name in MODULES}
    hashes = {name: digest(raw) for name, raw in files.items()}
    return {node: dict(files=dict(files), configuration=encoded(dict(schema=1,
        role='RU' if node == 'RU' else 'NL', gateway_slot=slot, gateway_ids=gateway_ids,
        anchor_sha256=digest(anchor), source_files=hashes, source_sha256=digest(encoded(hashes)),
        live='/not-followed/live', state='/not-followed/state', database='/not-followed/access.db',
        anchor='/not-followed/anchor.pub', api_archive='/not-followed/api.pyz', api_sha256='f' * 64,
        service_units=['synthetic.service'], admission_mode='all_activated')))
        for node, slot in sources.SLOTS.items()}


@pytest.fixture
def materials():
    return materials_for(ANCHOR, GATEWAYS)


def check(materials, expected=None):
    if expected is None:
        expected = sources.inspect(materials)[0]
    return sources.verify(materials, expected, anchor=ANCHOR, gateway_ids=GATEWAYS)


def change_config(materials, node, change):
    document = parse(materials[node]['configuration'])
    change(document)
    materials[node]['configuration'] = encoded(document)


def test_native_modules_and_exact_configuration_are_retained(materials):
    before = deepcopy(materials)
    result = check(materials)
    assert result == before == materials
    materials['RU']['files']['node.py'] = b'changed'
    materials['NL1']['configuration'] += b' '
    assert result == before


@pytest.mark.parametrize('node', ['RU', 'NL1', 'NL2', 'extra'])
def test_exact_fleet_coverage(materials, node):
    if node == 'extra':
        materials[node] = materials['RU']
    else:
        del materials[node]
    with pytest.raises(ImportRejected, match='FORWARD_SOURCE_MATERIAL_COVERAGE'):
        check(materials)


@pytest.mark.parametrize('node', sources.SLOTS)
@pytest.mark.parametrize('field', ['configuration', 'files'])
def test_material_fields_cannot_be_omitted(materials, node, field):
    del materials[node][field]
    with pytest.raises(ImportRejected, match='FORWARD_SOURCE_MATERIAL_FIELDS'):
        check(materials)


@pytest.mark.parametrize('node', sources.SLOTS)
@pytest.mark.parametrize('kind', ['changed', 'missing', 'extra'])
def test_every_module_is_bound(materials, node, kind):
    if kind == 'changed':
        materials[node]['files']['node.py'] += b'\n'
    elif kind == 'missing':
        del materials[node]['files']['node.py']
    else:
        materials[node]['files']['unapproved.py'] = b'pass'
    with pytest.raises(ImportRejected, match='FORWARD_SOURCE_FILE_(HASH|COVERAGE)'):
        check(materials)


@pytest.mark.parametrize('node', sources.SLOTS)
def test_exact_config_bytes_not_just_json_meaning(materials, node):
    expected = sources.inspect(materials)[0]
    materials[node]['configuration'] += b' '
    with pytest.raises(ImportRejected, match='FORWARD_SOURCE_BYTES_MISMATCH'):
        check(materials, expected)


@pytest.mark.parametrize('node', sources.SLOTS)
@pytest.mark.parametrize('change', [dict(schema=True), dict(schema=2), dict(role='other'),
    dict(gateway_slot='other'), dict(gateway_ids=GATEWAYS | {'NL2': '3' * 32}), dict(anchor_sha256='0' * 64)])
def test_new_pins_do_not_authorize_wrong_node_or_trust(materials, node, change):
    change_config(materials, node, lambda value: value.update(change))
    with pytest.raises(ImportRejected, match='FORWARD_SOURCE_(NODE_BINDING|GATEWAY_BINDING|ANCHOR)'):
        check(materials)


def test_swapping_secondary_nodes_cannot_be_reauthorized(materials):
    materials['NL1'], materials['NL2'] = materials['NL2'], materials['NL1']
    with pytest.raises(ImportRejected, match='FORWARD_SOURCE_NODE_BINDING'):
        check(materials)


@pytest.mark.parametrize('name', ['../escape.py', '/absolute.py', 'nested/module.py', '.hidden.py', 'node.py\n'])
def test_source_names_cannot_escape_runtime(materials, name):
    change_config(materials, 'RU', lambda value: value['source_files'].update({name: 'a' * 64}))
    with pytest.raises(ImportRejected, match='FORWARD_SOURCE_MANIFEST'):
        check(materials)


@pytest.mark.parametrize('kind', ['empty-manifest', 'incomplete', 'aggregate', 'hash', 'duplicate-json', 'nonfinite'])
def test_malformed_or_incomplete_configuration_refuses(materials, kind):
    def change(value):
        if kind == 'empty-manifest':
            value['source_files'] = {}
        elif kind == 'incomplete':
            del value['source_files']['runtime_controller.py']
        elif kind == 'aggregate':
            value['source_sha256'] = '0' * 64
        else:
            value['source_files']['node.py'] = 'BAD'
    if kind == 'duplicate-json':
        materials['RU']['configuration'] = b'{"source_files":{},"source_files":{}}'
    elif kind == 'nonfinite':
        materials['RU']['configuration'] = b'{"source_files":NaN}'
    else:
        change_config(materials, 'RU', change)
    with pytest.raises(ImportRejected):
        check(materials)


@pytest.mark.parametrize('field', ['configuration', 'module'])
@pytest.mark.parametrize('raw', [b'', b' ' * (sources.MAX_FILE + 1), 'not-bytes', bytearray(b'bytes')])
def test_bounds_and_immutable_bytes(materials, field, raw):
    if field == 'configuration':
        materials['RU'][field] = raw
    else:
        materials['RU']['files']['node.py'] = raw
    with pytest.raises(ImportRejected):
        check(materials)


def test_total_size_is_bounded(materials, monkeypatch):
    monkeypatch.setattr(sources, 'MAX_TOTAL', 100)
    with pytest.raises(ImportRejected, match='FORWARD_SOURCE_TOTAL_BOUNDS'):
        check(materials)


@pytest.fixture
def captured(materials, tmp_path):
    runtime = tmp_path / 'runtime'
    runtime.mkdir()
    for name, raw in materials['RU']['files'].items():
        (runtime / name).write_bytes(raw)
    config_path = tmp_path / 'node.json'
    config_path.write_bytes(materials['RU']['configuration'])
    return config_path, runtime, materials['RU']


def test_collect_never_executes_sources_or_follows_configuration_paths(captured, tmp_path):
    config_path, runtime, material = captured
    sentinel = tmp_path / 'EXECUTED'
    raw = f'from pathlib import Path\nPath({str(sentinel)!r}).touch()\nraise RuntimeError()'.encode()
    (runtime / 'node.py').write_bytes(raw)
    material['files']['node.py'] = raw
    document = parse(material['configuration'])
    document['source_files']['node.py'] = digest(raw)
    document['source_sha256'] = digest(encoded(document['source_files']))
    config_path.write_bytes(encoded(document))
    material['configuration'] = config_path.read_bytes()
    result = sources.collect(config_path, runtime)
    shutil.rmtree(runtime)
    config_path.unlink()
    assert result == material
    assert not sentinel.exists()


@pytest.mark.parametrize('kind', ['symlink-file', 'hardlink-file', 'symlink-directory', 'symlink-config', 'fifo', 'extra'])
def test_collector_refuses_unsafe_inputs(captured, tmp_path, kind):
    config_path, runtime, _ = captured
    module = runtime / 'node.py'
    if kind == 'extra':
        (runtime / 'hidden.py').write_bytes(b'pass')
    elif kind == 'symlink-directory':
        alias = tmp_path / 'alias'
        alias.symlink_to(runtime, target_is_directory=True)
        runtime = alias
    elif kind == 'symlink-config':
        alias = tmp_path / 'alias.json'
        alias.symlink_to(config_path)
        config_path = alias
    else:
        target = tmp_path / 'target.py'
        module.rename(target)
        if kind == 'symlink-file':
            module.symlink_to(target)
        elif kind == 'hardlink-file':
            os.link(target, module)
        else:
            os.mkfifo(module)
    with pytest.raises(ImportRejected):
        sources.collect(config_path, runtime)


@pytest.mark.parametrize('kind', ['module', 'configuration', 'directory'])
def test_collector_rechecks_observed_metadata(captured, monkeypatch, kind):
    config_path, runtime, _ = captured
    original = sources.Reader.verify
    def verify(reader):
        if kind == 'module':
            (runtime / 'node.py').write_bytes(b'changed')
        elif kind == 'configuration':
            config_path.write_bytes(b'changed')
        else:
            (runtime / 'extra.py').write_bytes(b'changed')
        return original(reader)
    monkeypatch.setattr(sources.Reader, 'verify', verify)
    with pytest.raises(ImportRejected, match='FORWARD_SOURCE_READ_REFUSED'):
        sources.collect(config_path, runtime)
