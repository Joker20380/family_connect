import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time
import zipfile

import pytest

from control.capture_gate import Busy, GateError, initialize
from control.friends.access import Access
from control.friends import restricted_admin, support_admin
from scripts import service_notices
from scripts.package_friends_http import build as build_http
from scripts.package_support_operator import build


ROOT = Path(__file__).resolve().parents[1]
MODULES = (restricted_admin, support_admin, service_notices)
ACTIONS = (
    (restricted_admin, ['migrate']),
    (restricted_admin, ['grant', '--device', 'a' * 32, '--expires', '2000']),
    (restricted_admin, ['revoke-device', '--device', 'a' * 32]),
    (restricted_admin, ['publish-crl']),
    (restricted_admin, ['gateway-certificate', '--output', 'certificate.pem']),
    *((support_admin, [action]) for action in
      ('backfill', 'inventory', 'lookup', 'enable-field', 'disable-field', 'audit')),
    (service_notices, ['grant', '--name', 'Synthetic', '--token-file', 'token']),
    (service_notices, ['grant-device', '--access-db', 'access.db', '--device', 'a' * 32, '--name', 'Synthetic']),
    (service_notices, ['revoke-device', '--device', 'a' * 32]),
    (service_notices, ['revoke', '--name', 'Synthetic']),
    (service_notices, ['publish', '--token-file', 'token', '--kind', 'information',
                       '--title', 'Synthetic', '--body-file', 'body', '--platform', 'android']),
    (service_notices, ['export', '--output', 'feed.json']),
)


def arguments(module, database, action, gate=None):
    result = ['--registry' if module is service_notices else '--db', str(database)]
    if gate is not None:
        result += ['--capture-gate', str(gate)]
    return result + action


def command(module, args):
    return [sys.executable, '-m', module.__name__, *args]


def environment():
    return dict(os.environ, PYTHONPATH=str(ROOT), PYTHONDONTWRITEBYTECODE='1')


def invoke(module, args, directory):
    return subprocess.run(command(module, args), cwd=directory, env=environment(),
                          capture_output=True, text=True, timeout=10)


def pending(gate):
    return sorted((gate.directory / 'pending').iterdir())


@pytest.fixture
def gate(tmp_path):
    return initialize(tmp_path / 'gate')


@pytest.mark.parametrize('module,action', ACTIONS)
def test_every_command_refuses_before_opening_store_or_private_files(module, action, gate, tmp_path):
    database = tmp_path / 'absent' / 'store.sqlite'
    before = set(tmp_path.rglob('*'))
    with gate.drain(.5):
        result = invoke(module, arguments(module, database, action, gate.directory), tmp_path)
    assert result.returncode == 75, result.stderr
    assert json.loads(result.stdout) == dict(error='CAPTURE_BUSY')
    assert not result.stderr and set(tmp_path.rglob('*')) == before and not pending(gate)


@pytest.mark.parametrize('module,action', ACTIONS)
@pytest.mark.parametrize('invalid', ['missing', 'symlink', 'permissions'])
def test_invalid_gate_never_falls_back_to_ungated_work(module, action, invalid, gate, tmp_path):
    selected = gate.directory
    if invalid == 'missing':
        selected = tmp_path / 'missing'
    elif invalid == 'symlink':
        selected = tmp_path / 'alias'
        selected.symlink_to(gate.directory, target_is_directory=True)
    else:
        gate.directory.chmod(0o755)
    before = set(tmp_path.rglob('*'))
    try:
        result = invoke(module, arguments(module, tmp_path / 'absent' / 'store.sqlite', action, selected), tmp_path)
        assert result.returncode != 0
        assert set(tmp_path.rglob('*')) == before and not pending(gate)
    finally:
        gate.directory.chmod(0o700)


def prepare(module, directory):
    database = directory / 'store.sqlite'
    if module is service_notices:
        store = service_notices.Notices(database)
        store.grant('Synthetic', directory / 'token')
        store.db.close()
        return database, ['revoke', '--name', 'Synthetic']
    access = Access(database)
    access.initialize()
    return database, ['migrate' if module is restricted_admin else 'backfill']


def verify(module, database):
    with sqlite3.connect(database) as connection:
        if module is service_notices:
            assert connection.execute('SELECT active FROM admins').fetchall() == [(0,)]
        else:
            table = 'restricted_grants' if module is restricted_admin else 'device_support'
            assert connection.execute('SELECT name FROM sqlite_master WHERE name=?', (table,)).fetchone() == (table,)


@pytest.mark.parametrize('module', MODULES)
@pytest.mark.parametrize('gated', [False, True])
def test_native_success_preserves_opt_in_behavior_and_releases_marker(module, gated, gate, tmp_path):
    database, action = prepare(module, tmp_path)
    result = invoke(module, arguments(module, database, action, gate.directory if gated else None), tmp_path)
    assert result.returncode == 0, result.stderr
    verify(module, database)
    with gate.drain(.2):
        assert not pending(gate)


@pytest.mark.parametrize('module', MODULES)
@pytest.mark.parametrize('terminate', [False, True])
def test_native_database_wait_holds_admission_and_process_death_retains_uncertainty(
        module, terminate, gate, tmp_path):
    database, action = prepare(module, tmp_path)
    connection = sqlite3.connect(database)
    connection.execute('BEGIN IMMEDIATE')
    process = subprocess.Popen(command(module, arguments(module, database, action, gate.directory)),
                               cwd=tmp_path, env=environment(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        deadline = time.monotonic() + 5
        while not pending(gate):
            assert process.poll() is None and time.monotonic() < deadline
            time.sleep(.005)
        with pytest.raises(Busy, match='DRAIN_TIMEOUT'):
            with gate.drain(.05):
                pytest.fail('admitted database writer escaped the barrier')
        markers = pending(gate)
        if terminate:
            process.kill()
        connection.rollback()
        stdout, stderr = process.communicate(timeout=10)
        if terminate:
            assert process.returncode < 0 and pending(gate) == markers
            with pytest.raises(GateError, match='UNSETTLED_OPERATION'):
                with gate.drain(.2):
                    pytest.fail('dead writer was treated as settled')
        else:
            assert process.returncode == 0, (stdout, stderr)
            verify(module, database)
            with gate.drain(.2):
                assert not pending(gate)
    finally:
        connection.close()
        if process.poll() is None:
            process.kill()
        process.communicate(timeout=5)


@pytest.mark.parametrize('module', MODULES)
def test_post_commit_failure_is_not_swallowed_and_later_success_cannot_clear_it(module, gate, tmp_path, monkeypatch):
    database, action = prepare(module, tmp_path)
    if module is service_notices:
        target, name = service_notices.Notices, 'revoke'
    elif module is support_admin:
        target, name = support_admin.support_ids, 'backfill'
    else:
        target, name = restricted_admin, 'migrate'
    original = getattr(target, name)

    def lose_ack(*args, **kwargs):
        original(*args, **kwargs)
        assert len(pending(gate)) == 1
        raise OSError('synthetic post-commit failure')

    monkeypatch.setattr(target, name, lose_ack)
    with pytest.raises((OSError, SystemExit)):
        module.main(arguments(module, database, action, gate.directory))
    verify(module, database)
    markers = pending(gate)
    assert len(markers) == 1
    monkeypatch.setattr(target, name, original)
    module.main(arguments(module, database, action, gate.directory))
    assert pending(gate) == markers
    with pytest.raises(GateError, match='UNSETTLED_OPERATION'):
        with gate.drain(.2):
            pytest.fail('lost acknowledgement forgotten')


def test_notice_cli_holds_gate_until_store_close_and_retains_close_failure(gate, tmp_path, monkeypatch):
    database, action = prepare(service_notices, tmp_path)
    original = service_notices.Notices
    observed = []

    class Connection:
        def __init__(self, database):
            self.database = database

        def __getattr__(self, name):
            return getattr(self.database, name)

        def __enter__(self):
            return self.database.__enter__()

        def __exit__(self, *args):
            return self.database.__exit__(*args)

        def close(self):
            assert len(pending(gate)) == 1
            self.database.close()
            observed.append('closed')
            raise OSError('synthetic close failure')

    def store(path):
        instance = original(path)
        instance.db = Connection(instance.db)
        return instance

    monkeypatch.setattr(service_notices, 'Notices', store)
    with pytest.raises(OSError, match='close failure'):
        service_notices.main(arguments(service_notices, database, action, gate.directory))
    assert observed == ['closed'] and len(pending(gate)) == 1
    verify(service_notices, database)


@pytest.mark.parametrize('lost_ack', [False, True])
def test_notice_cli_keeps_export_inside_gate_including_rename_failure(lost_ack, gate, tmp_path, monkeypatch):
    database, _ = prepare(service_notices, tmp_path)
    output = tmp_path / 'feed.json'
    original = service_notices.os.replace
    observed = []

    def replace(source, target):
        assert len(pending(gate)) == 1
        original(source, target)
        observed.append('renamed')
        if lost_ack:
            raise OSError('synthetic rename acknowledgement loss')

    monkeypatch.setattr(service_notices.os, 'replace', replace)
    argv = arguments(service_notices, database, ['export', '--output', str(output)], gate.directory)
    if lost_ack:
        with pytest.raises(OSError, match='acknowledgement loss'):
            service_notices.main(argv)
        assert len(pending(gate)) == 1
        with pytest.raises(GateError, match='UNSETTLED_OPERATION'):
            with gate.drain(.2):
                pytest.fail('uncertain published file was treated as settled')
    else:
        service_notices.main(argv)
        with gate.drain(.2):
            assert not pending(gate)
    assert observed == ['renamed']
    assert json.loads(output.read_text()) == dict(version=1, events=[])


@pytest.mark.parametrize('module', MODULES)
def test_closed_archive_refuses_and_recovers_without_checkout(module, gate, tmp_path):
    if module is service_notices:
        output = tmp_path / 'http'
        build_http(output)
        archive = output / 'friends-http.pyz'
    else:
        archive = tmp_path / 'operator.pyz'
        assert build(archive) == build(tmp_path / 'duplicate.pyz')
    database, action = prepare(module, tmp_path)
    code = '''
import importlib, sys
sys.path.insert(0, sys.argv[1])
module = importlib.import_module(sys.argv[2])
assert module.__file__.startswith(sys.argv[1] + '/')
module.main(sys.argv[3:])
'''
    argv = [sys.executable, '-I', '-c', code, str(archive), module.__name__,
            *arguments(module, database, action, gate.directory)]
    with zipfile.ZipFile(archive) as content:
        assert content.read('control/capture_gate.py') == (ROOT / 'control/capture_gate.py').read_bytes()
    with gate.drain(.5):
        result = subprocess.run(argv, cwd=tmp_path, capture_output=True, text=True, timeout=10)
    assert result.returncode == 75 and json.loads(result.stdout) == dict(error='CAPTURE_BUSY')
    result = subprocess.run(argv, cwd=tmp_path, capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    verify(module, database)
    assert not pending(gate)
