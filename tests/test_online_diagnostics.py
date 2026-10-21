import hashlib
import json
import sqlite3

import pytest

from control.friends import diagnostics
from control.friends.access import Access, Rejected
from control.friends.referrals import RateLimited
from test_support_ids import enroll, proof


@pytest.fixture
def setup(tmp_path):
    clock = [1000]
    access = Access(tmp_path / 'access.db', clock=lambda: clock[0])
    access.initialize()
    device, support = enroll(access)
    return access, device, support, tmp_path / 'diag.sqlite', clock


def report(**changes):
    value = dict(schema=1, report_id='a'*32, platform='android', version_code=98,
                 sampled_at_ms=1000000, consent=True,
                 metrics=dict(protocol_errors=17, state='CONNECTED', session_tag='b'*64))
    value.update(changes)
    return json.dumps(value, separators=(',', ':'))


def submit(setup, raw):
    access, device, _, path, _ = setup
    purpose = 'diagnostics:' + hashlib.sha256(raw.encode()).hexdigest()
    return diagnostics.request(access, path, dict(report=raw, proof=proof(access, device, purpose)))


def test_authenticated_bounded_idempotent_and_private(setup):
    result = submit(setup, report())
    assert result == submit(setup, report())
    assert setup[3].stat().st_mode & 0o777 == 0o600
    assert diagnostics.read(setup[3], setup[2], 1000)['report']['metrics']['protocol_errors'] == 17
    with pytest.raises(RateLimited):
        submit(setup, report(report_id='c'*32))
    setup[4][0] += 60
    submit(setup, report(report_id='c'*32))
    with sqlite3.connect(setup[3]) as database:
        assert database.execute('SELECT count(*) FROM snapshots').fetchone()[0] == 1
    assert diagnostics.read(setup[3], setup[2], 1000+diagnostics.RETENTION+61) is None
    diagnostics.prune(setup[3],1000+diagnostics.RETENTION+61)
    with sqlite3.connect(setup[3]) as database:
        assert database.execute('SELECT count(*) FROM snapshots').fetchone()[0] == 0


@pytest.mark.parametrize('changes', [dict(consent=False), dict(schema=True), dict(version_code=-1),
    dict(metrics={'secret': 'no'}), dict(metrics={'protocol_errors': True}),
    dict(metrics={'session_tag': 'https://host/room'}), dict(metrics={'protocol_errors': 2**53}),
    dict(metrics={'state': 'arbitrary error text'}), dict(metrics={'dns': ['private.example']})])
def test_reject_unknown_or_unsafe_fields(setup, changes):
    with pytest.raises((ValueError, TypeError)):
        submit(setup, report(**changes))
    assert not setup[3].exists()


def test_binding_replay_revocation_and_unregistered(setup):
    access, device, _, path, _ = setup
    raw = report()
    request = dict(report=raw, proof=proof(access, device, 'diagnostics:'+hashlib.sha256(raw.encode()).hexdigest()))
    with pytest.raises(Rejected):
        diagnostics.request(access, path, dict(request, report=report(version_code=99)))
    diagnostics.request(access, path, request)
    with pytest.raises(Rejected):
        diagnostics.request(access, path, request)
    pending = proof(access, device, 'diagnostics:'+hashlib.sha256(raw.encode()).hexdigest())
    with access.db() as database:
        database.execute('UPDATE devices SET revoked=1 WHERE device=?', (device.reference,))
    with pytest.raises(Rejected):
        diagnostics.request(access, path, dict(report=raw, proof=pending))


def test_conflicting_id_duplicate_json_and_size(setup):
    submit(setup, report())
    with pytest.raises(Rejected):
        submit(setup, report(version_code=99))
    for raw in ('{"schema":1,"schema":1}', ' '*4097, '{}'):
        with pytest.raises(ValueError):
            diagnostics.validate(raw)


@pytest.mark.parametrize('platform', ['android', 'linux', 'windows'])
def test_same_contract_all_platforms(setup, platform):
    assert submit(setup, report(platform=platform))['schema'] == 1


def test_variable_request_duration_needs_completion_based_cooldown(setup):
    setup[4][0] = 1014
    submit(setup, report())
    setup[4][0] = 1060
    with pytest.raises(RateLimited):
        submit(setup, report(report_id='c'*32))
    setup[4][0] = 1075
    assert submit(setup, report(report_id='d'*32))['stored_at'] == 1075
