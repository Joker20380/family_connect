"""Synthetic HTTPS/PG completion, including a commit outliving its sending process."""
from contextlib import ExitStack, contextmanager
from datetime import datetime, timedelta, timezone
import ipaddress
import json
import os
from pathlib import Path
import socket
import sqlite3
import ssl
import subprocess
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from django.contrib.auth import get_user_model
from django.db import connection, transaction
import pytest

from apps.console.models import AuditRecord, SystemMessage
from control.capture_gate import Busy, GateError, initialize
from tests.test_publication_fence import fence
import psycopg


CHILD = '''import os
import fc_control_plane.settings as settings
settings.DATABASES['default']['NAME'] = os.environ['SETTLEMENT_TEST_DATABASE']
import manage
raise SystemExit(manage.main())
'''


def private_write(path, contents):
    with path.open('xb') as stream:
        os.fchmod(stream.fileno(), 0o600)
        stream.write(contents)


def certificate(root):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'synthetic-settlement')])
    now = datetime.now(timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
            .public_key(key.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(minutes=1)).not_valid_after(now + timedelta(hours=1))
            .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
            .add_extension(x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address('127.0.0.1'))]),
                           critical=False).sign(key, hashes.SHA256()))
    private_write(root / 'tls.key', key.private_bytes(serialization.Encoding.PEM,
                  serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    private_write(root / 'tls.pem', cert.public_bytes(serialization.Encoding.PEM))
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(root / 'tls.pem', root / 'tls.key')
    return context


class NoticeEndpoint:
    def __init__(self, root, lost_reply):
        self.root, self.lost_reply = root, lost_reply
        self.committed, self.release = threading.Event(), threading.Event()
        self.failures = []
        self.requests = []
        self.database = root / 'remote.sqlite3'
        with sqlite3.connect(self.database) as database:
            database.execute('CREATE TABLE events (id TEXT PRIMARY KEY, payload TEXT NOT NULL)')
        self.database.chmod(0o600)

    def rows(self):
        with sqlite3.connect(self.database) as database:
            return [json.loads(row[0]) for row in database.execute('SELECT payload FROM events ORDER BY id')]

    def handler(self):
        endpoint = self

        class Handler(BaseHTTPRequestHandler):
            def setup(self):
                self.request.settimeout(3)
                super().setup()

            def log_message(self, *arguments):
                pass

            def respond(self, value):
                raw = json.dumps(value).encode()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def do_POST(self):
                try:
                    assert self.path == '/friends/notices/publish'
                    assert self.headers['Authorization'] == 'Bearer ' + 'a' * 64
                    size = int(self.headers['Content-Length'])
                    assert 0 < size < 10000
                    value = json.loads(self.rfile.read(size))
                    endpoint.requests.append(value)
                    event = {field: value[field] for field in ('id', 'kind', 'title', 'body', 'platforms')}
                    event.update(created=int(time.time()))
                    event['expires'] = event['created'] + value['days'] * 86400
                    with sqlite3.connect(endpoint.database) as database:
                        database.execute('PRAGMA synchronous=FULL')
                        database.execute('INSERT OR IGNORE INTO events VALUES (?, ?)',
                                         (value['id'], json.dumps(event)))
                    endpoint.committed.set()
                    assert endpoint.release.wait(10), 'synthetic response release timed out'
                    if endpoint.lost_reply:
                        self.connection.shutdown(socket.SHUT_RDWR)
                        self.close_connection = True
                    else:
                        self.respond(dict(id=value['id'], status='published'))
                except BaseException as failure:
                    endpoint.failures.append(failure)
                    self.close_connection = True

            def do_GET(self):
                try:
                    assert self.path == '/downloads/family-connect-events-v2.json'
                    self.respond(dict(version=2, events=endpoint.rows()))
                except BaseException as failure:
                    endpoint.failures.append(failure)
                    self.close_connection = True

        return Handler


@contextmanager
def endpoint_at(root, lost_reply):
    endpoint = NoticeEndpoint(root, lost_reply)
    server = HTTPServer(('127.0.0.1', 0), endpoint.handler())
    server.socket = certificate(root).wrap_socket(server.socket, server_side=True)
    endpoint.origin = 'https://127.0.0.1:' + str(server.server_port)
    worker = threading.Thread(target=server.serve_forever, kwargs=dict(poll_interval=.02))
    worker.start()
    try:
        yield endpoint
    finally:
        endpoint.release.set()
        server.shutdown()
        server.server_close()
        worker.join(4)
        assert not worker.is_alive()
        assert not endpoint.failures


@contextmanager
def publisher_process(root, gate, endpoint):
    environment = {name: value for name, value in os.environ.items()
                   if not name.startswith(('FC_', 'PG', 'POSTGRES_', 'DJANGO_', 'SSL_CERT_'))}
    database = connection.settings_dict
    environment.update(CONTROL_PLANE_MODE='synthetic', DJANGO_SECRET_KEY='synthetic-' + 's' * 64,
                       POSTGRES_HOST=database['HOST'], POSTGRES_PORT=str(database['PORT']),
                       POSTGRES_PASSWORD=database['PASSWORD'], SETTLEMENT_TEST_DATABASE=database['NAME'],
                       DJANGO_SETTINGS_MODULE='fc_control_plane.settings',
                       FC_CONTROL_CAPTURE_GATE=str(gate.directory), SSL_CERT_FILE=str(root / 'tls.pem'),
                       PGAPPNAME='fc-settlement-' + uuid.uuid4().hex)
    with subprocess.Popen([sys.executable, '-c', CHILD, 'publish_system_messages',
                           '--origin', endpoint.origin, '--token-file', str(root / 'publisher.token'), '--limit', '1'],
                          cwd=Path(__file__).resolve().parents[1], env=environment,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
        try:
            yield process, environment['PGAPPNAME']
        finally:
            if process.poll() is None:
                process.kill()
            process.communicate(timeout=5)


def pending(gate):
    return {entry.name: entry.read_bytes() for entry in (gate.directory / 'pending').iterdir()}


def wait_for_commit_lock(application, process):
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        assert process.poll() is None, 'synthetic publisher exited before commit observation'
        with connection.cursor() as cursor:
            cursor.execute('SELECT pg_stat_clear_snapshot()')
            cursor.execute('SELECT state, wait_event_type, query FROM pg_stat_activity WHERE application_name=%s',
                           [application])
            rows = cursor.fetchall()
        if len(rows) == 1 and rows[0] == ('active', 'Lock', 'COMMIT'):
            return
        time.sleep(.02)
    pytest.fail('synthetic publisher did not reach the native PostgreSQL commit lock')


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize('outcome', ['success', 'lost_reply', 'killed_during_commit'])
def test_native_publication_settles_only_after_remote_and_postgres(root_path, outcome):
    root = root_path
    gate = initialize(root / 'gate')
    private_write(root / 'publisher.token', ('a' * 64).encode())
    actor = get_user_model().objects.create_superuser(username='synthetic-settlement')
    message = SystemMessage.objects.create(created_by=actor, title='Synthetic', body='Not production',
                                          kind='information', platforms=['android'], days=1, status='queued')
    with endpoint_at(root, outcome == 'lost_reply') as endpoint, ExitStack() as stack:
        with transaction.atomic():
            get_user_model().objects.select_for_update().get(pk=actor.pk)
            process, application = stack.enter_context(publisher_process(root, gate, endpoint))
            assert endpoint.committed.wait(8), 'synthetic HTTPS request was not committed'
            assert len(endpoint.rows()) == 1 and len(pending(gate)) == 1
            message.refresh_from_db()
            assert message.status == 'queued'
            with pytest.raises(Busy, match='DRAIN_TIMEOUT'), gate.drain(.05):
                pytest.fail('in-flight HTTPS publication permitted capture')
            endpoint.release.set()
            wait_for_commit_lock(application, process)
            with pytest.raises(psycopg.errors.LockNotAvailable), fence():
                pytest.fail('HTTP acknowledgement is not PostgreSQL settlement')
            assert not AuditRecord.objects.filter(target=message.pk.hex).exists()
            with pytest.raises(Busy, match='DRAIN_TIMEOUT'), gate.drain(.05):
                pytest.fail('remote success before PostgreSQL commit permitted capture')
            retained = pending(gate)
            assert len(retained) == 1
            if outcome == 'killed_during_commit':
                process.kill()
                assert process.wait(timeout=5) < 0
                with pytest.raises(psycopg.errors.LockNotAvailable), fence():
                    pytest.fail('sender death did not settle its still-blocked PostgreSQL backend')
        stdout, stderr = process.communicate(timeout=8)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            with connection.cursor() as cursor:
                cursor.execute('SELECT count(*) FROM pg_stat_activity WHERE application_name=%s', [application])
                if cursor.fetchone()[0] == 0:
                    break
            time.sleep(.02)
        else:
            pytest.fail('owned publisher PostgreSQL backend did not settle')
        message.refresh_from_db()
        status_after_exit = message.status
        if status_after_exit == 'unknown':
            with pytest.raises(ValueError, match='UNRESOLVED_PUBLICATION'), fence():
                pytest.fail('unknown external outcome was accepted')
        else:
            with fence() as boundary:
                boundary.check()
                assert not boundary.observation['external_settlement_proven']
                assert not boundary.observation['capture_permitted']
        if outcome == 'success':
            assert process.returncode == 0 and b"'published': 1" in stdout and not stderr
            assert message.status == 'published' and not pending(gate)
            with gate.drain(.2):
                assert AuditRecord.objects.filter(target=message.pk.hex, action='system.published').count() == 1
        else:
            if outcome == 'lost_reply':
                assert process.returncode == 0 and b"'unknown': 1" in stdout and not stderr
                assert message.status == 'unknown'
            else:
                assert message.status in ('queued', 'published')
            assert pending(gate) == retained
            with pytest.raises(GateError, match='UNSETTLED_OPERATION'), gate.drain(.2):
                pytest.fail('lost outcome or killed publisher permitted capture')
            with publisher_process(root, gate, endpoint) as (retry, _application):
                retry.communicate(timeout=8)
                assert retry.returncode == 0
            assert pending(gate) == retained
            with pytest.raises(GateError, match='UNSETTLED_OPERATION'), gate.drain(.2):
                pytest.fail('a later successful command erased the prior uncertainty')
        assert len(endpoint.rows()) == 1
        assert all(value == endpoint.requests[0] for value in endpoint.requests)
        expected_requests = 2 if outcome == 'killed_during_commit' and status_after_exit == 'queued' else 1
        assert len(endpoint.requests) == expected_requests
        private_write(root / 'receipt.json', json.dumps(dict(outcome=outcome,
                      status_after_exit=status_after_exit, retained_markers=len(pending(gate)),
                      remote_events=len(endpoint.rows()), publication_requests=len(endpoint.requests),
                      runtime_qualified=False, capture_permitted=False)).encode())


@pytest.fixture
def root_path(tmp_path):
    tmp_path.chmod(0o700)
    return tmp_path
