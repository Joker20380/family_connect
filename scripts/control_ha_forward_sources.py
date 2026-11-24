"""Bounded renewal source custody; never imports captured code or follows config paths."""
from pathlib import Path
import re

from scripts.control_ha_import import ImportRejected, digest, encoded, require
from scripts.control_ha_installed_inventory import Reader, Refused
from scripts.control_ha_recovery_bundle import parse

SLOTS = {'RU': 'RU', 'NL1': 'NL', 'NL2': 'NL2'}
REQUIRED_MODULES = frozenset(('credential_renewal.py', 'expired_recovery.py', 'grant_cutover.py',
    'maintenance_policy.py', 'node.py', 'offline_handoff.py', 'production_controller.py',
    'production_node.py', 'production_transport.py', 'renewal_cli.py', 'renewal_health.py',
    'runtime_controller.py', 'scheduled_evaluate.py', 'gateway_set.py'))
MAX_FILE = 1024 * 1024
MAX_TOTAL = 16 * MAX_FILE
MAX_FILES = 128


def configuration(raw):
    require(type(raw) is bytes and 0 < len(raw) <= MAX_FILE, 'FORWARD_CONFIGURATION_BOUNDS')
    document = parse(raw)
    require(type(document) is dict, 'FORWARD_CONFIGURATION_SHAPE')
    declared = document.get('source_files')
    require(type(declared) is dict and REQUIRED_MODULES <= set(declared) and len(declared) <= MAX_FILES,
            'FORWARD_SOURCE_MANIFEST')
    require(all(type(name) is str and re.fullmatch(r'[a-z][a-z0-9_]*\.py', name) and
                type(value) is str and re.fullmatch('[a-f0-9]{64}', value) for name, value in declared.items()),
            'FORWARD_SOURCE_MANIFEST')
    require(document.get('source_sha256') == digest(encoded(declared)), 'FORWARD_SOURCE_AGGREGATE')
    return document


def inspect(materials):
    require(type(materials) is dict and set(materials) == set(SLOTS), 'FORWARD_SOURCE_MATERIAL_COVERAGE')
    copied, identities, total = {}, {}, 0
    for node, material in dict(materials).items():
        require(type(material) is dict and set(material) == {'configuration', 'files'}, 'FORWARD_SOURCE_MATERIAL_FIELDS')
        material = dict(material)
        raw, files = material['configuration'], material['files']
        require(type(files) is dict and len(files) <= MAX_FILES, 'FORWARD_SOURCE_FILES')
        files = dict(files)
        document = configuration(raw)
        require(set(files) == set(document['source_files']), 'FORWARD_SOURCE_FILE_COVERAGE')
        require(all(type(value) is bytes and 0 < len(value) <= MAX_FILE for value in files.values()),
                'FORWARD_SOURCE_FILE_BOUNDS')
        total += len(raw) + sum(len(value) for value in files.values())
        require(total <= MAX_TOTAL, 'FORWARD_SOURCE_TOTAL_BOUNDS')
        require({name: digest(value) for name, value in files.items()} == document['source_files'],
                'FORWARD_SOURCE_FILE_HASH')
        copied[node] = dict(configuration=raw, files=files)
        identities[node] = dict(runtime_sha256=document['source_sha256'], configuration_sha256=digest(raw))
    return identities, copied


def verify(materials, expected, *, anchor, gateway_ids):
    identities, copied = inspect(materials)
    require(identities == expected, 'FORWARD_SOURCE_BYTES_MISMATCH')
    require(type(anchor) is bytes and len(anchor) == 32, 'FORWARD_SOURCE_ANCHOR')
    require(type(gateway_ids) is dict and set(gateway_ids) == {'NL', 'NL2'} and
            all(type(value) is str and re.fullmatch('[a-f0-9]{32}', value) for value in gateway_ids.values()) and
            gateway_ids['NL'] != gateway_ids['NL2'], 'FORWARD_SOURCE_GATEWAYS')
    gateway_ids = dict(gateway_ids)
    for node, material in copied.items():
        document = configuration(material['configuration'])
        require(type(document.get('schema')) is int and document['schema'] == 1 and
                document.get('role') == ('RU' if node == 'RU' else 'NL') and
                document.get('gateway_slot') == SLOTS[node], 'FORWARD_SOURCE_NODE_BINDING')
        require(document.get('gateway_ids') == gateway_ids, 'FORWARD_SOURCE_GATEWAY_BINDING')
        require(document.get('anchor_sha256') == digest(anchor), 'FORWARD_SOURCE_ANCHOR')
    return copied


def collect(config_path, runtime):
    try:
        reader = Reader()
        raw = reader.raw(Path(config_path))
        declared = configuration(raw)['source_files']
        runtime = Path(runtime)
        names = reader.names(runtime, 256)
        require({name for name in names if name.endswith('.py')} == set(declared),
                'FORWARD_SOURCE_DIRECTORY_COVERAGE')
        files = {name: reader.raw(runtime / name) for name in sorted(declared)}
        require({name: digest(value) for name, value in files.items()} == declared, 'FORWARD_SOURCE_FILE_HASH')
        reader.verify()
        return dict(configuration=raw, files=files)
    except ImportRejected:
        raise
    except (Refused, OSError, ValueError, TypeError, OverflowError):
        raise ImportRejected('FORWARD_SOURCE_READ_REFUSED') from None
