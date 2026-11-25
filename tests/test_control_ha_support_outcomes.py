import copy
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import socket
import threading

import pytest
import RNS

from messenger import codec
from messenger.store import Store
from messenger.relay import Spool
from scripts import control_ha_support_outcomes as outcomes


@pytest.fixture
def cohort(tmp_path):
    key = b's' * 32
    directory = tmp_path / 'support'
    recipient = RNS.Identity()
    with_store = Store(directory, key, create=True)
    identity = with_store.chat_identity()
    public = identity.get_public_key().hex()
    packed = codec.pack(identity, recipient.get_public_key(), 'PRIVATE_TEST_MESSAGE')
    message = codec.unpack(packed, recipient=recipient.get_public_key(),
                           contacts={codec.address(identity.get_public_key()): identity.get_public_key()})
    message['peer'] = codec.address(recipient.get_public_key()).hex()
    with_store.add(message, packed, outgoing=True)
    blob = bytes.fromhex(message['peer']) + b'ciphertext' * 16
    with with_store._lock, with_store._db:
        stored = with_store._get('message:' + message['id'])
        stored.update(status='recipient_stored', relay_blob=blob.hex(), attempt=None)
        with_store._put('message:' + message['id'], stored)
        with_store._put('support-request:synthetic', dict(id=message['id'], request=dict(text='PRIVATE_TEST_MESSAGE')))
    with_store.close()
    spool = tmp_path / 'spool.sqlite'
    with sqlite3.connect(spool) as database:
        database.execute('CREATE TABLE messages (id BLOB PRIMARY KEY,sender BLOB NOT NULL,recipient BLOB NOT NULL,received REAL NOT NULL,body BLOB NOT NULL)')
    spool.chmod(0o600)
    return directory, key, public, spool, blob, message


def local(cohort):
    directory, key, public, *_ = cohort
    return outcomes.local_snapshot(directory, key, public, os.getuid())


def remote(cohort, request):
    return outcomes.remote_snapshot(cohort[3], request, os.getuid())


def add_spool(cohort, *, sender=None, recipient=None, ident=None, blob=None):
    _, _, public, spool, original, message = cohort
    blob = original if blob is None else blob
    with sqlite3.connect(spool) as database:
        database.execute('INSERT INTO messages VALUES (?,?,?,?,?)',
                         (hashlib.sha256(blob).digest() if ident is None else ident,
                          hashlib.sha256(bytes.fromhex(public)).digest()[:16] if sender is None else sender,
                          bytes.fromhex(message['peer']) if recipient is None else recipient, 1000.0, blob))


def test_absent_ciphertext_and_local_recipient_status_do_not_prove_settlement(cohort):
    before = local(cohort)
    request = outcomes.request_for(before, 'a'*64)
    result = outcomes.assess(before, local(cohort), request, remote(cohort, request))
    assert result['absent_unknown'] == 1 and result['retained_incoming_acks'] == 0
    assert result['local_status_counts'] == {'outgoing:recipient_stored': 1}
    assert not any(result[name] for name in ('writer_fenced', 'activation_ready', 'external_settlement_proven', 'capture_permitted'))
    raw = json.dumps(result)
    for secret in ('PRIVATE_TEST_MESSAGE', cohort[2], cohort[4].hex(), cohort[5]['id'], cohort[5]['peer']):
        assert secret not in raw


def test_present_exact_ciphertext_is_observed_not_delivered_or_fenced(cohort):
    add_spool(cohort)
    before = local(cohort)
    request = outcomes.request_for(before, 'b'*64)
    result = outcomes.assess(before, local(cohort), request, remote(cohort, request))
    assert result['matched_present'] == 1 and result['absent_unknown'] == 0
    assert result['result'] == 'OBSERVED_UNFENCED' and not result['activation_ready']


@pytest.mark.parametrize('change', [dict(sender=b'other-sender-key!'), dict(recipient=b'other-recipient!'), dict(ident=b'i'*32)])
def test_independent_spool_binding_mismatch_refuses(cohort, change):
    add_spool(cohort, **change)
    with pytest.raises(ValueError):
        remote(cohort, outcomes.request_for(local(cohort), 'c'*64))


def test_other_sender_envelope_remains_an_explicit_gap(cohort):
    add_spool(cohort, blob=cohort[4] + b'other')
    before = local(cohort)
    request = outcomes.request_for(before, 'd'*64)
    result = outcomes.assess(before, before, request, remote(cohort, request))
    assert result['sender_rows_not_in_request'] == 1 and result['absent_unknown'] == 1
    assert not result['activation_ready']


@pytest.mark.parametrize('field,value', [('writer_fenced', True), ('request_sha256', 'e'*64), ('matched_present', -1), ('absent_unknown', 0), ('schema', True)])
def test_unbound_or_fabricated_remote_receipt_refuses(cohort, field, value):
    before = local(cohort)
    request = outcomes.request_for(before, 'f'*64)
    response = remote(cohort, request)
    response[field] = value
    with pytest.raises(ValueError):
        outcomes.assess(before, before, request, response)


def test_changed_local_snapshot_is_not_a_coherent_boundary(cohort):
    before = local(cohort)
    request = outcomes.request_for(before, 'a'*64)
    after = copy.deepcopy(before)
    after['sealed_sha256'] = 'b'*64
    result = outcomes.assess(before, after, request, remote(cohort, request))
    assert result['result'] == 'LOCAL_CHANGED_DURING_OBSERVATION'
    assert not result['local_unchanged'] and not result['activation_ready']


def test_wrong_sender_identity_refuses(cohort):
    with pytest.raises(ValueError, match='SENDER_IDENTITY'):
        outcomes.local_snapshot(cohort[0], cohort[1], RNS.Identity().get_public_key().hex(), os.getuid())


def test_readers_leave_ciphertext_schema_and_journal_files_unchanged(cohort):
    add_spool(cohort)
    paths = (cohort[0] / 'history.sqlite', cohort[3])
    before = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in paths}
    state = local(cohort)
    remote(cohort, outcomes.request_for(state, 'c'*64))
    assert before == {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in paths}
    assert all(not Path(str(path)+suffix).exists() for path in paths for suffix in ('-wal','-shm','-journal'))


@pytest.mark.parametrize('mode', ['symlink', 'sidecar', 'schema', 'permissions', 'busy'])
def test_unsafe_or_busy_database_refuses_without_mutation(cohort, mode, tmp_path):
    path = cohort[3]
    connection = None
    if mode == 'symlink':
        link = tmp_path / 'alias.sqlite'
        link.symlink_to(path)
        path = link
    elif mode == 'sidecar':
        Path(str(path)+'-journal').touch()
    elif mode == 'permissions':
        path.chmod(0o644)
    elif mode == 'schema':
        with sqlite3.connect(path) as database:
            database.execute('CREATE TABLE unexpected (value TEXT)')
    elif mode == 'busy':
        connection = sqlite3.connect(path)
        connection.execute('BEGIN EXCLUSIVE')
    before = path.read_bytes()
    try:
        with pytest.raises((ValueError, sqlite3.OperationalError)):
            outcomes.read_rows(path, 'messages', os.getuid())
        assert path.read_bytes() == before
    finally:
        if connection:
            connection.rollback()
            connection.close()


def test_native_relay_can_commit_after_sender_disconnect_and_an_absent_snapshot(cohort, tmp_path):
    root = tmp_path / 'late-relay'
    entered, release, ready = threading.Event(), threading.Event(), threading.Event()
    public, blob = cohort[2], cohort[4]
    sender = hashlib.sha256(bytes.fromhex(public)).digest()[:16]
    with socket.socket() as listener, ThreadPoolExecutor(max_workers=1) as executor:
        listener.bind(('127.0.0.1', 0))
        listener.listen(1)
        listener.settimeout(3)

        def server():
            spool = Spool(root)
            try:
                ready.set()
                with listener.accept()[0] as connection:
                    connection.settimeout(3)
                    received = bytearray()
                    while len(received) < len(blob):
                        chunk = connection.recv(len(blob)-len(received))
                        assert chunk
                        received.extend(chunk)
                    assert bytes(received) == blob
                    entered.set()
                    assert release.wait(5)
                    return spool.put(sender, blob)
            finally:
                spool.close()

        future = executor.submit(server)
        try:
            assert ready.wait(3)
            with socket.create_connection(listener.getsockname(), timeout=3) as connection:
                connection.sendall(blob)
            assert entered.wait(3)
            before = local(cohort)
            request = outcomes.request_for(before, 'a'*64)
            observed = outcomes.remote_snapshot(root/'spool.sqlite', request, os.getuid())
            assert observed['absent_unknown'] == 1
            assert not outcomes.assess(before, local(cohort), request, observed)['activation_ready']
            release.set()
            assert future.result(timeout=3) == hashlib.sha256(blob).digest()
            after = outcomes.remote_snapshot(root/'spool.sqlite', request, os.getuid())
            assert after['matched_present'] == 1
            assert not outcomes.assess(before, local(cohort), request, after)['activation_ready']
        finally:
            release.set()
            future.result(timeout=3)


@pytest.mark.parametrize('removal', ['recipient_purge', 'retention'])
def test_native_relay_absence_cannot_distinguish_purge_from_expiry(cohort, tmp_path, removal):
    root = tmp_path / 'removed-relay'
    now = [1000]
    spool = Spool(root, clock=lambda: now[0])
    blob, message = cohort[4], cohort[5]
    try:
        ident = spool.put(hashlib.sha256(bytes.fromhex(cohort[2])).digest()[:16], blob)
        if removal == 'recipient_purge':
            assert spool.get(bytes.fromhex(message['peer']), [None, [ident]]) == []
        else:
            now[0] += 86401
            spool.expire()
        before = local(cohort)
        request = outcomes.request_for(before, 'b'*64)
        response = outcomes.remote_snapshot(root/'spool.sqlite', request, os.getuid())
        result = outcomes.assess(before, local(cohort), request, response)
        assert result['absent_unknown'] == 1 and not result['external_settlement_proven']
    finally:
        spool.close()
