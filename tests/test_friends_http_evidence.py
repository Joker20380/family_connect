import contextlib
import http.server
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import threading
import time

import pytest

from scripts.friends_http_acceptance import Evidence, accepted, classify, gate, probe, ProbeFailed, wait_backend, observe


@contextlib.contextmanager
def responder(status=400, payload=b'{"private":"never-record"}', delay=0):
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            time.sleep(delay)
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            try:
                self.wfile.write(payload)
            except OSError:
                pass

        do_GET = do_POST
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield 'http://127.0.0.1:' + str(server.server_address[1])
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


@pytest.mark.parametrize('status', [200, 400, 403, 404, 405, 429, 500, 502, 503])
def test_exact_status_redacted_and_durable(tmp_path, status):
    evidence = Evidence(tmp_path / 'evidence', 'attempt4-isolated')
    try:
        with responder(status) as origin:
            record = probe(origin, 'ordinary_challenge', evidence)
        assert record['status'] == status and record['transport_error'] is None
        assert accepted(record) == (status == 400)
    finally:
        evidence.close()
    path, = (tmp_path / 'evidence').glob('*.json')
    saved = json.loads(path.read_text())
    assert saved['status'] == status and saved['response_class'] == 'json-object'
    assert saved['generation'] == 'attempt4-isolated' and saved['timestamp'].endswith('Z')
    assert 'never-record' not in path.read_text() and 'body' not in saved and 'hash' not in saved
    assert path.stat().st_mode & 0o777 == 0o600


def test_record_before_failure_classification_and_rollback(tmp_path):
    evidence = Evidence(tmp_path / 'evidence', 'enabled')
    try:
        with responder(503) as origin:
            with pytest.raises(ProbeFailed):
                try:
                    gate(origin, evidence, {})
                finally:
                    saved = list(evidence.directory.glob('*.json'))
                    assert len(saved) == 1 and json.loads(saved[0].read_text())['status'] == 503
                    (tmp_path / 'rollback-done').write_text('done')
    finally:
        evidence.close()
    assert (tmp_path / 'rollback-done').exists()


def test_hard_exit_after_probe_keeps_receipt(tmp_path):
    script = Path('scripts/friends_http_acceptance.py').resolve()
    program = ('import runpy,sys,os;api=runpy.run_path(sys.argv[1]);'
               'evidence=api["Evidence"](sys.argv[2],"hard-exit");'
               'api["probe"](sys.argv[3],"restricted_canary",evidence);os._exit(23)')
    with responder(200, b'{"challenge":"secret-challenge"}') as origin:
        result = subprocess.run([sys.executable, '-I', '-c', program, str(script), str(tmp_path / 'evidence'), origin],
                                cwd=tmp_path, capture_output=True, timeout=10)
    assert result.returncode == 23 and not result.stdout and not result.stderr
    path, = (tmp_path / 'evidence').glob('*.json')
    assert json.loads(path.read_text())['status'] == 200 and 'secret-challenge' not in path.read_text()


def test_signal_during_probe_persists_interruption(tmp_path):
    script = Path('scripts/friends_http_acceptance.py').resolve()
    with responder(delay=2) as origin:
        process = subprocess.Popen([sys.executable, '-I', str(script), 'ready', '--origin', origin,
                                    '--generation', 'interrupted', '--evidence', str(tmp_path / 'evidence')],
                                   cwd=tmp_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            deadline = time.monotonic() + 5
            while not (tmp_path / 'evidence').exists():
                assert time.monotonic() < deadline and process.poll() is None
                time.sleep(.01)
            time.sleep(.1)
            process.send_signal(signal.SIGTERM)
            stdout, stderr = process.communicate(timeout=5)
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
    assert process.returncode != 0 and not stdout and not stderr
    path, = (tmp_path / 'evidence').glob('*.json')
    assert json.loads(path.read_text())['transport_error'] == 'interrupted'


@pytest.mark.parametrize('kind', ['connection', 'timeout', 'tls'])
def test_transport_error_categories(tmp_path, kind):
    evidence = Evidence(tmp_path / 'evidence', kind)
    try:
        if kind == 'connection':
            with socket.socket() as listener:
                listener.bind(('127.0.0.1', 0))
                origin = 'http://127.0.0.1:' + str(listener.getsockname()[1])
                record = probe(origin, 'status', evidence, timeout=.1)
        else:
            with responder(delay=1 if kind == 'timeout' else 0) as origin:
                record = probe(origin.replace('http:', 'https:') if kind == 'tls' else origin,
                               'status', evidence, timeout=.1)
        assert record['transport_error'] == kind and not accepted(record)
    finally:
        evidence.close()


def test_readiness_bounded_and_no_retry_in_gate(tmp_path):
    evidence = Evidence(tmp_path / 'evidence', 'not-ready')
    try:
        with responder(502) as origin:
            with pytest.raises(ProbeFailed):
                wait_backend(origin, evidence, seconds=.15)
        count = len(list(evidence.directory.glob('*.json')))
        assert 2 <= count <= 4
        with responder(502) as origin:
            with pytest.raises(ProbeFailed):
                gate(origin, evidence, {})
        assert len(list(evidence.directory.glob('*.json'))) == count + 1
    finally:
        evidence.close()


def test_evidence_rejects_unsafe_path_and_generation(tmp_path):
    directory = tmp_path / 'world'
    directory.mkdir(mode=0o755)
    with pytest.raises(ValueError):
        Evidence(directory, 'generation')
    with pytest.raises(ValueError):
        Evidence(tmp_path / 'bad-generation', 'https://private-url')
    link = tmp_path / 'link'
    link.symlink_to(directory)
    with pytest.raises(OSError):
        Evidence(link, 'generation')


def test_body_bounds_and_classification():
    assert classify(b'x' * 65537, 'application/json') == 'oversized'
    assert classify(b'[]', 'application/json') == 'json-other'
    assert classify(b'broken', 'application/json') == 'invalid-json'
    assert classify(b'<html>private</html>', 'text/html') == 'html'


def test_canary_200_requires_challenge_shape(tmp_path):
    evidence = Evidence(tmp_path / 'evidence', 'wrong-route')
    try:
        with responder(200, b'{}') as origin:
            record = probe(origin, 'restricted_canary', evidence)
        assert record['response_class'] == 'invalid-challenge' and not accepted(record)
    finally:
        evidence.close()


def test_fsync_precedes_classification_and_failure_is_fatal(tmp_path, monkeypatch):
    evidence = Evidence(tmp_path / 'evidence', 'fsync')
    calls = []
    original = os.fsync
    def fsync(descriptor):
        calls.append(descriptor)
        return original(descriptor)
    monkeypatch.setattr(os, 'fsync', fsync)
    try:
        with responder(502) as origin:
            record = probe(origin, 'ordinary_challenge', evidence)
        assert len(calls) == 2 and calls[-1] == evidence.descriptor
        assert not accepted(record)
        def failed(descriptor):
            raise OSError('Synthetic fsync failure')
        monkeypatch.setattr(os, 'fsync', failed)
        with responder(400) as origin, pytest.raises(OSError):
            probe(origin, 'ordinary_challenge', evidence)
    finally:
        evidence.close()


def test_observer_keeps_all_failures_without_claiming_acceptance(tmp_path):
    evidence = Evidence(tmp_path / 'evidence', 'transition')
    try:
        with responder(502) as origin:
            observe(origin, evidence, .15)
    finally:
        evidence.close()
    records = [json.loads(path.read_text()) for path in evidence.directory.glob('*.json')]
    assert len(records) >= 3 and all(record['status'] == 502 for record in records)
    assert set(record['label'] for record in records) == {'status', 'ordinary_challenge', 'ordinary_chat'}


@pytest.mark.parametrize('count', [1, 26])
def test_cli_default_requires_all_26_and_failure_keeps_evidence(tmp_path, count):
    script = Path('scripts/friends_http_acceptance.py').resolve()
    identities = tmp_path / 'identities.json'
    identities.write_text(json.dumps({'canary': {'public_identity': 'private-canary-marker', 'wireguard_public_key': 'test'},
                         'non_canary': [{'public_identity': 'private-test-' + str(index), 'wireguard_public_key': 'test'}
                                        for index in range(count)]}))
    identities.chmod(0o600)
    with responder(503) as origin:
        result = subprocess.run([sys.executable, '-I', str(script), 'gate', '--origin', origin,
                                 '--generation', 'cli-failure', '--evidence', str(tmp_path / 'evidence'),
                                 '--identities', str(identities)], cwd=tmp_path, capture_output=True, timeout=5)
    assert result.returncode != 0
    assert b'private-' not in result.stdout + result.stderr
    receipts = list((tmp_path / 'evidence').glob('*.json'))
    assert len(receipts) == (1 if count == 26 else 0)
    if receipts:
        assert json.loads(receipts[0].read_text())['status'] == 503
        assert 'private-' not in receipts[0].read_text()
