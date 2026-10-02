import contextlib
import http.client
import json
import os
from pathlib import Path
import subprocess
import time

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
import pytest
import RNS

from control.friends.restricted import migrate
from device_identity.device import DeviceIdentity
from test_friends_http_runtime import runtime, request

GOLDEN = Path(__file__).parent / 'vectors/friends-readiness-challenge.json'


@pytest.fixture
def android(runtime):
    identity = RNS.Identity(create_keys=False)
    assert identity.load_private_key(bytes(64))
    owner = DeviceIdentity(identity, X25519PrivateKey.from_private_bytes(bytes(32)))
    access = runtime['access']
    code = access.invite()
    challenge = access.challenge(owner.public_identity, owner.wireguard_public_key, 'activate', code)
    access.complete(owner.prove_transport_key(challenge['challenge']), 'activate')
    (runtime['state'] / 'admission.json').write_text(json.dumps(dict(devices=[owner.reference])))
    runtime['owner'] = owner
    runtime['wire'] = json.loads(GOLDEN.read_bytes())
    assert json.loads(runtime['wire']['body']) == dict(public_identity=owner.public_identity, wireguard_public_key=owner.wireguard_public_key)
    return runtime


@contextlib.contextmanager
def listening(runtime):
    log = runtime['temporary'] / 'safe-errors.log'
    with log.open('wb') as output:
        process = subprocess.Popen(runtime['command'], env=runtime['environment'], cwd=runtime['temporary'], stdout=subprocess.DEVNULL, stderr=output)
        try:
            deadline = time.monotonic() + 10
            while True:
                assert process.poll() is None
                try:
                    if request(runtime['backend'], '/friends/challenge')[0] == 400:
                        break
                except OSError:
                    pass
                assert time.monotonic() < deadline
                time.sleep(.05)
            yield log
        finally:
            process.terminate()
            process.wait(timeout=5)


def post(runtime, wire=None):
    wire = runtime['wire'] if wire is None else wire
    connection = http.client.HTTPConnection('127.0.0.1', runtime['backend'], timeout=5)
    try:
        connection.request(wire['method'], wire['path'], wire['body'].encode('utf-8'), wire['headers'])
        response = connection.getresponse()
        return response.status, json.loads(response.read(65537))
    finally:
        connection.close()


def test_android_bytes_legacy_schema_503_then_explicit_migration_200(android):
    with android['access'].db() as database:
        database.execute('DROP TABLE restricted_readiness_results')
    with listening(android) as log:
        assert post(android) == (503, {'error': 'unavailable'})
        with android['access'].db() as database:
            assert database.execute("SELECT COUNT(*) FROM challenges WHERE purpose='restricted'").fetchone()[0] == 0
        migrate(android['access'])
        assert post(android)[0] == 200
    assert log.read_text() == 'restricted_challenge stage=correlation_store reason=CORRELATION_SCHEMA_UNAVAILABLE\n'


def test_android_current_schema_needs_no_fetch_result_or_ack(android):
    with listening(android):
        status, challenge = post(android)
        assert status == 200
        with android['access'].db() as database:
            row = database.execute('SELECT * FROM restricted_readiness_results').fetchone()
            assert row['fetch_id'] is row['fetch_at'] is row['ack'] is None
        proof = android['owner'].prove_transport_key(challenge['challenge'])
        assert request(android['backend'], '/friends/restricted-readiness', body=proof)[0] == 200
        assert request(android['backend'], '/friends/restricted-readiness', body=proof)[0] == 403


@pytest.mark.parametrize('mutation', ['non_canary', 'device', 'invite', 'grant', 'family', 'revision', 'expired', 'binding'])
def test_android_authorization_not_weakened(android, mutation):
    owner = android['owner']
    with android['access'].db() as database:
        database.execute('INSERT INTO restricted_grants VALUES (?,?,?,?,0)', (owner.reference, 'a' * 32, 1, int(time.time()) + 3600))
        if mutation in ('device', 'invite'):
            database.execute('UPDATE ' + ('devices' if mutation == 'device' else 'invites') + ' SET revoked=1 WHERE device=?', (owner.reference,))
        elif mutation in ('grant', 'family', 'revision', 'expired'):
            assignment = {'grant': 'revoked=1', 'family': "family='wrong'", 'revision': 'revision=0', 'expired': 'expires=1'}[mutation]
            database.execute('UPDATE restricted_grants SET ' + assignment + ' WHERE device=?', (owner.reference,))
    if mutation == 'non_canary':
        (android['state'] / 'admission.json').write_text('{"devices":[]}')
    if mutation == 'binding':
        body = json.loads(android['wire']['body'])
        body['wireguard_public_key'] = android['identities']['non_canary'][0]['wireguard_public_key']
        android['wire']['body'] = json.dumps(body)
    with listening(android):
        assert post(android)[0] == 403


@pytest.mark.parametrize('body', ['{}', 'null', '{"public_identity":null,"wireguard_public_key":null}', '{"public_identity":"x","public_identity":"y"}'])
def test_malformed_wire_is_rejected(android, body):
    android['wire']['body'] = body
    with listening(android):
        assert post(android)[0] == 400


def test_temporary_authority_failure_is_safe(android):
    (android['state'] / 'issuer.json').write_text('{}')
    with listening(android) as log:
        assert post(android) == (503, {'error': 'unavailable'})
    assert log.read_text() == 'restricted_challenge stage=authority reason=AUTHORITY_UNAVAILABLE\n'


@pytest.mark.parametrize('table,stage,reason', [
    ('restricted_grants', 'device_lookup', 'DEVICE_MAPPING_UNAVAILABLE'),
    ('restricted_challenges', 'challenge_store', 'CHALLENGE_STORE_FAILURE'),
])
def test_missing_dependency_has_safe_stage(android, table, stage, reason):
    with android['access'].db() as database:
        database.execute('DROP TABLE ' + table)
    with listening(android) as log:
        assert post(android) == (503, {'error': 'unavailable'})
    assert log.read_text() == 'restricted_challenge stage=' + stage + ' reason=' + reason + '\n'


@pytest.mark.parametrize('mutation', ['expired_nonce', 'revision_changed', 'wrong_purpose'])
def test_android_stale_proof_rejected(android, mutation):
    with listening(android):
        status, challenge = post(android)
        assert status == 200
        with android['access'].db() as database:
            if mutation == 'expired_nonce':
                database.execute('UPDATE challenges SET expires=1')
            elif mutation == 'wrong_purpose':
                database.execute("UPDATE challenges SET purpose='status'")
            else:
                database.execute('UPDATE restricted_grants SET revision=revision+1')
        assert request(android['backend'], '/friends/restricted-readiness', body=android['owner'].prove_transport_key(challenge['challenge']))[0] == 403


def test_duplicate_correlation_is_not_rebound(android):
    with listening(android) as log:
        assert post(android)[0] == 200
        assert post(android) == (503, {'error': 'unavailable'})
        with android['access'].db() as database:
            assert database.execute('SELECT COUNT(*) FROM restricted_readiness_results').fetchone()[0] == 1
            assert database.execute("SELECT COUNT(*) FROM challenges WHERE purpose='restricted'").fetchone()[0] == 1
    assert log.read_text() == 'restricted_challenge stage=correlation_store reason=CORRELATION_STORE_FAILURE\n'


def test_challenge_capacity_preserved(android):
    with listening(android) as log:
        for sequence in range(8):
            android['wire']['headers']['X-FC-Probe-ID'] = format(sequence, '032x')
            assert post(android)[0] == 200
        android['wire']['headers']['X-FC-Probe-ID'] = 'f' * 32
        assert post(android) == (503, {'error': 'unavailable'})
    assert log.read_text() == 'restricted_challenge stage=challenge_store reason=CHALLENGE_CAPACITY_EXHAUSTED\n'


def test_android_response_parser_and_proof_roundtrip(android):
    classpath = os.environ.get('FC_ANDROID_GOLDEN_CLASSPATH')
    if not classpath:
        pytest.skip('Java cross-language CI job supplies FC_ANDROID_GOLDEN_CLASSPATH')
    with listening(android):
        result = subprocess.run([os.environ.get('FC_JAVA', 'java'), '-cp', classpath, 'com.familyconnect.app.FriendsReadinessGoldenTest',
                                 'roundtrip', 'http://127.0.0.1:' + str(android['backend'])], capture_output=True, timeout=20)
        assert result.returncode == 0, 'Android response parser/proof failed (no sensitive response dump)'
        assert result.stdout == b'ANDROID_PYTHON_ROUNDTRIP_PASS\n'
