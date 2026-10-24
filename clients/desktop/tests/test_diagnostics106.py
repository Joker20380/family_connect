import copy
import hashlib
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from backend import DesktopDiagnostics, NativeDiagnostics106
from scripts.diagnostic106_vectors import baseline, cases, projected


CONTRACT = json.loads((ROOT/'clients/shared/android106-diagnostics.json').read_text())


@pytest.mark.parametrize('name', list(cases()))
def test_exact_accepted_java_projection_hash(name):
    result = projected(NativeDiagnostics106, cases()[name])
    raw = json.dumps(result, sort_keys=True, separators=(',', ':')).encode()
    assert hashlib.sha256(raw).hexdigest() == CONTRACT['expected_sha256'][name]
    assert b'PRIVATE-DO-NOT-EXPORT' not in raw and b'private-proof' not in raw


def service(value, state='CONNECTED'):
    return dict(state=state, reason='NONE', desired_connected=True, attempt=1,
        readiness=dict(stage='COMMITTED', code='READY', durable=True), native=dict(native=dict(
            selected_profile='P1', tun_ready=state == 'CONNECTED', startup=value['startup'],
            packet=dict(diagnostic=value['session']))))


def test_full_json_keeps_native_delivery_credit_arrays_and_correlators(tmp_path):
    collector = DesktopDiagnostics('0.2.11', tmp_path/'private/record.json', clock=lambda: 2)
    collector.support('FC-3Y3W-EBZE')
    collector.sample('CONNECTED', 'mesh', 'P1', service(baseline()))
    collector.persist()
    record = json.loads(collector.export())['ring']
    session = record['restricted_session']
    assert session['device_support_id'] == record['device_support_id']
    assert session['connection_id'] == record['connection_id']
    assert session['incident_id'] == record['incident_id']
    assert session['reliable_limits']['local_write_completion'] is True
    assert session['lifecycle']['trace'][0]['delivery']['flow']['head_sacked'] is False
    assert session['lifecycle']['boundaries']['events'][0]['stage'] == 'reliable_send'
    assert session['mux_lifecycle']['events'][0]['kind'] == 3
    assert session['mux_lifecycle']['first_unknown']['stream']['send_done'] == list(range(1000, 1009))
    assert session['mux_lifecycle']['first_unknown']['detail'] == 'inflight_data_on_abort'
    resumed = DesktopDiagnostics('0.2.11', collector.storage)
    history = json.loads(resumed.export())['ring']['restricted_history']
    assert history[-1] == session


def test_no_missing_snapshot_or_later_sample_replaces_first_terminal_incident(tmp_path):
    collector = DesktopDiagnostics('0.2.11', tmp_path/'private/record.json', clock=lambda: 2)
    value = baseline()
    value['session'].update(terminal_reason='EOF', sent_bytes=17)
    collector.sample('FAILED', 'mesh', 'P1', service(value, 'FAILED'))
    first = copy.deepcopy(collector.current['restricted_session'])
    value['session'].update(terminal_reason='NONE', sent_bytes=999)
    value['session']['lifecycle']['first_failure']['reason'] = 'REMOTE_CLOSE'
    collector.sample('FAILED', 'mesh', 'P1', service(value, 'FAILED'))
    assert collector.current['restricted_session']['sent_bytes'] == 17
    assert collector.current['restricted_session']['lifecycle']['first_failure'] == first['lifecycle']['first_failure']
    collector.sample('FAILED', 'mesh', 'P1', {})
    assert collector.current['restricted_session'] == first
    collector.persist()
    resumed = DesktopDiagnostics('0.2.11', collector.storage)
    assert json.loads(resumed.export())['incident']['restricted_session'] == first
    collector.sample('CONNECTED', 'awg')
    assert collector.current['restricted_session'] == {} and collector.current['restricted_history'][-1] == first


def test_completed_startup_cannot_be_replaced_by_old_or_partial_callback():
    collector = DesktopDiagnostics('0.2.11')
    value = baseline()
    value['startup'].update(complete=True, status='FAILED', cause='DEADLINE')
    collector.sample('FAILED', 'mesh', service=service(value, 'FAILED'))
    original = copy.deepcopy(collector.current['restricted_startup'])
    for attempt in (1, 2):
        value['startup'].update(attempt=attempt, complete=False, status='RUNNING', cause='NONE')
        collector.sample('FAILED', 'mesh', service=service(value, 'FAILED'))
        assert collector.current['restricted_startup'] == original


def test_new_service_attempt_accepts_restarted_worker_startup_counter():
    collector = DesktopDiagnostics('0.2.11')
    value = baseline()
    value['startup'].update(complete=True, status='SUCCEEDED', cause='NONE')
    collector.sample('CONNECTED', 'mesh', service=service(value))
    value['startup'].update(attempt=1, complete=True, status='CANCELLED', cause='CANCELLED')
    next_attempt = service(value, 'RESTORING')
    next_attempt['attempt'] = 2
    collector.sample('RESTORING', 'mesh', service=next_attempt)
    assert collector.current['restricted_startup']['attempt'] == 1
    assert collector.current['restricted_startup']['cause'] == 'CANCELLED'


@pytest.mark.parametrize('bad', [True, -1, 1.5, float('nan'), float('inf'), 9007199254740992, '17'])
def test_invalid_native_numbers_never_become_counters(bad):
    value = baseline()
    value['session']['sent_bytes'] = bad
    value['session']['mux_lifecycle']['first_unknown']['stream']['send_done'][0] = bad
    projector = NativeDiagnostics106()
    result = projector.session(value['session'])
    assert 'sent_bytes' not in result and result['mux_lifecycle']['first_unknown']['stream']['send_done'][0] == 0
    assert projector.lost > 0
    json.dumps(result, allow_nan=False)


def test_mismatched_correlation_and_invalid_negotiation_are_not_exported():
    value = baseline()
    value['session']['lifecycle']['session_tag'] = 'd'*64
    value['session']['reliable_limits']['effective_send'] = 16
    value['session']['mux_window'] = 65536
    projector = NativeDiagnostics106()
    result = projector.session(value['session'])
    assert not {'lifecycle', 'reliable_limits', 'mux_profile', 'mux_window'} & result.keys()
    assert projector.lost >= 3


def test_projection_drop_counts_survive_saved_record_reprojection():
    value = cases()['trace-capacity']
    projector = NativeDiagnostics106()
    first = projector.session(value['session'])
    assert first['lifecycle']['projection_dropped'] == 8
    assert first['lifecycle']['delivery_projection_dropped'] == 184
    second = NativeDiagnostics106().session(first)
    assert second == first


def test_valid_native_volume_uses_106_record_budget_without_mutating_archive():
    value = cases()['trace-capacity']
    value['session']['mux_lifecycle']['incidents'] = cases()['mux-incident-capacity']['session']['mux_lifecycle']['incidents']
    collector = DesktopDiagnostics('0.2.11', clock=lambda: 2)
    for index in range(5):
        tag = format(index, '064x')
        encoded = json.dumps(value).replace('a'*64, tag)
        collector.sample('CONNECTED', 'mesh', 'P1', service(json.loads(encoded)))
    original = copy.deepcopy(collector.current)
    raw = collector.export()
    record = json.loads(raw)['ring']
    assert len(collector._encode(record)) <= collector.RECORD_LIMIT
    assert collector.current == original
    assert 'record_budget' in record and record['record_budget']['omitted_detail_items']
    for session in [*record['restricted_history'], record['restricted_session']]:
        assert session['lifecycle']['first_failure']['reason'] == 'ICE_FAILED'
        assert session['lifecycle']['trace'][0]['sequence'] == 9
        assert session['lifecycle']['trace'][-1]['sequence'] == 200
