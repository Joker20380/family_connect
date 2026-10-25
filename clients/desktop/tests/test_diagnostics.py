import copy
import json
import os
from pathlib import Path
import re

import pytest

from backend import BackendError, DesktopDiagnostics


def service(state='CONNECTED', tag='a' * 64, reason='NONE'):
    return dict(state=state, reason=reason, first_reason=reason, desired_connected=True, attempt=2,
        events=[dict(state=state, reason=reason, attempt=2, elapsed_ms=17)], events_dropped=3,
        readiness=dict(stage='COMMITTED', code='READY', durable=True), native=dict(events_dropped=5,
        startup=dict(schema=1, status='SUCCEEDED', stage='DEDICATED_MUX', cause='NONE', complete=True, attempt=2, started_unix_ms=100),
        native=dict(selected_profile='P1', tun_ready=state == 'CONNECTED', packet=dict(dns=3, tcp=2,
        diagnostic=dict(session_tag=tag, speed_profile='P1', mux_profile='LEGACY64', mux_window=65536,
        reliable_limits=dict(local_send=32, local_receive=32, peer_receive=16, effective_send=16, local_write_completion=True),
        terminal_reason=reason, lifecycle=dict(session_tag=tag, correlation_status='VALID', trace_dropped=7, first_failure=dict(
        session_tag=tag, stage='ICE', state='FAILED', reason='ICE_FAILED', sequence=1, timestamp_ms=123), trace=[dict(
        session_tag=tag, stage='ICE', state='ESTABLISHED', reason='NONE', sequence=2, timestamp_ms=124)]))))))


def test_actual_profile_and_correlator_fields_not_selected_claim():
    collector = DesktopDiagnostics('0.2.11', clock=lambda: 17)
    collector.support('FC-3Y3W-EBZE')
    collector.sample('CONNECTED', 'mesh', 'P1', service())
    bundle = json.loads(collector.export())
    record = bundle['ring']
    assert set(bundle) == {'ring'}
    assert record['device_support_id'] == 'FC-3Y3W-EBZE'
    assert record['selected_profile'] == 'P1'
    assert record['actual_transport'] == 'restricted'
    assert record['restricted_session']['mux_profile'] == 'LEGACY64'
    assert record['restricted_session']['reliable_limits']['effective_send'] == 16
    assert record['restricted_startup']['attempt'] == 2
    assert record['restricted_readiness'] == 'READY'
    assert record['diagnostic_losses']['service_events_dropped'] == 3
    assert record['diagnostic_losses']['native_events_dropped'] == 5
    assert record['restricted_session']['lifecycle']['trace_dropped'] == 7
    assert record['restricted_session']['lifecycle']['first_failure']['reason'] == 'ICE_FAILED'


def test_export_excludes_secrets_unknown_strings_and_nonfinite_counters():
    value = service()
    secret = 'private-key-room-url-proof-message-DO-NOT-EXPORT'
    value['readiness'].update(identity=secret, proof=secret, code=secret)
    diagnostic = value['native']['native']['packet']['diagnostic']
    diagnostic.update(room_url=secret, token=secret, sent_bytes=float('nan'), received_bytes=True)
    diagnostic['lifecycle']['trace'].append(dict(stage=secret, private_key=secret, sequence=-1))
    collector = DesktopDiagnostics('0.2.11')
    collector.sample('CONNECTED', 'mesh', service=value)
    raw = collector.export()
    assert secret.encode() not in raw
    assert b'room_url' not in raw and b'private_key' not in raw and b'"proof"' not in raw
    record = json.loads(raw)['ring']
    assert record['diagnostic_losses']['projection_dropped'] >= 8
    assert 'sent_bytes' not in record['restricted_session']
    assert 'received_bytes' not in record['restricted_session']


def test_archive_event_bound_first_failure_and_ui_restart(tmp_path):
    storage = tmp_path / 'private' / 'snapshot.json'
    collector = DesktopDiagnostics('0.2.11', storage)
    for number in range(160):
        state = 'FAILED' if number % 2 else 'CONNECTED'
        collector.sample(state, 'mesh', 'P1', service(state, format(number, '064x'), 'NETWORK'))
    collector.persist()
    assert not collector.persistence_failed
    record = json.loads(storage.read_bytes())
    assert len(record['ring']['events']) == 128
    assert record['ring']['diagnostic_losses']['events_dropped'] == 32
    assert len(record['ring']['restricted_history']) == 4
    assert record['incident']['first_failure'] == 'NETWORK'
    assert storage.stat().st_mode & 0o777 == 0o600
    assert storage.parent.stat().st_mode & 0o777 == 0o700
    resumed = DesktopDiagnostics('0.2.11', storage)
    resumed.sample('DISCONNECTED', 'mesh')
    exported = json.loads(resumed.export())
    assert exported['ring']['state'] == 'DISCONNECTED'
    assert exported['ring']['actual_transport'] == 'none'
    assert exported['incident']['first_failure'] == 'NETWORK'
    assert len(exported['ring']['restricted_history']) == 4
    assert len(exported['ring']['events']) == 128
    assert exported['ring']['diagnostic_losses']['events_dropped'] == 33


def test_awg_export_never_claims_previous_mesh_session():
    collector = DesktopDiagnostics('0.2.11')
    collector.sample('CONNECTED', 'mesh', 'P1', service())
    collector.sample('CONNECTED', 'awg', service=service())
    record = json.loads(collector.export())['ring']
    assert record['actual_transport'] == 'awg'
    assert record['restricted_session'] == {}
    assert record['restricted_history'][0]['session_tag'] == 'a' * 64


def test_normal_refusal_diagnostic_is_bounded_and_survives_poll(tmp_path):
    path=tmp_path/'private'/'snapshot.json'
    collector=DesktopDiagnostics('0.2.11',path)
    refused=dict(category='TRANSPORT_BUSY',phase='IDLE',outcome='PRE_START_REJECTED',cleanup_confirmed=True,generation=2,pending=False)
    assert collector.operation_failure(refused)
    collector.sample('DISCONNECTED','awg');collector.persist()
    record=json.loads(collector.export())['ring']
    assert record['first_failure']=='TRANSPORT_BUSY' and record['normal_operation']==refused
    assert not collector.operation_failure(dict(refused,profile='private'))
    resumed=DesktopDiagnostics('0.2.11',path);resumed.sample('DISCONNECTED','awg')
    assert resumed.current['normal_operation']==refused
    resumed.sample('CONNECTING','awg')
    assert 'normal_operation' not in resumed.current


def test_size_budget_is_valid_json_keeps_first_last_and_reports_omissions():
    record = DesktopDiagnostics('0.2.11').current
    details = [dict(sequence=index, diagnostic='x' * 1800) for index in range(192)]
    record['restricted_session'] = dict(lifecycle=dict(trace=details, first_failure=dict(reason='NETWORK')))
    record['restricted_history'] = [copy.deepcopy(record['restricted_session']) for _ in range(4)]
    bounded = DesktopDiagnostics.bounded(record)
    assert len(DesktopDiagnostics._encode(bounded)) <= DesktopDiagnostics.RECORD_LIMIT
    assert bounded['record_budget']['omitted_detail_items']
    for session in [*bounded['restricted_history'], bounded['restricted_session']]:
        assert session['lifecycle']['trace'][0]['sequence'] == 0
        assert session['lifecycle']['trace'][-1]['sequence'] == 191
        assert session['lifecycle']['first_failure']['reason'] == 'NETWORK'
    assert len(record['restricted_history'][0]['lifecycle']['trace']) == 192


def test_unrepresentable_export_fails_not_substring_truncates():
    record = DesktopDiagnostics('0.2.11').current
    record['restricted_session'] = dict(first_failure='x' * DesktopDiagnostics.RECORD_LIMIT)
    with pytest.raises(BackendError, match='safe export limit'):
        DesktopDiagnostics.bounded(record)


def test_export_atomic_failure_keeps_previous_file_and_symlink_target(tmp_path, monkeypatch):
    target = tmp_path / 'export.json'
    original = b'{"previous":true}'
    target.write_bytes(original)
    link = tmp_path / 'link.json'
    link.symlink_to(target)
    data = DesktopDiagnostics('0.2.11').export()
    with pytest.raises(BackendError):
        DesktopDiagnostics.save_export(link, data)
    def denied(*args):
        raise OSError('test failure')
    monkeypatch.setattr(os, 'replace', denied)
    with pytest.raises(OSError):
        DesktopDiagnostics.save_export(target, data)
    assert target.read_bytes() == original
    assert not list(tmp_path.glob('.fc-diagnostics-*'))


def test_saved_snapshot_injection_never_reexports_private_fields(tmp_path):
    storage = tmp_path / 'private' / 'snapshot.json'
    collector = DesktopDiagnostics('0.2.11', storage)
    collector.persist()
    storage.write_text(json.dumps(dict(ring={}, incident=dict(first_failure='KEYSECRET',
        restricted_session=dict(private_key='KEYSECRET', terminal_reason='KEYSECRET')))))
    resumed = DesktopDiagnostics('0.2.11', storage)
    assert b'KEYSECRET' not in resumed.export()


def test_missing_identity_does_not_manufacture_support_id():
    collector = DesktopDiagnostics('0.2.11')
    collector.support('FC-ANDROID-COPIED')
    assert json.loads(collector.export())['ring']['device_support_id'] is None


def test_same_generation_recovery_does_not_replace_first_failure(tmp_path):
    directory = tmp_path/'private';directory.mkdir(mode=0o700)
    storage = directory/'diagnostics.json'
    first = dict(category='CHANNEL_LOST', phase='APPLYING', outcome='OUTCOME_UNKNOWN',
                 cleanup_confirmed=False, generation=1, pending=True)
    collector = DesktopDiagnostics('internal', storage=storage)
    assert collector.operation_failure(first)
    collector.sample('FAILED', 'awg');collector.persist()
    restarted = DesktopDiagnostics('internal', storage=storage)
    assert not restarted.operation_failure(dict(first, category='HELPER_FAILED'))
    restarted.sample('FAILED', 'awg')
    assert restarted.current['normal_operation'] == first
    assert restarted.current['first_failure'] == 'CHANNEL_LOST'
    assert restarted.operation_failure(dict(first, generation=3, category='HELPER_TIMEOUT'))


def test_accepted_startup_and_trace_enumerations_remain_exportable():
    directory = Path(__file__).resolve().parents[3] / 'state-client-build/owner-diagnostic106-20261022/android-source/clients/android/app/src/main/java/com/familyconnect/app'
    if not directory.exists():
        pytest.skip('exact reference capsule is local evidence')
    for name in ('RestrictedTrace.java', 'RestrictedStartup.java'):
        source = (directory / name).read_text()
        for choices in re.findall(r'"([A-Za-z_0-9]+(?:\|[A-Za-z_0-9]+)+)"', source):
            assert set(choices.split('|')) <= DesktopDiagnostics.CODES


def test_native_failure_and_health_preserved_not_replaced_by_selected_state():
    collector = DesktopDiagnostics('0.2.11')
    value = service('FAILED', reason='TLS_TRUST_REJECTED')
    value['native']['health'] = dict(state='unavailable', probes=3, probe_ok=False, traffic_progress=False,
        progress_overrides=0, failures=3, last_elapsed_ms=30000, probe_duration_ms=3000)
    value['native']['events'] = ['bootstrap_cache_loaded', 'startup_failed', 'private-secret']
    collector.sample('FAILED', 'mesh', service=value)
    record = json.loads(collector.export())['ring']
    assert record['first_failure'] == 'TLS_TRUST_REJECTED'
    assert record['health'] == value['native']['health']
    assert record['native_events'] == ['bootstrap_cache_loaded', 'startup_failed']
    collector.sample('FAILED', 'mesh', service={})
    assert json.loads(collector.export())['ring']['first_failure'] == 'TLS_TRUST_REJECTED'
