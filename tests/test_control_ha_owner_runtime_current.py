import base64
from copy import deepcopy
import json
import os
from pathlib import Path

import pytest

from control.capture_gate import Gate, GateError, MARKER, initialize
from scripts import control_ha_owner_runtime as legacy
from scripts import control_ha_owner_runtime_current as current
from scripts.control_ha_owner_capture import digest, encoded
from scripts.control_ha_installed_inventory import Refused
from test_control_ha_owner_runtime import bundle, source


ROOT = Path(__file__).resolve().parents[1]


def body(raw):
    return base64.b64encode(raw).decode()


def replace_file(value, name, document):
    value['files'][name] = body(encoded(document))


def gate_pins(offset):
    return {name: [10, offset + number] for number, name in enumerate(
        ('.', 'pending', 'admission.lock', 'operations.lock'))}


@pytest.fixture
def current_bundle(bundle):
    value = deepcopy(bundle)
    files = legacy.unpack(value)
    value['purpose'] = current.PURPOSE
    expected = current.manifest()
    gates = {role: dict(directory=current.GATES[role][0], pins=gate_pins(offset))
             for role, offset in (('inventory', 20), ('probe', 40))}
    hosts = {}
    overrides = {
        ('inventory', 'control_plane/probe_network.py'): 'probe_legacy.py',
        ('manual', 'control_plane/apps/console/transport_collector.py'): 'transport_collector_legacy.py',
        ('manual', 'control_plane/apps/console/technical_metadata_collector.py'): 'metadata_collector_legacy.py',
        ('manual', 'control_plane/collect_technical_metadata.py'): 'technical_metadata_legacy_mandatory.py',
    }
    for profile, contract in expected['profiles'].items():
        sources = {}
        for name, pin in contract['sources'].items():
            override = overrides.get((profile, name))
            path = ROOT / 'tests/fixtures/owner_upgrade' / override if override else ROOT / name
            raw = path.read_bytes()
            assert digest(raw) == pin
            sources[name] = body(raw)
        binding = dict(schema=1, baseline='owner-user-collectors-mandatory-v1', uid=1000,
                       application=contract['application'], sources=contract['sources'], gates=gates)
        raw = (json.dumps(binding, sort_keys=True, separators=(',', ':')) + '\n').encode()
        hosts[profile] = dict(binding=body(raw), sources=sources, binding_uid=0, binding_mode=0o644)
    containers = legacy.document(files['containers.json'])
    for role, image in current.IMAGES.items():
        containers[role]['image'] = image
        if role != 'postgres':
            containers[role]['environment'].append('FC_CONTROL_CAPTURE_GATE=/run/family-connect-capture')
            containers[role]['mounts'].append(dict(Type='bind', Source=current.GATES[role][0],
                Destination='/run/family-connect-capture', RW=True, Propagation='rprivate'))
    containers['console']['mounts'].append(dict(Type='bind', Source='/run/family-connect-support',
        Destination='/run/family-connect-support', RW=False, Propagation='rprivate'))
    files['containers.json'] = encoded(containers)
    files['host-collectors.json'] = encoded(hosts)
    files['image-sources.json'] = encoded({name: body((ROOT / name).read_bytes()) for name in expected['image_sources']})
    groups, number = {}, 1
    for group, (role, count) in current.GROUPS.items():
        groups[group] = []
        count = count if count is not None else 2
        for unused in range(count):
            groups[group].append(dict(name=f'{number:032x}', body=body(MARKER), dev=10, ino=number,
                uid=current.HISTORY_UIDS[role], mode=0o600, mtime_ns=number))
            number += 1
    files['pending-history.json'] = encoded(dict(schema=1, groups=groups, user_gates=gates))
    files['origins.json'] = encoded({name: '/fixture/' + name for name in current.FILES - {'origins.json'}})
    value['files'] = {name: body(raw) for name, raw in files.items()}
    return value


def test_exact_current_roundtrip_is_not_capture_permit(current_bundle, bundle, source, tmp_path):
    before = (source[0] / 'registry.sqlite3').read_bytes()
    report = current.validate(current_bundle)
    assert report['baseline'] == current.BASELINE and report['files'] == 23
    assert not report['capture_permitted'] and not report['external_work_settled']
    assert report['history']['inventory3'] == 3 and report['history']['root119'] == 119
    key = os.urandom(32)
    capsule, checkpoint = current.seal(current_bundle, key)
    assert b'p' * 40 not in capsule and b's' * 64 not in capsule
    assert current.unseal(capsule, key, checkpoint) == current_bundle
    assert current.restore(current_bundle, tmp_path / 'restored') == report
    assert all(path.stat().st_mode & 0o777 == 0o600 for path in (tmp_path / 'restored').iterdir())
    assert (source[0] / 'registry.sqlite3').read_bytes() == before
    with pytest.raises(ValueError, match='DOCUMENT_SCOPE'):
        legacy.validate(current_bundle)
    with pytest.raises(ValueError, match='DOCUMENT_SCOPE'):
        current.validate(bundle)
    with pytest.raises(ValueError, match='CAPSULE_FORMAT'):
        legacy.unseal(capsule, key, checkpoint)


@pytest.mark.parametrize('profile', ('manual', 'inventory', 'probe'))
@pytest.mark.parametrize('fault', ('missing-source', 'changed-source', 'rebound-source', 'missing-binding',
    'wrong-root', 'binding-mode', 'binding-uid', 'gate-directory', 'gate-pins', 'gate-alias', 'foreign-binding',
    'noncanonical', 'duplicate', 'unknown-baseline'))
def test_host_unknown_changed_incomplete_refuse(current_bundle, profile, fault):
    hosts = legacy.document(current.unpack(current_bundle)['host-collectors.json'])
    entry = hosts[profile]
    binding = legacy.document(current.decoded(entry['binding']))
    name = next(iter(entry['sources']))
    if fault == 'missing-source': del entry['sources'][name]
    elif fault == 'changed-source': entry['sources'][name] = body(b'changed')
    elif fault == 'rebound-source':
        entry['sources'][name] = body(b'changed')
        binding['sources'][name] = digest(b'changed')
    elif fault == 'missing-binding': del entry['binding']
    elif fault == 'wrong-root': binding['application'] += '-replaced'
    elif fault == 'binding-mode': entry['binding_mode'] = 0o666
    elif fault == 'binding-uid': entry['binding_uid'] = 1000
    elif fault == 'gate-directory': binding['gates']['inventory']['directory'] += '-replaced'
    elif fault == 'gate-pins': binding['gates']['inventory']['pins']['.'][0] = 0
    elif fault == 'gate-alias': binding['gates']['inventory']['pins'] = binding['gates']['probe']['pins']
    elif fault == 'foreign-binding': binding['gates']['inventory']['pins']['.'][1] += 1000
    elif fault == 'unknown-baseline': binding['baseline'] = 'future'
    if 'binding' in entry:
        raw = (json.dumps(binding, sort_keys=True, separators=(',', ':')) + '\n').encode()
        if fault == 'noncanonical': raw += b'\n'
        elif fault == 'duplicate': raw = b'{"schema":1,' + raw[1:]
        entry['binding'] = body(raw)
    replace_file(current_bundle, 'host-collectors.json', hosts)
    with pytest.raises((ValueError, Refused)): current.validate(current_bundle)


@pytest.mark.parametrize('fault', ('missing', 'changed', 'legacy-image', 'unknown-image', 'gate-env',
    'gate-mount', 'gate-rw', 'gate-propagation', 'duplicate-mount', 'support-mount', 'support-rw'))
def test_images_and_effective_gate_refuse_drift(current_bundle, fault):
    files = current.unpack(current_bundle)
    sources = legacy.document(files['image-sources.json'])
    containers = legacy.document(files['containers.json'])
    item = containers['console']
    if fault == 'missing': del sources[next(iter(sources))]
    elif fault == 'changed': sources[next(iter(sources))] = body(b'changed')
    elif fault == 'legacy-image': item['image'] = legacy.IMAGES['console']
    elif fault == 'unknown-image': item['image'] = 'sha256:' + 'f' * 64
    elif fault == 'gate-env': item['environment'] = [value for value in item['environment'] if not value.startswith('FC_CONTROL_CAPTURE_GATE=')]
    elif fault == 'gate-mount': item['mounts'] = []
    elif fault == 'gate-rw': item['mounts'][0]['RW'] = False
    elif fault == 'gate-propagation': item['mounts'][0]['Propagation'] = 'shared'
    elif fault == 'duplicate-mount': item['mounts'] *= 2
    elif fault == 'support-mount': item['mounts'].pop()
    elif fault == 'support-rw': item['mounts'][-1]['RW'] = True
    replace_file(current_bundle, 'image-sources.json', sources)
    replace_file(current_bundle, 'containers.json', containers)
    with pytest.raises(ValueError): current.validate(current_bundle)


@pytest.mark.parametrize('fault', ('missing-group', 'merge-originals', 'erase-marker', 'changed-body',
    'duplicate-marker', 'bad-name', 'mode', 'uid', 'metadata', 'foreign-gates', 'reorder'))
def test_history_partitions_are_not_settlement(current_bundle, fault):
    history = legacy.document(current.unpack(current_bundle)['pending-history.json'])
    groups = history['groups']
    entry = groups['inventory3'][0]
    if fault == 'missing-group': del groups['root119']
    elif fault == 'merge-originals': groups['inventory3'] += groups.pop('inventory12')
    elif fault == 'erase-marker': groups['support33'].pop()
    elif fault == 'changed-body': entry['body'] = body(b'completed\n')
    elif fault == 'duplicate-marker': groups['inventory-additional'].append(deepcopy(entry))
    elif fault == 'bad-name': entry['name'] = '../../escape'
    elif fault == 'mode': entry['mode'] = 0o644
    elif fault == 'uid': entry['uid'] = 0
    elif fault == 'metadata': entry['ino'] = -1
    elif fault == 'foreign-gates': history['user_gates']['probe']['pins']['.'][1] += 100
    elif fault == 'reorder': groups['inventory3'].reverse()
    replace_file(current_bundle, 'pending-history.json', history)
    with pytest.raises(ValueError): current.validate(current_bundle)


def test_unknown_outer_scope_and_stale_checkpoint_refuse(current_bundle):
    key = os.urandom(32)
    capsule, checkpoint = current.seal(current_bundle, key)
    changed = deepcopy(current_bundle)
    groups = legacy.document(current.unpack(changed)['pending-history.json'])
    groups['groups']['root-additional'][0]['mtime_ns'] += 1
    replace_file(changed, 'pending-history.json', groups)
    newer, new_checkpoint = current.seal(changed, key)
    with pytest.raises(ValueError, match='STALE_OR_CHANGED_CAPSULE'):
        current.unseal(newer, key, checkpoint)
    assert current.unseal(newer, key, new_checkpoint) == changed
    with pytest.raises(ValueError, match='CAPSULE_AUTHENTICATION'):
        current.unseal(capsule, os.urandom(32), checkpoint)
    for field in ('activation', 'pg_pair_fence'):
        changed = deepcopy(current_bundle)
        changed[field] = True
        with pytest.raises(ValueError): current.validate(changed)


def test_current_custody_does_not_relax_gate_drain(current_bundle, tmp_path):
    gate = initialize(tmp_path / 'gate')
    marker = gate.directory / 'pending' / ('1' * 32)
    marker.write_bytes(MARKER)
    marker.chmod(0o600)
    before = marker.stat(), marker.read_bytes()
    assert current.validate(current_bundle)['external_work_settled'] is False
    with pytest.raises(GateError, match='UNSETTLED_OPERATION'):
        with Gate(gate.directory).drain(0.1): pytest.fail('ambiguous work admitted')
    assert (marker.stat(), marker.read_bytes()) == before


def test_shared_restore_rejects_path_escape(tmp_path):
    with pytest.raises(ValueError, match='RESTORE_FILE_NAMES'):
        legacy.restore_files({'../escape': b'no'}, tmp_path / 'restored')
    assert not (tmp_path / 'restored').exists()


def test_live_selector_is_explicit_and_unknown_refuses_before_docker(current_bundle, monkeypatch):
    from scripts import control_ha_owner_collect as collect
    containers = legacy.document(current.unpack(current_bundle)['containers.json'])
    observed = [dict(Name=value['name'], Id=value['id'], Image=value['image'], State=dict(Running=True,
        StartedAt=value['started']), Config=dict(Env=value['environment'], Cmd=value['command'],
        Entrypoint=value['entrypoint'], Labels=value['labels']), Mounts=value['mounts']) for value in containers.values()]
    assert collect.selected(observed, baseline=current.BASELINE) == containers
    with pytest.raises(ValueError, match='CONTAINER_IMAGE'): collect.selected(observed)
    monkeypatch.setattr(collect.subprocess, 'run', lambda *args, **kwargs: pytest.fail('unqualified dispatch'))
    with pytest.raises(ValueError, match='OWNER_BASELINE_UNKNOWN'): collect.inspect(baseline='unknown')
    with pytest.raises(ValueError, match='OWNER_EXTRA_READER'): collect.collect(observed, baseline=current.BASELINE)
    with pytest.raises(ValueError, match='OWNER_EXTRA_COVERAGE'):
        collect.collect(observed, baseline=current.BASELINE, extra_reader=lambda: {})


def test_native_current_command_is_private_offline_and_explicit(tmp_path):
    from scripts.control_ha_owner_qualify import command
    arguments = command(tmp_path, 'fc-ha-owner-current', baseline=current.BASELINE)
    assert arguments[arguments.index('--entrypoint') + 1:] == ['python', current.IMAGES['console'], '-B', '-']
    assert arguments[arguments.index('--network') + 1] == 'none'
    assert arguments.count('--mount') == 1 and '--read-only' in arguments
    assert not any('docker.sock' in argument or '/etc/family-connect' in argument for argument in arguments)
    with pytest.raises(ValueError, match='OWNER_BASELINE_UNKNOWN'): command(tmp_path, 'fc-ha-owner-test', baseline='new')
