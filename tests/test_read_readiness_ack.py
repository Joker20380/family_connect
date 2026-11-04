import json
import subprocess
import sys
import time

import pytest

from control.friends import readiness_receipts
from control.friends.access import Access
from control.friends.restricted import PRIMARY_GATEWAY, SECONDARY_GATEWAY, from_env
from scripts import read_readiness_ack as reader
from scripts.package_friends_http import ARCHIVE, build
from test_friends_restricted import configured
from test_restricted_gateway_selection import pair, proof, receipt, write_material


@pytest.fixture
def acknowledged(tmp_path, monkeypatch):
    primary, device, now = configured(tmp_path, int(time.time()))
    secondary, _ = pair(primary)
    write_material(tmp_path, primary, secondary)
    monkeypatch.setenv('FC_FRIENDS_RESTRICTED_DIR', str(tmp_path))
    service = from_env(primary.access, SECONDARY_GATEWAY)
    response = service.fetch(proof(service, device, 'a' * 32), request_id='b' * 32)
    payload = receipt(response, now)
    challenge = readiness_receipts.ack_challenge(service, dict(public_identity=device.public_identity,
        wireguard_public_key=device.wireguard_public_key, receipt=payload))
    readiness_receipts.acknowledge(service, dict(proof=device.prove_transport_key(challenge['challenge']), receipt=payload))
    return service, device, payload


def observe(acknowledged, **options):
    service, device, _ = acknowledged
    arguments = dict(gateway_id=SECONDARY_GATEWAY, device_reference=device.reference, version_code=112)
    arguments.update(options)
    return reader.inspect(service.access.path, service.access.path.parent, 'a' * 32, **arguments)


def test_targeted_all_activated_readback_is_readonly_and_safe(acknowledged, monkeypatch):
    service, device, payload = acknowledged
    before = service.access.path.read_bytes()
    monkeypatch.setenv('FC_FRIENDS_RESTRICTED_DIR', '/retained-environment')
    monkeypatch.setattr(Access, 'db', lambda *_: pytest.fail('Readback must not open a writable connection'))
    result = observe(acknowledged)
    assert result['status'] == 'ACK_RECEIVED'
    assert result['receipt'] == payload
    assert result['gateway_id'] == SECONDARY_GATEWAY
    assert result['expected_version_code'] == 112
    assert service.access.path.read_bytes() == before
    assert reader.os.environ['FC_FRIENDS_RESTRICTED_DIR'] == '/retained-environment'
    raw = json.dumps(result)
    for secret in (device.reference, device.public_identity, device.wireguard_public_key, 'join_url', 'issuer.key'):
        assert secret not in raw


@pytest.mark.parametrize('options', [dict(gateway_id=PRIMARY_GATEWAY), dict(device_reference='f' * 32),
                                    dict(version_code=111), dict(version_code=113)])
def test_target_owner_and_version_cannot_cross(acknowledged, options):
    result = observe(acknowledged, **options)
    assert result['status'] == 'UNKNOWN'
    assert result['receipt'] is None
    assert 'received_at' not in result


def test_all_activated_never_infers_a_device(acknowledged):
    with pytest.raises(ValueError):
        observe(acknowledged, device_reference=None)


@pytest.mark.parametrize('table', ['devices', 'invites', 'restricted_grants'])
def test_readback_retains_revocation_checks(acknowledged, table):
    service, device, _ = acknowledged
    with service.access.db() as database:
        database.execute('UPDATE ' + table + ' SET revoked=1 WHERE device=?', (device.reference,))
    result = observe(acknowledged)
    assert result['status'] == 'ACK_PENDING'
    assert result['receipt'] is None


def test_legacy_sole_owner_default_is_unchanged(acknowledged):
    service, device, _ = acknowledged
    root = service.access.path.parent
    (root / 'admission.json').write_text(json.dumps({'devices': [device.reference]}))
    result = reader.inspect(service.access.path, root, 'a' * 32)
    assert result == dict(version=1, correlation_id='a' * 32, status='UNKNOWN', receipt=None)
    primary = from_env(service.access)
    device_proof = proof(primary, device, 'c' * 32)
    response = primary.fetch(device_proof, request_id='d' * 32)
    payload = dict(receipt(response, int(time.time())), correlation_id='c' * 32, challenge_id='c' * 32, fetch_id='d' * 32)
    challenge = readiness_receipts.ack_challenge(primary, dict(public_identity=device.public_identity,
        wireguard_public_key=device.wireguard_public_key, receipt=payload))
    readiness_receipts.acknowledge(primary, dict(proof=device.prove_transport_key(challenge['challenge']), receipt=payload))
    assert reader.inspect(service.access.path, root, 'c' * 32) == readiness_receipts.readback(primary, 'c' * 32, device.reference)


def test_expired_readiness_is_not_accepted(acknowledged, monkeypatch):
    _, _, payload = acknowledged
    monkeypatch.setattr(reader, 'Access', lambda database: Access(database, clock=lambda: payload['expires_at']))
    result = observe(acknowledged)
    assert result['status'] == 'ACK_PENDING' and result['receipt'] is None


def test_missing_ack_is_not_manufactured(acknowledged):
    service, _, _ = acknowledged
    with service.access.db() as database:
        database.execute('UPDATE restricted_readiness_results SET ack=NULL,ack_at=NULL')
    before = service.access.path.read_bytes()
    result = observe(acknowledged)
    assert result['status'] == 'ACK_PENDING' and result['receipt'] is None
    assert service.access.path.read_bytes() == before


def test_failed_import_ack_remains_a_failed_import(acknowledged):
    service, device, original = acknowledged
    payload = dict(original, result='NATIVE_VALIDATION_FAILED', failure_reason='NATIVE_VALIDATION_FAILED',
                   provisioning='NOT_READY', bootstrap='NOT_READY', orchestrator_usable=False,
                   revision=0, minimum_crl=0, expires_at=0, observed_at=original['observed_at'] + 1)
    challenge = readiness_receipts.ack_challenge(service, dict(public_identity=device.public_identity,
        wireguard_public_key=device.wireguard_public_key, receipt=payload))
    readiness_receipts.acknowledge(service, dict(proof=device.prove_transport_key(challenge['challenge']), receipt=payload))
    result = observe(acknowledged)
    assert result['status'] == 'ACK_RECEIVED'
    assert result['receipt']['result'] == 'NATIVE_VALIDATION_FAILED'
    assert result['receipt']['orchestrator_usable'] is False


@pytest.mark.parametrize('options', [dict(gateway_id='unknown'), dict(device_reference='*'),
                                    dict(device_reference='f' * 31), dict(version_code=0),
                                    dict(version_code=True), dict(version_code=2**53)])
def test_invalid_selection_is_rejected_without_writes(acknowledged, options):
    service, _, _ = acknowledged
    before = service.access.path.read_bytes()
    with pytest.raises(ValueError):
        observe(acknowledged, **options)
    assert service.access.path.read_bytes() == before


def test_missing_secondary_material_does_not_fall_back(acknowledged, monkeypatch):
    service, _, _ = acknowledged
    (service.access.path.parent / 'gateways' / SECONDARY_GATEWAY / 'issuer.json').unlink()
    monkeypatch.delenv('FC_FRIENDS_RESTRICTED_DIR')
    with pytest.raises(OSError):
        observe(acknowledged)
    assert 'FC_FRIENDS_RESTRICTED_DIR' not in reader.os.environ


def arguments(acknowledged, monkeypatch):
    service, device, _ = acknowledged
    root = service.access.path.parent
    selected = root / 'selected-device'
    selected.write_text(device.reference + '\n')
    selected.chmod(0o600)
    monkeypatch.setattr(sys, 'argv', ['read_readiness_ack', '--database', str(service.access.path),
        '--material', str(root), '--correlation', 'a' * 32, '--gateway-id', SECONDARY_GATEWAY,
        '--device-file', str(selected), '--version-code', '112'])
    return selected


def test_cli_reads_private_selection_without_printing_it(acknowledged, monkeypatch, capsys):
    arguments(acknowledged, monkeypatch)
    reader.main()
    captured = capsys.readouterr()
    assert not captured.err
    result = json.loads(captured.out)
    assert result['status'] == 'ACK_RECEIVED' and result['gateway_id'] == SECONDARY_GATEWAY
    assert acknowledged[1].reference not in captured.out


def test_packaged_operator_entrypoint_matches_source(acknowledged, monkeypatch, tmp_path):
    arguments(acknowledged, monkeypatch)
    output = tmp_path / 'artifact'
    build(output)
    archive = output / ARCHIVE
    command = 'import runpy,sys;sys.path.insert(0,sys.argv.pop(1));runpy.run_module("scripts.read_readiness_ack",run_name="__main__")'
    result = subprocess.run([sys.executable, '-I', '-c', command, str(archive), *sys.argv[1:]],
                            cwd=tmp_path, capture_output=True, text=True, timeout=20)
    assert result.returncode == 0 and not result.stderr
    assert json.loads(result.stdout) == observe(acknowledged)
    assert acknowledged[1].reference not in result.stdout


@pytest.mark.parametrize('failure', ['symlink', 'permissions', 'oversize', 'invalid'])
def test_cli_refuses_unsafe_device_file_without_echo(acknowledged, monkeypatch, capsys, failure):
    selected = arguments(acknowledged, monkeypatch)
    if failure == 'symlink':
        original = selected.with_suffix('.original')
        selected.rename(original)
        selected.symlink_to(original)
    elif failure == 'permissions':
        selected.chmod(0o644)
    else:
        selected.write_text('private-device-input' * (100 if failure == 'oversize' else 1))
    with pytest.raises(SystemExit) as result:
        reader.main()
    assert result.value.code == 1
    captured = capsys.readouterr()
    assert not captured.err
    assert json.loads(captured.out) == dict(version=1, status='UNKNOWN', reason='READBACK_UNAVAILABLE')
    assert acknowledged[1].reference not in captured.out and 'private-device-input' not in captured.out
