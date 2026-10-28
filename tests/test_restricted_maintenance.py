import base64
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from types import SimpleNamespace

import pytest
from cryptography import x509
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from cryptography.x509.oid import NameOID

from control.friends import restricted_maintenance as maintenance
from control.friends.restricted import directory, iso, utc


def private_file(path, raw):
    path.write_bytes(raw)
    path.chmod(0o600)
    return path


def make_crl(setup, number=27211, *, signing=None, issuer=None, issued=None, expires=None):
    return (x509.CertificateRevocationListBuilder().issuer_name(issuer or setup.authority.subject)
            .last_update(utc(setup.now - 1 if issued is None else issued))
            .next_update(utc(setup.now + 899 if expires is None else expires))
            .add_extension(x509.CRLNumber(number), False).sign(signing or setup.signing, None)
            .public_bytes(Encoding.PEM))


def permit_for(setup, payload=None, action='reconcile_current_floor'):
    payload = setup.payload if payload is None else payload
    request = maintenance.encode(dict(revocations=payload.decode()))
    number = x509.load_pem_x509_crl(payload).extensions.get_extension_for_class(x509.CRLNumber).value.crl_number
    permit = dict(schema=1, operation_id='restricted_maintenance_' + 'a' * 32, action=action,
        expected_profile_sha256=maintenance.digest(setup.profile.read_bytes()),
        expected_directory_sha256=maintenance.digest(setup.directory.read_bytes()),
        expected_embedded_crl_sha256=maintenance.digest(setup.payload), expected_embedded_crl_number=27211,
        expected_minimum_crl=27088, request_sha256=maintenance.digest(request), target_crl_sha256=maintenance.digest(payload),
        target_crl_number=number, target_minimum_crl=number, not_before=setup.now, not_after=setup.now + 300)
    return permit, request


@pytest.fixture
def setup(tmp_path):
    root = tmp_path / 'private'
    root.mkdir(mode=0o700)
    operations = root / 'operations'
    operations.mkdir(mode=0o700)
    now = 1800000000
    signing = Ed25519PrivateKey.generate()
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'synthetic maintenance authority')])
    authority = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(signing.public_key())
        .serial_number(1).not_valid_before(utc(now - 100)).not_valid_after(utc(now + 86400))
        .add_extension(x509.BasicConstraints(ca=True, path_length=0), True)
        .add_extension(x509.KeyUsage(False, False, False, False, False, True, True, False, False), True).sign(signing, None))
    fixture = SimpleNamespace(now=now, signing=signing, authority=authority, root=root)
    fixture.payload = make_crl(fixture)
    fixture.profile = private_file(root / 'profile.json', json.dumps(dict(authority=authority.public_bytes(Encoding.PEM).decode(),
        revocations=fixture.payload.decode(), minimum_crl=27088, family='a' * 32, gateway='b' * 32,
        minimum_revision=1, certificate='synthetic certificate projection', private_key='synthetic-key-marker',
        unrelated=dict(settings=[1, 'unchanged', True])), indent=2).encode())
    fixture.directory = private_file(root / 'directory.json', maintenance.encode(dict(version=1, family='a' * 32,
        issued_at=iso(now - 1), expires_at=iso(now + 899), seeds=[dict(gateway='b' * 32,
        transport='telemost-webrtc', join_url='https://telemost.yandex.ru/j/maintenance-synthetic-only')])))
    fixture.config = maintenance.Configuration(fixture.profile, fixture.directory, operations, b'x' * 32,
                                               owner_uid=os.getuid(), boundary=root)
    fixture.permit, fixture.request = permit_for(fixture)
    fixture.operation = maintenance.Operation(fixture.config, fixture.permit, clock=lambda: fixture.now)
    return fixture


def journal(setup):
    return maintenance.strict((setup.operation.root / 'journal.json').read_bytes(), 16384, 'INVALID_REQUEST')['journal']


def test_reconcile_floor_exact_payload_and_private_receipt(setup):
    before = json.loads(setup.profile.read_bytes())
    before_directory = setup.directory.read_bytes()
    result = setup.operation.execute(setup.request)
    after = json.loads(setup.profile.read_bytes())
    assert result['result'] == 'PASS' and result['minimum_crl'] == result['crl_number'] == 27211
    assert after == dict(before, minimum_crl=27211)
    assert after['revocations'].encode() == setup.payload and setup.directory.read_bytes() == before_directory
    assert journal(setup)['state'] == 'COMMITTED' and journal(setup)['attempt_count'] == 1
    assert setup.operation.root.stat().st_mode & 0o777 == 0o700
    assert all(path.stat().st_mode & 0o777 == 0o600 for path in setup.operation.root.iterdir())
    raw = maintenance.encode(maintenance.sanitized(result))
    for secret in (b'PRIVATE', b'BEGIN', b'synthetic-key-marker', b'join_url', b'certificate', b'operation_id', b'/tmp/', b'x' * 32):
        assert secret not in raw


@pytest.mark.parametrize('field,value', [('expected_profile_sha256', '0' * 64), ('expected_directory_sha256', '0' * 64),
    ('expected_minimum_crl', 27087), ('expected_embedded_crl_sha256', '0' * 64), ('expected_embedded_crl_number', 27210)])
def test_expected_state_mismatch(setup, field, value):
    permit = dict(setup.permit, **{field: value})
    if field == 'expected_embedded_crl_sha256':
        permit['target_crl_sha256'] = value
    if field == 'expected_embedded_crl_number':
        permit.update(target_crl_number=value, target_minimum_crl=value)
    before = setup.profile.read_bytes()
    with pytest.raises(maintenance.MaintenanceError, match='MAINTENANCE_PRECONDITION_CHANGED'):
        maintenance.Operation(setup.config, permit, clock=lambda: setup.now).execute(setup.request)
    assert setup.profile.read_bytes() == before and not setup.operation.root.exists()


def test_same_number_different_bytes_rejected(setup):
    changed = make_crl(setup, issued=setup.now)
    request = maintenance.encode(dict(revocations=changed.decode()))
    with pytest.raises(maintenance.MaintenanceError, match='CRL_PAYLOAD_CONFLICT'):
        setup.operation.execute(request)
    assert not setup.operation.root.exists()


@pytest.mark.parametrize('case', ['expired', 'future', 'lifetime', 'signature', 'issuer'])
def test_invalid_crl_before_write(setup, case):
    options = dict(number=27212)
    if case == 'expired':
        options.update(issued=setup.now - 100, expires=setup.now)
    elif case == 'future':
        options['issued'] = setup.now + 1
    elif case == 'lifetime':
        options['expires'] = setup.now + 14400
    elif case == 'signature':
        options['signing'] = Ed25519PrivateKey.generate()
    else:
        options['issuer'] = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'wrong synthetic authority')])
    payload = make_crl(setup, **options)
    permit, request = permit_for(setup, payload, 'apply_exact_crl')
    before = setup.profile.read_bytes()
    with pytest.raises(maintenance.MaintenanceError, match='PROFILE_VALIDATION_FAILED'):
        maintenance.Operation(setup.config, permit, clock=lambda: setup.now).execute(request)
    assert setup.profile.read_bytes() == before


@pytest.mark.parametrize('delay', [-1, 300, 301])
def test_execution_window(setup, delay):
    setup.now += delay
    with pytest.raises(maintenance.MaintenanceError, match='INVALID_PERMIT'):
        setup.operation.execute(setup.request)
    assert not setup.operation.root.exists()


@pytest.mark.parametrize('change', ['unknown', 'missing', 'boolean', 'hash', 'operation', 'window', 'float', 'action'])
def test_permit_shape(setup, change):
    permit = dict(setup.permit)
    if change == 'unknown':
        permit['host'] = 'forbidden'
    elif change == 'missing':
        del permit['target_minimum_crl']
    elif change == 'boolean':
        permit['expected_minimum_crl'] = True
    elif change == 'hash':
        permit['target_crl_sha256'] = 'A' * 64
    elif change == 'operation':
        permit['operation_id'] = '../forbidden'
    elif change == 'window':
        permit['not_after'] += 1
    elif change == 'float':
        permit['expected_minimum_crl'] = 27088.0
    else:
        permit['action'] = 'shell'
    with pytest.raises(maintenance.MaintenanceError, match='INVALID_PERMIT'):
        maintenance.Operation(setup.config, permit)


@pytest.mark.parametrize('raw', [b'{"revocations":"","revocations":""}', b'{"revocations":NaN}',
    b'{"revocations":Infinity}', b'{"revocations":1e999}', b'{"revocations":"","extra":1}', b' ' * 20001])
def test_strict_request(raw):
    with pytest.raises(maintenance.MaintenanceError, match='INVALID_REQUEST'):
        maintenance.request_payload(raw)


def test_replay_and_conflict(setup):
    setup.operation.execute(setup.request)
    before = setup.profile.read_bytes()
    assert setup.operation.execute(setup.request)['result'] == 'IDEMPOTENT'
    assert journal(setup)['attempt_count'] == 1
    with pytest.raises(maintenance.MaintenanceError, match='MAINTENANCE_STATE_CONFLICT'):
        setup.operation.execute(setup.request + b' ')
    changed = dict(setup.permit, not_after=setup.permit['not_after'] - 1)
    with pytest.raises(maintenance.MaintenanceError, match='MAINTENANCE_STATE_CONFLICT'):
        maintenance.Operation(setup.config, changed, clock=lambda: setup.now).execute(setup.request)
    assert setup.profile.read_bytes() == before


@pytest.mark.parametrize('state', ['APPLYING', 'UNKNOWN'])
def test_recovery_target_already_installed(setup, state):
    setup.operation.execute(setup.request)
    value = journal(setup)
    value.update(committed_write=False, applied_at=None)
    setup.operation._save(value, state)
    before = setup.profile.read_bytes()
    assert setup.operation.reconcile(setup.request)['result'] == 'IDEMPOTENT'
    assert setup.profile.read_bytes() == before and journal(setup)['attempt_count'] == 1


@pytest.mark.parametrize('max_attempts,allowed', [(1, False), (2, True)])
def test_recovery_proven_before_state_budget(setup, max_attempts, allowed):
    operation = maintenance.Operation(replace(setup.config, max_attempts=max_attempts), setup.permit, clock=lambda: setup.now)
    value = operation._prepare(setup.request)
    value['attempt_count'] = 1
    operation._save(value, 'APPLYING')
    if allowed:
        assert operation.execute(setup.request)['result'] == 'PASS'
        assert journal(setup)['attempt_count'] == 2
    else:
        with pytest.raises(maintenance.MaintenanceError, match='MAINTENANCE_STATE_CONFLICT'):
            operation.execute(setup.request)


def test_unproven_before_state_cannot_retry_even_with_two_attempt_budget(setup):
    operation = maintenance.Operation(replace(setup.config, max_attempts=2), setup.permit, clock=lambda: setup.now)
    value = operation._prepare(setup.request)
    value.update(attempt_count=1, replace_started=True)
    operation._save(value, 'UNKNOWN')
    with pytest.raises(maintenance.MaintenanceError, match='MAINTENANCE_STATE_CONFLICT'):
        operation.execute(setup.request)


def test_conflicting_state_not_overwritten(setup):
    setup.operation._prepare(setup.request)
    changed = setup.profile.read_bytes() + b'\n'
    setup.profile.write_bytes(changed)
    with pytest.raises(maintenance.MaintenanceError, match='MAINTENANCE_STATE_CONFLICT'):
        setup.operation.execute(setup.request)
    assert setup.profile.read_bytes() == changed


def test_postwrite_rollback_exact_backup(setup, monkeypatch):
    before = setup.profile.read_bytes()
    def fail(journal):
        raise maintenance.MaintenanceError('READBACK_MISMATCH')
    monkeypatch.setattr(setup.operation, '_target', fail)
    with pytest.raises(maintenance.MaintenanceError, match='MAINTENANCE_ROLLED_BACK'):
        setup.operation.execute(setup.request)
    assert setup.profile.read_bytes() == before and journal(setup)['state'] == 'ROLLED_BACK'
    with pytest.raises(maintenance.MaintenanceError, match='MAINTENANCE_STATE_CONFLICT'):
        setup.operation.execute(setup.request)


def test_rollback_failure_classified_without_overwriting_conflict(setup, monkeypatch):
    def fail(journal):
        setup.profile.write_bytes(b'conflicting concurrent state')
        raise maintenance.MaintenanceError('READBACK_MISMATCH')
    monkeypatch.setattr(setup.operation, '_target', fail)
    with pytest.raises(maintenance.MaintenanceError, match='MAINTENANCE_ROLLBACK_FAILED'):
        setup.operation.execute(setup.request)
    assert setup.profile.read_bytes() == b'conflicting concurrent state' and journal(setup)['state'] == 'UNKNOWN'


def test_killed_after_replace_reconciles_without_second_apply(setup, monkeypatch):
    original = setup.operation._complete
    def killed(*args, **kwargs):
        raise SystemExit(99)
    monkeypatch.setattr(setup.operation, '_complete', killed)
    with pytest.raises(SystemExit):
        setup.operation.execute(setup.request)
    assert journal(setup)['state'] == 'APPLYING'
    monkeypatch.setattr(setup.operation, '_complete', original)
    assert setup.operation.reconcile(setup.request)['result'] == 'IDEMPOTENT'
    assert journal(setup)['attempt_count'] == 1


def test_apply_next_crl_and_helper_trusted_readback(setup):
    payload = make_crl(setup, 27212, issued=setup.now)
    permit, request = permit_for(setup, payload, 'apply_exact_crl')
    operation = maintenance.Operation(setup.config, permit, clock=lambda: setup.now)
    response = operation.execute(request)
    assert response['crl_number'] == response['minimum_crl'] == 27212
    assert json.loads(setup.profile.read_bytes())['revocations'].encode() == payload
    from control.friends.paid_canary_crl import TransportResult, TrustedReadback
    readback = maintenance.trusted_readback(response)
    assert type(readback) is TrustedReadback and readback.directory_bytes == setup.directory.read_bytes()
    assert TransportResult('ACCEPTED', readback).readback.payload_sha256 == maintenance.digest(payload)
    assert operation.execute(request)['result'] == 'IDEMPOTENT'
    changed = maintenance.encode(dict(revocations=make_crl(setup, 27212, issued=setup.now + 1).decode()))
    with pytest.raises(maintenance.MaintenanceError, match='MAINTENANCE_STATE_CONFLICT'):
        operation.execute(changed)


@pytest.mark.parametrize('case', ['operation_symlink', 'profile_symlink', 'mode', 'hardlink', 'partial_directory', 'mac'])
def test_private_files_fail_closed(setup, case):
    if case == 'operation_symlink':
        setup.operation.root.symlink_to(setup.root)
    elif case == 'profile_symlink':
        backup = setup.root / 'original'
        setup.profile.rename(backup)
        setup.profile.symlink_to(backup)
    elif case == 'mode':
        setup.profile.chmod(0o644)
    elif case == 'hardlink':
        os.link(setup.profile, setup.root / 'other')
    elif case == 'partial_directory':
        setup.operation.root.mkdir(mode=0o700)
    else:
        setup.operation._prepare(setup.request)
        value = json.loads((setup.operation.root / 'journal.json').read_bytes())
        value['journal']['attempt_count'] = 99
        (setup.operation.root / 'journal.json').write_bytes(maintenance.encode(value))
    with pytest.raises((maintenance.MaintenanceError, OSError)):
        setup.operation.execute(setup.request)


def test_directory_validated_before_write(setup):
    value = json.loads(setup.directory.read_bytes())
    value['family'] = 'c' * 32
    setup.directory.write_bytes(maintenance.encode(value))
    permit, request = permit_for(setup)
    before = setup.profile.read_bytes()
    with pytest.raises(maintenance.MaintenanceError, match='DIRECTORY_VALIDATION_FAILED'):
        maintenance.Operation(setup.config, permit, clock=lambda: setup.now).execute(request)
    assert setup.profile.read_bytes() == before and not setup.operation.root.exists()


def test_staged_file_fsynced_before_applying_and_replace(setup, monkeypatch):
    original = maintenance.os.replace
    def checked(source, target):
        if target == setup.profile:
            assert source.parent == setup.profile.parent and source.stat().st_mode & 0o777 == 0o600
            assert source.read_bytes() == (setup.operation.root / 'target-profile.json').read_bytes()
            assert journal(setup)['state'] == 'APPLYING' and journal(setup)['attempt_count'] == 1
        return original(source, target)
    monkeypatch.setattr(maintenance.os, 'replace', checked)
    assert setup.operation.execute(setup.request)['result'] == 'PASS'


def test_lock_contention(setup):
    with setup.config.lock():
        with pytest.raises(maintenance.MaintenanceError, match='MAINTENANCE_PRECONDITION_CHANGED'):
            setup.operation.execute(setup.request)


def test_profile_drift_during_staging_is_not_overwritten(setup, monkeypatch):
    original = maintenance.atomic
    changed = setup.profile.read_bytes() + b'\n'
    def drift(path, raw, **kwargs):
        if path == setup.profile:
            setup.profile.write_bytes(changed)
        return original(path, raw, **kwargs)
    monkeypatch.setattr(maintenance, 'atomic', drift)
    with pytest.raises(maintenance.MaintenanceError, match='MAINTENANCE_PRECONDITION_CHANGED'):
        setup.operation.execute(setup.request)
    assert setup.profile.read_bytes() == changed and journal(setup)['state'] == 'CONFLICT'


@pytest.mark.parametrize('field,value', [('schema', True), ('minimum_crl', True), ('crl_number', -1),
    ('payload_sha256', 'wrong'), ('directory_base64', 'invalid'), ('directory_sha256', '0' * 64)])
def test_readback_rejects_tampering(setup, field, value):
    result = setup.operation.execute(setup.request)
    result[field] = value
    with pytest.raises(maintenance.MaintenanceError, match='READBACK_MISMATCH'):
        maintenance.trusted_readback(result)


def test_same_target_number_different_bytes_on_new_operation_conflicts(setup):
    payload = make_crl(setup, 27212, issued=setup.now)
    permit, request = permit_for(setup, payload, 'apply_exact_crl')
    maintenance.Operation(setup.config, permit, clock=lambda: setup.now).execute(request)
    changed = make_crl(setup, 27212, issued=setup.now + 1)
    request = maintenance.encode(dict(revocations=changed.decode()))
    next_permit = dict(permit, operation_id='restricted_maintenance_' + 'd' * 32,
        action='reconcile_current_floor', expected_profile_sha256=maintenance.digest(setup.profile.read_bytes()),
        expected_embedded_crl_sha256=maintenance.digest(payload), expected_embedded_crl_number=27212,
        expected_minimum_crl=27212, target_crl_sha256=maintenance.digest(payload), request_sha256=maintenance.digest(request))
    with pytest.raises(maintenance.MaintenanceError, match='CRL_PAYLOAD_CONFLICT'):
        maintenance.Operation(setup.config, next_permit, clock=lambda: setup.now + 1).execute(request)


def test_credential_restrictions_removal_and_caller_commands(setup, monkeypatch, capsys):
    public = Ed25519PrivateKey.generate().public_key().public_bytes(Encoding.OpenSSH, PublicFormat.OpenSSH).decode()
    line = maintenance.credential_line(public, '/usr/bin/python3', '/private/operation.pyz')
    for restriction in (b'restrict,', b'no-pty', b'no-port-forwarding', b'no-agent-forwarding', b'no-X11-forwarding', b'no-user-rc', b'timeout --signal=KILL 35'):
        assert restriction in line
    snapshot_line = b'restrict,command="readonly-snapshot" synthetic-original-key\n'
    assert maintenance.remove_credential(snapshot_line + line, line) == snapshot_line
    for command in ('sh', 'READ_ONLY_SECURITY_SNAPSHOT', 'apply_exact_crl', 'reconcile_current_floor', 'echo secret'):
        monkeypatch.setenv('SSH_ORIGINAL_COMMAND', command)
        assert maintenance.main([]) == 2
        assert json.loads(capsys.readouterr().out)['result'] == 'INVALID_REQUEST'


def test_registry_not_opened_or_changed(setup, monkeypatch):
    registry = setup.root / 'synthetic-registry.db'
    with sqlite3.connect(registry) as database:
        for name in ('paid_beta_subscriptions', 'paid_beta_events', 'devices', 'invites', 'restricted_grants'):
            database.execute('CREATE TABLE ' + name + '(value TEXT)')
            database.execute('INSERT INTO ' + name + ' VALUES (?)', ('unchanged',))
    before = registry.read_bytes()
    def forbidden(*args, **kwargs):
        raise AssertionError('Registry connection forbidden')
    monkeypatch.setattr(sqlite3, 'connect', forbidden)
    setup.operation.execute(setup.request)
    assert registry.read_bytes() == before


@pytest.mark.parametrize('lifetime', [899, 900, 3599, 3600, 3601, 10799, 10800, 10801, 13399, 13402, 14399, 14400, 14401])
def test_parser_lifetime_matrix(setup, lifetime):
    value = json.loads(setup.directory.read_bytes())
    value.update(issued_at=iso(setup.now), expires_at=iso(setup.now + lifetime))
    raw = maintenance.encode(value)
    if lifetime <= 14400:
        assert directory(raw, 'a' * 32, 'b' * 32, setup.now)
    else:
        with pytest.raises(ValueError):
            directory(raw, 'a' * 32, 'b' * 32, setup.now)


@pytest.mark.parametrize('request_kind', ['snapshot', 'maintenance', 'snapshot_after_reconcile'])
def test_exact_snapshot_runtime_unchanged_readonly(setup, request_kind):
    archive = os.environ.get('FC_TEST_SNAPSHOT_ARCHIVE')
    if not archive:
        pytest.skip('Exact retained generic snapshot archive required for deployed-contract proof')
    raw = Path(archive).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == '0120dad028ead353b8b83a600538f3e578b2b46ddf871bf16e97529f9449f450'
    source = '''import sys,json,base64
sys.path.insert(0,sys.argv[1])
from control.friends.restricted_sync import gateway
from pathlib import Path
request=json.loads(sys.stdin.buffer.read())
try:
 result=gateway(Path(sys.argv[2]),Path(sys.argv[3]),base64.b64decode(request['raw']),request['now'])
 print(json.dumps({'result':'PASS','response':base64.b64encode(result).decode()}))
except Exception as error:
 print(json.dumps({'result':str(error) if str(error)=='MAINTENANCE_TRANSACTION_REQUIRED' else 'FAILED'}))
'''
    if request_kind == 'snapshot_after_reconcile':
        setup.operation.execute(setup.request)
    request = maintenance.encode(dict(schema=1, operation='READ_ONLY_SECURITY_SNAPSHOT')) if request_kind != 'maintenance' else setup.request
    before = setup.profile.read_bytes(), setup.directory.read_bytes()
    process = subprocess.run([sys.executable, '-I', '-B', '-c', source, archive, str(setup.profile), str(setup.directory)],
        input=maintenance.encode(dict(raw=base64.b64encode(request).decode(), now=setup.now)), capture_output=True, check=True)
    assert not process.stderr
    result = json.loads(process.stdout)
    if request_kind != 'maintenance':
        response = json.loads(base64.b64decode(result['response']))
        assert set(response) == {'schema', 'profile', 'directory'} and response['schema'] == 1
        assert set(response['profile']) == {'authority', 'certificate', 'revocations', 'family', 'gateway', 'minimum_revision', 'minimum_crl'}
        assert base64.b64decode(response['directory']) == setup.directory.read_bytes()
        assert response['profile']['minimum_crl'] == (27211 if request_kind == 'snapshot_after_reconcile' else 27088)
    else:
        assert result['result'] == 'MAINTENANCE_TRANSACTION_REQUIRED'
    assert before == (setup.profile.read_bytes(), setup.directory.read_bytes()) and Path(archive).read_bytes() == raw
