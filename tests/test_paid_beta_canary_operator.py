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
    receipt = package.build(output, 'HEAD', envelope(registry), repository=repository)
    other = tmp_path / 'second.pyz'
    assert package.build(other, 'HEAD', envelope(registry), repository=repository) == receipt
    assert output.read_bytes() == other.read_bytes()
    with zipfile.ZipFile(output) as archive:
        assert set(package.SOURCES) <= set(archive.namelist())
        assert b'dirty_source_must_not_ship' not in archive.read('control/friends/paid_beta.py')
        assert not any(name.endswith(('.db', '.sqlite3', '.env', '.key')) for name in archive.namelist())
    with pytest.raises(FileExistsError):
        package.build(output, 'HEAD', repository=repository)
    response = subprocess.run([sys.executable, str(output), '--db', str(registry[0].path), 'status'],
                              input=json.dumps(dict(hmac_key=KEY.hex())), text=True, capture_output=True, check=True,
                              cwd=tmp_path)
    assert json.loads(response.stdout)['safe_ref'] == envelope(registry)['safe_ref']
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
