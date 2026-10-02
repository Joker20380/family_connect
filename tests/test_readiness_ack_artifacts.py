import base64
import hashlib
import http.client
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from control.friends import readiness_receipts
from control.friends.restricted import delegation
from device_identity.device import DeviceIdentity
from test_friends_http_runtime import runtime, running
from test_readiness_receipts import ready


def post(runtime, route, body, request_id='c' * 32):
    connection = http.client.HTTPConnection('127.0.0.1', runtime['backend'], timeout=5)
    try:
        connection.request('POST', '/friends/restricted-readiness' + route, json.dumps(body),
                           {'Content-Type': 'application/json', 'X-FC-Probe-ID': request_id})
        response = connection.getresponse()
        raw = response.read(65537)
        assert len(raw) <= 65536
        return response.status, json.loads(raw)
    finally:
        connection.close()


def fetched(runtime, fetch=True):
    owner = runtime['canary']
    status, challenge = post(runtime, '/challenge', runtime['identities']['canary'], 'a' * 32)
    assert status == 200
    response = dict(revision=1, minimum_crl=1, expires_at=int(time.time()) + 300)
    if fetch:
        status, response = post(runtime, '', owner.prove_transport_key(challenge['challenge']), 'b' * 32)
        assert status == 200
    payload = dict(version=1, type='READINESS_IMPORT_RESULT', correlation_id='a' * 32,
                   challenge_id='a' * 32, fetch_id='b' * 32, result='READY',
                   provisioning='PRESENT_VALID', bootstrap='PRESENT_VALID', orchestrator_usable=True,
                   revision=response['revision'], minimum_crl=response['minimum_crl'],
                   expires_at=response['expires_at'], observed_at=int(time.time()), phase='import',
                   app_version='server_contract_fixture', version_code=55, failure_reason='NONE')
    return response, payload


def ack_challenge(runtime, payload, owner=None):
    owner = runtime['canary'] if owner is None else owner
    return post(runtime, '/ack-challenge', dict(public_identity=owner.public_identity,
                wireguard_public_key=owner.wireguard_public_key, receipt=payload))


@pytest.mark.parametrize('field,value', [
    ('unknown', 'x' * 9000), ('identity', 'private-marker'), ('public_identity', 'private-marker'),
    ('proof', 'private-marker'), ('join_url', 'https://private.invalid/seed'),
    ('certificate', 'private-marker'), ('credentials', 'private-marker'),
    ('revision', True), ('revision', -1), ('revision', '1'), ('minimum_crl', 2**53),
    ('expires_at', 0), ('expires_at', 2**53), ('result', 'EXCEPTION:private-marker'),
    ('app_version', 'x' * 65), ('version', 2), ('orchestrator_usable', False),
])
def test_exact_http_ack_rejects_non_allowlisted_payload(runtime, field, value):
    with running(runtime):
        _, payload = fetched(runtime)
        payload[field] = value
        status, response = ack_challenge(runtime, payload)
        assert status == (400 if field == 'unknown' else 503)
        assert set(response) == {'error'} and 'private-marker' not in json.dumps(response)
        assert 'https://' not in json.dumps(response)
        with runtime['access'].db() as database:
            assert database.execute("SELECT COUNT(*) FROM challenges WHERE purpose='readiness-ack'").fetchone()[0] == 0
            assert database.execute('SELECT ack FROM restricted_readiness_results').fetchone()[0] is None


@pytest.mark.parametrize('mutation', ['missing_fetch', 'correlation', 'fetch', 'revision', 'expiry',
                                    'stale_correlation', 'unauthorized', 'revoked'])
def test_exact_http_ack_cannot_invent_or_rebind_readiness(runtime, mutation):
    with running(runtime):
        _, payload = fetched(runtime, fetch=mutation != 'missing_fetch')
        if mutation == 'correlation':
            payload.update(correlation_id='d' * 32, challenge_id='d' * 32)
        elif mutation == 'fetch':
            payload['fetch_id'] = 'd' * 32
        elif mutation in ('revision', 'expiry'):
            payload['revision' if mutation == 'revision' else 'expires_at'] += 1
        elif mutation == 'stale_correlation':
            with runtime['access'].db() as database:
                database.execute('UPDATE restricted_readiness_results SET challenge_at=?', (int(time.time()) - 86401,))
        elif mutation == 'revoked':
            with runtime['access'].db() as database:
                database.execute('UPDATE restricted_grants SET revoked=1')
        status, response = ack_challenge(runtime, payload, DeviceIdentity.generate() if mutation == 'unauthorized' else None)
        assert status == 403 and response == {'error': 'access-rejected'}


def test_exact_http_malformed_unsigned_altered_and_replayed_ack(runtime):
    with running(runtime):
        assert post(runtime, '/ack-challenge', {}) == (503, {'error': 'unavailable'})
        assert post(runtime, '/ack', {}) == (503, {'error': 'unavailable'})
        _, payload = fetched(runtime)
        with runtime['access'].db() as database:
            before = database.execute('SELECT * FROM restricted_certificates').fetchall()
        status, challenge = ack_challenge(runtime, payload)
        assert status == 200 and set(challenge) == {'challenge', 'expires_at', 'audience'}
        proof = runtime['canary'].prove_transport_key(challenge['challenge'])
        assert post(runtime, '/ack', dict(receipt=payload)) == (503, {'error': 'unavailable'})
        assert post(runtime, '/ack', dict(proof=proof, receipt=dict(payload, app_version='altered')))[0] == 403
        status, result = post(runtime, '/ack', dict(proof=proof, receipt=payload))
        assert status == 200 and result == dict(version=1, correlation_id='a' * 32, status='ACK_RECEIVED')
        assert post(runtime, '/ack', dict(proof=proof, receipt=payload))[0] == 403
        status, challenge = ack_challenge(runtime, payload)
        assert status == 200
        with runtime['access'].db() as database:
            database.execute("UPDATE challenges SET expires=? WHERE purpose='readiness-ack'", (int(time.time()) - 1,))
        assert post(runtime, '/ack', dict(proof=runtime['canary'].prove_transport_key(challenge['challenge']), receipt=payload))[0] == 403
        with runtime['access'].db() as database:
            after = database.execute('SELECT * FROM restricted_certificates').fetchall()
        assert [tuple(row) for row in before] == [tuple(row) for row in after]


def test_correlation_storage_is_bounded_and_cleans_expired_rows(ready):
    service, owner, now, _ = ready
    with service.access.db() as database:
        for number in range(40):
            readiness_receipts.challenge(database, f'{number:032x}', f'fixture-{number}', owner.reference, now + number)
            assert database.execute('SELECT COUNT(*) FROM restricted_readiness_results WHERE device=?', (owner.reference,)).fetchone()[0] <= 16
        readiness_receipts.challenge(database, 'f' * 32, 'fixture-new-day', owner.reference, now + 86440)
        assert database.execute('SELECT COUNT(*) FROM restricted_readiness_results').fetchone()[0] == 1


def test_offline_sync_http_native_result_ack_readonly_contract_fixture(runtime, tmp_path):
    supplied = os.environ.get('FC_TEST_SYNC_ARTIFACT')
    native_bundle = os.environ.get('FC_TEST_READINESS_ARTIFACT')
    if not supplied or not native_bundle:
        pytest.skip('Pinned sync/readiness artifacts required')
    archive = Path(supplied).resolve()
    archive = archive / 'restricted-sync.pyz' if archive.is_dir() else archive
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == os.environ['FC_TEST_SYNC_SHA256']
    state, service = runtime['state'], runtime['restricted']
    trust, _ = delegation(service.manifest, service.anchor, int(time.time()))
    profile, seed = tmp_path / 'gateway.json', tmp_path / 'seed.json'
    profile.write_text(json.dumps(dict(authority=trust['authority'], revocations=service.crl_source().decode(),
                                     minimum_crl=1, family=trust['family'], gateway=trust['gateway'])))
    seed.write_bytes(service.seed_source())
    for path in (profile, seed):
        path.chmod(0o600)
    for name in ('sync.key', 'known_hosts'):
        (state / name).write_text('offline-test-placeholder')
        (state / name).chmod(0o600)
    script = '''import contextlib,io,runpy,subprocess,sys
archive,root,profile,seed=sys.argv[1:];sys.argv=[archive,'--help']
with contextlib.redirect_stdout(io.StringIO()):
    try:runpy.run_path(archive,run_name='__main__')
    except SystemExit as result:assert result.code==0
from control.friends import restricted_sync as sync
assert sync.__file__.startswith(archive+'/')
real_run=subprocess.run
def offline_only(command,**kwargs):
    assert command[0]=='/usr/bin/ssh' and command[-1]=='restricted-sync'
    assert 'StrictHostKeyChecking=yes' in command
    result=real_run([sys.executable,'-I',archive,'gateway','--profile',profile,'--directory',seed],input=kwargs['input'],capture_output=True,timeout=15)
    assert result.returncode==0
    kwargs['stdout'].write(result.stdout);kwargs['stdout'].flush()
    return subprocess.CompletedProcess(command,0)
subprocess.run=offline_only
sys.argv=[archive,'sync','--db',root+'/access.db','--host','186.246.45.246','--ssh-key',root+'/sync.key','--known-hosts',root+'/known_hosts']
sync.main()
'''
    result = subprocess.run([sys.executable, '-I', '-c', script, str(archive), str(state), str(profile), str(seed)],
                            env=runtime['environment'], cwd=tmp_path, capture_output=True, timeout=25)
    assert result.returncode == 0 and not result.stderr
    check = subprocess.run([sys.executable, '-I', str(archive), 'sync', '--check', '--db', str(state / 'access.db'),
                            '--host', '186.246.45.246', '--ssh-key', str(state / 'sync.key'), '--known-hosts', str(state / 'known_hosts')],
                           env=runtime['environment'], cwd=tmp_path, capture_output=True, timeout=10)
    assert check.returncode == 0 and not check.stderr
    with runtime['access'].db() as database:
        assert database.execute('SELECT sequence FROM restricted_crl_sequence').fetchone()[0] == 2
    with running(runtime):
        response, payload = fetched(runtime)
        assert payload['minimum_crl'] == 2
        native = subprocess.run([str(Path(native_bundle).resolve() / 'readiness-delivery-check')],
                                input=json.dumps(dict(response=response, public=runtime['canary'].public_identity,
                                                      anchor=base64.b64encode(service.anchor).decode(), now=int(time.time()))).encode(),
                                cwd=tmp_path, capture_output=True, timeout=5)
        assert native.returncode == 0 and native.stdout == b'compatible\n'
        status, challenge = ack_challenge(runtime, payload)
        assert status == 200
        assert post(runtime, '/ack', dict(proof=runtime['canary'].prove_transport_key(challenge['challenge']), receipt=payload))[0] == 200
    before = (state / 'access.db').read_bytes()
    inspected = subprocess.run([sys.executable, '-I', str(runtime['artifact'] / 'friends-http.pyz'), '--root', str(state),
                                '--readiness-ack', 'a' * 32, '--material', str(state)],
                               env=runtime['environment'], cwd=tmp_path, capture_output=True, timeout=10)
    assert inspected.returncode == 0 and not inspected.stderr
    assert before == (state / 'access.db').read_bytes()
    result = json.loads(inspected.stdout)
    assert result['status'] == 'ACK_RECEIVED' and result['receipt'] == payload
    assert not any(token in inspected.stdout for token in (b'join_url', b'certificate', b'proof', b'https://'))
    assert runtime['canary'].public_identity.encode() not in inspected.stdout
    print(json.dumps(dict(receipt_class='server_contract_fixture', sync=True, native=True, ack=True,
                          readonly_inspection=True, owner_product_ready=False)))
