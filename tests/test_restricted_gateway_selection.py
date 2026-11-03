import base64
import copy
import http.client
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import time

import pytest
from cryptography import x509
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat

from control.friends import readiness_receipts
from control.friends.access import Rejected
from control.friends.restricted import DOMAIN, PRIMARY_GATEWAY, SECONDARY_GATEWAY, delegation, from_env, request, utc
from provisioning.readiness_relay import ReadinessRelay
from test_friends_http_runtime import running, runtime
from test_friends_restricted import configured


def signed(root, payload):
    raw = json.dumps(payload).encode()
    return dict(payload=base64.b64encode(raw).decode(), signature=base64.b64encode(root.sign(DOMAIN + raw)).decode())


def pair(primary):
    root = Ed25519PrivateKey.generate()
    primary.anchor = root.public_key().public_bytes_raw()
    payload = json.loads(base64.b64decode(primary.manifest['payload']))
    primary.manifest = signed(root, payload)
    secondary = copy.copy(primary)
    secondary.gateway_id = SECONDARY_GATEWAY
    secondary.manifest = signed(root, dict(payload, gateway='c' * 32))
    seeds = json.loads(primary.seed_source())
    seeds['seeds'][0].update(gateway='c' * 32, join_url='https://telemost.yandex.ru/j/second-test-only')
    secondary.seed_source = lambda: json.dumps(seeds).encode()
    return secondary, root


def write_material(root, primary, secondary):
    values = {'anchor.pub': base64.b64encode(primary.anchor),
              'issuer.json': json.dumps(primary.manifest).encode(),
              'issuer.key': primary.signing_key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()),
              'admission.json': b'{"version":2,"eligibility":"all_activated"}',
              'revocations.pem': primary.crl_source(), 'directory.json': primary.seed_source(),
              'gateways/' + SECONDARY_GATEWAY + '/issuer.json': json.dumps(secondary.manifest).encode(),
              'gateways/' + SECONDARY_GATEWAY + '/directory.json': secondary.seed_source()}
    for name, raw in values.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        path.chmod(0o600)


@pytest.fixture
def gateways(tmp_path, monkeypatch):
    primary, device, now = configured(tmp_path, int(time.time()))
    secondary, root = pair(primary)
    write_material(tmp_path, primary, secondary)
    monkeypatch.setenv('FC_FRIENDS_RESTRICTED_DIR', str(tmp_path))
    return primary, secondary, device, now, root


def proof(service, device, correlation=None):
    challenge = service.challenge(device.public_identity, device.wireguard_public_key, request_id=correlation)
    return device.prove_transport_key(challenge['challenge'])


def receipt(response, now):
    return dict(version=1, type='READINESS_IMPORT_RESULT', correlation_id='a' * 32,
                challenge_id='a' * 32, fetch_id='b' * 32, result='READY', provisioning='PRESENT_VALID',
                bootstrap='PRESENT_VALID', orchestrator_usable=True, revision=response['revision'],
                minimum_crl=response['minimum_crl'], expires_at=response['expires_at'], observed_at=now,
                phase='import', app_version='gateway-test', version_code=112, failure_reason='NONE')


def test_two_gateways_preserve_identity_certificate_and_entitlements(gateways):
    primary, _, device, now, _ = gateways
    with primary.access.db() as database:
        before = {name: [tuple(row) for row in database.execute('SELECT * FROM ' + name)]
                  for name in ('devices', 'invites', 'restricted_grants')}
    responses = []
    for target in (None, PRIMARY_GATEWAY, SECONDARY_GATEWAY, None):
        service = from_env(primary.access, target)
        responses.append(service.fetch(proof(service, device)))
    assert {response['device'] for response in responses} == {device.reference}
    assert len({response['certificate'] for response in responses}) == 1
    assert len({response['revocations'] for response in responses}) == 1
    assert [response['directory']['seeds'][0]['gateway'] for response in responses] == ['b' * 32, 'b' * 32, 'c' * 32, 'b' * 32]
    assert all(response['version'] == 1 for response in responses)
    with primary.access.db() as database:
        assert before == {name: [tuple(row) for row in database.execute('SELECT * FROM ' + name)] for name in before}
        assert database.execute('SELECT COUNT(*) FROM restricted_certificates').fetchone()[0] == 1


@pytest.mark.parametrize('reverse', [False, True])
def test_proof_cannot_cross_nodes_or_be_replayed(gateways, reverse):
    primary, secondary, device, _, _ = gateways
    source, other = (secondary, primary) if reverse else (primary, secondary)
    value = proof(source, device)
    with pytest.raises(Rejected):
        other.fetch(value)
    source.fetch(value)
    with pytest.raises(Rejected):
        source.fetch(value)


@pytest.mark.parametrize('target', ['', 'nl', 'ru', '../nl-amsterdam-2', 'NL-AMSTERDAM-2', 2, False, ['nl-amsterdam-2']])
def test_invalid_target_is_not_defaulted(gateways, target):
    primary, _, device, _, _ = gateways
    with pytest.raises(ValueError):
        request(primary.access, 'challenge', dict(public_identity=device.public_identity,
                wireguard_public_key=device.wireguard_public_key), gateway_id=target)


@pytest.mark.parametrize('field', ['family', 'authority', 'minimum_revision', 'gateway', 'signature', 'expired'])
def test_secondary_manifest_must_match_shared_authority_and_distinct_gateway(gateways, field):
    primary, secondary, _, now, root = gateways
    payload = json.loads(base64.b64decode(secondary.manifest['payload']))
    if field == 'expired':
        payload['expires_at'] = now - 1
    elif field == 'minimum_revision':
        payload[field] += 1
    elif field in ('family', 'gateway'):
        payload[field] = 'b' * 32
    elif field == 'authority':
        other_root = primary.access.path.parent / 'other-authority'
        other_root.mkdir()
        other, _, _ = configured(other_root, now)
        payload[field] = json.loads(base64.b64decode(other.manifest['payload']))['authority']
    secondary.manifest = signed(Ed25519PrivateKey.generate() if field == 'signature' else root, payload)
    write_material(primary.access.path.parent, primary, secondary)
    with pytest.raises((ValueError, InvalidSignature)):
        from_env(primary.access, SECONDARY_GATEWAY)
    assert from_env(primary.access).gateway_id == PRIMARY_GATEWAY


def test_missing_secondary_material_does_not_break_legacy(gateways):
    primary, _, device, _, _ = gateways
    (primary.access.path.parent / 'gateways' / SECONDARY_GATEWAY / 'issuer.json').unlink()
    with pytest.raises(RuntimeError):
        request(primary.access, 'challenge', dict(public_identity=device.public_identity,
                wireguard_public_key=device.wireguard_public_key), gateway_id=SECONDARY_GATEWAY)
    service = from_env(primary.access)
    assert service.fetch(proof(service, device))['device'] == device.reference


@pytest.mark.parametrize('component', ['gateways', SECONDARY_GATEWAY, 'issuer.json', 'directory.json'])
def test_secondary_symlinks_fail_closed(gateways, component):
    primary, _, device, _, _ = gateways
    parent = primary.access.path.parent
    relative = {'gateways': 'gateways', SECONDARY_GATEWAY: 'gateways/' + SECONDARY_GATEWAY}
    path = parent / relative.get(component, 'gateways/' + SECONDARY_GATEWAY + '/' + component)
    moved = parent / 'retained'
    path.rename(moved)
    path.symlink_to(moved, target_is_directory=moved.is_dir())
    with pytest.raises((ValueError, OSError)):
        service = from_env(primary.access, SECONDARY_GATEWAY)
        service.fetch(proof(service, device))


@pytest.mark.parametrize('table', ['devices', 'invites', 'restricted_grants'])
def test_revocation_between_challenge_and_fetch_is_shared(gateways, table):
    primary, secondary, device, _, _ = gateways
    proofs = [(service, proof(service, device)) for service in (primary, secondary)]
    with primary.access.db() as database:
        database.execute('UPDATE ' + table + ' SET revoked=1 WHERE device=?', (device.reference,))
    for service, value in proofs:
        with pytest.raises(Rejected):
            service.fetch(value)


def test_leaf_revocation_is_enforced_on_both_nodes(gateways):
    primary, secondary, device, now, _ = gateways
    response = primary.fetch(proof(primary, device))
    certificate = x509.load_pem_x509_certificate(response['certificate'].encode())
    _, authority = delegation(primary.manifest, primary.anchor, now)
    revoked = x509.RevokedCertificateBuilder().serial_number(certificate.serial_number).revocation_date(utc(now - 1)).build()
    crl = (x509.CertificateRevocationListBuilder().issuer_name(authority.subject)
           .last_update(utc(now - 1)).next_update(utc(now + 3599)).add_extension(x509.CRLNumber(2), False)
           .add_revoked_certificate(revoked).sign(primary.signing_key, None))
    primary.crl_source = secondary.crl_source = lambda: crl.public_bytes(Encoding.PEM)
    for service in (primary, secondary):
        with pytest.raises(Rejected):
            service.fetch(proof(service, device))


@pytest.mark.parametrize('reverse', [False, True])
def test_import_receipt_and_ack_are_bound_to_node(gateways, reverse):
    primary, secondary, device, now, _ = gateways
    source, other = (secondary, primary) if reverse else (primary, secondary)
    response = source.fetch(proof(source, device, 'a' * 32), request_id='b' * 32)
    payload = receipt(response, now)
    request_value = dict(public_identity=device.public_identity, wireguard_public_key=device.wireguard_public_key, receipt=payload)
    with pytest.raises(Rejected):
        readiness_receipts.ack_challenge(other, request_value)
    challenge = readiness_receipts.ack_challenge(source, request_value)
    value = dict(proof=device.prove_transport_key(challenge['challenge']), receipt=payload)
    with pytest.raises(Rejected):
        readiness_receipts.acknowledge(other, value)
    assert readiness_receipts.readback(other, 'a' * 32, device.reference)['status'] == 'UNKNOWN'
    assert readiness_receipts.acknowledge(source, value)['status'] == 'ACK_RECEIVED'
    assert readiness_receipts.readback(source, 'a' * 32, device.reference)['status'] == 'ACK_RECEIVED'
    with pytest.raises(Rejected):
        readiness_receipts.acknowledge(source, value)


def test_gateway_identity_change_invalidates_inflight_proof(gateways):
    _, secondary, device, _, root = gateways
    value = proof(secondary, device)
    payload = json.loads(base64.b64decode(secondary.manifest['payload']))
    secondary.manifest = signed(root, dict(payload, gateway='d' * 32))
    seeds = json.loads(secondary.seed_source())
    seeds['seeds'][0]['gateway'] = 'd' * 32
    secondary.seed_source = lambda: json.dumps(seeds).encode()
    with pytest.raises(Rejected):
        secondary.fetch(value)


def test_receipt_schema_migration_preserves_legacy_rows_and_is_repeatable():
    database = sqlite3.connect(':memory:')
    database.execute('CREATE TABLE restricted_readiness_results (correlation TEXT PRIMARY KEY, nonce TEXT UNIQUE NOT NULL, '
                     'device TEXT NOT NULL, challenge_at INTEGER NOT NULL, fetch_id TEXT, fetch_at INTEGER, '
                     'revision INTEGER, minimum_crl INTEGER, expires INTEGER, ack TEXT, ack_at INTEGER)')
    database.execute("INSERT INTO restricted_readiness_results(correlation,nonce,device,challenge_at) VALUES ('old','nonce','device',123)")
    readiness_receipts.migrate(database)
    readiness_receipts.migrate(database)
    assert database.execute('SELECT correlation,nonce,device,challenge_at,gateway_binding FROM restricted_readiness_results').fetchone() == ('old', 'nonce', 'device', 123, '')
    database.close()


def http_request(runtime, path, body, target=None):
    connection = http.client.HTTPConnection('127.0.0.1', runtime['backend'], timeout=3)
    if target is not None:
        body = dict(gateway_id=target, request=body)
    raw = json.dumps(body).encode()
    connection.putrequest('POST', '/friends/restricted-readiness' + path)
    connection.putheader('Content-Type', 'application/json')
    connection.putheader('Content-Length', str(len(raw)))
    connection.endheaders(raw)
    response = connection.getresponse()
    result = response.status, json.loads(response.read(65537))
    connection.close()
    return result


def test_packaged_http_node_selection_and_legacy_compatibility(runtime):
    secondary, _ = pair(runtime['restricted'])
    write_material(runtime['state'], runtime['restricted'], secondary)
    device = runtime['canary']
    body = dict(public_identity=device.public_identity, wireguard_public_key=device.wireguard_public_key)
    with running(runtime):
        for target, expected in [(None, 'b' * 32), (PRIMARY_GATEWAY, 'b' * 32), (SECONDARY_GATEWAY, 'c' * 32)]:
            status, challenge = http_request(runtime, '/challenge', body, target)
            assert status == 200
            if target is not None:
                assert set(challenge) == {'gateway_id', 'response'} and challenge['gateway_id'] == target
                challenge = challenge['response']
            value = device.prove_transport_key(challenge['challenge'])
            other = PRIMARY_GATEWAY if target == SECONDARY_GATEWAY else SECONDARY_GATEWAY
            assert http_request(runtime, '', value, other)[0] == 403
            status, response = http_request(runtime, '', value, target)
            assert status == 200
            if target is not None:
                assert set(response) == {'gateway_id', 'response'} and response['gateway_id'] == target
                response = response['response']
            assert status == 200 and response['directory']['seeds'][0]['gateway'] == expected
        for target in ['', 'nl', '../nl-amsterdam-2', [PRIMARY_GATEWAY], False]:
            assert http_request(runtime, '/challenge', body, target)[0] == 400
        for malformed in [dict(gateway_id=None, request=body), dict(gateway_id=SECONDARY_GATEWAY, request=[]),
                          dict(gateway_id=SECONDARY_GATEWAY, **body),
                          dict(gateway_id=SECONDARY_GATEWAY, request=body, eligibility='all_activated')]:
            assert http_request(runtime, '/challenge', malformed)[0] == 400
        (runtime['state'] / 'gateways' / SECONDARY_GATEWAY / 'issuer.json').unlink()
        assert http_request(runtime, '/challenge', body, SECONDARY_GATEWAY)[0] == 503
        assert http_request(runtime, '/challenge', body)[0] == 200


def test_target_survives_existing_bounded_relay(runtime):
    secondary, _ = pair(runtime['restricted'])
    write_material(runtime['state'], runtime['restricted'], secondary)
    device = runtime['canary']
    relay = ReadinessRelay(lambda: http.client.HTTPConnection('127.0.0.1', runtime['backend'], timeout=3))

    def forwarded(suffix, body):
        raw = json.dumps(dict(gateway_id=SECONDARY_GATEWAY, request=body)).encode()
        envelope = json.loads(relay.respond('/friends/restricted-readiness' + suffix, raw))
        assert envelope['status'] == 200
        response = json.loads(base64.b64decode(envelope['body']))
        assert response['gateway_id'] == SECONDARY_GATEWAY
        return response['response']

    with running(runtime):
        challenge = forwarded('/challenge', dict(public_identity=device.public_identity, wireguard_public_key=device.wireguard_public_key))
        response = forwarded('', device.prove_transport_key(challenge['challenge']))
        assert response['directory']['seeds'][0]['gateway'] == 'c' * 32


@pytest.mark.parametrize('target', [PRIMARY_GATEWAY, SECONDARY_GATEWAY])
def test_targeted_delivery_retains_native_contract(gateways, target):
    tool = os.environ.get('FC_TEST_GO')
    if not tool:
        pytest.skip('set FC_TEST_GO to the locked Go toolchain for native delivery verification')
    primary, _, device, now, _ = gateways
    service = from_env(primary.access, target)
    response = service.fetch(proof(service, device))
    value = dict(response=response, identity=base64.b64encode(device._identity.get_private_key()).decode(),
                 anchor=base64.b64encode(service.anchor).decode(), now=now)
    result = subprocess.run([tool, 'run', './wholedevice/testdata/delivery-check.go'],
                            input=json.dumps(value).encode(), capture_output=True,
                            cwd=Path(__file__).resolve().parents[1] / 'carrier', timeout=90)
    assert result.returncode == 0 and result.stdout == b'compatible\n', 'targeted delivery/native incompatibility'
