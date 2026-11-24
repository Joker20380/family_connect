import base64
import fcntl
import json
import os
from pathlib import Path
import signal
import sqlite3
import subprocess
import sys

import pytest

from scripts import control_ha_worker_custody as custody
from scripts import control_ha_worker_qualify as native
from control.product.store import ProductStore
from tests.test_product_provisioning import setup


@pytest.fixture
def source(setup, tmp_path):
    root = tmp_path / 'source'
    root.mkdir(mode=0o700)
    repository = Path(__file__).resolve().parents[1]
    for name in custody.PINS:
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((repository / name).read_bytes())
    database = root / 'state-product/db/product.db'
    database.parent.mkdir(parents=True, mode=0o700)
    database.write_bytes(Path(setup[0].path).read_bytes())
    database.chmod(0o600)
    keys = root / 'state-v2/wireguard'
    keys.mkdir(parents=True, mode=0o700)
    (keys / 'peers').mkdir(mode=0o700)
    (keys / '.enrollment.lock').touch(mode=0o600)
    for name in ('android.pub', 'linux.pub', 'server.pub'):
        (keys / name).write_text(setup[4]['gateways'][0]['public_key'] + '\n')
    (root / 'state-product/gateways.json').write_text(json.dumps(dict(g1=dict(
        container='family-connect-pilot-gateway-1', keys=str(custody.ROOT / 'state-v2/wireguard')))))
    environment = tmp_path / 'product.env'
    environment.write_text('\n'.join(name + '=' + str(custody.ROOT / relative) for name, relative in (
        ('FC_PROJECT_ROOT', ''), ('FC_PRODUCT_DB', 'state-product/db/product.db'),
        ('FC_PRODUCT_DB_DIRECTORY', 'state-product/db'), ('FC_GATEWAYS', 'state-product/gateways.json'),
        ('FC_GATEWAY_KEYS', 'state-v2/wireguard'))))
    unit = tmp_path / 'worker.service'
    unit.write_text('[Service]\nExecStart=/not/executed\n')
    return root, environment, unit


def test_exact_private_roundtrip_without_dispatch(source, tmp_path, monkeypatch):
    before = {str(path): path.read_bytes() for path in source[0].rglob('*') if path.is_file()}
    value = custody.capture(*source)
    summary = custody.validate(value)
    assert len(summary['tables']) == 13
    key = os.urandom(32)
    capsule, pin = custody.seal(value, key)
    restored = custody.unseal(capsule, key, pin)
    assert custody.restore(restored, tmp_path / 'offline') == summary
    monkeypatch.setattr(subprocess, 'run', lambda *args, **kwargs: pytest.fail('real command'))
    assert native.qualify(restored, tmp_path / 'native')['durable_retry_restart']
    assert before == {str(path): path.read_bytes() for path in source[0].rglob('*') if path.is_file()}
    assert signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0)
    assert all(path.stat().st_mode & 0o777 == (0o700 if path.is_dir() else 0o600)
               for path in (tmp_path / 'offline').rglob('*'))


@pytest.mark.parametrize('lock', ('database', 'enrollment'))
def test_zero_wait_contention_and_release(source, lock):
    if lock == 'database':
        connection = sqlite3.connect(source[0] / 'state-product/db/product.db', isolation_level=None)
        connection.execute('BEGIN IMMEDIATE')
        try:
            with pytest.raises(sqlite3.OperationalError, match='locked'):
                custody.capture(*source)
        finally:
            connection.rollback()
            connection.close()
    else:
        with (source[0] / 'state-v2/wireguard/.enrollment.lock').open('rb') as stream:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            with pytest.raises(BlockingIOError):
                custody.capture(*source)
    assert signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0)
    assert custody.validate(custody.capture(*source))['activation'] is False


@pytest.mark.parametrize('change', ('source', 'environment', 'gateway', 'journal', 'hardlink', 'symlink', 'temporary_peer'))
def test_unsafe_live_input_refused(source, change):
    root, environment, unit = source
    if change == 'source':
        (root / next(iter(custody.PINS))).write_bytes(b'changed')
    elif change == 'environment':
        environment.write_text(environment.read_text() + '\nFC_PRODUCT_DB=/another/database')
    elif change == 'gateway':
        (root / 'state-product/gateways.json').write_text('{}')
    elif change == 'journal':
        (root / 'state-product/db/product.db-journal').touch()
    elif change == 'hardlink':
        os.link(root / 'state-product/db/product.db', root / 'alias')
    elif change == 'symlink':
        (root / 'state-product/gateways.json').unlink()
        (root / 'state-product/gateways.json').symlink_to(environment)
    else:
        (root / 'state-v2/wireguard/peers/.product-pending').touch()
    with pytest.raises((ValueError, OSError)):
        custody.capture(*source)
    assert signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0)


@pytest.mark.parametrize('change', ('schema', 'foreign_key', 'version', 'extra_file', 'missing_file', 'source', 'fence', 'deadline', 'path'))
def test_corrupt_or_expanded_recovery_refused(source, change):
    value = custody.capture(*source)
    if change in ('schema', 'foreign_key', 'version'):
        connection = sqlite3.connect(':memory:')
        connection.deserialize(base64.b64decode(value['files']['product.sqlite']))
        if change == 'schema':
            connection.execute('CREATE TABLE unknown(secret)')
        elif change == 'foreign_key':
            connection.execute('DELETE FROM devices')
        else:
            connection.execute('PRAGMA user_version=4')
        connection.commit()
        value['files']['product.sqlite'] = base64.b64encode(connection.serialize()).decode()
        connection.close()
    elif change in ('extra_file', 'path'):
        value['files']['server.key' if change == 'extra_file' else 'peers/../escape.conf'] = 'YQ=='
    elif change == 'missing_file':
        del value['files']['worker.service']
    elif change == 'source':
        value['files'][next(iter(custody.PINS))] = 'YQ=='
    elif change == 'fence':
        value['external_command_fence'] = True
    else:
        value['barrier_seconds'] = float('nan')
    with pytest.raises(ValueError):
        custody.validate(value)


def test_stale_cipher_wrong_key_checkpoint_and_destination(source, tmp_path):
    value, key = custody.capture(*source), os.urandom(32)
    capsule, pin = custody.seal(value, key)
    newer, newer_pin = custody.seal(value, key)
    for blob, secret, checkpoint in ((capsule, key, newer_pin), (capsule, os.urandom(32), pin),
            (capsule, key, dict(pin, document_sha256='0' * 64)), (capsule + b'x', key, pin)):
        with pytest.raises(ValueError):
            custody.unseal(blob, secret, checkpoint)
    custody.restore(value, tmp_path / 'occupied')
    with pytest.raises(FileExistsError):
        custody.restore(value, tmp_path / 'occupied')
    assert custody.unseal(newer, key, newer_pin) == value


def test_kernel_deadline_releases_database_and_file_lock(source):
    code = '''
import sys,time
from pathlib import Path
from scripts import control_ha_worker_custody as custody
original=custody.Reader.names
def delayed(self,*args,**kwargs):
    time.sleep(5)
    return original(self,*args,**kwargs)
custody.Reader.names=delayed
custody.capture(*(Path(value) for value in sys.argv[1:]))
'''
    process = subprocess.run([sys.executable, '-c', code, *map(str, source)], capture_output=True, timeout=3)
    assert process.returncode == -signal.SIGALRM
    assert custody.validate(custody.capture(*source))['activation'] is False


@pytest.mark.parametrize('state', ('active', 'device_revoked', 'entitlement_revoked', 'key_revoked', 'retry_pending'))
def test_native_authorization_and_retry_floors(source, setup, tmp_path, state):
    store = ProductStore(source[0] / 'state-product/db/product.db', clock=lambda: 1001)
    if state == 'device_revoked':
        store.revoke_device(setup[2].reference)
    elif state == 'entitlement_revoked':
        store.revoke_entitlement(store.authorization(setup[2].reference)['entitlement_id'])
    elif state in ('key_revoked', 'retry_pending'):
        with store._transaction() as database:
            database.execute('UPDATE transport_keys SET revoked_at=1001' if state == 'key_revoked' else
                             "UPDATE peer_outbox SET applied=NULL,retry_at=1005,attempts=2,error='GATEWAY_UNAVAILABLE'")
    value = custody.capture(*source)
    value.update(locked_at_ns=1001000000000, captured_at_ns=1001001000000)
    summary = native.qualify(value, tmp_path / 'native-case')
    assert summary['allowed_at_capture'] == (1 if state in ('active', 'retry_pending') else 0)
    assert summary['real_gateway_commands'] == 0


def test_peer_intent_preserved_but_private_server_key_excluded(source, setup):
    keys = source[0] / 'state-v2/wireguard'
    raw = f'[Peer]\nPublicKey = {setup[2].wireguard_public_key}\nAllowedIPs = 10.77.0.4/32\n'.encode()
    name = 'product-' + setup[2].reference + '.conf'
    (keys / 'peers' / name).write_bytes(raw)
    (keys / 'peers' / name).chmod(0o600)
    (keys / 'server.key').write_bytes(b'never read or archived')
    value = custody.capture(*source)
    assert custody.validate(value)['peers'] == 1
    assert custody.unpack(value)['peers/' + name] == raw
    assert not any(name.endswith('.key') for name in value['files'])


def test_changed_preflight_file_refuses_capture(source, monkeypatch):
    original = custody.Reader.names
    def changed(reader, *args, **kwargs):
        source[1].write_text(source[1].read_text() + '\n')
        return original(reader, *args, **kwargs)
    monkeypatch.setattr(custody.Reader, 'names', changed)
    from scripts.control_ha_installed_inventory import Refused
    with pytest.raises(Refused, match='OBSERVATION_CHANGED'):
        custody.capture(*source)
    assert signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0)
