import json
import time

import pytest

from control.friends.access import Rejected
from control.friends import readiness_receipts as receipts
from device_identity.device import DeviceIdentity
from scripts.friends_http_transition import Evidence, OwnerProduct
from test_friends_restricted import configured
from test_friends_http_runtime import runtime, running


@pytest.fixture
def ready(tmp_path):
    service, owner, now = configured(tmp_path, int(time.time()))
    service.eligible_devices = frozenset([owner.reference])
    challenge = service.challenge(owner.public_identity, owner.wireguard_public_key, request_id='a' * 32)
    response = service.fetch(owner.prove_transport_key(challenge['challenge']), request_id='b' * 32)
    payload = dict(version=1, type='READINESS_IMPORT_RESULT', correlation_id='a' * 32,
                   challenge_id='a' * 32, fetch_id='b' * 32, result='READY', provisioning='PRESENT_VALID',
                   bootstrap='PRESENT_VALID', orchestrator_usable=True, revision=response['revision'],
                   minimum_crl=response['minimum_crl'], expires_at=response['expires_at'], observed_at=now,
                   phase='import', app_version='0.1.18-canary55-receipt', version_code=55, failure_reason='NONE')
    return service, owner, now, payload


def challenge_ack(service, owner, payload):
    return receipts.ack_challenge(service, dict(public_identity=owner.public_identity,
                                               wireguard_public_key=owner.wireguard_public_key, receipt=payload))


def acknowledge(service, owner, payload):
    challenge = challenge_ack(service, owner, payload)
    return receipts.acknowledge(service, dict(proof=owner.prove_transport_key(challenge['challenge']), receipt=payload))


def test_authenticated_ack_and_owner_bound_safe_readback(ready):
    service, owner, now, payload = ready
    assert receipts.readback(service, 'a' * 32, owner.reference)['status'] == 'ACK_PENDING'
    assert acknowledge(service, owner, payload)['status'] == 'ACK_RECEIVED'
    result = receipts.readback(service, 'a' * 32, owner.reference)
    assert result['receipt'] == payload and result['received_at'] == now
    assert receipts.readback(service, 'a' * 32, DeviceIdentity.generate().reference)['status'] == 'UNKNOWN'
    raw = json.dumps(result)
    for secret in (owner.reference, owner.public_identity, owner.wireguard_public_key, 'join_url', 'certificate', 'proof', 'oauth', 'https://'):
        assert secret not in raw


@pytest.mark.parametrize('code', sorted(receipts.CODES - {'READY'}))
def test_failed_import_ack_never_claims_ready(ready, code):
    service, owner, _, payload = ready
    payload.update(result=code, failure_reason=code, provisioning='NOT_READY', bootstrap='NOT_READY',
                   orchestrator_usable=False, revision=0, minimum_crl=0, expires_at=0)
    assert acknowledge(service, owner, payload)['status'] == 'ACK_RECEIVED'
    result = receipts.readback(service, 'a' * 32, owner.reference)
    assert not result['receipt']['orchestrator_usable']


def test_proof_binds_exact_payload_and_cannot_replay(ready):
    service, owner, _, payload = ready
    challenge = challenge_ack(service, owner, payload)
    proof = owner.prove_transport_key(challenge['challenge'])
    altered = dict(payload, app_version='forged')
    with pytest.raises(Rejected):
        receipts.acknowledge(service, dict(proof=proof, receipt=altered))
    receipts.acknowledge(service, dict(proof=proof, receipt=payload))
    with pytest.raises(Rejected):
        receipts.acknowledge(service, dict(proof=proof, receipt=payload))


@pytest.mark.parametrize('mutation', ['device', 'invite', 'grant', 'revision', 'expired', 'correlation', 'fetch', 'floor', 'expiry', 'wrong_owner', 'proof'])
def test_revoked_stale_unbound_and_invalid_ack_rejected(ready, mutation):
    service, owner, now, payload = ready
    challenge = challenge_ack(service, owner, payload)
    proof = owner.prove_transport_key(challenge['challenge'])
    if mutation in ('device', 'invite', 'grant', 'revision'):
        sql = {'device':'UPDATE devices SET revoked=1', 'invite':'UPDATE invites SET revoked=1',
               'grant':'UPDATE restricted_grants SET revoked=1', 'revision':'UPDATE restricted_grants SET revision=revision+1'}[mutation]
        with service.access.db() as database:
            database.execute(sql)
    elif mutation == 'expired':
        service.access.clock = lambda: now + 3600
    elif mutation == 'correlation':
        payload.update(correlation_id='c' * 32, challenge_id='c' * 32)
    elif mutation == 'fetch':
        payload['fetch_id'] = 'd' * 32
    elif mutation == 'floor':
        payload['minimum_crl'] += 1
    elif mutation == 'expiry':
        payload['expires_at'] += 1
    elif mutation == 'wrong_owner':
        proof = DeviceIdentity.generate().prove_transport_key(challenge['challenge'])
    else:
        proof['signature'] = 'invalid'
    with pytest.raises((Rejected, ValueError)):
        receipts.acknowledge(service, dict(proof=proof, receipt=payload))


@pytest.mark.parametrize('field,value', [('private_key','secret'), ('join_url','https://private.invalid'), ('proof','secret'),
                                       ('observed_at',True), ('version',True), ('version_code',0),
                                       ('app_version','\nsecret'), ('result','arbitrary exception text'), ('expires_at',2**53)])
def test_strict_schema_redaction(ready, field, value):
    payload = dict(ready[3], **{field:value})
    with pytest.raises(ValueError):
        receipts.validate(payload)


def test_readback_rechecks_revocation_and_expiry(ready):
    service, owner, now, payload = ready
    acknowledge(service, owner, payload)
    with service.access.db() as database:
        database.execute('UPDATE restricted_grants SET revoked=1')
    assert receipts.readback(service, 'a' * 32, owner.reference)['status'] == 'ACK_PENDING'
    with service.access.db() as database:
        database.execute('UPDATE restricted_grants SET revoked=0')
    service.access.clock = lambda: now + 3600
    assert receipts.readback(service, 'a' * 32, owner.reference)['status'] == 'ACK_PENDING'


def test_ui_unavailable_server_ack_is_authoritative(ready, tmp_path):
    service, owner, now, payload = ready
    evidence = Evidence(tmp_path / 'acceptance', 'candidate')
    try:
        product = OwnerProduct(evidence, 'candidate')
        acknowledge(service, owner, payload)
        trace = [dict(probe_id=payload[field], generation='candidate', timestamp=product.opened,
                      status=200, upstream_status='200', product_step=step)
                 for field, step in [('challenge_id','challenge'), ('fetch_id','readiness')]]
        assert product.observe(receipts.readback(service, 'a' * 32, owner.reference), trace)
        assert product.passed
    finally:
        evidence.close()


def test_pending_ack_does_not_prove_owner_ready(ready, tmp_path):
    service, owner, _, payload = ready
    evidence = Evidence(tmp_path / 'acceptance', 'candidate')
    try:
        assert not OwnerProduct(evidence, 'candidate').observe(receipts.readback(service, 'a' * 32, owner.reference), [])
    finally:
        evidence.close()


def test_source_guards_no_exported_diagnostics_or_ui_requirement():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    java = root / 'clients/android/app/src/main/java/com/familyconnect/app'
    for name in ('ReadinessImportResult.java','ReadinessProduct.java','ReadinessReceiptStore.java'):
        raw = (java / name).read_text()
        assert 'adb' not in raw and 'ContentProvider' not in raw and 'Log.' not in raw
    storage = (java / 'ReadinessReceiptStore.java').read_text()
    assert 'getNoBackupFilesDir()' in storage and 'getFD().sync()' in storage and 'file.failWrite' in storage
    runtime = (java / 'FriendsRestricted.java').read_text()
    assert 'cache.accept(response)' not in runtime and 'product.imported(response' in runtime and 'product.restart(' in runtime


def test_closed_http_challenge_fetch_ack_and_isolated_readback(runtime):
    import http.client
    import subprocess
    import sys
    owner = runtime['canary']
    def post(path, body, request_id):
        connection = http.client.HTTPConnection('127.0.0.1', runtime['backend'], timeout=5)
        try:
            connection.request('POST', '/friends/restricted-readiness' + path, json.dumps(body),
                               {'Content-Type':'application/json', 'X-FC-Probe-ID':request_id})
            response = connection.getresponse()
            result = json.loads(response.read())
            assert response.status == 200
            return result
        finally:
            connection.close()
    with running(runtime):
        challenge = post('/challenge', dict(public_identity=owner.public_identity, wireguard_public_key=owner.wireguard_public_key), 'a' * 32)
        response = post('', owner.prove_transport_key(challenge['challenge']), 'b' * 32)
        now = int(time.time())
        payload = dict(version=1, type='READINESS_IMPORT_RESULT', correlation_id='a' * 32, challenge_id='a' * 32,
                       fetch_id='b' * 32, result='READY', provisioning='PRESENT_VALID', bootstrap='PRESENT_VALID',
                       orchestrator_usable=True, revision=response['revision'], minimum_crl=response['minimum_crl'],
                       expires_at=response['expires_at'], observed_at=now, phase='import', app_version='test', version_code=55, failure_reason='NONE')
        ack = post('/ack-challenge', dict(public_identity=owner.public_identity, wireguard_public_key=owner.wireguard_public_key, receipt=payload), 'c' * 32)
        assert post('/ack', dict(proof=owner.prove_transport_key(ack['challenge']), receipt=payload), 'd' * 32)['status'] == 'ACK_RECEIVED'
    result = subprocess.run([sys.executable, '-I', str(runtime['artifact'] / 'friends-http.pyz'), '--root', str(runtime['state']),
                             '--readiness-ack', 'a' * 32, '--material', str(runtime['state'])], cwd='/tmp', capture_output=True, timeout=10)
    assert result.returncode == 0 and not result.stderr
    assert json.loads(result.stdout)['receipt'] == payload
