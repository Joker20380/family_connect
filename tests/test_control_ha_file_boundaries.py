"""Synthetic file recovery boundaries, not an all-store migration or live restore."""
import base64
import importlib.util
import io
import json
from pathlib import Path
import sqlite3
from types import SimpleNamespace

import pytest

from control.friends import pseudonyms


@pytest.fixture
def aliases(monkeypatch):
    identities = iter(f'{number:032x}' for number in range(1, 20))
    monkeypatch.setattr(pseudonyms.uuid, 'uuid4', lambda: SimpleNamespace(hex=next(identities)))
    return pseudonyms.prepare(dict(device=['a' * 32], panel_event=['event-001']),
                             b'n' * 32, legacy_key=b'o' * 32)


def test_alias_regeneration_with_identical_keys_is_not_a_restore(aliases):
    regenerated = pseudonyms.prepare(dict(device=['a' * 32], panel_event=['event-001']),
                                     b'n' * 32, legacy_key=b'o' * 32)
    for domain in pseudonyms.DOMAINS:
        original = aliases.document['entities'][domain][0]
        recreated = regenerated.document['entities'][domain][0]
        assert original['aliases'] == recreated['aliases']
        assert original['handle'] == recreated['handle']
        assert original['entity'] != recreated['entity']
    assert pseudonyms.digest(aliases.document) != pseudonyms.digest(regenerated.document)
    envelope = pseudonyms.seal(dict(devices=[]), 'inventory', b'n' * 32, aliases)
    with pytest.raises(ValueError):
        pseudonyms.unseal(envelope, 'inventory', regenerated)


def test_alias_restore_preserves_history_and_delta_without_old_key(aliases, tmp_path):
    path = tmp_path / 'aliases.json'
    pseudonyms.save(path, aliases)
    accepted = path.read_bytes()
    path = tmp_path / 'restored.json'
    path.write_bytes(accepted)
    path.chmod(0o600)
    restored = pseudonyms.load(path)
    assert restored.document == aliases.document
    extended = pseudonyms.prepare(dict(device=['b' * 32], panel_event=[]),
                                  b'n' * 32, existing=restored)
    for domain in pseudonyms.DOMAINS:
        assert extended.document['entities'][domain][0] == aliases.document['entities'][domain][0]
    historical = pseudonyms.pseudonym(b'n' * 32, 'device', 'a' * 32)
    assert extended.resolve('device', historical) == pseudonyms.pseudonym(b'o' * 32, 'device', 'a' * 32)
    future = pseudonyms.pseudonym(b'n' * 32, 'device', 'b' * 32)
    assert extended.resolve('device', future) == future
    pseudonyms.save(path, extended)
    envelope = pseudonyms.seal(dict(devices=[dict(pseudonym=future)]), 'inventory', b'n' * 32, extended)
    assert pseudonyms.unseal(envelope, 'inventory', pseudonyms.load(path))['devices'][0]['pseudonym'] == future
    stale = tmp_path / 'stale.json'
    stale.write_bytes(accepted)
    stale.chmod(0o600)
    with pytest.raises(ValueError):
        pseudonyms.unseal(envelope, 'inventory', pseudonyms.load(stale))


@pytest.fixture
def gateway(tmp_path, monkeypatch):
    path = Path(__file__).parents[1] / 'deploy/friends/awg-gateway.py'
    spec = importlib.util.spec_from_file_location('ha_file_boundary_gateway', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    (tmp_path / 'settings.json').write_text(json.dumps(dict(network='10.83.0.0/16')))
    monkeypatch.setattr(module, 'paid_engine', lambda: None)
    monkeypatch.setattr(module, 'add_peer', lambda *args: None)
    monkeypatch.setattr(module, 'tcp_user', lambda *args: None)
    monkeypatch.setattr(module, 'command', lambda *args, **kwargs: pytest.fail('No gateway command allowed'))
    return module


def register(gateway, number, monkeypatch, capsys):
    public = base64.b64encode(bytes([number]) * 32).decode()
    request = dict(public_key=public, device=f'{number:032x}',
                   tcp_id=f'00000000-0000-4000-8000-{number:012x}')
    monkeypatch.setattr(gateway.sys, 'stdin', SimpleNamespace(buffer=io.BytesIO(json.dumps(request).encode())))
    gateway.register()
    return json.loads(capsys.readouterr().out)['address']


def test_peer_reconstruction_from_same_keys_changes_assignments(gateway, monkeypatch, capsys):
    original = {number: register(gateway, number, monkeypatch, capsys) for number in (1, 2)}
    replacement = gateway.ROOT / 'reconstructed'
    replacement.mkdir()
    (replacement / 'settings.json').write_bytes((gateway.ROOT / 'settings.json').read_bytes())
    monkeypatch.setattr(gateway, 'ROOT', replacement)
    reconstructed = {number: register(gateway, number, monkeypatch, capsys) for number in (2, 1)}
    assert original == {1: '10.83.0.2/32', 2: '10.83.0.3/32'}
    assert reconstructed == {2: '10.83.0.2/32', 1: '10.83.0.3/32'}


@pytest.mark.parametrize('remove_highest', [False, True])
def test_peer_sqlite_backup_preserves_bindings_and_allocator(gateway, monkeypatch, capsys, remove_highest):
    original = {number: register(gateway, number, monkeypatch, capsys) for number in (1, 2, 3)}
    restored_root = gateway.ROOT / 'restored'
    restored_root.mkdir()
    (restored_root / 'settings.json').write_bytes((gateway.ROOT / 'settings.json').read_bytes())
    source = gateway.database()
    destination = sqlite3.connect(restored_root / 'peers.db')
    try:
        if remove_highest:
            with source:
                source.execute('DELETE FROM peers WHERE id=3')
        source.backup(destination)
        assert source.execute('SELECT * FROM peers ORDER BY id').fetchall() == destination.execute(
            'SELECT * FROM peers ORDER BY id').fetchall()
        assert destination.execute("SELECT seq FROM sqlite_sequence WHERE name='peers'").fetchone() == (3,)
    finally:
        destination.close()
        source.close()
    monkeypatch.setattr(gateway, 'ROOT', restored_root)
    assert register(gateway, 2, monkeypatch, capsys) == original[2]
    assert register(gateway, 1, monkeypatch, capsys) == original[1]
    assert register(gateway, 4, monkeypatch, capsys) == '10.83.0.5/32'
