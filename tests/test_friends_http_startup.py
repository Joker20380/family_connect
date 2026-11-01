import io
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import shutil
import subprocess
import threading
from types import SimpleNamespace
import urllib.error

import pytest

from scripts.observe_friends_service import ObservationError, http_ready, wait_started


LISTENER = b'LISTEN 0 128 127.0.0.1:18086 0.0.0.0:* users:(("synthetic",pid=123,fd=3))\n'


def observation():
    return dict(service=dict(MainPID=123, NRestarts=0, effective_execstart_matches=True,
        running_argv_matches=True, ActiveState='active', SubState='running', NeedDaemonReload=False), jobs=dict(count=0))


def health_response(request, timeout):
    assert timeout == 2 and request.data == b'{}'
    raise urllib.error.HTTPError(request.full_url, 400, 'synthetic', {}, io.BytesIO(b'{"error":"invalid-request"}'))


def runner(raw=LISTENER, status=0):
    def run(command, **kwargs):
        assert command == ['ss', '-Hlntp', 'sport = :18086']
        assert kwargs == dict(stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=5, check=False)
        return SimpleNamespace(stdout=raw, returncode=status)

    return run


def test_listener_absent_is_pending_and_recorded():
    records = []
    assert not http_ready(observation(), run=runner(b''), record=records.append)
    assert records[0]['present'] is False and records[0]['owners'] == []


def test_exact_listener_and_all_http_routes_pass():
    records = []
    assert http_ready(observation(), run=runner(), open_url=health_response, record=records.append)
    assert len(records) == 4 and records[0]['owners'] == [123]
    assert all(record['status'] == 400 for record in records[1:])


@pytest.mark.parametrize('raw', [LISTENER.replace(b'pid=123', b'pid=456'),
    LISTENER + LISTENER.replace(b'pid=123', b'pid=456'), b'LISTEN 0 128 localhost:18086 *:*\n'])
def test_wrong_or_unattributed_listener_fails_closed(raw):
    records = []
    with pytest.raises(ObservationError, match='LISTENER_OWNER_MISMATCH'):
        http_ready(observation(), run=runner(raw), record=records.append)
    assert records[0]['present'] is True


@pytest.mark.parametrize('raw,status', [(b'', 1), (b'x' * 65537, 0), ('not-bytes', 0)])
def test_listener_read_failure_is_not_pending(raw, status):
    with pytest.raises(ObservationError, match='LISTENER_READ_FAILED'):
        http_ready(observation(), run=runner(raw, status))


@pytest.mark.parametrize('error', [ConnectionRefusedError(), TimeoutError(),
    urllib.error.URLError(ConnectionRefusedError()), urllib.error.URLError(TimeoutError())])
def test_initial_http_connection_race_is_pending(error):
    def open_url(request, timeout):
        raise error

    assert not http_ready(observation(), run=runner(), open_url=open_url)


def test_unrecognized_http_failure_is_not_retried():
    def open_url(request, timeout):
        raise urllib.error.URLError('unexpected-error')

    with pytest.raises(urllib.error.URLError):
        http_ready(observation(), run=runner(), open_url=open_url)


@pytest.mark.parametrize('status,body', [(500, b'{}'), (400, b'{}'), (400, b'bad-json'),
    (400, b'x' * 4097), (400, b'{"error":"invalid-request","error":"invalid-request"}')])
def test_unexpected_health_response_is_fatal(status, body):
    def open_url(request, timeout):
        raise urllib.error.HTTPError(request.full_url, status, 'synthetic', {}, io.BytesIO(body))

    with pytest.raises(ObservationError, match='HEALTH_RESPONSE_MISMATCH'):
        http_ready(observation(), run=runner(), open_url=open_url)


@pytest.mark.parametrize('port', [True, 0, 65536, '18086'])
def test_port_must_be_bounded_integer(port):
    with pytest.raises(ObservationError, match='INVALID_PORT'):
        http_ready(observation(), port=port)


def test_wait_covers_real_listener_health_gate_without_restart():
    moment = [0]
    listeners = iter([b'', LISTENER])
    records = []

    def pause(seconds):
        moment[0] += seconds

    def readiness(sample):
        return http_ready(sample, run=runner(next(listeners)), open_url=health_response, record=records.append)

    result = wait_started(['synthetic'], read=lambda expected: observation(), readiness=readiness,
        record=records.append, clock=lambda: moment[0], pause=pause, timeout=1, interval=.5)
    assert result == observation() and moment[0] == .5
    assert [record['present'] for record in records if record.get('result') == 'LISTENER_OBSERVED'] == [False, True]


@pytest.mark.skipif(shutil.which('ss') is None, reason='Real listener regression requires ss')
def test_real_delayed_listener_and_http_startup():
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            self.rfile.read(int(self.headers['Content-Length']))
            body = b'{"error":"invalid-request"}'
            self.send_response(400)
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *arguments):
            pass

    server = HTTPServer(('127.0.0.1', 0), Handler, bind_and_activate=False)
    server.server_bind()
    records = []
    sample = observation()
    sample['service']['MainPID'] = os.getpid()

    def readiness(value):
        return http_ready(value, port=server.server_port, record=records.append)

    def serve():
        server.server_activate()
        server.serve_forever(poll_interval=.05)

    worker = threading.Timer(.15, serve)
    try:
        assert not readiness(sample)
        worker.start()
        assert wait_started(['synthetic'], read=lambda expected: sample, readiness=readiness,
            timeout=5, interval=.05) == sample
        assert any(record.get('present') is True for record in records)
    finally:
        if worker.ident is not None:
            server.shutdown()
            worker.join(timeout=5)
        server.server_close()
