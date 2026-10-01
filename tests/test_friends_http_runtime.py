import ast
import base64
import contextlib
from datetime import datetime, timedelta, timezone
import hashlib
import http.client
import ipaddress
import json
import os
from pathlib import Path
import re
import shutil
import shlex
import socket
import subprocess
import sys
import time
import zipfile

from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat
from cryptography import x509
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.x509.oid import NameOID
import pytest

from device_identity.device import DeviceIdentity
from scripts.package_friends_http import ARCHIVE, ROOT, build
from scripts.friends_http_acceptance import Evidence, ProbeFailed, gate, probe, wait_backend
from test_friends_restricted import configured


def port():
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        return listener.getsockname()[1]


def request(number, path, method='POST', body=None):
    connection = http.client.HTTPConnection('127.0.0.1', number, timeout=3)
    connection.request(method, path, body=None if method in ('GET', 'HEAD') else json.dumps({} if body is None else body),
                       headers={'Content-Type': 'application/json'})
    response = connection.getresponse()
    value = response.read(65537)
    connection.close()
    return response.status, value


@pytest.fixture
def runtime(tmp_path):
    supplied = os.environ.get('FC_TEST_HTTP_ARTIFACT')
    artifact = Path(supplied).resolve() if supplied else tmp_path / 'bundle'
    if not supplied:
        build(artifact)
    state = tmp_path / 'private'
    state.mkdir(mode=0o700)
    service, canary, _ = configured(state, int(time.time()))
    non_canary = DeviceIdentity.generate()
    invitation = service.access.invite()
    challenge = service.access.challenge(non_canary.public_identity, non_canary.wireguard_public_key, 'activate', invitation)
    service.access.complete(non_canary.prove_transport_key(challenge['challenge']), 'activate')
    values = {'issuer.json': json.dumps(service.manifest).encode(),
              'issuer.key': service.signing_key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()),
              'anchor.pub': base64.b64encode(service.anchor),
              'admission.json': json.dumps({'devices': [canary.reference]}).encode(),
              'revocations.pem': service.crl_source(), 'directory.json': service.seed_source()}
    for name, value in values.items():
        path = state / name
        path.write_bytes(value)
        path.chmod(0o600)
    environment = dict(PATH=os.defpath, HOME=str(tmp_path), FC_FRIENDS_RESTRICTED_DIR=str(state), PYTHONDONTWRITEBYTECODE='1')
    backend = port()
    command = [sys.executable, '-I', str(artifact / ARCHIVE), '--root', str(state), '--port', str(backend)]
    identities = {'canary': dict(public_identity=canary.public_identity, wireguard_public_key=canary.wireguard_public_key),
                  'non_canary': [dict(public_identity=non_canary.public_identity, wireguard_public_key=non_canary.wireguard_public_key)]}
    yield dict(artifact=artifact, state=state, environment=environment, backend=backend, command=command,
               canary=canary, access=service.access, identities=identities, temporary=tmp_path)


@contextlib.contextmanager
def running(runtime):
    process = subprocess.Popen(runtime['command'], env=runtime['environment'], cwd=runtime['temporary'],
                               stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        deadline = time.monotonic() + 10
        while True:
            assert process.poll() is None, 'Packaged HTTP handler exited'
            try:
                if request(runtime['backend'], '/friends/challenge')[0] == 400:
                    break
            except OSError:
                pass
            assert time.monotonic() < deadline
            time.sleep(.05)
        yield
    finally:
        process.terminate()
        process.communicate(timeout=5)


def nginx_sections():
    source = (ROOT / 'deploy/friends/install-access.py').read_text()
    ordinary = source[source.index('        location ~ ^/friends/'):source.index("\n'''", source.index('        location ~ ^/friends/'))]
    old = 'referral/(issue|claim)|device/status|notices/publish)'
    assert ordinary.count(old) == 1
    ordinary = ordinary.replace(old, 'referral/(issue|claim)|notices/(publish|device/(role|publish|list|edit)))')
    tree = ast.parse((ROOT / 'deploy/server-load/publish.py').read_text())
    status = next(ast.literal_eval(node.value) for node in tree.body
                  if isinstance(node, ast.Assign) and node.targets[0].id == 'section')
    return ordinary, status


@contextlib.contextmanager
def ingress(runtime, enabled, tls=False):
    executable = os.environ.get('FC_TEST_NGINX')
    if not executable:
        pytest.skip('FC_TEST_NGINX required for real nginx activation matrix')
    work = runtime['temporary'] / ('enabled' if enabled else 'normal')
    work.mkdir()
    snapshot = work / 'snapshot.json'
    snapshot.write_text('{"version":1,"gateways":[]}')
    frontend = port()
    tls_config = ''
    if tls:
        key = Ed25519PrivateKey.generate()
        name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'isolated HTTP contract')])
        now = datetime.now(timezone.utc)
        certificate = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
                       .serial_number(x509.random_serial_number()).not_valid_before(now - timedelta(minutes=1))
                       .not_valid_after(now + timedelta(hours=1)).add_extension(x509.BasicConstraints(ca=True, path_length=0), True)
                       .add_extension(x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address('127.0.0.1'))]), False)
                       .sign(key, None))
        certificate_path = work / 'certificate.pem'
        private_path = work / 'private.pem'
        certificate_path.write_bytes(certificate.public_bytes(Encoding.PEM))
        private_path.write_bytes(key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()))
        private_path.chmod(0o600)
        runtime['https_anchor'] = certificate_path
        tls_config = ' ssl;ssl_certificate ' + str(certificate_path) + ';ssl_certificate_key ' + str(private_path)
    ordinary, status = nginx_sections()
    location = (ROOT / 'deploy/friends/restricted/nginx-location.conf').read_text() if enabled else ''
    server = status.replace('/etc/fc/server-load/snapshot.json', str(snapshot)) + location + ordinary
    server = server.replace('127.0.0.1:18084', '127.0.0.1:' + str(runtime['backend']))
    config = work / 'nginx.conf'
    config.write_text('pid ' + str(work / 'nginx.pid') + ';\nerror_log ' + str(work / 'errors.log') + ';\n'
                      'events {}\nhttp { access_log off; client_body_temp_path ' + str(work / 'body') + ';'
                      + ''.join(kind + '_temp_path ' + str(work / kind) + ';' for kind in ('proxy', 'fastcgi', 'uwsgi', 'scgi')) +
                      'server {listen 127.0.0.1:' + str(frontend) + tls_config + ';' + server + '\nlocation / {return 404;} }}')
    command = shlex.split(executable) + ['-p', str(work), '-c', str(config), '-e', str(work / 'errors.log')]
    subprocess.run(command + ['-t'], capture_output=True, check=True)
    process = subprocess.Popen(command + ['-g', 'daemon off;'], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        deadline = time.monotonic() + 10
        while True:
            assert process.poll() is None, 'Isolated nginx exited'
            try:
                if tls:
                    with socket.create_connection(('127.0.0.1', frontend), timeout=.1):
                        break
                elif request(frontend, '/status/server-load.json', 'GET')[0] == 200:
                    break
            except OSError:
                pass
            assert time.monotonic() < deadline
            time.sleep(.05)
        yield frontend
    finally:
        process.terminate()
        process.communicate(timeout=5)


def test_final_artifact_closure(runtime):
    artifact = runtime['artifact']
    with zipfile.ZipFile(artifact / ARCHIVE) as archive:
        for name in archive.namelist():
            if name.endswith('.py') and name != '__main__.py':
                assert archive.read(name) == (artifact / 'app' / name).read_bytes()
        assert archive.read('friends_http.py') == (ROOT / 'deploy/friends/access-api.py').read_bytes()
    for name, digest in json.loads((artifact / 'sha256.json').read_text()).items():
        assert hashlib.sha256((artifact / name).read_bytes()).hexdigest() == digest
    result = subprocess.run(runtime['command'] + ['--help'], cwd=runtime['temporary'], env=runtime['environment'], capture_output=True)
    assert result.returncode == 0 and not result.stderr
    program = ('import runpy,sys,json,argparse;sys.argv=[sys.argv[1],"--help"]\n'
               'def inspect(parser):\n'
               ' from control.friends import notices,restricted\n'
               ' assert "/opt/apps/family_connect/friends-access/app" not in sys.path\n'
               ' print(json.dumps({name:sys.modules[name].__file__ for name in '
               '["friends_http","control.friends.access","control.friends.chat","control.friends.notices",'
               '"control.friends.restricted","messenger.service_events","scripts.service_notices",'
               '"clients.desktop.profile_config"]}))\n'
               'argparse.ArgumentParser.print_help=inspect\n'
               'try:runpy.run_path(sys.argv[0],run_name="__main__")\n'
               'except SystemExit as result:assert result.code==0')
    result = subprocess.run([sys.executable, '-I', '-c', program, str(artifact / ARCHIVE)],
                            cwd=runtime['temporary'], env=dict(runtime['environment'], PYTHONPATH=str(ROOT)),
                            capture_output=True, text=True, check=True)
    assert all(path.startswith(str(artifact / ARCHIVE) + '/') for path in json.loads(result.stdout.splitlines()[-1]).values())
    with running(runtime):
        assert request(runtime['backend'], '/friends/challenge')[0] == 400


def test_build_reproducible_and_explicit_source_guard(tmp_path, monkeypatch):
    first, second = tmp_path / 'first', tmp_path / 'second'
    initial = build(first)
    copyfile = shutil.copyfile

    def copy_with_different_metadata(source, destination):
        result = copyfile(source, destination)
        os.utime(destination, (1800000000, 1800000000))
        return result

    monkeypatch.setattr(shutil, 'copyfile', copy_with_different_metadata)
    assert build(second) == initial
    manifest = json.loads((ROOT / 'deploy/friends/restricted/http-runtime-files.json').read_text())
    expected = set(manifest) | {'friends_http.py', '__main__.py'}
    with zipfile.ZipFile(first / ARCHIVE) as archive:
        assert {entry.filename for entry in archive.infolist() if not entry.is_dir()} == expected
        assert all(entry.date_time == (1980, 1, 1, 0, 0, 0) for entry in archive.infolist())
        for name in expected:
            content = archive.read(name)
            assert not re.search(rb'-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----\s+[A-Za-z0-9+/=]{32}', content)
            assert not re.search(rb'https://telemost\.yandex\.ru/j/[A-Za-z0-9_-]+', content)
            assert b'y0_Ag' not in content
            if name != '__main__.py':
                source = ROOT / ('deploy/friends/access-api.py' if name == 'friends_http.py' else name)
                assert content == source.read_bytes()


@pytest.mark.parametrize('mutation', ['valid', 'future', 'malformed'])
def test_embedded_http_nanosecond_delivery(runtime, mutation):
    clock_ns = int(time.time()) * 1_000_000_000 + 532900000
    second = datetime.fromtimestamp(clock_ns // 1_000_000_000, timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')
    directory_path = runtime['state'] / 'directory.json'
    value = json.loads(directory_path.read_text())
    value['issued_at'] = second + ('.532900001Z' if mutation == 'future' else '.532852358Z')
    if mutation == 'malformed':
        value['seeds'][0]['transport'] = 'invalid'
    directory_path.write_text(json.dumps(value))
    program = ('import runpy,sys,time\n'
               'instant=int(sys.argv.pop(1));time.time_ns=lambda:instant\n'
               'time.time=lambda:instant/1000000000\n'
               'sys.argv=sys.argv[1:];runpy.run_path(sys.argv[0],run_name="__main__")\n')
    runtime['command'] = [sys.executable, '-I', '-c', program, str(clock_ns), *runtime['command'][2:]]
    with running(runtime):
        status, raw = request(runtime['backend'], '/friends/restricted-readiness/challenge', body=runtime['identities']['canary'])
        assert status == 200
        proof = runtime['canary'].prove_transport_key(json.loads(raw)['challenge'])
        status, raw = request(runtime['backend'], '/friends/restricted-readiness', body=proof)
        assert status == (200 if mutation == 'valid' else 503)
        if mutation == 'valid':
            response = json.loads(raw)
            assert response['directory'] == value and response['revision'] == 1
            assert response['minimum_crl'] == 1 and response['expires_at'] > clock_ns // 1_000_000_000
        else:
            assert json.loads(raw) == {'error': 'unavailable'}


def test_accepted_sync_directory_to_http_readiness(runtime):
    supplied = os.environ.get('FC_TEST_SYNC_ARTIFACT')
    if not supplied:
        pytest.skip('FC_TEST_SYNC_ARTIFACT required for pinned archive interoperability')
    archive = Path(supplied).resolve()
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == 'cb6f050ec49ee4b65fa65c5327e32d6271d714ef6f8e695f16cb3c85b60f386f'
    profile = runtime['temporary'] / 'synthetic-gateway.json'
    profile.write_text(json.dumps({'family': 'a' * 32, 'gateway': 'b' * 32}))
    profile.chmod(0o600)
    receipt = runtime['temporary'] / 'sync-directory-receipt.json'
    result = subprocess.run([sys.executable, '-I', str(archive), 'directory-check', '--profile', str(profile),
                             '--directory', str(runtime['state'] / 'directory.json'), '--receipt', str(receipt),
                             '--generation', 'http-package-cross-component'], cwd=runtime['temporary'],
                            env=runtime['environment'], capture_output=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert json.loads(receipt.read_text())['result'] == 'passed'
    with running(runtime):
        status, raw = request(runtime['backend'], '/friends/restricted-readiness/challenge', body=runtime['identities']['canary'])
        assert status == 200
        proof = runtime['canary'].prove_transport_key(json.loads(raw)['challenge'])
        status, raw = request(runtime['backend'], '/friends/restricted-readiness', body=proof)
        assert status == 200
        assert json.loads(raw)['directory'] == json.loads((runtime['state'] / 'directory.json').read_text())


@pytest.mark.parametrize('enabled', [False, True])
def test_actual_nginx_handler_matrix(runtime, enabled):
    if not enabled:
        runtime['environment'].pop('FC_FRIENDS_RESTRICTED_DIR')
    with running(runtime), ingress(runtime, enabled) as frontend:
        assert request(frontend, '/status/server-load.json', 'GET')[0] == 200
        assert request(frontend, '/status/server-load.json', 'POST')[0] == 403
        for route in ('challenge', 'chat/challenge', 'activate', 'configuration/ru', 'referral/claim', 'notices/device/role'):
            assert request(frontend, '/friends/' + route)[0] == 400
            assert request(frontend, '/friends/' + route, 'GET')[0] == 405
        path = '/friends/restricted-readiness/challenge'
        assert request(frontend, path)[0] == (400 if enabled else 404)
        assert request(frontend, path, 'GET')[0] == (405 if enabled else 404)
        for suffix in ('/', '/extra', '-other'):
            assert request(frontend, path + suffix)[0] == 404
        assert request(frontend, '/friends/unknown')[0] == 404
        assert request(frontend, '/friends/challenge/', body={})[0] == 404
        ordinary = dict(runtime['identities']['canary'], purpose='ru', invitation='')
        assert request(frontend, '/friends/challenge', body=ordinary)[0] == 200
        new_device = DeviceIdentity.generate()
        invitation = runtime['access'].invite()
        status, raw = request(frontend, '/friends/challenge', body=dict(public_identity=new_device.public_identity,
                              wireguard_public_key=new_device.wireguard_public_key, purpose='activate', invitation=invitation))
        assert status == 200
        proof = new_device.prove_transport_key(json.loads(raw)['challenge'])
        status, raw = request(frontend, '/friends/activate', body=proof)
        assert status == 200 and json.loads(raw)['device'] == new_device.reference
        status, raw = request(frontend, path, body=runtime['identities']['canary'])
        assert status == (200 if enabled else 404)
        assert request(frontend, path, body=runtime['identities']['non_canary'][0])[0] == (403 if enabled else 404)
        if enabled:
            response = json.loads(raw)
            assert set(response) == {'challenge', 'expires_at', 'audience'}
            proof = runtime['canary'].prove_transport_key(response['challenge'])
            status, raw = request(frontend, '/friends/restricted-readiness', body=proof)
            assert status == 200
            assert 'private_key' not in json.loads(raw)
            evidence = Evidence(runtime['temporary'] / 'gate', 'enabled')
            try:
                gate('http://127.0.0.1:' + str(frontend), evidence, runtime['identities'])
            finally:
                evidence.close()
            assert len(list(evidence.directory.glob('*.json'))) == 6


@pytest.mark.parametrize('missing', ['friends_http.py', 'control/friends/chat.py', 'messenger/admission.py',
                                  'scripts/service_notices.py', 'clients/desktop/profile_config.py'])
def test_missing_artifact_dependency_fails_in_isolation(runtime, missing):
    broken = runtime['temporary'] / 'broken.pyz'
    with zipfile.ZipFile(runtime['artifact'] / ARCHIVE) as original, zipfile.ZipFile(broken, 'w') as output:
        for entry in original.infolist():
            if entry.filename != missing:
                output.writestr(entry, original.read(entry))
    program = ('import runpy,sys,argparse;sys.argv=[sys.argv[1],"--help"]\n'
               'def inspect(parser):\n'
               ' from control.friends import restricted,notices\n'
               'argparse.ArgumentParser.print_help=inspect\n'
               'try:runpy.run_path(sys.argv[0],run_name="__main__")\n'
               'except SystemExit as result:assert result.code==0')
    result = subprocess.run([sys.executable, '-I', '-c', program, str(broken)], cwd=runtime['temporary'],
                            env=dict(runtime['environment'], PYTHONPATH=str(ROOT)), capture_output=True)
    assert result.returncode != 0 and (b'ImportError' in result.stderr or b'ModuleNotFoundError' in result.stderr)


@pytest.mark.parametrize('body', [None, [], {'public_identity': 'bad', 'wireguard_public_key': 'bad'},
                               {'extra': True}, 'x' * 8193])
def test_malformed_restricted_bounded_without_config(runtime, body):
    runtime['environment'].pop('FC_FRIENDS_RESTRICTED_DIR')
    with running(runtime):
        assert request(runtime['backend'], '/friends/restricted-readiness/challenge', body=body)[0] == 400
        assert request(runtime['backend'], '/friends/restricted-readiness/challenge', body=runtime['identities']['canary'])[0] == 503


def test_nginx_reports_unready_upstream_without_status_regression(runtime):
    with ingress(runtime, True) as frontend:
        assert request(frontend, '/status/server-load.json', 'GET')[0] == 200
        assert request(frontend, '/friends/challenge')[0] == 502
        with running(runtime):
            assert request(frontend, '/friends/challenge')[0] == 400


def test_probe_receipt_survives_failed_gate_and_rollback(runtime):
    with ingress(runtime, True) as frontend:
        evidence = Evidence(runtime['temporary'] / 'receipts', 'restricted-enabled-test')
        try:
            with pytest.raises(ProbeFailed):
                try:
                    gate('http://127.0.0.1:' + str(frontend), evidence, runtime['identities'])
                finally:
                    records = [json.loads(path.read_text()) for path in evidence.directory.glob('*.json')]
                    assert [record['status'] for record in records if record['label'] == 'ordinary_challenge'] == [502]
        finally:
            evidence.close()
    assert len(records) == 2
    assert all(record['generation'] == 'restricted-enabled-test' for record in records)


def test_exact_future_https_gate_verifies_tls(runtime, monkeypatch):
    with running(runtime), ingress(runtime, True, tls=True) as frontend:
        evidence = Evidence(runtime['temporary'] / 'https-evidence', 'attempt4-fixture')
        try:
            origin = 'https://127.0.0.1:' + str(frontend)
            assert probe(origin, 'status', evidence)['transport_error'] == 'tls'
            monkeypatch.setenv('SSL_CERT_FILE', str(runtime['https_anchor']))
            gate(origin, evidence, runtime['identities'])
        finally:
            evidence.close()
    records = [json.loads(path.read_text()) for path in evidence.directory.glob('*.json')]
    assert len(records) == 7
    assert any(record['response_class'] == 'restricted-challenge' for record in records)


def test_packaged_operator_shell_trap_preserves_receipts(runtime):
    receipts = runtime['temporary'] / 'shell-receipts'
    identities = runtime['temporary'] / 'probe-identities.json'
    identities.write_text(json.dumps(runtime['identities']))
    identities.chmod(0o600)
    rollback = runtime['temporary'] / 'rollback.py'
    rollback.write_text(
        'import json,sys\nfrom pathlib import Path\n'
        'records = [json.loads(path.read_text()) for path in Path(sys.argv[1]).glob("*.json")]\n'
        'assert len(records) == 2\n'
        'assert {record["label"]: record["status"] for record in records} == '
        '{"status": 200, "ordinary_challenge": 502}\n'
        'assert all(record["generation"] == "shell-trap" for record in records)\n'
        'Path(sys.argv[2]).write_text("rollback-after-durable-receipts")\n'
    )
    marker = runtime['temporary'] / 'rollback-marker'
    operator = runtime['temporary'] / 'operator.sh'
    operator.write_text(
        'set -eu\n'
        'trap \'"$1" -I "$6" "$4" "$7"\' EXIT\n'
        '"$1" -I "$2" gate --origin "$3" --evidence "$4" '
        '--generation shell-trap --identities "$5" --expected-non-canary 1\n'
    )
    with ingress(runtime, True) as frontend:
        result = subprocess.run(
            ['/bin/sh', str(operator), sys.executable,
             str(runtime['artifact'] / 'friends-http-acceptance.py'),
             'http://127.0.0.1:' + str(frontend), str(receipts), str(identities), str(rollback), str(marker)],
            cwd=runtime['temporary'], capture_output=True, timeout=10,
        )
        assert result.returncode != 0 and not result.stdout
        assert b'Friends HTTP acceptance failed; inspect protected receipts' in result.stderr
        assert marker.read_text() == 'rollback-after-durable-receipts'
        saved = {path.name: path.read_bytes() for path in receipts.glob('*.json')}
        assert all(value['public_identity'].encode() not in result.stderr + b''.join(saved.values())
                   for value in [runtime['identities']['canary'], *runtime['identities']['non_canary']])
        with running(runtime):
            assert request(frontend, '/friends/challenge')[0] == 400
        assert {path.name: path.read_bytes() for path in receipts.glob('*.json')} == saved
    assert {path.name: path.read_bytes() for path in receipts.glob('*.json')} == saved
