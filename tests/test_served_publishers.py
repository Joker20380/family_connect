import ast
import base64
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import time
import types
import zipfile

import pytest
from cryptography import x509

from control.friends import paid_beta
from control.friends.access import Access
from control.friends.chat import ChatAccess
from control.friends.restricted import from_env
from control.friends.restricted_admin import publish_crl
from device_identity.device import DeviceIdentity
from provisioning import friends_catalog
from provisioning.chat_publishers import validate
from scripts.package_paid_boundary import ROOT, source_gate
from test_friends_chat import SigningChat
from test_friends_http_runtime import request, running, runtime

BASELINE = ROOT / 'deploy/friends/restricted/served-baseline.json'


@pytest.fixture
def served():
    path = os.environ.get('FC_SERVED_HTTP_ARTIFACT')
    if not path:
        pytest.skip('Exact private served archive required for provenance comparison')
    contract = json.loads(BASELINE.read_bytes())
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == contract['served']['sha256']
    with zipfile.ZipFile(path) as archive:
        yield archive


def normalized_access(raw):
    imports, body = [], []
    for node in ast.parse(raw).body:
        if isinstance(node, ast.Import):
            imports.extend((alias.name, alias.asname) for alias in node.names)
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            continue
        else:
            body.append(ast.dump(node, include_attributes=False))
    return sorted(imports), body


def test_restored_members_and_access_import_api_equivalence(served):
    for member, path in [('friends_http.py', 'deploy/friends/access-api.py'),
                         ('control/friends/chat_publishers.py', 'control/friends/chat_publishers.py'),
                         ('provisioning/chat_publishers.py', 'provisioning/chat_publishers.py')]:
        assert served.read(member) == (ROOT / path).read_bytes()
    assert normalized_access(served.read('control/friends/access.py')) == normalized_access((ROOT / 'control/friends/access.py').read_bytes())


@pytest.mark.parametrize('version', ['served', 'current'])
def test_access_activation_proof_replay_and_revocation(served, version, tmp_path, monkeypatch):
    module = types.ModuleType('control.friends._equivalence')
    monkeypatch.setitem(sys.modules, module.__name__, module)
    raw = served.read('control/friends/access.py') if version == 'served' else (ROOT / 'control/friends/access.py').read_bytes()
    exec(compile(raw, 'verified-access-source', 'exec'), module.__dict__)
    access = module.Access(tmp_path / 'synthetic.db', clock=lambda: 1000)
    access.initialize()
    device = DeviceIdentity.generate()
    invite = access.invite()
    challenge = access.challenge(device.public_identity, device.wireguard_public_key, 'activate', invite)
    proof = device.prove_transport_key(challenge['challenge'])
    assert access.complete(proof, 'activate')['device'] == device.reference
    with pytest.raises(module.Rejected):
        access.complete(proof, 'activate')
    challenge = access.challenge(device.public_identity, device.wireguard_public_key, 'ru')
    assert access.complete(device.prove_transport_key(challenge['challenge']), 'ru')['device'] == device.reference
    with access.db() as database:
        database.execute('UPDATE devices SET revoked=1 WHERE device=?', (device.reference,))
    with pytest.raises(module.Rejected):
        access.challenge(device.public_identity, device.wireguard_public_key, 'ru')


def test_catalog_legacy_compatibility_and_strict_floor(served, monkeypatch):
    module = types.ModuleType('provisioning._served_catalog')
    monkeypatch.setitem(sys.modules, module.__name__, module)
    exec(compile(served.read('provisioning/friends_catalog.py'), 'verified-catalog-source', 'exec'), module.__dict__)
    fixture = json.loads((ROOT / 'tests/fixtures/desktop-friends-catalog-v2.json').read_bytes())
    anchor, key = base64.b64decode(fixture['anchor']), base64.b64decode(fixture['wireguard_key'])
    for vector in fixture['vectors']:
        if not vector['valid']:
            continue
        reply = vector['reply']
        args = (reply, anchor, fixture['device'], reply['country'], key)
        options = dict(floor=vector['floor'], previous_hash=vector.get('previous_hash'))
        assert vars(module.verify(*args, **options)) == vars(friends_catalog.verify(*args, **options))
        current = friends_catalog.verify(*args, **options)
        floor = friends_catalog.verify_catalog(reply['catalog'], anchor, **options)
        assert floor.sequence == current.sequence and floor.catalog_hash == current.catalog_hash
        for bad in [dict(floor=current.sequence + 1), dict(floor=current.sequence, previous_hash='0' * 64)]:
            with pytest.raises(ValueError):
                friends_catalog.verify_catalog(reply['catalog'], anchor, **bad)
        tampered = deepcopy(reply['catalog'])
        tampered['signature'] = base64.b64encode(bytes(64)).decode()
        with pytest.raises(ValueError):
            friends_catalog.verify_catalog(tampered, anchor)
        oversized = dict(payload=base64.b64encode(bytes(8193)).decode(), signature=tampered['signature'])
        with pytest.raises(ValueError):
            friends_catalog.verify_catalog(oversized, anchor)


@pytest.mark.parametrize('change', ['binding', 'chat_binding', 'schema', 'revision', 'expired', 'too_long', 'duplicate', 'oversize', 'extra'])
def test_publisher_parser_fails_closed(change):
    value = dict(schema=1, device='synthetic-device', chat_public='1' * 128, revision=3,
        expires_at=1100, publishers=[dict(role='service_publisher', public_key='2' * 128)])
    if change == 'binding': value['device'] = 'other-synthetic-device'
    elif change == 'chat_binding': value['chat_public'] = '3' * 128
    elif change == 'schema': value['schema'] = 2
    elif change == 'revision': value['revision'] = 0
    elif change == 'expired': value['expires_at'] = 1000
    elif change == 'too_long': value['expires_at'] = 1121
    elif change == 'duplicate': value['publishers'] *= 2
    elif change == 'oversize': value['publishers'] *= 5
    else: value['url'] = 'https://synthetic.invalid'
    with pytest.raises(ValueError):
        validate(value, 'synthetic-device', '1' * 128, 1000)


@pytest.mark.parametrize('case', ['empty', 'valid', 'malformed', 'duplicate', 'oversize', 'revision', 'duplicate_json'])
def test_packaged_authenticated_publisher_delivery(runtime, case):
    ChatAccess(runtime['access']).initialize()
    (runtime['state'] / 'chat-node.json').write_text('{}')
    chat = SigningChat()
    public = chat.profile()['public']
    publisher = SigningChat().profile()['public']
    entry = dict(revision=3, publishers=[dict(role='service_publisher', public_key=publisher)])
    if case == 'malformed': entry['unexpected'] = True
    if case == 'duplicate': entry['publishers'] *= 2
    if case == 'revision': entry['revision'] = 0
    document = dict(schema=1, devices={} if case == 'empty' else {runtime['canary'].reference: entry})
    raw = json.dumps(document)
    if case == 'oversize': raw += ' ' * 8192
    if case == 'duplicate_json': raw = raw.replace('"schema": 1', '"schema": 1, "schema": 1')
    (runtime['state'] / 'chat-publishers.json').write_text(raw)
    code = ('import sys; sys.path.insert(0,sys.argv[1]); import friends_http; '
        'friends_http.synchronize=lambda registry: (registry.snapshot(), {"expires_at":int(registry.access.clock())+100}); '
        'sys.argv=sys.argv[1:]; friends_http.main()')
    runtime['command'] = [sys.executable, '-I', '-c', code, *runtime['command'][2:]]
    with running(runtime):
        unauthorized = DeviceIdentity.generate()
        assert request(runtime['backend'], '/friends/chat/challenge', body=dict(public_identity=unauthorized.public_identity,
            wireguard_public_key=unauthorized.wireguard_public_key, chat_public=public))[0] == 403
        assert request(runtime['backend'], '/friends/chat/publishers')[0] == 404
        identity = dict(runtime['identities']['canary'], chat_public=public)
        status, raw = request(runtime['backend'], '/friends/chat/challenge', body=identity)
        assert status == 200
        challenge = json.loads(raw)
        proof = dict(proof=runtime['canary'].prove_transport_key(challenge['challenge']),
            **chat.enrollment_proof(challenge['device'], challenge['challenge']))
        bad = dict(proof, chat_signature='0' * 128)
        assert request(runtime['backend'], '/friends/chat/register', body=bad)[0] == 403
        status, raw = request(runtime['backend'], '/friends/chat/register', body=proof)
        if case not in ('empty', 'valid'):
            assert status == 400 and json.loads(raw) == {'error': 'invalid-request'}
            assert publisher.encode() not in raw
        else:
            assert status == 200
            result = json.loads(raw)
            if case == 'empty': assert 'publisher_configuration' not in result
            else:
                value = result['publisher_configuration']
                assert validate(value, runtime['canary'].reference, public, value['expires_at'] - 100) == value
                assert value['publishers'] == entry['publishers']
        assert request(runtime['backend'], '/friends/chat/register', body=proof)[0] == 403
        assert request(runtime['backend'], '/friends/restricted-readiness/challenge', body=runtime['identities']['canary'])[0] == 200


@pytest.mark.parametrize('target', ['served', 'candidate', 'contract'])
def test_reviewed_baseline_is_exact_not_a_path_allowlist(served, runtime, tmp_path, target):
    served_path = Path(os.environ['FC_SERVED_HTTP_ARTIFACT'])
    candidate = runtime['artifact'] / 'friends-http.pyz'
    assert source_gate(served_path, candidate, BASELINE)['result'] == 'PASS'
    baseline = BASELINE
    if target == 'contract':
        baseline = tmp_path / 'contract.json'
        document = json.loads(BASELINE.read_bytes())
        document['served']['members']['friends_http.py'] = '0' * 64
        baseline.write_text(json.dumps(document))
    else:
        changed = tmp_path / 'changed.pyz'
        changed.write_bytes((served_path if target == 'served' else candidate).read_bytes() + b'unreviewed')
        if target == 'served': served_path = changed
        else: candidate = changed
    assert source_gate(served_path, candidate, baseline)['result'] == 'BLOCKED_SERVED_SOURCE_DRIFT'


def test_exact_http_synthetic_material_and_registry_recovery(runtime, tmp_path, monkeypatch):
    device, access = runtime['canary'], runtime['access']
    now = int(time.time())
    with access.db() as database:
        database.execute('UPDATE device_support SET platform=?,app_version=?,version_code=106,last_seen=? WHERE device=?',
            ('android', paid_beta.VERSION, now, device.reference))
        support = database.execute('SELECT support_id FROM device_support WHERE device=?', (device.reference,)).fetchone()[0]
    (runtime['state'] / 'admission.json').write_text('{"version":2,"eligibility":"all_activated"}')
    with paid_beta.connection(access.path, write=True) as database:
        paid_beta.apply_event(database, support, 'payment', 'synthetic-recovery-001', 'synthetic-reference', now=now,
            period_start=now, paid_until=now + 600, apk_sha256=paid_beta.APK_SHA256)
    identity = runtime['identities']['canary']
    with running(runtime):
        status, raw = request(runtime['backend'], '/friends/restricted-readiness/challenge', body=identity)
        assert status == 200
        proof = device.prove_transport_key(json.loads(raw)['challenge'])
        status, raw = request(runtime['backend'], '/friends/restricted-readiness', body=proof)
        assert status == 200
        certificate = json.loads(raw)['certificate']
    backup = tmp_path / 'synthetic-application-backup'
    restored = tmp_path / 'synthetic-application-restored'
    backup.mkdir(mode=0o700)
    restored.mkdir(mode=0o700)
    for name in ('issuer.json', 'issuer.key', 'anchor.pub', 'admission.json', 'revocations.pem', 'directory.json'):
        shutil.copyfile(runtime['state'] / name, backup / name)
        (backup / name).chmod(0o600)
        shutil.copyfile(backup / name, restored / name)
        (restored / name).chmod(0o600)
    with sqlite3.connect(access.path.resolve().as_uri() + '?mode=ro', uri=True) as source, sqlite3.connect(backup / 'access.db') as target:
        source.backup(target)
    with sqlite3.connect(backup / 'access.db') as source, sqlite3.connect(restored / 'access.db') as target:
        source.backup(target)
        assert target.execute('PRAGMA integrity_check').fetchall() == [('ok',)]
    runtime['environment']['FC_FRIENDS_RESTRICTED_DIR'] = str(restored)
    runtime['command'][runtime['command'].index('--root') + 1] = str(restored)
    with running(runtime):
        assert request(runtime['backend'], '/friends/restricted-readiness', body=proof)[0] == 403
        status, raw = request(runtime['backend'], '/friends/restricted-readiness/challenge', body=identity)
        assert status == 200
        status, raw = request(runtime['backend'], '/friends/restricted-readiness', body=device.prove_transport_key(json.loads(raw)['challenge']))
        assert status == 200 and json.loads(raw)['certificate'] == certificate
        with paid_beta.connection(restored / 'access.db', write=True) as database:
            paid_beta.apply_event(database, support, 'revoke', 'synthetic-revoke-001', 'synthetic-reference', now=now)
            assert database.execute('SELECT count(*) FROM paid_beta_events').fetchone()[0] == 2
        assert request(runtime['backend'], '/friends/restricted-readiness/challenge', body=identity)[0] == 403
        assert request(runtime['backend'], '/friends/restricted-readiness/challenge', body=runtime['identities']['non_canary'][0])[0] == 200
    monkeypatch.setenv('FC_FRIENDS_RESTRICTED_DIR', str(restored))
    service = from_env(Access(restored / 'access.db'))
    publish_crl(service, restored / 'revocations.pem')
    revocations = x509.load_pem_x509_crl((restored / 'revocations.pem').read_bytes())
    assert revocations.get_revoked_certificate_by_serial_number(x509.load_pem_x509_certificate(certificate.encode()).serial_number) is not None
