import json
import os
import sqlite3
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import pytest
import RNS

from messenger.local import LocalChat, LocalError, contact_card
from messenger.store import Store


@pytest.fixture(scope='module', autouse=True)
def runtime(chat_runtime):
    return chat_runtime


@pytest.fixture
def account(tmp_path):
    key = os.urandom(32)
    local = LocalChat(tmp_path / 'chat', key, create=True)
    peer = contact_card(RNS.Identity().get_public_key().hex())
    local.trust_contact(peer['public'], peer['fingerprint'])
    yield local, peer, key, tmp_path / 'chat'
    local.close()


def test_native_history_survives_reopen_without_exposing_core_records(account):
    local, peer, key, root = account
    profile = local.profile()
    message_id = local.queue(peer['address'], 'Сохрани меня :)')
    first = local.history(peer['address'])
    assert first['messages'][0] == dict(id=message_id, peer=peer['address'],
        text='Сохрани меня :)', timestamp=first['messages'][0]['timestamp'],
        outgoing=True, status='queued')
    assert first['total'] == 1 and first['next_offset'] is None
    local.close()
    resumed = LocalChat(root, key, create=False)
    try:
        assert resumed.profile() == profile
        assert resumed.contacts() == [peer]
        assert resumed.history(peer['address']) == first
    finally:
        resumed.close()
    for path in root.iterdir():
        assert 'Сохрани меня'.encode() not in path.read_bytes()
        assert key not in path.read_bytes()


@pytest.mark.parametrize('damage', ['directory', 'database', 'identity', 'wrong_key', 'ciphertext'])
def test_resume_never_recreates_missing_or_damaged_account(account, damage):
    local, peer, key, root = account
    local.queue(peer['address'], 'private text')
    local.close()
    if damage == 'directory':
        root = root.parent / 'missing'
    elif damage == 'database':
        (root / 'history.sqlite').unlink()
    elif damage == 'identity':
        with sqlite3.connect(root / 'history.sqlite') as db:
            db.execute("DELETE FROM records WHERE id='identity'")
    elif damage == 'wrong_key':
        key = os.urandom(32)
    else:
        with sqlite3.connect(root / 'history.sqlite') as db:
            db.execute("UPDATE records SET sealed=zeroblob(64) WHERE id LIKE 'message:%'")
    with pytest.raises(LocalError, match='^store_unavailable$'):
        LocalChat(root, key, create=False)
    if damage == 'directory':
        assert not root.exists()
    elif damage == 'database':
        assert not (root / 'history.sqlite').exists()
    elif damage == 'identity':
        with sqlite3.connect(root / 'history.sqlite') as db:
            assert db.execute("SELECT count(*) FROM records WHERE id='identity'").fetchone()[0] == 0


def test_duplicate_enrollment_and_second_owner_preserve_existing_account(account):
    local, _, key, root = account
    profile = local.profile()
    for create in (True, False):
        with pytest.raises(LocalError, match='^store_unavailable$'):
            LocalChat(root, key, create=create)
    assert local.profile() == profile
    local.close()
    resumed = LocalChat(root, key, create=False)
    assert resumed.profile() == profile
    resumed.close()


def test_contact_verification_and_utf8_validation(account):
    local, peer, _, _ = account
    stranger = contact_card(RNS.Identity().get_public_key().hex())
    with pytest.raises(LocalError, match='^fingerprint_mismatch$'):
        local.trust_contact(stranger['public'], '00' * 32)
    assert local.contacts() == [peer]
    with pytest.raises(LocalError, match='^unverified_contact$'):
        local.queue(stranger['address'], 'hello')
    own = local.profile()
    with pytest.raises(LocalError, match='^own_contact$'):
        local.trust_contact(own['public'], own['fingerprint'])
    for text in ('', 'я' * 2049, '\ud800', None):
        with pytest.raises(LocalError, match='^invalid_input$'):
            local.queue(peer['address'], text)
    local.queue(peer['address'], 'я' * 2048)
    assert local.history(peer['address'])['total'] == 1


def test_history_order_and_stale_attempt_after_process_restart(account):
    local, peer, key, root = account
    ids = [local.queue(peer['address'], str(n)) for n in range(3)]
    local.close()
    # Simulate the carrier dying during its first outbound attempt.
    store = Store(root, key, create=False)
    old_token, packed = store.begin_attempt(ids[0])
    store.close()
    resumed = LocalChat(root, key, create=False)
    try:
        page = resumed.history(peer['address'], limit=2)
        assert [m['id'] for m in page['messages']] == ids[:2]
        assert page['messages'][0]['status'] == 'queued'
        assert page['next_offset'] == 2 and page['total'] == 3
        last = resumed.history(peer['address'], offset=2, limit=2)
        assert [m['id'] for m in last['messages']] == ids[2:]
        assert last['next_offset'] is None
        serialized = json.dumps(page)
        assert old_token not in serialized and packed.hex() not in serialized
    finally:
        resumed.close()
    store = Store(root, key, create=False)
    try:
        new_token, retry = store.begin_attempt(ids[0])
        assert retry == packed
        assert not store.finish_attempt(ids[0], old_token, delivered=True)
        assert store.finish_attempt(ids[0], new_token, delivered=True)
    finally:
        store.close()


def test_concurrent_queue_and_close_are_serialized(account):
    local, peer, key, root = account
    def queue(n):
        try:
            return local.queue(peer['address'], str(n))
        except LocalError as error:
            assert str(error) == 'closed'
            return None
    with ThreadPoolExecutor(max_workers=5) as pool:
        tasks = [pool.submit(queue, n) for n in range(20)]
        local.close()
        saved = [f.result() for f in tasks if f.result() is not None]
    resumed = LocalChat(root, key, create=False)
    try:
        assert {m['id'] for m in resumed.history(peer['address'])['messages']} == set(saved)
    finally:
        resumed.close()
    local.close()
    for call in (local.profile, local.contacts, lambda: local.history(peer['address'])):
        with pytest.raises(LocalError, match='^closed$'):
            call()


def test_failed_save_rolls_back_and_does_not_leak_storage_error(account, monkeypatch):
    local, peer, _, _ = account
    original = Store._put
    def disk_failure(store, ident, value):
        original(store, ident, value)
        raise sqlite3.OperationalError('synthetic-private-path-and-plaintext')
    with monkeypatch.context() as patch:
        patch.setattr(Store, '_put', disk_failure)
        with pytest.raises(LocalError, match='^message_not_saved$'):
            local.queue(peer['address'], 'not committed')
    assert local.history(peer['address'])['total'] == 0
    local.queue(peer['address'], 'committed')
    assert local.history(peer['address'])['total'] == 1


def test_abrupt_process_exit_keeps_committed_queue(tmp_path):
    key = os.urandom(32)
    peer = contact_card(RNS.Identity().get_public_key().hex())
    code = '''
import json, os, pathlib, sys
import RNS
from messenger.local import LocalChat
data = json.load(sys.stdin)
root = pathlib.Path(data['root'])
runtime = root / 'runtime'
runtime.mkdir()
(runtime / 'config').write_text('[reticulum]\\nshare_instance = No\\nenable_transport = No\\n[logging]\\nloglevel = -1\\n[interfaces]\\n')
RNS.Reticulum(configdir=str(runtime), loglevel=-1)
chat = LocalChat(root / 'chat', bytes.fromhex(data['key']), create=True)
chat.trust_contact(data['peer']['public'], data['peer']['fingerprint'])
ident = chat.queue(data['peer']['address'], 'survives abrupt exit')
print(json.dumps(dict(profile=chat.profile(), id=ident)), flush=True)
os._exit(0)
'''
    result = subprocess.run([sys.executable, '-c', code], input=json.dumps(
        dict(root=str(tmp_path), key=key.hex(), peer=peer)), capture_output=True,
        text=True, timeout=15)
    assert result.returncode == 0
    saved = json.loads(result.stdout)
    resumed = LocalChat(tmp_path / 'chat', key, create=False)
    try:
        assert resumed.profile() == saved['profile']
        messages = resumed.history(peer['address'])['messages']
        assert len(messages) == 1 and messages[0]['id'] == saved['id']
        assert messages[0]['text'] == 'survives abrupt exit'
        assert messages[0]['status'] == 'queued'
    finally:
        resumed.close()


@pytest.mark.parametrize('offset,limit', [(-1, 10), (0, 101), (True, 1), (0, False)])
def test_history_bounds(account, offset, limit):
    local, peer, _, _ = account
    with pytest.raises(LocalError, match='^invalid_input$'):
        local.history(peer['address'], offset=offset, limit=limit)
