"""Private offline readback only; cached leases are not new authority."""
import base64
from contextlib import closing
import io
import ipaddress
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import stat
import tarfile
import uuid

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from control.friends import transport_policy as policy
from scripts import control_ha_node_capture as capture
from scripts.control_ha_installed_inventory import Reader, pairs
from scripts.control_ha_live_sqlite import require

MAGIC = b'FCNODE1\x00'
LIMIT = 9 * capture.LIMIT + 32768
PEER_SCHEMA = [
    ('index', 'sqlite_autoindex_peers_1', 'peers', None),
    ('table', 'peers', 'peers', 'CREATE TABLE peers (id INTEGER PRIMARY KEY AUTOINCREMENT, public TEXT UNIQUE NOT NULL)'),
    ('table', 'sqlite_sequence', 'sqlite_sequence', 'CREATE TABLE sqlite_sequence(name,seq)'),
]


def document(raw):
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda value: require(False, 'NONFINITE_JSON'))


def unpack(raw):
    require(type(raw) is bytes and 0 < len(raw) <= LIMIT, 'ARCHIVE_BOUNDS')
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:') as bundle:
        members = bundle.getmembers()
        expected = set(capture.FILES) | {'peers.sqlite', 'manifest.json'}
        require(len(members) == len(expected) and {entry.name for entry in members} == expected, 'ARCHIVE_COVERAGE')
        require(all(entry.isfile() and entry.sparse is None and not entry.pax_headers and
                    0 < entry.size <= (16384 if entry.name == 'manifest.json' else capture.LIMIT)
                    for entry in members), 'ARCHIVE_ENTRY')
        files = {entry.name: bundle.extractfile(entry).read() for entry in members}
    manifest = document(files.pop('manifest.json'))
    require(type(manifest) is dict and set(manifest) == {'purpose', 'slot', 'node', 'boot', 'monotonic',
            'locked_at_ns', 'captured_at_ns', 'barrier_seconds', 'deadline_seconds', 'fleet_fence', 'activation', 'files'},
            'MANIFEST_SHAPE')
    require(manifest['purpose'] == capture.PURPOSE and manifest['slot'] in capture.NODES and
            manifest['node'] == capture.NODES[manifest['slot']] and manifest['fleet_fence'] is False and
            manifest['activation'] is False, 'CAPTURE_SCOPE')
    require(all(type(manifest[name]) in (int, float) and math.isfinite(manifest[name]) and manifest[name] >= 0
                for name in ('barrier_seconds', 'deadline_seconds', 'monotonic')) and
            manifest['barrier_seconds'] < capture.SECONDS and manifest['deadline_seconds'] == capture.SECONDS,
            'CAPTURE_DEADLINE')
    require(all(type(manifest[name]) is int for name in ('locked_at_ns', 'captured_at_ns')) and
            0 < manifest['locked_at_ns'] <= manifest['captured_at_ns'] < manifest['locked_at_ns'] + capture.SECONDS * 1e9,
            'CAPTURE_TIME')
    require(str(uuid.UUID(manifest['boot'])) == manifest['boot'], 'CAPTURE_BOOT')
    require(type(manifest['files']) is dict and set(manifest['files']) == set(files), 'FILE_COVERAGE')
    for name, body in files.items():
        require(manifest['files'][name] == dict(bytes=len(body), sha256=capture.digest(body)), 'FILE_PIN')
    for name, expected in zip(('gateway.py', 'transport.pyz'), capture.SOURCES[manifest['slot']]):
        require(capture.digest(files[name]) == expected, 'INSTALLED_SOURCE_CHANGED')
    return files, manifest


def seal(raw, key):
    unpack(raw)
    require(type(key) is bytes and len(key) == 32, 'KEY_BOUNDS')
    nonce = os.urandom(12)
    capsule = MAGIC + nonce + AESGCM(key).encrypt(nonce, raw, capture.PURPOSE.encode())
    return capsule, dict(ciphertext_sha256=capture.digest(capsule), archive_sha256=capture.digest(raw))


def unseal(capsule, key, checkpoint):
    require(type(checkpoint) is dict and set(checkpoint) == {'ciphertext_sha256', 'archive_sha256'} and
            all(type(value) is str and re.fullmatch('[a-f0-9]{64}', value) for value in checkpoint.values()),
            'CHECKPOINT_SHAPE')
    require(type(capsule) is bytes and len(MAGIC) + 28 <= len(capsule) <= LIMIT + 64 and
            capture.digest(capsule) == checkpoint['ciphertext_sha256'], 'STALE_OR_CHANGED_CAPSULE')
    require(capsule.startswith(MAGIC) and type(key) is bytes and len(key) == 32, 'CAPSULE_FORMAT')
    try:
        raw = AESGCM(key).decrypt(capsule[len(MAGIC):len(MAGIC)+12], capsule[len(MAGIC)+12:], capture.PURPOSE.encode())
    except InvalidTag:
        raise ValueError('CAPSULE_AUTHENTICATION') from None
    require(capture.digest(raw) == checkpoint['archive_sha256'], 'ARCHIVE_PIN')
    return unpack(raw)


def validate(files, manifest):
    settings = document(files['settings.json'])
    network = ipaddress.IPv4Network('10.84.0.0/16' if manifest['slot'] == 'RU' else '10.83.0.0/16')
    require(type(settings) is dict and set(settings) == {'network', 'address', 'external'} and
            settings['network'] == str(network) and settings['address'] == str(network[1]) + '/16' and
            type(settings['external']) is str and re.fullmatch('[A-Za-z0-9_-]{1,15}', settings['external']), 'SETTINGS')
    with closing(sqlite3.connect(':memory:')) as database:
        database.deserialize(files['peers.sqlite'])
        database.execute('PRAGMA trusted_schema=OFF')
        database.execute('PRAGMA query_only=ON')
        database.set_progress_handler(lambda: 1, 2000000)
        require(database.execute('PRAGMA quick_check').fetchall() == [('ok',)] and
                database.execute('SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name').fetchall()
                == PEER_SCHEMA, 'ALLOCATOR_SCHEMA')
        require(database.execute('PRAGMA user_version').fetchone() == (0,) and
                database.execute('PRAGMA application_id').fetchone() == (0,) and
                database.execute('PRAGMA encoding').fetchone() == ('UTF-8',), 'ALLOCATOR_VERSION')
        peers = database.execute('SELECT id,public FROM peers ORDER BY id LIMIT 20001').fetchall()
        sequences = database.execute('SELECT name,seq FROM sqlite_sequence').fetchall()
    require(0 < len(peers) <= 20000 and all(type(index) is int and 1 <= index < network.num_addresses - 2 and
            type(public) is str and len(base64.b64decode(public, validate=True)) == 32 for index, public in peers),
            'ALLOCATOR_BINDINGS')
    require(len(sequences) == 1 and sequences[0][0] == 'peers' and type(sequences[0][1]) is int and
            max(index for index, public in peers) <= sequences[0][1] < network.num_addresses - 2, 'ALLOCATOR_FLOOR')
    require(document(files['enforcement.json']) == dict(schema=1, profile=policy.PROFILE,
            node=manifest['node'], enabled=True), 'RECEIVER_CONFIG')
    state = document(files['state.json'])
    require(type(state) is dict and set(state) == {'schema', 'node', 'records', 'observed_at'} and
            type(state['schema']) is int and state['schema'] == 1 and state['node'] == manifest['node'] and
            type(state['observed_at']) is int and 0 <= state['observed_at'] <= manifest['captured_at_ns'] / 1e9 + 5 and
            type(state['records']) is dict and len(state['records']) <= 10000, 'RECEIVER_STATE')
    keys, users = set(), set()
    for device, cached in state['records'].items():
        require(type(cached) is dict and set(cached) == {'decision', 'boot', 'deadline', 'applied', 'prepared'} and
                str(uuid.UUID(cached['boot'])) == cached['boot'] and type(cached['deadline']) in (int, float) and
                math.isfinite(cached['deadline']) and 0 <= cached['deadline'] < 2**53 and
                (cached['prepared'] is None or type(cached['prepared']) is str and
                 re.fullmatch('[a-f0-9]{64}', cached['prepared'])), 'RECEIVER_CACHE')
        decision = cached['decision']
        policy.validate(dict(schema=1, profile=policy.PROFILE, node=manifest['node'],
            observed_at=decision['observed_at'], decisions=[decision]), manifest['node'], decision['observed_at'])
        require(device == decision['device'] and decision['public_key'] not in keys and decision['tcp_id'] not in users
                and decision['observed_at'] <= state['observed_at'], 'RECEIVER_BINDINGS')
        keys.add(decision['public_key'])
        users.add(decision['tcp_id'])
    require({public for index, public in peers} <= keys, 'UNACCOUNTED_PEERS')
    return dict(result='NODE_OFFLINE_CUSTODY_PASS', slot=manifest['slot'], peers=len(peers),
                sequence_floor=sequences[0][1], records=len(state['records']), files=len(files),
                activation=False, fleet_fence=False, canonical_registry_comparison=False)


def restore(capsule, key, checkpoint, destination):
    files, manifest = unseal(capsule, key, checkpoint)
    summary = validate(files, manifest)
    destination = Path(destination)
    require(destination.is_absolute() and '..' not in destination.parts, 'RESTORE_PATH')
    with Reader().opened(destination.parent) as descriptor:
        info = os.fstat(descriptor)
        require(stat.S_ISDIR(info.st_mode) and stat.S_IMODE(info.st_mode) == 0o700 and
                info.st_uid == os.geteuid(), 'PRIVATE_PARENT_REQUIRED')
    destination.mkdir(mode=0o700)
    for name, raw in dict(files, **{'manifest.json': json.dumps(manifest, sort_keys=True).encode()}).items():
        descriptor = os.open(destination / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        require((destination / name).read_bytes() == raw, 'RESTORE_READBACK')
    for path in (destination, destination.parent):
        descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    return summary
