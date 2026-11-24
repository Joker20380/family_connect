import base64
from contextlib import closing
from copy import deepcopy
import fcntl
import io
import json
import os
from pathlib import Path
import signal
import sqlite3
import subprocess
import sys
import tarfile
import time
import uuid

import pytest

from scripts import control_ha_node_capture as capture
from scripts import control_ha_node_restore as recovery


@pytest.fixture
def node(tmp_path, monkeypatch):
    root = tmp_path / 'source'
    (root / 'friends-awg').mkdir(parents=True)
    (root / 'friends-tcp').mkdir()
    now = int(time.time())
    records = {}
    with closing(sqlite3.connect(root / 'friends-awg/peers.db')) as database:
        database.execute(recovery.PEER_SCHEMA[1][3])
        for index in range(2):
            public = base64.b64encode(bytes([index + 1]) * 32).decode()
            device = str(index + 1) * 32
            decision = dict(device=device, public_key=public, tcp_id=str(uuid.uuid4()), cohort=True, revision=2,
                state='active' if index else 'revoked', identity_allowed=bool(index), allowed=bool(index),
                paid_until=now + 3600, grace_until=None, observed_at=now, valid_until=now + 120)
            records[device] = dict(decision=decision, boot=str(uuid.uuid4()), deadline=time.monotonic() + 120,
                                   applied=None, prepared=None)
            database.execute('INSERT INTO peers(public) VALUES (?)', (public,))
        database.execute("UPDATE sqlite_sequence SET seq=7 WHERE name='peers'")
        database.commit()
    documents = {'settings.json': dict(network='10.84.0.0/16', address='10.84.0.1/16', external='ens3'),
        'state.json': dict(schema=1, node='gateway-ru', records=records, observed_at=now),
        'enforcement.json': dict(schema=1, node='gateway-ru', profile='paid-transports-v2', enabled=True),
        'tcp.json': dict(inbounds=[])}
    for name, relative in capture.FILES.items():
        (root / relative).write_bytes(json.dumps(documents[name]).encode() if name in documents else b'fixture-only')
    for name in ('application.lock', 'registration.lock'):
        (root / 'friends-awg' / name).touch()
    monkeypatch.setitem(capture.SOURCES, 'RU', (capture.digest(b'fixture-only'),) * 2)
    return root


def checkpoint(node):
    files, manifest = capture.capture('RU', node)
    key = os.urandom(32)
    capsule, pin = recovery.seal(capture.archive(files, manifest), key)
    return files, manifest, capsule, key, pin


def assert_unlocked(node):
    for name in ('application.lock', 'registration.lock'):
        with (node / 'friends-awg' / name).open('rb') as stream:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    with closing(sqlite3.connect(node / 'friends-awg/peers.db', timeout=0)) as database:
        database.execute('BEGIN IMMEDIATE')
        database.rollback()
    assert signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0)


def test_actual_shape_roundtrip_is_exact_private_and_not_activation(node, tmp_path):
    before = {str(path): path.read_bytes() for path in node.rglob('*') if path.is_file()}
    files, manifest, capsule, key, pin = checkpoint(node)
    summary = recovery.restore(capsule, key, pin, tmp_path / 'offline')
    assert summary == dict(result='NODE_OFFLINE_CUSTODY_PASS', slot='RU', peers=2, sequence_floor=7,
        records=2, files=8, activation=False, fleet_fence=False, canonical_registry_comparison=False)
    assert {str(path): path.read_bytes() for path in node.rglob('*') if path.is_file()} == before
    assert manifest['barrier_seconds'] < .25
    for name, raw in files.items():
        target = tmp_path / 'offline' / name
        assert target.read_bytes() == raw and target.stat().st_mode & 0o777 == 0o600
    assert (tmp_path / 'offline').stat().st_mode & 0o777 == 0o700
    assert_unlocked(node)


@pytest.mark.parametrize('name', ('application.lock', 'registration.lock', 'database'))
def test_contention_refuses_without_wait_or_mutation(node, name):
    with closing(sqlite3.connect(node / 'friends-awg/peers.db')) as database:
        with (node / 'friends-awg' / ('application.lock' if name == 'database' else name)).open('rb') as stream:
            if name == 'database':
                database.execute('BEGIN IMMEDIATE')
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            started = time.monotonic()
            with pytest.raises((BlockingIOError, sqlite3.OperationalError)):
                capture.capture('RU', node)
            assert time.monotonic() - started < .25
        database.rollback()
    assert_unlocked(node)


@pytest.mark.parametrize('suffix', ('-wal', '-shm', '-journal'))
def test_even_cold_sidecars_are_outside_reviewed_capture_scope(node, suffix):
    (node / ('friends-awg/peers.db' + suffix)).touch()
    with pytest.raises(ValueError, match='SIDECAR_PRESENT'):
        capture.capture('RU', node)


@pytest.mark.parametrize('relative', list(capture.FILES.values()) +
                         ['friends-awg/peers.db', 'friends-awg/application.lock', 'friends-awg/registration.lock'])
@pytest.mark.parametrize('link', ('symlink', 'hardlink'))
def test_links_refused(node, relative, link):
    path = node / relative
    saved = path.with_name(path.name + '.saved')
    path.rename(saved)
    if link == 'symlink':
        path.symlink_to(saved)
    else:
        os.link(saved, path)
    with pytest.raises(Exception):
        capture.capture('RU', node)
    assert signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0)


def test_source_change_refused_before_locking(node):
    (node / capture.FILES['gateway.py']).write_bytes(b'new-unreviewed-source')
    with pytest.raises(ValueError, match='INSTALLED_SOURCE_CHANGED'):
        capture.capture('RU', node)
    assert_unlocked(node)


def test_reader_failure_and_same_byte_rewrite_release_all_locks(node, monkeypatch):
    original = capture.Reader.raw
    def rewrite(reader, path):
        raw = original(reader, path)
        if path.name == 'server.json':
            target = node / capture.FILES['state.json']
            target.write_bytes(target.read_bytes())
        return raw
    monkeypatch.setattr(capture.Reader, 'raw', rewrite)
    with pytest.raises(Exception, match='OBSERVATION_CHANGED'):
        capture.capture('RU', node)
    assert_unlocked(node)


def test_kernel_deadline_releases_locks_even_during_hung_read(node):
    program = '''
import sys, time
from pathlib import Path
from scripts import control_ha_node_capture as capture
capture.SOURCES['RU'] = (capture.digest(b'fixture-only'),) * 2
original = capture.Reader.raw
def hanging(reader, path):
    if path.name == 'transport-state.json': time.sleep(5)
    return original(reader, path)
capture.Reader.raw = hanging
capture.capture('RU', Path(sys.argv[1]))
'''
    result = subprocess.run([sys.executable, '-c', program, str(node)], capture_output=True, timeout=3)
    assert result.returncode == -signal.SIGALRM
    assert result.stdout == b''
    assert_unlocked(node)


def test_changed_old_and_wrong_key_capsules_refused(node):
    files, manifest, old, key, old_pin = checkpoint(node)
    current, pin = recovery.seal(capture.archive(files, manifest), key)
    with pytest.raises(ValueError, match='STALE_OR_CHANGED_CAPSULE'):
        recovery.unseal(old, key, pin)
    with pytest.raises(ValueError, match='STALE_OR_CHANGED_CAPSULE'):
        recovery.unseal(current[:-1] + bytes([current[-1] ^ 1]), key, pin)
    with pytest.raises(ValueError, match='CAPSULE_AUTHENTICATION'):
        recovery.unseal(current, os.urandom(32), pin)


@pytest.mark.parametrize('change', ('extra-table', 'floor-regression', 'unknown-peer', 'wrong-network',
                                    'bad-interface', 'future-state', 'duplicate-binding', 'nonfinite-clock'))
def test_semantic_corruption_refused(node, change):
    files, manifest = capture.capture('RU', node)
    if change in ('extra-table', 'floor-regression', 'unknown-peer'):
        with closing(sqlite3.connect(':memory:')) as database:
            database.deserialize(files['peers.sqlite'])
            if change == 'extra-table':
                database.execute('CREATE TABLE surprise(secret TEXT)')
            elif change == 'floor-regression':
                database.execute('UPDATE sqlite_sequence SET seq=1')
            else:
                database.execute('UPDATE peers SET public=? WHERE id=1', (base64.b64encode(b'x'*32).decode(),))
            database.commit()
            files['peers.sqlite'] = database.serialize()
    elif change in ('wrong-network', 'bad-interface'):
        value = json.loads(files['settings.json'])
        value['network' if change == 'wrong-network' else 'external'] = '10.83.0.0/16' if change == 'wrong-network' else '/tmp/x'
        files['settings.json'] = json.dumps(value).encode()
    else:
        value = json.loads(files['state.json'])
        records = list(value['records'].values())
        if change == 'future-state':
            value['observed_at'] += 1000
        elif change == 'duplicate-binding':
            records[1]['decision']['public_key'] = records[0]['decision']['public_key']
        else:
            records[0]['deadline'] = float('nan')
        files['state.json'] = json.dumps(value).encode()
    with pytest.raises(ValueError):
        recovery.validate(files, manifest)


@pytest.mark.parametrize('change', ('scope', 'deadline', 'pin', 'duplicate', 'traversal', 'symlink'))
def test_untrusted_archive_refused(node, change):
    files, manifest = capture.capture('RU', node)
    manifest = deepcopy(manifest)
    if change == 'scope': manifest['activation'] = True
    if change == 'deadline': manifest['barrier_seconds'] = .25
    if change == 'pin': manifest['files']['state.json']['sha256'] = '0' * 64
    raw = capture.archive(files, manifest)
    if change in ('duplicate', 'traversal', 'symlink'):
        stream = io.BytesIO(raw)
        with tarfile.open(fileobj=stream, mode='a') as bundle:
            entry = tarfile.TarInfo('../escape' if change == 'traversal' else 'state.json')
            if change == 'symlink':
                entry.type, entry.linkname = tarfile.SYMTYPE, '/etc/passwd'
            bundle.addfile(entry)
        raw = stream.getvalue()
    with pytest.raises(ValueError):
        recovery.unpack(raw)


def test_restore_refuses_existing_and_nonprivate_parent(node, tmp_path):
    files, manifest, capsule, key, pin = checkpoint(node)
    existing = tmp_path / 'existing'
    existing.mkdir()
    with pytest.raises(FileExistsError):
        recovery.restore(capsule, key, pin, existing)
    existing.chmod(0o755)
    with pytest.raises(ValueError, match='PRIVATE_PARENT_REQUIRED'):
        recovery.restore(capsule, key, pin, existing / 'new')
