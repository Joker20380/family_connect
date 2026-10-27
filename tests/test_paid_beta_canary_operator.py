import copy
import hashlib
import io
import json
import subprocess
import sys
import zipfile

import pytest

from control.friends import paid_beta, paid_beta_canary as canary
from scripts import package_paid_canary_operator as package
from test_paid_beta import NOW, activated_device, event, registry, snapshot

KEY = b'\x17' * 32


def envelope(registry, version=0, now=NOW, duration=60):
    access, device, _ = registry
    token = canary.token_for(KEY, device.reference)
    return dict(schema=1, alias=canary.ALIAS, device_token=token, safe_ref='dev_' + token[:12],
                permit=dict(action='expire' if version == 2 else 'activate', event_id='canary_' + f'{version:032x}',
                            expected_version=version, not_before=now, not_after=now + 30,
                            period_start=None if version == 2 else now,
                            paid_until=None if version == 2 else now + duration))


def test_transient_lookup_is_readonly_and_sanitized(registry):
    access, device, selector = registry
    before = snapshot(access)
    receipt = canary.lookup(access.path, selector, KEY, NOW)
    serialized = json.dumps(receipt)
    assert selector not in serialized and device.reference not in serialized and KEY.hex() not in serialized
    assert receipt['binding'] == envelope(registry) | {'permit': None}
    assert receipt['observation']['paid_allow'] is None
    assert snapshot(access) == before


def test_four_bounded_stages_delegate_and_recover_without_identity_change(registry):
    access, device, selector = registry
    before = snapshot(access)
    first = envelope(registry)
    activated = canary.apply(access.path, KEY, first, NOW)
    assert activated['paid_allow'] and activated['event_type'] == 'payment'
    assert activated['amount_minor'] == 0 and activated['purpose'] == 'internal_canary'
    expired = canary.observe(access.path, KEY, first, NOW + 60)
    assert expired['effective_state'] == 'expired' and expired['paid_allow'] is False
    second = envelope(registry, 1, NOW + 61)
    canary.apply(access.path, KEY, second, NOW + 61)
    with paid_beta.connection(access.path, write=True) as database:
        database.execute('CREATE TABLE restricted_certificates(device TEXT,expires INTEGER)')
        database.execute('INSERT INTO restricted_certificates VALUES (?,?)', (device.reference, NOW + 121))
    third = envelope(registry, 2, NOW + 62)
    assert canary.apply(access.path, KEY, third, NOW + 62)['effective_state'] == 'expired'
    fourth = envelope(registry, 3, NOW + 122, 30 * 86400)
    recovered = canary.apply(access.path, KEY, fourth, NOW + 122)
    assert recovered['paid_allow'] and recovered['version'] == recovered['event_count'] == 4
    for old in (first, second, third, fourth):
        duplicate = canary.apply(access.path, KEY, old, NOW + 123)
        assert duplicate['duplicate'] and duplicate['paid_allow'] and duplicate['version'] == 4
    for table in ('devices', 'invites', 'device_support'):
        assert snapshot(access)[table] == before[table]
    raw = json.dumps(recovered)
    assert selector not in raw and device.reference not in raw and KEY.hex() not in raw


@pytest.mark.parametrize('version,reason', [(1, 'STALE'), (2, 'STALE'), (3, 'STALE')])
def test_cannot_skip_stages(registry, version, reason):
    with pytest.raises(paid_beta.PaidBetaError, match=reason):
        canary.apply(registry[0].path, KEY, envelope(registry, version), NOW)
    assert snapshot(registry[0])['paid_beta_events'] == []


def test_stale_window_natural_expiry_and_certificate_recovery_guards(registry):
    access, device, _ = registry
    first = envelope(registry)
    with pytest.raises(paid_beta.PaidBetaError, match='WINDOW'):
        canary.apply(access.path, KEY, first, NOW + 30)
    canary.apply(access.path, KEY, first, NOW)
    with pytest.raises(paid_beta.PaidBetaError, match='EXPIRY_NOT'):
        canary.apply(access.path, KEY, envelope(registry, 1, NOW + 1), NOW + 1)
    canary.apply(access.path, KEY, envelope(registry, 1, NOW + 60), NOW + 60)
    third = envelope(registry, 2, NOW + 61)
    with pytest.raises(paid_beta.PaidBetaError, match='CERTIFICATE_INVENTORY'):
        canary.apply(access.path, KEY, third, NOW + 61)
    with paid_beta.connection(access.path, write=True) as database:
        database.execute('CREATE TABLE restricted_certificates(device TEXT,expires INTEGER)')
    with pytest.raises(paid_beta.PaidBetaError, match='EXPIRE_REQUIRES_VALID'):
        canary.apply(access.path, KEY, third, NOW + 61)
    with paid_beta.connection(access.path, write=True) as database:
        database.execute('INSERT INTO restricted_certificates VALUES (?,?)', (device.reference, NOW + 120))
    canary.apply(access.path, KEY, third, NOW + 61)
    recovery = envelope(registry, 3, NOW + 62)
    with pytest.raises(paid_beta.PaidBetaError, match='CERTIFICATES_STILL'):
        canary.apply(access.path, KEY, recovery, NOW + 62)


@pytest.mark.parametrize('change', [dict(action='revoke'), dict(action='grace'), dict(expected_version=4),
                                  dict(not_after=NOW+901), dict(paid_until=NOW+32*86400),
                                  dict(event_id='arbitrary-reference'), dict(expected_version=True)])
def test_permit_rejects_unbounded_or_forbidden_commands(registry, change):
    request = envelope(registry)
    request['permit'].update(change)
    with pytest.raises(paid_beta.PaidBetaError):
        canary.apply(registry[0].path, KEY, request, NOW)
    assert not snapshot(registry[0])['paid_beta_events']


def test_wrong_key_binding_and_other_member_fail_without_writes(registry):
    access, _, _ = registry
    request = envelope(registry)
    for key in (b'\x18' * 32, b'short'):
        with pytest.raises(paid_beta.PaidBetaError):
            canary.apply(access.path, key, request, NOW)
    other, selector = activated_device(access)
    event((access, other, selector))
    before = snapshot(access)
    with pytest.raises(paid_beta.PaidBetaError, match='OTHER_COHORT'):
        canary.apply(access.path, KEY, request, NOW)
    assert snapshot(access) == before


def test_backend_conflict_and_unrelated_trigger_rollback(registry):
    access, _, _ = registry
    request = envelope(registry)
    with paid_beta.connection(access.path, write=True) as database:
        database.execute('CREATE TRIGGER unrelated AFTER INSERT ON paid_beta_events BEGIN UPDATE devices SET revoked=1; END')
    before = snapshot(access)
    with pytest.raises(paid_beta.PaidBetaError, match='NON_PAID_STATE_CHANGED'):
        canary.apply(access.path, KEY, request, NOW)
    assert snapshot(access) == before
    with paid_beta.connection(access.path, write=True) as database:
        database.execute('DROP TRIGGER unrelated')
    canary.apply(access.path, KEY, request, NOW)
    request['permit']['paid_until'] += 1
    with pytest.raises(paid_beta.PaidBetaError, match='EVENT_ID_CONFLICT'):
        canary.apply(access.path, KEY, request, NOW)


@pytest.mark.parametrize('raw', [b'{"x":1,"x":2}', b'{"x":NaN}', b'{}'*3000, b'\xff', b'[]'])
def test_cli_rejects_bad_input_without_echo(registry, monkeypatch, capsys, raw):
    monkeypatch.setattr(sys, 'stdin', io.TextIOWrapper(io.BytesIO(raw)))
    assert canary.main(['--db', str(registry[0].path), 'lookup']) == 2
    output = capsys.readouterr()
    assert output.err == '' and json.loads(output.out)['result'] == 'REJECTED'


def test_cli_bound_writes_have_no_selector_or_clock_argument(registry, monkeypatch, capsys):
    access, device, selector = registry
    monkeypatch.setattr(sys, 'stdin', io.TextIOWrapper(io.BytesIO(json.dumps(dict(hmac_key=KEY.hex())).encode())))
    assert canary.main(['--db', str(access.path), 'apply']) == 2
    assert json.loads(capsys.readouterr().out)['reason'] == 'BOUND_PACKAGE_REQUIRED'
    for option in ('--support-id', '--now', '--reference', '--event-id'):
        assert canary.main(['--db', str(access.path), 'status', option, 'forbidden'], envelope=envelope(registry)) == 2
        assert json.loads(capsys.readouterr().out)['reason'] == 'INVALID_ARGUMENTS'
    monkeypatch.setattr(canary.time, 'time', lambda: NOW)
    assert canary.main(['--db', str(access.path), 'apply'], envelope=envelope(registry)) == 0
    raw = capsys.readouterr().out
    assert selector not in raw and device.reference not in raw and KEY.hex() not in raw


def test_package_uses_committed_inventory_and_is_deterministic(tmp_path, registry):
    repository = tmp_path / 'source'
    repository.mkdir()
    subprocess.run(['git', 'init', '-q', str(repository)], check=True)
    for name in package.SOURCES:
        path = repository / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((package.ROOT / name).read_bytes())
    subprocess.run(['git', 'add', '.'], cwd=repository, check=True)
    subprocess.run(['git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture'], cwd=repository, check=True)
    (repository / 'control/friends/paid_beta.py').write_text('dirty_source_must_not_ship = True\n')
    output = tmp_path / 'first.pyz'
    receipt = package.build(output, 'HEAD', repository=repository)
    other = tmp_path / 'second.pyz'
    assert package.build(other, 'HEAD', repository=repository) == receipt
    assert output.read_bytes() == other.read_bytes()
    with zipfile.ZipFile(output) as archive:
        assert set(package.SOURCES) <= set(archive.namelist())
        assert b'dirty_source_must_not_ship' not in archive.read('control/friends/paid_beta.py')
        assert not any(name.endswith(('.db', '.sqlite3', '.env', '.key')) for name in archive.namelist())
        assert json.loads(archive.read('canary-envelope.json')) is None
        assert receipt['binding'] == 'lookup_only'
    with pytest.raises(FileExistsError):
        package.build(output, 'HEAD', repository=repository)
    response = subprocess.run([sys.executable, str(output), '--help'], text=True, capture_output=True, check=True,
                              cwd=tmp_path)
    assert 'lookup' in response.stdout
    assert response.stderr == ''


@pytest.mark.parametrize('change', ['extra_field', 'safe_ref', 'alias', 'schema', 'permit_field'])
def test_binding_and_permit_are_strict(registry, change):
    request = envelope(registry)
    if change == 'permit_field':
        request['permit']['reference'] = 'not-permitted'
    elif change == 'safe_ref':
        request['safe_ref'] = 'dev_' + 'f' * 12
    else:
        request[change] = 'invalid'
    with pytest.raises(paid_beta.PaidBetaError):
        canary.apply(registry[0].path, KEY, request, NOW)
    assert not snapshot(registry[0])['paid_beta_events']


@pytest.mark.parametrize('change', ['version', 'revoked', 'invite_revoked'])
def test_backend_eligibility_is_not_bypassed(registry, change):
    access, device, selector = registry
    with paid_beta.connection(access.path, write=True) as database:
        if change == 'version':
            database.execute('UPDATE device_support SET version_code=84')
        else:
            table = 'devices' if change == 'revoked' else 'invites'
            database.execute('UPDATE ' + table + ' SET revoked=1')
    before = snapshot(access)
    for operation in (lambda: canary.lookup(access.path, selector, KEY, NOW),
                      lambda: canary.apply(access.path, KEY, envelope(registry), NOW)):
        with pytest.raises(paid_beta.PaidBetaError):
            operation()
    assert snapshot(access) == before


def recovery_envelope(registry, version, now):
    request = envelope(registry, version, now, canary.RECOVERY_SECONDS)
    request['permit'].update(action='recover', event_id='canary_' + 'e' * 32,
                            period_start=now, paid_until=now + canary.RECOVERY_SECONDS,
                            not_after=now + 300)
    return request


def recovery_phase(registry, version):
    access, device, _ = registry
    canary.apply(access.path, KEY, envelope(registry), NOW)
    if version == 2:
        canary.apply(access.path, KEY, envelope(registry, 1, NOW + 60), NOW + 60)
    now = NOW + version * 60
    with paid_beta.connection(access.path, write=True) as database:
        database.execute('CREATE TABLE restricted_certificates(device TEXT,expires INTEGER,serial TEXT)')
        database.execute('INSERT INTO restricted_certificates VALUES (?,?,?)', (device.reference, now, '123'))
        database.execute('CREATE TABLE restricted_crl_sequence(singleton INTEGER PRIMARY KEY, sequence INTEGER)')
        database.execute('INSERT INTO restricted_crl_sequence VALUES (1,7)')
    return now, recovery_envelope(registry, version, now)


@pytest.mark.parametrize('version,classification', [
    (1, 'NATURAL_PHASE_ABORTED_OWNER_RECOVERED'), (2, 'CRL_PHASE_ABORTED_OWNER_RECOVERED')])
@pytest.mark.parametrize('delay', [0, 1, 150, 299])
def test_recovery_delegates_exact_period_preserves_state_and_sanitizes_output(registry, monkeypatch, version, classification, delay):
    access, device, selector = registry
    now, request = recovery_phase(registry, version)
    before = snapshot(access)
    with paid_beta.connection(access.path) as database:
        non_paid = canary.preserved_tables(database)
    original = paid_beta.apply_event
    captured = []
    def traced(*args, **kwargs):
        receipt = original(*args, **kwargs)
        captured.append(copy.deepcopy(receipt))
        return receipt
    monkeypatch.setattr(paid_beta, 'apply_event', traced)
    original_request = copy.deepcopy(request)
    receipt = canary.apply(access.path, KEY, request, now + delay)
    assert request == original_request
    assert receipt['classification'] == classification and receipt['branch'] == 'emergency_recovery'
    assert receipt['effective_state'] == 'active' and receipt['paid_allow'] is True
    assert receipt['version'] == receipt['event_count'] == version + 1
    assert receipt['paid_until'] == receipt['entitlement_until'] == now + 2592000
    assert receipt['purpose'] == 'internal_canary' and receipt['amount_minor'] == 0
    reference = 'internal-canary-recovery:' + request['permit']['event_id']
    with paid_beta.connection(access.path) as database:
        assert canary.preserved_tables(database) == non_paid
        record = dict(database.execute('SELECT * FROM paid_beta_events WHERE event_id=?', (receipt['event_id'],)).fetchone())
        assert record == captured[0]['event']
        assert record['event_type'] == 'payment' and record['period_start'] == now
        assert record['paid_until'] == now + 2592000
        assert record['applied_at'] == now + delay
        assert record['reference_hash'] == hashlib.sha256(reference.encode()).hexdigest()
    after = snapshot(access)
    for table in ('devices', 'invites', 'device_support'):
        assert after[table] == before[table]
    text = json.dumps(receipt)
    assert all(secret not in text for secret in (selector, device.reference, KEY.hex(), reference))
    assert not set(receipt) & {'device', 'support_id', 'hmac_key', 'reference', 'invite', 'certificate', 'revenue'}


@pytest.mark.parametrize('version', [0, 3])
def test_recovery_version_zero_and_three_forbidden(registry, version):
    with pytest.raises(paid_beta.PaidBetaError, match='INVALID_CANARY_STAGE'):
        canary.apply(registry[0].path, KEY, recovery_envelope(registry, version, NOW), NOW)
    assert not snapshot(registry[0])['paid_beta_events']


@pytest.mark.parametrize('version', [1, 2])
def test_recovery_active_entitlement_and_valid_certificate_rejected(registry, version):
    access, device, _ = registry
    now, request = recovery_phase(registry, version)
    active_request = recovery_envelope(registry, version, now - 1)
    with pytest.raises(paid_beta.PaidBetaError, match='EXPIRY_NOT_OBSERVED'):
        canary.apply(access.path, KEY, active_request, now - 1)
    with paid_beta.connection(access.path, write=True) as database:
        database.execute('INSERT INTO restricted_certificates VALUES (?,?,?)', (device.reference, now + 1, '124'))
    before = snapshot(access)
    with pytest.raises(paid_beta.PaidBetaError, match='CERTIFICATES_STILL_VALID'):
        canary.apply(access.path, KEY, request, now)
    assert snapshot(access) == before


@pytest.mark.parametrize('delta', [-1, 1, -2592000, 86400])
def test_recovery_rejects_every_non_30_day_period(registry, delta):
    now, request = recovery_phase(registry, 1)
    request['permit']['paid_until'] += delta
    with pytest.raises(paid_beta.PaidBetaError, match='INVALID_RECOVERY_PERIOD'):
        canary.apply(registry[0].path, KEY, request, now)
    assert len(snapshot(registry[0])['paid_beta_events']) == 1


@pytest.mark.parametrize('change,reason', [
    ('long_window', 'INVALID_EXECUTION_WINDOW'), ('empty_window', 'INVALID_EXECUTION_WINDOW'),
    ('before_window', 'RECOVERY_DISPATCH_WINDOW_CLOSED'),
    ('end_window', 'RECOVERY_DISPATCH_WINDOW_CLOSED'),
    ('late_dispatch', 'RECOVERY_DISPATCH_WINDOW_CLOSED'),
    ('short_window_end', 'RECOVERY_DISPATCH_WINDOW_CLOSED'),
    ('future_start', 'RECOVERY_DISPATCH_WINDOW_CLOSED'),
    ('start_at_window_end', 'RECOVERY_DISPATCH_WINDOW_CLOSED'),
    ('outside_start', 'INVALID_RECOVERY_PERIOD'), ('before_start', 'INVALID_RECOVERY_PERIOD')])
def test_recovery_requires_bounded_dispatch_and_execution_window(registry, change, reason):
    now, request = recovery_phase(registry, 1)
    before = snapshot(registry[0])
    permit = request['permit']
    if change == 'long_window':
        permit['not_after'] = now + 301
    elif change == 'empty_window':
        permit['not_after'] = now
    elif change == 'before_window':
        now -= 1
    elif change == 'end_window':
        now += 300
    elif change == 'late_dispatch':
        now += 301
    elif change == 'short_window_end':
        permit['not_after'] = now + 2
        now += 2
    else:
        shift = {'future_start': 1, 'start_at_window_end': 300, 'outside_start': 301, 'before_start': -1}[change]
        permit['period_start'] += shift
        permit['paid_until'] += shift
    with pytest.raises(paid_beta.PaidBetaError, match=reason):
        canary.apply(registry[0].path, KEY, request, now)
    assert snapshot(registry[0]) == before


@pytest.mark.parametrize('change', ['token', 'safe_ref', 'alias', 'key', 'other_device'])
def test_recovery_remains_bound_to_one_device(registry, change):
    access, _, _ = registry
    now, request = recovery_phase(registry, 1)
    key = KEY
    if change == 'token':
        request['device_token'] = '0' * 64
        request['safe_ref'] = 'dev_' + '0' * 12
    elif change == 'key':
        key = b'\x18' * 32
    elif change == 'other_device':
        other, _ = activated_device(access)
        request['device_token'] = canary.token_for(KEY, other.reference)
        request['safe_ref'] = 'dev_' + request['device_token'][:12]
    else:
        request[change] = 'invalid'
    before = snapshot(access)
    with pytest.raises(paid_beta.PaidBetaError):
        canary.apply(access.path, key, request, now)
    assert snapshot(access) == before


@pytest.mark.parametrize('version', [1, 2])
def test_terminal_recovery_idempotency_conflict_and_no_normal_continuation(registry, version):
    access, _, _ = registry
    now, request = recovery_phase(registry, version)
    first = canary.apply(access.path, KEY, request, now)
    after = snapshot(access)
    for later in (now + 1, now + 301, now + 2592001):
        replay = canary.apply(access.path, KEY, request, later)
        assert replay['duplicate'] is True and replay['applied_at'] == now
        assert replay['classification'] == first['classification']
        assert replay['event_count'] == version + 1
        assert snapshot(access) == after
    changed = copy.deepcopy(request)
    changed['permit']['period_start'] += 1
    changed['permit']['paid_until'] += 1
    with pytest.raises(paid_beta.PaidBetaError, match='EVENT_ID_CONFLICT'):
        canary.apply(access.path, KEY, changed, now + 1)
    for delta in (-1, 1, -2592000):
        changed = copy.deepcopy(request)
        changed['permit']['paid_until'] += delta
        with pytest.raises(paid_beta.PaidBetaError, match='EVENT_ID_CONFLICT'):
            canary.apply(access.path, KEY, changed, now + 1)
    for next_request in [envelope(registry, stage, now) for stage in range(4)] + [copy.deepcopy(request)]:
        if next_request['permit']['action'] == 'recover':
            next_request['permit']['event_id'] = 'canary_' + 'f' * 32
        with pytest.raises(paid_beta.PaidBetaError, match='RECOVERY_TERMINAL'):
            canary.apply(access.path, KEY, next_request, now)
    assert snapshot(access) == after
    assert canary.apply(access.path, KEY, request, now + 1)['duplicate']
    second_recovery = recovery_envelope(registry, version + 1, now)
    second_recovery['permit']['event_id'] = 'canary_' + 'd' * 32
    with pytest.raises(paid_beta.PaidBetaError, match='RECOVERY_TERMINAL'):
        canary.apply(access.path, KEY, second_recovery, now)


@pytest.mark.parametrize('action', ['revoke', 'grace'])
def test_recovery_does_not_enable_forbidden_actions(registry, action):
    now, request = recovery_phase(registry, 1)
    request['permit']['action'] = action
    with pytest.raises(paid_beta.PaidBetaError, match='INVALID_CANARY_STAGE'):
        canary.apply(registry[0].path, KEY, request, now)


@pytest.mark.parametrize('change,reason', [
    ('revoked', 'ACTIVE_IDENTITY_REQUIRED'), ('invite_revoked', 'ACTIVE_IDENTITY_REQUIRED'),
    ('version', 'ANDROID106_REQUIRED'), ('terminal_revoke', 'REVOCATION_TERMINAL'),
    ('explicit_expire', 'NATURAL_EXPIRY_REQUIRED'), ('missing_certificates', 'CERTIFICATE_INVENTORY_REQUIRED'),
    ('other_member', 'OTHER_COHORT_MEMBER')])
def test_recovery_eligibility_and_history_fail_closed(registry, change, reason):
    access, _, selector = registry
    now, request = recovery_phase(registry, 1)
    with paid_beta.connection(access.path, write=True) as database:
        if change == 'version':
            database.execute('UPDATE device_support SET version_code=84')
        elif change in ('revoked', 'invite_revoked'):
            table = 'devices' if change == 'revoked' else 'invites'
            database.execute('UPDATE ' + table + ' SET revoked=1')
        elif change in ('terminal_revoke', 'explicit_expire'):
            paid_beta.apply_event(database, selector, 'revoke' if change == 'terminal_revoke' else 'expire',
                                 'fixture-outside-canary', 'fixture', now=now)
            request['permit']['expected_version'] = 2
        elif change == 'missing_certificates':
            database.execute('DROP TABLE restricted_certificates')
    if change == 'other_member':
        other, support = activated_device(access)
        event((access, other, support))
    before = snapshot(access)
    with pytest.raises(paid_beta.PaidBetaError, match=reason):
        canary.apply(access.path, KEY, request, now)
    assert snapshot(access) == before


def test_recovery_rolls_back_nonpaid_side_effect_and_does_not_rewrite_crl(registry):
    access, _, _ = registry
    now, request = recovery_phase(registry, 1)
    with paid_beta.connection(access.path, write=True) as database:
        database.execute('CREATE TRIGGER bad_recovery AFTER INSERT ON paid_beta_events '
                         'BEGIN UPDATE restricted_crl_sequence SET sequence=99; END')
    before = snapshot(access)
    with pytest.raises(paid_beta.PaidBetaError, match='NON_PAID_STATE_CHANGED'):
        canary.apply(access.path, KEY, request, now)
    assert snapshot(access) == before
    with paid_beta.connection(access.path) as database:
        assert database.execute('SELECT sequence FROM restricted_crl_sequence').fetchone()[0] == 7


def test_recovery_rejects_real_version_three_after_explicit_expire(registry):
    access, _, _ = registry
    now, _ = recovery_phase(registry, 2)
    expired = canary.apply(access.path, KEY, envelope(registry, 2, now - 1), now - 1)
    assert expired['version'] == expired['event_count'] == 3
    before = snapshot(access)
    with pytest.raises(paid_beta.PaidBetaError, match='INVALID_CANARY_STAGE'):
        canary.apply(access.path, KEY, recovery_envelope(registry, 3, now), now)
    assert snapshot(access) == before


def test_terminal_replay_uses_backend_payload_and_skips_new_certificate_guards(registry):
    access, device, _ = registry
    now, request = recovery_phase(registry, 1)
    initial = canary.apply(access.path, KEY, request, now)
    with paid_beta.connection(access.path, write=True) as database:
        database.execute('INSERT INTO restricted_certificates VALUES (?,?,?)', (device.reference, now + 100, '125'))
    replay = copy.deepcopy(request)
    replay['permit']['expected_version'] = 2
    result = canary.apply(access.path, KEY, replay, now + 1)
    assert result['duplicate'] and result['classification'] == initial['classification']
    assert result['paid_until'] == initial['paid_until'] and result['event_count'] == 2


def test_recovery_serializes_concurrent_replay_to_one_event(registry):
    from concurrent.futures import ThreadPoolExecutor

    now, request = recovery_phase(registry, 1)
    with ThreadPoolExecutor(max_workers=2) as executor:
        receipts = list(executor.map(lambda _: canary.apply(registry[0].path, KEY, request, now), range(2)))
    assert sorted(receipt['duplicate'] for receipt in receipts) == [False, True]
    assert all(receipt['event_count'] == receipt['version'] == 2 for receipt in receipts)


@pytest.mark.parametrize('delay', [0, 1, 299])
def test_recovery_cli_uses_server_clock_without_rebasing_permit(registry, monkeypatch, capsys, delay):
    access, device, selector = registry
    now, request = recovery_phase(registry, 1)
    monkeypatch.setattr(canary.time, 'time', lambda: now + 300)
    def run():
        monkeypatch.setattr(sys, 'stdin', io.TextIOWrapper(io.BytesIO(json.dumps(dict(hmac_key=KEY.hex())).encode())))
        return canary.main(['--db', str(access.path), 'apply'], envelope=request)
    assert run() == 2
    output = capsys.readouterr()
    assert json.loads(output.out)['reason'] == 'RECOVERY_DISPATCH_WINDOW_CLOSED' and output.err == ''
    monkeypatch.setattr(canary.time, 'time', lambda: now + delay)
    assert run() == 0
    output = capsys.readouterr()
    receipt = json.loads(output.out)
    assert receipt['branch'] == 'emergency_recovery' and output.err == ''
    assert receipt['paid_until'] == now + canary.RECOVERY_SECONDS
    assert receipt['applied_at'] == now + delay
    assert all(secret not in output.out for secret in (selector, device.reference, KEY.hex(), 'internal-canary-recovery:'))
