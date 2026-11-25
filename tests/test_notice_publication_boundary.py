import importlib.util
import json
import os
from pathlib import Path
import select
import socket
import sqlite3
import stat
import struct
import subprocess
import sys
import threading

import pytest

from control.capture_gate import Busy, GateError, initialize
from control.friends.notices import publish
from scripts import service_notices
from scripts.service_notices import Notices


ROOT = Path(__file__).resolve().parents[1]
NOTICE = dict(id='a' * 32, kind='information', title='Synthetic notice', body='Not production',
              platforms=['android'], days=1)


@pytest.fixture
def publication(tmp_path):
    gate = initialize(tmp_path / 'gate')
    registry = tmp_path / 'notices.sqlite'
    token_file = tmp_path / 'token'
    store = Notices(registry)
    store.grant('Synthetic operator', token_file)
    output = tmp_path / 'public'
    output.mkdir(mode=0o700)
    store.db.close()
    return gate, registry, token_file, output / 'family-connect-events-v1.json'


def feeds(output):
    return [json.loads(path.read_text()) for path in (output, output.with_name('family-connect-events-v2.json'))]


def pending(gate):
    return list((gate.directory / 'pending').iterdir())


def submit(publication):
    gate, registry, token, output = publication
    with gate.operation():
        return publish(registry, output, 'Bearer ' + token.read_text().strip(), NOTICE)


def test_success_syncs_each_rename_before_return_and_releases_locks(publication, monkeypatch):
    gate, registry, _, output = publication
    original_sync, original_replace = os.fsync, os.replace
    steps = []
    def sync(descriptor):
        path = Path(os.readlink('/proc/self/fd/' + str(descriptor)))
        if path == output.parent or path.parent == output.parent:
            steps.append('directory-sync' if stat.S_ISDIR(os.fstat(descriptor).st_mode) else 'file-sync')
            assert pending(gate)
        return original_sync(descriptor)
    def replace(source, target):
        steps.append('replace')
        return original_replace(source, target)
    monkeypatch.setattr(service_notices.os, 'fsync', sync)
    monkeypatch.setattr(service_notices.os, 'replace', replace)
    assert submit(publication) == dict(id=NOTICE['id'], status='published')
    assert steps == ['file-sync', 'replace', 'directory-sync'] * 2
    assert not pending(gate) and not list(output.parent.glob('.notices-*'))
    assert [value['version'] for value in feeds(output)] == [1, 2]
    assert all(value['events'][0]['id'] == NOTICE['id'] for value in feeds(output))
    assert all(path.stat().st_mode & 0o777 == 0o644 for path in output.parent.iterdir())
    with gate.drain(.1), sqlite3.connect(registry, timeout=.1) as database:
        database.execute('BEGIN IMMEDIATE')


@pytest.mark.parametrize('version', [1, 2])
@pytest.mark.parametrize('failure', ['file-sync', 'replace', 'directory-sync'])
def test_caught_partial_export_keeps_pending_even_after_success(publication, monkeypatch, version, failure):
    gate, registry, token, output = publication
    original_sync, original_replace = os.fsync, os.replace
    counts = dict(file_sync=0, replace=0, directory_sync=0)
    def sync(descriptor):
        path = Path(os.readlink('/proc/self/fd/' + str(descriptor)))
        kind = 'directory-sync' if path == output.parent else 'file-sync' if path.parent == output.parent else None
        if kind is not None:
            counts[kind.replace('-', '_')] += 1
            if kind == failure and counts[kind.replace('-', '_')] == version:
                raise OSError('synthetic publication sync failure')
        return original_sync(descriptor)
    def replace(source, target):
        counts['replace'] += 1
        if failure == 'replace' and counts['replace'] == version:
            raise OSError('synthetic publication replace failure')
        return original_replace(source, target)
    with monkeypatch.context() as patch:
        patch.setattr(service_notices.os, 'fsync', sync)
        patch.setattr(service_notices.os, 'replace', replace)
        with gate.operation():
            with pytest.raises(OSError, match='synthetic publication'):
                publish(registry, output, 'Bearer ' + token.read_text().strip(), NOTICE)
    assert len(pending(gate)) == 1
    assert not list(output.parent.glob('.notices-*'))
    with sqlite3.connect(registry, timeout=.1) as database:
        database.execute('BEGIN IMMEDIATE')
        assert database.execute('SELECT count(*) FROM events').fetchone() == (1,)
    assert submit(publication)['status'] == 'published'
    assert len(pending(gate)) == 1
    with pytest.raises(GateError, match='UNSETTLED_OPERATION'), gate.drain(.1):
        pytest.fail('successful retry erased the earlier partial publication')


def test_single_export_failure_also_retains_uncertainty(publication, monkeypatch):
    gate, registry, _, output = publication
    store = Notices(registry)
    def failure(*args):
        raise OSError('synthetic write failure')
    monkeypatch.setattr(store, '_write_feed', failure)
    try:
        with gate.operation(), pytest.raises(OSError):
            store.export(output)
        assert len(pending(gate)) == 1 and not store.db.in_transaction
    finally:
        store.db.close()


def test_both_versions_share_one_locked_snapshot_and_clock(publication, monkeypatch):
    _, registry, _, output = publication
    assert submit(publication)['status'] == 'published'
    store = Notices(registry)
    original = store._write_feed
    times = []
    def write(path, version, now):
        assert store.db.in_transaction
        times.append(now)
        with sqlite3.connect(registry, timeout=.01) as contender:
            with pytest.raises(sqlite3.OperationalError, match='locked'):
                contender.execute('BEGIN IMMEDIATE')
        return original(path, version, now)
    monkeypatch.setattr(store, '_write_feed', write)
    try:
        store.export_all(output)
        assert len(times) == 2 and times[0] == times[1]
        assert not store.db.in_transaction
    finally:
        store.db.close()


@pytest.mark.parametrize('failure', ['serialize', 'tempfile', 'commit'])
def test_prewrite_or_commit_error_does_not_leave_transaction_open(publication, monkeypatch, failure):
    gate, registry, _, output = publication
    store = Notices(registry)
    def fail(*args, **kwargs):
        raise OSError('synthetic boundary failure')
    if failure == 'serialize':
        monkeypatch.setattr(store, 'feed', fail)
    elif failure == 'tempfile':
        monkeypatch.setattr(service_notices.tempfile, 'mkstemp', fail)
    else:
        store.db.set_authorizer(lambda action, argument, *rest:
            sqlite3.SQLITE_DENY if action == sqlite3.SQLITE_TRANSACTION and argument == 'COMMIT' else sqlite3.SQLITE_OK)
    try:
        with gate.operation(), pytest.raises((OSError, sqlite3.DatabaseError)):
            store.export_all(output)
        assert len(pending(gate)) == 1 and not store.db.in_transaction
    finally:
        store.db.close()


@pytest.mark.parametrize('failure', ['resume', 'kill'])
def test_native_receiver_child_between_files_blocks_capture(publication, failure):
    gate, registry, token, output = publication
    code = '''import sys,time
from pathlib import Path
from control.capture_gate import Gate
from control.friends.notices import publish
from scripts.service_notices import Notices
original=Notices._write_feed
def write(self,path,version,now):
    original(self,path,version,now)
    if version==1:
        print('FIRST_DURABLE',flush=True)
        if sys.stdin.readline()!='resume\\n':raise RuntimeError('controller lost')
Notices._write_feed=write
with Gate(Path(sys.argv[1])).operation():
    import json
    publish(Path(sys.argv[2]),Path(sys.argv[4]),'Bearer '+Path(sys.argv[3]).read_text().strip(),json.loads(sys.argv[5]))
print('COMPLETE',flush=True)
'''
    child = subprocess.Popen([sys.executable, '-c', code, str(gate.directory), str(registry), str(token),
        str(output), json.dumps(NOTICE)], cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True)
    try:
        assert select.select([child.stdout], [], [], 5)[0]
        assert child.stdout.readline() == 'FIRST_DURABLE\n'
        assert output.exists() and not output.with_name('family-connect-events-v2.json').exists()
        with pytest.raises(Busy, match='DRAIN_TIMEOUT'), gate.drain(.05):
            pytest.fail('first file was mistaken for complete publication')
        if failure == 'resume':
            stdout, stderr = child.communicate('resume\n', timeout=5)
            assert child.returncode == 0 and stdout == 'COMPLETE\n' and not stderr
            assert not pending(gate)
            with gate.drain(.1):
                assert len(feeds(output)) == 2
        else:
            child.kill()
            child.communicate(timeout=5)
            assert child.returncode < 0 and len(pending(gate)) == 1
            assert submit(publication)['status'] == 'published'
            with pytest.raises(GateError, match='UNSETTLED_OPERATION'), gate.drain(.1):
                pytest.fail('dead receiver was incorrectly considered settled')
    finally:
        if child.poll() is None:
            child.kill()
        child.communicate(timeout=5)


@pytest.mark.parametrize('failure', ['success', 'export-error', 'lost-ack'])
def test_real_http_receiver_does_not_ack_before_both_exports(publication, monkeypatch, failure):
    gate, registry, token, output = publication
    spec = importlib.util.spec_from_file_location('notice_boundary_http', ROOT / 'deploy/friends/access-api.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ROOT = registry.parent
    module.capture_gate = gate
    default = '/opt/apps/family_connect/state-product-https/config/downloads/family-connect-events-v1.json'
    module.Path = lambda value: output if str(value) == default else Path(value)
    first, resume, finished = threading.Event(), threading.Event(), threading.Event()
    original = Notices._write_feed
    def write(store, path, version, now):
        original(store, path, version, now)
        if version == 1:
            first.set()
            assert resume.wait(5)
            if failure == 'export-error':
                raise OSError('synthetic receiver failure after first export')
    monkeypatch.setattr(Notices, '_write_feed', write)
    handler_errors = []
    class Handler(module.Handler):
        def do_POST(self):
            try:
                super().do_POST()
            except Exception as error:
                handler_errors.append(type(error).__name__)
                raise
            finally:
                finished.set()
    server = module.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    server.handle_error = lambda *args: None
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    connection = socket.create_connection(server.server_address, timeout=3)
    try:
        raw = json.dumps(NOTICE).encode()
        header = ('POST /friends/notices/publish HTTP/1.0\r\nHost: localhost\r\nContent-Type: application/json\r\n'
                  'Authorization: Bearer ' + token.read_text().strip() + '\r\nContent-Length: ' + str(len(raw)) + '\r\n\r\n')
        connection.sendall(header.encode() + raw)
        assert first.wait(3)
        assert not select.select([connection], [], [], .05)[0]
        with pytest.raises(Busy, match='DRAIN_TIMEOUT'), gate.drain(.05):
            pytest.fail('HTTP receiver still owns an incomplete export')
        if failure == 'lost-ack':
            connection.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))
            connection.close()
        resume.set()
        if failure != 'lost-ack':
            with connection.makefile('rb') as response:
                result = response.read(65536)
            assert result.startswith(b'HTTP/1.0 503' if failure == 'export-error' else b'HTTP/1.0 200')
    finally:
        resume.set()
        connection.close()
        completed = finished.wait(5)
        server.shutdown()
        server.server_close()
        thread.join(5)
        assert completed and not thread.is_alive()
    if failure != 'success':
        assert len(pending(gate)) == 1
        if failure == 'export-error':
            assert not output.with_name('family-connect-events-v2.json').exists()
        else:
            assert handler_errors and all(value['events'][0]['id'] == NOTICE['id'] for value in feeds(output))
        with pytest.raises(GateError, match='UNSETTLED_OPERATION'), gate.drain(.1):
            pytest.fail('caught HTTP error discarded uncertain publication')
    else:
        assert not pending(gate) and all(value['events'][0]['id'] == NOTICE['id'] for value in feeds(output))


def test_closed_http_package_uses_same_export_and_gate(publication, tmp_path):
    from scripts.package_friends_http import build, ARCHIVE
    gate, registry, token, output = publication
    bundle = tmp_path / 'bundle'
    build(bundle)
    code = '''import json,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from control.capture_gate import Gate
from control.friends.notices import publish
import scripts.service_notices as notices
assert notices.__file__.startswith(sys.argv[1]+'/')
with Gate(Path(sys.argv[2])).operation():
    value=publish(Path(sys.argv[3]),Path(sys.argv[5]),'Bearer '+Path(sys.argv[4]).read_text().strip(),json.loads(sys.argv[6]))
assert value['status']=='published'
print('PACKAGED_EXPORT_OK')
'''
    result = subprocess.run([sys.executable, '-I', '-B', '-c', code, str(bundle / ARCHIVE), str(gate.directory),
        str(registry), str(token), str(output), json.dumps(NOTICE)], cwd=tmp_path, capture_output=True, timeout=10)
    assert result.returncode == 0 and result.stdout == b'PACKAGED_EXPORT_OK\n' and not result.stderr
    assert not pending(gate) and len(feeds(output)) == 2
