import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sqlite3
from types import SimpleNamespace

import pytest
from cryptography import x509
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding

from control.friends import paid_canary_crl as crl, paid_beta, restricted_admin
from control.friends.restricted import delegation, iso, utc
from control.friends.restricted_sync import gateway
from test_friends_restricted import proof
from test_paid_beta_canary_operator import KEY, canary, envelope
from test_paid_beta_readiness import paid_setup


def private_file(path, raw):
    path.write_bytes(raw)
    path.chmod(0o600)
    return path


def snapshot(setup):
    with sqlite3.connect(setup.service.access.path) as database:
        rows = '\n'.join(database.iterdump())
    return rows, setup.config.crl.read_bytes(), setup.config.directory.read_bytes(), setup.profile.read_bytes()


def readback(setup):
    profile = json.loads(setup.profile.read_bytes())
    payload = profile['revocations'].encode()
    number = x509.load_pem_x509_crl(payload).extensions.get_extension_for_class(x509.CRLNumber).value.crl_number
    return crl.TrustedReadback(number, crl.digest(payload), profile['minimum_crl'], setup.remote_directory.read_bytes())


@pytest.fixture
def operation(paid_setup, tmp_path, monkeypatch):
    service, device, support, now = paid_setup
    registry = service.access, device, support
    canary.apply(service.access.path, KEY, envelope(registry), now)
    service.access.clock = lambda: now + 60
    canary.apply(service.access.path, KEY, envelope(registry, 1, now + 60, 600), now + 60)
    material = service.fetch(proof(service, device))
    certificate = x509.load_pem_x509_certificate(material['certificate'].encode())
    service.access.clock = lambda: now + 61
    canary.apply(service.access.path, KEY, envelope(registry, 2, now + 61), now + 61)
    root = tmp_path / 'private'
    root.mkdir(mode=0o700)
    operations = root / 'operations'
    operations.mkdir(mode=0o700)
    config = crl.Configuration(service, operations, private_file(root / 'sync.lock', b''),
        private_file(root / 'local-crl.pem', service.crl_source()), private_file(root / 'local-directory.json', service.seed_source()), KEY)
    service.crl_source = config.crl.read_bytes
    with service.access.db() as database:
        database.execute('CREATE TABLE restricted_crl_sequence(singleton INTEGER PRIMARY KEY, sequence INTEGER NOT NULL)')
        database.execute('INSERT INTO restricted_crl_sequence VALUES(1,1)')
    token = canary.token_for(KEY, device.reference)
    permit = dict(schema=1, alias=canary.ALIAS, operation_id='canary_crl_' + 'a' * 32,
        device_token=token, safe_ref='dev_' + token[:12], expected_subscription_version=3, expected_event_count=3,
        expected_effective_state='expired', expected_certificate_safe_token=crl.serial_token(KEY, certificate.serial_number),
        not_before=now + 61, not_after=now + 361)
    trust, authority = delegation(service.manifest, service.anchor, now)
    profile = private_file(root / 'gateway.json', crl.encode(dict(authority=trust['authority'], family=trust['family'],
        gateway=trust['gateway'], revocations=config.crl.read_text(), minimum_crl=1)))
    remote_directory = json.loads(config.directory.read_bytes())
    remote_directory['issued_at'] = iso(now + 60)
    setup = SimpleNamespace(service=service, device=device, support=support, now=now + 61, config=config, permit=permit,
        certificate=certificate, authority=authority, profile=profile,
        remote_directory=private_file(root / 'remote-directory.json', crl.encode(remote_directory)), calls=[], requests=[])
    builder = restricted_admin.build_crl_payload
    def counted(*args, **kwargs):
        setup.calls.append(1)
        return builder(*args, **kwargs)
    monkeypatch.setattr(restricted_admin, 'build_crl_payload', counted)
    setup.engine = crl.Operation(config, permit)
    def transport(raw):
        setup.requests.append(raw)
        before = profile.read_bytes()
        try:
            result = gateway(profile, setup.remote_directory, raw, int(service.access.clock()))
        except Exception:
            if before != profile.read_bytes():
                return crl.TransportResult('UNKNOWN')
            current = json.loads(before)
            incoming = json.loads(raw)['revocations']
            try:
                incoming_number = x509.load_pem_x509_crl(incoming.encode()).extensions.get_extension_for_class(x509.CRLNumber).value.crl_number
                old_number = x509.load_pem_x509_crl(current['revocations'].encode()).extensions.get_extension_for_class(x509.CRLNumber).value.crl_number
                conflict = incoming_number == old_number and incoming != current['revocations']
            except ValueError:
                conflict = False
            return crl.TransportResult('REJECTED', rejection='CRL_PAYLOAD_CONFLICT' if conflict else 'REMOTE_REJECTED')
        observed = readback(setup)
        assert result == observed.directory_bytes
        return crl.TransportResult('ACCEPTED', observed)
    setup.transport = transport
    return setup


def resume(setup):
    return crl.Operation(setup.config, copy.deepcopy(setup.permit))


def test_pure_builder_matches_publisher_and_does_not_write(operation, tmp_path):
    before = snapshot(operation)
    with paid_beta.connection(operation.service.access.path) as database:
        assert database.execute('PRAGMA query_only').fetchone()[0] == 1
        raw, metadata = restricted_admin.build_crl_payload(operation.service, database,
            operation.config.crl.read_bytes(), 1, operation.now, 900, receipt_key=KEY)
    assert snapshot(operation) == before
    target = tmp_path / 'published.pem'
    assert restricted_admin.publish_crl(operation.service, target) == metadata['generated_number'] == 2
    assert raw == target.read_bytes()
    assert metadata['next_update'] - metadata['this_update'] == 900
    assert metadata['revoked_serials'] == (operation.certificate.serial_number,)
    assert metadata['safe_serial_tokens'] == (operation.permit['expected_certificate_safe_token'],)


def test_prepare_is_readonly_and_generation_cannot_repeat(operation):
    before = snapshot(operation)
    result = operation.engine.prepare()
    assert result['state'] == 'PREPARED' and result['generation_count'] == 1
    assert snapshot(operation) == before
    assert operation.engine.path.stat().st_mode & 0o777 == 0o700
    for path in operation.engine.path.iterdir():
        assert path.stat().st_mode & 0o777 == 0o600 and path.stat().st_nlink == 1 and not path.is_symlink()
    with pytest.raises(crl.CRLError, match='CRL_GENERATION_ALREADY_COMPLETED'):
        resume(operation).prepare()
    assert len(operation.calls) == 1


def test_success_and_actual_gateway_idempotency(operation):
    before = snapshot(operation)
    operation.engine.prepare()
    result = operation.engine.deliver(operation.transport)
    assert result['state'] == 'REMOTE_ACCEPTED' and result['gateway_minimum_crl'] == 2
    assert snapshot(operation)[:3] == before[:3]
    repeated = operation.transport(operation.requests[0])
    assert repeated.outcome == 'ACCEPTED'
    result = operation.engine.commit()
    assert result['state'] == 'COMMITTED' and result['local_commit'] == 'PASS'
    assert operation.config.crl.read_bytes() == (operation.engine.path / 'payload.pem').read_bytes()
    assert resume(operation).commit()['state'] == 'COMMITTED'
    assert len(operation.calls) == 1
    with paid_beta.connection(operation.service.access.path) as database:
        assert operation.engine.sequence(database) == 2
        assert database.execute('SELECT count(*) FROM paid_beta_events').fetchone()[0] == 3


def test_not_sent_retry_is_exact_bytes_and_no_reallocation(operation):
    operation.engine.prepare()
    first = []
    def not_sent(raw):
        first.append(raw)
        return crl.TransportResult('NOT_SENT', pre_send_proof='PROCESS_NOT_STARTED')
    assert operation.engine.deliver(not_sent)['state'] == 'TRANSPORT_NOT_SENT'
    before = (operation.engine.path / 'payload.pem').read_bytes()
    assert resume(operation).deliver(operation.transport)['state'] == 'REMOTE_ACCEPTED'
    assert first[0] == operation.requests[0] == (operation.engine.path / 'request.json').read_bytes()
    assert crl.digest(first[0]) == crl.digest(operation.requests[0])
    assert before == (operation.engine.path / 'payload.pem').read_bytes()
    assert len(operation.calls) == 1
    assert resume(operation).commit()['generated_crl_number'] == 2


@pytest.mark.parametrize('outcome', ['UNKNOWN', 'REJECTED', 'unproven', 'exception', 'malformed'])
def test_no_retry_without_proven_pre_send_failure(operation, outcome):
    operation.engine.prepare()
    def transport(raw):
        if outcome == 'exception':
            raise TimeoutError('private transport output')
        if outcome == 'malformed':
            return b'partial-response'
        return crl.TransportResult('NOT_SENT' if outcome == 'unproven' else outcome)
    result = operation.engine.deliver(transport)
    assert result['state'] == ('REMOTE_REJECTED' if outcome == 'REJECTED' else 'DELIVERY_UNRESOLVED')
    with pytest.raises(crl.CRLError):
        resume(operation).deliver(operation.transport)
    assert len(operation.calls) == 1 and not operation.requests
    assert (operation.engine.path / 'payload.pem').exists()


def test_third_attempt_is_never_allowed(operation):
    operation.engine.prepare()
    transport = lambda raw: crl.TransportResult('NOT_SENT', pre_send_proof='REMOTE_NOT_STARTED')
    operation.engine.deliver(transport)
    assert resume(operation).deliver(transport)['result'] == 'TRANSPORT_FAILED'
    with pytest.raises(crl.CRLError, match='TRANSPORT_FAILED'):
        resume(operation).deliver(operation.transport)
    assert len(operation.calls) == 1 and operation.engine.status()['delivery_attempts'] == 2


def test_process_failure_during_transport_requires_readback(operation):
    operation.engine.prepare()
    def interrupted(raw):
        operation.transport(raw)
        raise KeyboardInterrupt()
    with pytest.raises(KeyboardInterrupt):
        operation.engine.deliver(interrupted)
    assert resume(operation).status()['state'] == 'DELIVERY_UNRESOLVED'
    assert resume(operation).reconcile(readback(operation))['state'] == 'REMOTE_ACCEPTED'
    assert resume(operation).commit()['state'] == 'COMMITTED'
    assert len(operation.calls) == len(operation.requests) == 1


@pytest.mark.parametrize('point', ['crl_replace', 'directory_replace', 'after_db_commit'])
def test_crash_during_local_commit_recovers_without_delivery(operation, monkeypatch, point):
    operation.engine.prepare()
    operation.engine.deliver(operation.transport)
    original_install = crl.install_file
    original_save = operation.engine.save
    def interrupted_install(temporary, path):
        original_install(temporary, path)
        if path == (operation.config.crl if point == 'crl_replace' else operation.config.directory) and point != 'after_db_commit':
            raise KeyboardInterrupt()
    def interrupted_save(journal):
        if point == 'after_db_commit' and journal['state'] == 'COMMITTED':
            raise KeyboardInterrupt()
        original_save(journal)
    monkeypatch.setattr(crl, 'install_file', interrupted_install)
    monkeypatch.setattr(operation.engine, 'save', interrupted_save)
    with pytest.raises(KeyboardInterrupt):
        operation.engine.commit()
    monkeypatch.setattr(crl, 'install_file', original_install)
    assert resume(operation).commit()['state'] == 'COMMITTED'
    assert len(operation.calls) == len(operation.requests) == 1


@pytest.mark.parametrize('kind', ['old', 'conflict', 'exact'])
def test_unresolved_readback(operation, kind):
    operation.engine.prepare()
    operation.engine.deliver(lambda raw: crl.TransportResult('UNKNOWN'))
    observed = readback(operation)
    if kind == 'exact':
        operation.transport((operation.engine.path / 'request.json').read_bytes())
        observed = readback(operation)
    if kind == 'conflict':
        observed = crl.TrustedReadback(2, '0' * 64, 2, observed.directory_bytes)
        with pytest.raises(crl.CRLError, match='READBACK_MISMATCH'):
            resume(operation).reconcile(observed)
    else:
        result = resume(operation).reconcile(observed)
        assert result['state'] == ('REMOTE_ACCEPTED' if kind == 'exact' else 'DELIVERY_UNRESOLVED')
    assert len(operation.calls) == 1


@pytest.mark.parametrize('change', ['minimum', 'hash', 'number', 'family', 'gateway', 'future', 'seeds', 'oversize', 'duplicate', 'nonfinite'])
def test_remote_validation_never_commits_local(operation, change):
    before = snapshot(operation)
    operation.engine.prepare()
    def transport(raw):
        accepted = operation.transport(raw).readback
        values = json.loads(accepted.directory_bytes)
        raw_directory = accepted.directory_bytes
        if change in ('family', 'gateway'):
            if change == 'family':
                values['family'] = 'c' * 32
            else:
                values['seeds'][0]['gateway'] = 'c' * 32
        if change == 'future':
            values['issued_at'] = '2099-01-01T00:00:00Z'
        if change == 'seeds':
            values['seeds'] = []
        raw_directory = crl.encode(values)
        if change == 'oversize':
            raw_directory = b' ' * 8193
        if change == 'duplicate':
            raw_directory = b'{"version":1,' + raw_directory[1:]
        if change == 'nonfinite':
            raw_directory = raw_directory.replace(b'"version":1', b'"version":NaN')
        return crl.TransportResult('ACCEPTED', crl.TrustedReadback(3 if change == 'number' else 2,
            '0' * 64 if change == 'hash' else accepted.payload_sha256, 1 if change == 'minimum' else 2, raw_directory))
    with pytest.raises(crl.CRLError, match='GATEWAY_VALIDATION_FAILED|DIRECTORY_VALIDATION_FAILED'):
        operation.engine.deliver(transport)
    assert snapshot(operation)[:3] == before[:3]
    assert resume(operation).status()['state'] == 'DELIVERY_UNRESOLVED'
    with pytest.raises(crl.CRLError):
        resume(operation).commit()


@pytest.mark.parametrize('case', ['A', 'B', 'C', 'D', 'E'])
def test_local_recovery_matrix(operation, case):
    operation.engine.prepare()
    operation.engine.deliver(operation.transport)
    journal, payload, _ = operation.engine.load()
    response = (operation.engine.path / 'response.json').read_bytes()
    journal['state'] = 'LOCAL_COMMIT_IN_PROGRESS'
    operation.engine.save(journal)
    if case in ('B', 'D'):
        with operation.service.access.db() as database:
            database.execute('UPDATE restricted_crl_sequence SET sequence=2')
    if case in ('B', 'C'):
        private_file(operation.config.crl, payload)
    if case == 'B':
        private_file(operation.config.directory, response)
    if case == 'E':
        private_file(operation.config.crl, b'unknown payload')
        with pytest.raises(crl.CRLError, match='LOCAL_COMMIT_CONFLICT'):
            resume(operation).commit()
    else:
        assert resume(operation).commit()['state'] == 'COMMITTED'
    assert len(operation.calls) == len(operation.requests) == 1


def test_remote_accepted_local_failure_only_reconciles_local(operation, monkeypatch):
    operation.engine.prepare()
    operation.engine.deliver(operation.transport)
    original = crl.install_file
    def broken(temporary, path):
        if path == operation.config.directory:
            raise OSError('private path and error')
        return original(temporary, path)
    monkeypatch.setattr(crl, 'install_file', broken)
    with pytest.raises(crl.CRLError, match='REMOTE_ACCEPTED_LOCAL_COMMIT_FAILED'):
        operation.engine.commit()
    assert resume(operation).status()['state'] == 'LOCAL_COMMIT_FAILED'
    monkeypatch.setattr(crl, 'install_file', original)
    assert resume(operation).commit()['state'] == 'COMMITTED'
    assert len(operation.calls) == len(operation.requests) == 1


def test_local_drift_does_not_overwrite_or_regenerate(operation):
    operation.engine.prepare()
    operation.engine.deliver(operation.transport)
    with operation.service.access.db() as database:
        database.execute('UPDATE device_support SET version_code=105')
    before = snapshot(operation)
    with pytest.raises(crl.CRLError, match='LOCAL_PRECONDITION_CHANGED'):
        operation.engine.commit()
    assert snapshot(operation) == before and len(operation.calls) == 1


@pytest.mark.parametrize('mutation', ['active', 'expired_cert', 'revoked_device', 'revoked_invite', 'version', 'cohort', 'revision', 'serial_token'])
def test_preconditions_fail_closed(operation, mutation):
    if mutation == 'serial_token':
        operation.permit['expected_certificate_safe_token'] = '0' * 12
        operation.engine = resume(operation)
    else:
        statements = dict(active="UPDATE paid_beta_subscriptions SET state='active'", expired_cert='UPDATE restricted_certificates SET expires=0',
            revoked_device='UPDATE devices SET revoked=1', revoked_invite='UPDATE invites SET revoked=1',
            version='UPDATE paid_beta_subscriptions SET version=2', revision='UPDATE restricted_certificates SET revision=9')
        if mutation == 'cohort':
            from test_paid_beta import activated_device
            other, support = activated_device(operation.service.access)
            with paid_beta.connection(operation.service.access.path, write=True) as database:
                paid_beta.apply_event(database, support, 'payment', 'fixture-other-cohort', 'fixture', now=operation.now,
                    period_start=operation.now, paid_until=operation.now + 100, apk_sha256=paid_beta.APK_SHA256)
        else:
            with operation.service.access.db() as database:
                database.execute(statements[mutation])
    before = snapshot(operation)
    with pytest.raises(crl.CRLError, match='PRECONDITION_FAILED'):
        operation.engine.prepare()
    assert snapshot(operation) == before and not operation.calls


def test_lock_busy(operation):
    with operation.config.sync_lock.open('rb') as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(crl.CRLError, match='LOCK_BUSY'):
            operation.engine.prepare()


@pytest.mark.parametrize('change', ['preexisting', 'symlink', 'mode', 'hardlink', 'traversal'])
def test_private_path_guards(operation, change):
    if change == 'preexisting':
        operation.engine.path.mkdir(mode=0o700)
    elif change == 'symlink':
        operation.engine.path.symlink_to(operation.config.operations, target_is_directory=True)
    elif change == 'mode':
        operation.config.operations.chmod(0o755)
    elif change == 'hardlink':
        os.link(operation.config.crl, operation.config.crl.with_suffix('.linked'))
    else:
        operation.permit['operation_id'] = '../escape'
        with pytest.raises(crl.CRLError, match='INVALID_PERMIT'):
            resume(operation)
        return
    with pytest.raises(crl.CRLError):
        operation.engine.prepare()
    assert not operation.calls


@pytest.mark.parametrize('raw', [b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":Infinity}', b' ' * 20001])
def test_strict_json_and_request_bounds(raw):
    with pytest.raises(crl.CRLError):
        crl.strict(raw, crl.MAX_REQUEST)


def test_receipt_privacy(operation):
    operation.engine.prepare()
    operation.engine.deliver(operation.transport)
    result = operation.engine.commit()
    allowed = set(('schema operation_safe_label result state previous_crl_number generated_crl_number payload_sha256 payload_size '
        'request_sha256 generation_count delivery_attempts this_update next_update expected_revoked_count unrelated_revocation_count '
        'gateway_minimum_crl directory_validation local_commit observed_at').split())
    assert set(result) == allowed
    raw = json.dumps(result)
    for secret in (operation.support, operation.device.reference, KEY.hex(), str(operation.certificate.serial_number),
                   str(operation.config.crl), 'BEGIN', 'test-only', 'stderr'):
        assert secret not in raw
    private = (operation.engine.path / 'journal.json').read_text()
    for secret in (operation.support, operation.device.reference, KEY.hex(), str(operation.certificate.serial_number), 'BEGIN'):
        assert secret not in private


@pytest.mark.parametrize('args', [['generate'], ['deliver'], ['commit'], ['--db', '/tmp/no'], ['--host', 'arbitrary'],
                                 ['--key', '/tmp/no'], ['--command', 'anything'], ['--lifetime', '900']])
def test_no_operational_cli(args, capsys):
    assert crl.main(args) == 2
    output = capsys.readouterr()
    assert json.loads(output.out) == dict(schema=1, result='INVALID_PERMIT') and output.err == ''


def signed_payload(setup, *, number=2, serials=None, issuer=None, signing_key=None, issued=None, expires=None):
    builder = (x509.CertificateRevocationListBuilder().issuer_name(issuer or setup.authority.subject)
        .last_update(utc(setup.now - 5 if issued is None else issued))
        .next_update(utc(setup.now + 895 if expires is None else expires)).add_extension(x509.CRLNumber(number), False))
    for serial in ([setup.certificate.serial_number] if serials is None else serials):
        builder = builder.add_revoked_certificate(x509.RevokedCertificateBuilder().serial_number(serial)
            .revocation_date(utc(setup.now)).build())
    return builder.sign(signing_key or setup.service.signing_key, None).public_bytes(Encoding.PEM)


@pytest.mark.parametrize('change', ['signature', 'issuer', 'number', 'this_update', 'continuity', 'next_update', 'lifetime', 'same_number_conflict'])
def test_actual_gateway_rejects_invalid_crls(operation, change):
    operation.engine.prepare()
    values = {}
    if change == 'signature':
        values['signing_key'] = Ed25519PrivateKey.generate()
    elif change == 'issuer':
        values['issuer'] = x509.Name([x509.NameAttribute(x509.NameOID.COMMON_NAME, 'wrong test issuer')])
    elif change == 'number':
        values['number'] = 0
    elif change == 'this_update':
        values['issued'] = operation.now + 1
    elif change == 'continuity':
        values['issued'] = operation.now - 100
    elif change == 'next_update':
        values['expires'] = operation.now
    elif change == 'lifetime':
        values['expires'] = operation.now + 14401
    else:
        operation.transport((operation.engine.path / 'request.json').read_bytes())
        values['serials'] = [1234567]
    before = operation.profile.read_bytes()
    request = crl.encode(dict(revocations=signed_payload(operation, **values).decode()))
    outcome = operation.transport(request)
    assert outcome.outcome == 'REJECTED' and operation.profile.read_bytes() == before
    result = operation.engine.deliver(lambda raw: outcome)
    assert result['result'] == ('CRL_PAYLOAD_CONFLICT' if change == 'same_number_conflict' else 'REMOTE_REJECTED')
    assert len(operation.calls) == 1


def other_certificate(setup):
    from test_paid_beta import activated_device
    device, _ = activated_device(setup.service.access)
    material = setup.service.fetch(proof(setup.service, device))
    return device, x509.load_pem_x509_certificate(material['certificate'].encode())


@pytest.mark.parametrize('change', ['missing', 'unknown', 'allowed', 'already_revoked'])
def test_expected_new_set_and_unrelated_allow_checks(operation, monkeypatch, change):
    extra = 123456789
    if change == 'allowed':
        _, certificate = other_certificate(operation)
        extra = certificate.serial_number
    if change == 'already_revoked':
        raw = signed_payload(operation, number=1, issued=operation.now - 6)
        private_file(operation.config.crl, raw)
    original = restricted_admin.build_crl_payload
    def changed(*args, **kwargs):
        raw, metadata = original(*args, **kwargs)
        if change != 'already_revoked':
            serials = [] if change == 'missing' else [operation.certificate.serial_number, extra]
            raw = signed_payload(operation, serials=serials)
        return raw, metadata
    monkeypatch.setattr(restricted_admin, 'build_crl_payload', changed)
    before = snapshot(operation)
    reason = 'CRL_EXPECTED_SET_MISMATCH' if change in ('missing', 'already_revoked') else 'CRL_UNEXPECTED_REVOCATION'
    with pytest.raises(crl.CRLError, match=reason):
        operation.engine.prepare()
    assert snapshot(operation) == before and len(operation.calls) == 1
    with pytest.raises(crl.CRLError, match='CRL_GENERATION_ALREADY_COMPLETED'):
        resume(operation).prepare()


def test_unrelated_allowed_excluded_and_proven_denied_included(operation):
    _, allowed = other_certificate(operation)
    denied_device, denied = other_certificate(operation)
    with operation.service.access.db() as database:
        database.execute('UPDATE devices SET revoked=1 WHERE device=?', (denied_device.reference,))
    result = operation.engine.prepare()
    payload = x509.load_pem_x509_crl((operation.engine.path / 'payload.pem').read_bytes())
    assert {item.serial_number for item in payload} == {operation.certificate.serial_number, denied.serial_number}
    assert payload.get_revoked_certificate_by_serial_number(allowed.serial_number) is None
    assert result['unrelated_revocation_count'] == 1


def test_allowed_paid_certificate_not_revoked_by_builder(operation):
    with operation.service.access.db() as database:
        database.execute("UPDATE paid_beta_subscriptions SET state='active'")
    with paid_beta.connection(operation.service.access.path) as database:
        raw, _ = restricted_admin.build_crl_payload(operation.service, database, operation.config.crl.read_bytes(), 1, operation.now, 900)
    assert len(x509.load_pem_x509_crl(raw)) == 0


@pytest.mark.parametrize('change', ['payload', 'request', 'journal', 'response_symlink'])
def test_tamper_or_unsafe_recovery_files_rejected(operation, change):
    operation.engine.prepare()
    if change == 'response_symlink':
        operation.engine.deliver(operation.transport)
        (operation.engine.path / 'response.json').unlink()
        (operation.engine.path / 'response.json').symlink_to(operation.remote_directory)
        action = resume(operation).commit
    else:
        path = operation.engine.path / {'payload': 'payload.pem', 'request': 'request.json', 'journal': 'journal.json'}[change]
        path.write_bytes(path.read_bytes() + b'corrupt')
        action = resume(operation).status
    with pytest.raises(crl.CRLError):
        action()
    assert len(operation.calls) == 1


@pytest.mark.parametrize('field,value', [('alias', 'OTHER'), ('schema', True), ('expected_subscription_version', 2),
    ('expected_event_count', 4), ('expected_effective_state', 'active'), ('safe_ref', 'dev_' + '0' * 12),
    ('expected_certificate_safe_token', 'unsafe'), ('device_token', 'unsafe'), ('not_after', 0)])
def test_permit_contract_is_strict(operation, field, value):
    operation.permit[field] = value
    with pytest.raises(crl.CRLError, match='INVALID_PERMIT'):
        resume(operation)


@pytest.mark.parametrize('delay', [-1, 300])
def test_closed_generation_window(operation, delay):
    operation.service.access.clock = lambda: operation.now + delay
    with pytest.raises(crl.CRLError, match='PRECONDITION_FAILED'):
        operation.engine.prepare()
    assert not operation.calls


def test_builder_failure_cannot_be_retried(operation, monkeypatch):
    calls = []
    def broken(*args, **kwargs):
        calls.append(1)
        raise ValueError('private exception')
    monkeypatch.setattr(restricted_admin, 'build_crl_payload', broken)
    with pytest.raises(crl.CRLError, match='CRL_GENERATION_FAILED'):
        operation.engine.prepare()
    with pytest.raises(crl.CRLError, match='CRL_GENERATION_ALREADY_COMPLETED'):
        resume(operation).prepare()
    assert calls == [1]


def test_expired_crypto_certificate_prevents_generation(operation):
    now = int(operation.certificate.not_valid_after_utc.timestamp())
    operation.service.access.clock = lambda: now
    operation.permit.update(not_before=now, not_after=now + 300)
    with pytest.raises(crl.CRLError, match='PRECONDITION_FAILED'):
        resume(operation).prepare()
    assert not operation.calls


def test_oversized_generated_request_rejected_without_mutation(operation, monkeypatch):
    before = snapshot(operation)
    monkeypatch.setattr(crl, 'MAX_REQUEST', 1)
    with pytest.raises(crl.CRLError, match='CRL_GENERATION_FAILED'):
        operation.engine.prepare()
    assert snapshot(operation) == before and len(operation.calls) == 1


def test_previous_sequence_is_used_as_number_floor(operation):
    with operation.service.access.db() as database:
        database.execute('UPDATE restricted_crl_sequence SET sequence=7')
    result = operation.engine.prepare()
    assert result['previous_crl_number'] == 1 and result['generated_crl_number'] == 8
    with paid_beta.connection(operation.service.access.path) as database:
        assert operation.engine.sequence(database) == 7


def test_early_or_long_permit_window_invalid(operation):
    for duration in (0, 301):
        operation.permit['not_after'] = operation.permit['not_before'] + duration
        with pytest.raises(crl.CRLError, match='INVALID_PERMIT'):
            resume(operation)
