"""Pinned installed OWNER custody successor; no dispatch settlement or capture permit."""
import base64
import json
import os
from pathlib import Path
import re

from control.capture_gate import MARKER
from control_plane import collector_binding
from scripts import control_ha_owner_capture as capture
from scripts import control_ha_owner_runtime as legacy
from scripts.control_ha_live_sqlite import require


BASELINE = 'owner-all-writer-runtime-20261127-v1'
PURPOSE = 'family-connect/owner-runtime-custody/v2/' + BASELINE + '/no-dispatch'
MAGIC = b'FCORUN2\x00'
MANIFEST_SHA256 = '45ee81401504dbad89d61c4e8972557dcd3b1e84423097608e587e6e948ac8d2'
IMAGES = dict(legacy.IMAGES,
    console='sha256:3af9fbf95b36b33f1c0414ac41b84687f502391e311ff0bc35658cbf50da5cb1',
    system_publisher='sha256:35158514371e2a321643dbfe4b64b9a87a9b85b32228a5184d2c95e3b8ac19e8')
FILES = legacy.FILES | {'host-collectors.json', 'image-sources.json', 'pending-history.json'}
GATE_ROOT = '/home/joker/.local/share/family-connect/control-ha/20261125-collector-activation-4sc56eop'
GATES = {'inventory': (GATE_ROOT + '/inventory-gate', 1000),
         'probe': (GATE_ROOT + '/probe-gate', 1000),
         'console': ('/var/lib/family-connect/capture/owner-console', 10001),
         'system_publisher': ('/var/lib/family-connect/capture/owner-publisher', 1000)}
GROUPS = {'root119': ('root', 119), 'root-additional': ('root', None),
          'inventory3': ('inventory', 3), 'inventory12': ('inventory', 12),
          'inventory6': ('inventory', 6), 'inventory-additional': ('inventory', None),
          'probe14': ('probe', 14), 'probe-additional': ('probe', None),
          'support33': ('support', 33), 'support-additional': ('support', None),
          'console': ('console', None), 'system_publisher': ('system_publisher', None)}
HISTORY_UIDS = dict(root=0, support=997, **{role: value[1] for role, value in GATES.items()})


def manifest():
    raw = Path(__file__).with_name('owner_runtime_20261127.json').read_bytes()
    require(capture.digest(raw) == MANIFEST_SHA256, 'RUNTIME_MANIFEST_CHANGED')
    return legacy.document(raw)


def decoded(value, limit=capture.LIMIT):
    require(type(value) is str and len(value) <= 2 * limit, 'CUSTODY_ENCODING_BOUNDS')
    raw = base64.b64decode(value, validate=True)
    require(len(raw) <= limit and base64.b64encode(raw).decode() == value, 'CUSTODY_ENCODING')
    return raw


def pins(value):
    require(type(value) is dict and set(value) == {'.', 'pending', 'admission.lock', 'operations.lock'} and
            all(type(pair) is list and len(pair) == 2 and all(type(number) is int and number > 0 for number in pair)
                for pair in value.values()) and len({tuple(pair) for pair in value.values()}) == 4,
            'CUSTODY_GATE_PINS')


def hosts(raw, expected):
    value = legacy.document(raw)
    require(type(value) is dict and set(value) == set(expected['profiles']), 'HOST_PROFILE_COVERAGE')
    gates = None
    for profile, contract in expected['profiles'].items():
        entry = value[profile]
        require(type(entry) is dict and set(entry) == {'binding', 'sources', 'binding_uid', 'binding_mode'} and
                type(entry['binding_uid']) is int and entry['binding_uid'] == 0 and
                type(entry['binding_mode']) is int and entry['binding_mode'] == 0o644, 'HOST_BINDING_CUSTODY')
        binding_raw = decoded(entry['binding'], 16384)
        binding = legacy.document(binding_raw)
        require(type(binding) is dict and set(binding) == {'schema', 'baseline', 'application', 'uid', 'sources', 'gates'} and
                type(binding['schema']) is int and binding['schema'] == 1 and
                binding['baseline'] == collector_binding.BASELINE and
                binding['application'] == contract['application'] and
                type(binding['uid']) is int and binding['uid'] == contract['uid'] and
                binding['sources'] == contract['sources'] and
                binding_raw == (json.dumps(binding, sort_keys=True, separators=(',', ':')) + '\n').encode(),
                'HOST_BINDING_CHANGED')
        require(type(entry['sources']) is dict and set(entry['sources']) == set(contract['sources']),
                'HOST_SOURCE_COVERAGE')
        for name, digest in contract['sources'].items():
            require(capture.digest(decoded(entry['sources'][name], 256 * 1024)) == digest, 'HOST_SOURCE_CHANGED')
        require(type(binding['gates']) is dict and set(binding['gates']) == {'inventory', 'probe'}, 'HOST_GATE_COVERAGE')
        for role, gate in binding['gates'].items():
            require(type(gate) is dict and set(gate) == {'directory', 'pins'} and
                    gate['directory'] == GATES[role][0], 'HOST_GATE_DIRECTORY')
            pins(gate['pins'])
        require({tuple(pair) for pair in binding['gates']['inventory']['pins'].values()}.isdisjoint(
                tuple(pair) for pair in binding['gates']['probe']['pins'].values()), 'HOST_GATE_ALIAS')
        require(gates is None or gates == binding['gates'], 'HOST_GATE_DISAGREEMENT')
        gates = binding['gates']
    return gates


def history(raw, gates):
    value = legacy.document(raw)
    require(type(value) is dict and set(value) == {'schema', 'groups', 'user_gates'} and
            type(value['schema']) is int and value['schema'] == 1 and value['user_gates'] == gates and
            type(value['groups']) is dict and set(value['groups']) == set(GROUPS), 'HISTORY_COVERAGE')
    seen, counts = set(), {}
    for group, (role, count) in GROUPS.items():
        entries = value['groups'][group]
        require(type(entries) is list and len(entries) <= 4096 and
                (count is None or len(entries) == count), 'HISTORY_PARTITION')
        names = []
        for entry in entries:
            require(type(entry) is dict and set(entry) == {'name', 'body', 'dev', 'ino', 'uid', 'mode', 'mtime_ns'} and
                    type(entry['name']) is str and re.fullmatch('[a-f0-9]{32}', entry['name']) and
                    all(type(entry[field]) is int and entry[field] > 0 for field in ('dev', 'ino', 'mtime_ns')) and
                    type(entry['uid']) is int and entry['uid'] >= 0 and
                    type(entry['mode']) is int and entry['mode'] == 0o600 and decoded(entry['body'], 128) == MARKER,
                    'HISTORY_RECORD')
            require(entry['uid'] == HISTORY_UIDS[role], 'HISTORY_OWNER')
            require((role, entry['name']) not in seen, 'HISTORY_DUPLICATE')
            seen.add((role, entry['name']))
            names.append(entry['name'])
        require(names == sorted(names), 'HISTORY_ORDER')
        counts[group] = len(entries)
    return counts


def unpack(value):
    return legacy.unpack(value, purpose=PURPOSE, names=FILES)


def validate(value):
    files, expected = unpack(value), manifest()
    summary = legacy.validate_files(files, images=IMAGES, names=FILES)
    gates = hosts(files['host-collectors.json'], expected)
    counts = history(files['pending-history.json'], gates)
    sources = legacy.document(files['image-sources.json'])
    require(type(sources) is dict and set(sources) == set(expected['image_sources']), 'IMAGE_SOURCE_COVERAGE')
    for name, digest in expected['image_sources'].items():
        require(capture.digest(decoded(sources[name], 256 * 1024)) == digest, 'IMAGE_SOURCE_CHANGED')
    containers = legacy.document(files['containers.json'])
    for role in ('console', 'system_publisher'):
        item = containers[role]
        require('FC_CONTROL_CAPTURE_GATE=/run/family-connect-capture' in item['environment'], 'RUNTIME_GATE_ENV')
        mounts = [mount for mount in item['mounts'] if mount.get('Destination') == '/run/family-connect-capture']
        require(len(mounts) == 1 and mounts[0].get('Type') == 'bind' and
                mounts[0].get('Source') == GATES[role][0] and mounts[0].get('RW') is True and
                mounts[0].get('Propagation') == 'rprivate', 'RUNTIME_GATE_MOUNT')
    support_mounts = [mount for mount in containers['console']['mounts']
                      if mount.get('Destination') == '/run/family-connect-support']
    require(len(support_mounts) == 1 and support_mounts[0].get('Type') == 'bind' and
            support_mounts[0].get('Source') == '/run/family-connect-support' and
            support_mounts[0].get('RW') is False, 'SUPPORT_RUNTIME_MOUNT')
    return dict(summary, result='OWNER_CURRENT_RUNTIME_OFFLINE_CUSTODY_PASS', baseline=BASELINE,
                host_source=expected['host_source'], image_source=expected['image_source'],
                history=counts, capture_permitted=False, external_work_settled=False)


def build(snapshot, extra_files, started_at_ns, finished_at_ns):
    require(type(snapshot) is dict and set(snapshot) == {'purpose', 'locked_at_ns', 'captured_at_ns',
            'barrier_seconds', 'files', 'activation', 'pg_pair_fence'} and snapshot['purpose'] == capture.PURPOSE and
            snapshot['activation'] is False and snapshot['pg_pair_fence'] is False and
            set(snapshot['files']) == {'synthetic.sqlite', 'panel-aliases.json'} and
            set(extra_files) == FILES - snapshot['files'].keys(), 'CURRENT_SNAPSHOT_SCOPE')
    value = dict(snapshot, purpose=PURPOSE, started_at_ns=started_at_ns, finished_at_ns=finished_at_ns,
                 files=snapshot['files'] | {name: base64.b64encode(raw).decode() for name, raw in extra_files.items()})
    validate(value)
    return value


def seal(value, key):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    validate(value)
    require(type(key) is bytes and len(key) == 32, 'KEY_BOUNDS')
    raw, nonce = capture.encoded(value), os.urandom(12)
    capsule = MAGIC + nonce + AESGCM(key).encrypt(nonce, raw, PURPOSE.encode())
    return capsule, dict(ciphertext_sha256=capture.digest(capsule), document_sha256=capture.digest(raw))


def unseal(capsule, key, checkpoint):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.exceptions import InvalidTag
    require(type(checkpoint) is dict and set(checkpoint) == {'ciphertext_sha256', 'document_sha256'} and
            all(type(pin) is str and re.fullmatch('[a-f0-9]{64}', pin) for pin in checkpoint.values()), 'CHECKPOINT_SHAPE')
    require(type(capsule) is bytes and len(MAGIC) + 28 <= len(capsule) <= legacy.LIMIT + 64 and
            capture.digest(capsule) == checkpoint['ciphertext_sha256'], 'STALE_OR_CHANGED_CAPSULE')
    require(capsule.startswith(MAGIC) and type(key) is bytes and len(key) == 32, 'CAPSULE_FORMAT')
    try:
        raw = AESGCM(key).decrypt(capsule[len(MAGIC):len(MAGIC)+12], capsule[len(MAGIC)+12:], PURPOSE.encode())
    except InvalidTag:
        raise ValueError('CAPSULE_AUTHENTICATION') from None
    require(capture.digest(raw) == checkpoint['document_sha256'], 'DOCUMENT_PIN')
    value = legacy.document(raw)
    require(capture.encoded(value) == raw, 'DOCUMENT_ENCODING')
    validate(value)
    return value


def restore(value, destination):
    summary = validate(value)
    legacy.restore_files(unpack(value), destination)
    return summary


def read_hosts():
    expected, result = manifest(), {}
    for profile, contract in expected['profiles'].items():
        binding = collector_binding.read_regular(Path(contract['binding']), 0, 0o644, 16384)
        sources = {name: collector_binding.read_regular(Path(contract['application']) / name, contract['uid'])
                   for name in contract['sources']}
        result[profile] = dict(binding=base64.b64encode(binding).decode(), binding_uid=0, binding_mode=0o644,
                               sources={name: base64.b64encode(raw).decode() for name, raw in sources.items()})
    raw = capture.encoded(result)
    hosts(raw, expected)
    return raw
