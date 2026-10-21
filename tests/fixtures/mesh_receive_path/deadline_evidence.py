"""Summarize existing receipts and ordinary bounded captures; no new probes."""

import collections
import datetime
import json
from pathlib import Path
import re
import subprocess

from deadline import WORK
from late_arrival import ROOT, SAVED, FIXTURE, digest
from late_arrival_evidence import tests


def normal_trace(path):
    rows = [json.loads(json.loads(line)['MESSAGE'])['trace'] for line in path.read_text().splitlines()]
    sessions = sorted({row['session_tag'] for row in rows})
    assert len(sessions) == 1
    events = {}
    for row in rows:
        for event in row.get('delivery', {}).get('boundaries', {}).get('events', []):
            assert event['index'] not in events or events[event['index']] == event
            events[event['index']] = event
    ordered = sorted(rows, key=lambda row: row['sequence'])
    with_delivery = [row for row in ordered if row.get('delivery')]
    first, last = with_delivery[0], with_delivery[-1]
    flows = [row['delivery']['flow'] for row in with_delivery]
    assembly = {key: last['delivery']['assembly'].get(key, 0)-first['delivery']['assembly'].get(key, 0)
                for key in ('fragments', 'completed', 'expired', 'malformed', 'duplicate', 'conflict', 'capacity', 'crc_failed', 'rtp', 'rtp_gaps', 'vp8_frames')}
    previous, held_since, max_held = None, None, 0
    for row in with_delivery:
        flow = row['delivery']['flow']
        current = flow['send_base'] if flow.get('pending', 0) else None
        if current is None or current != previous:
            held_since = row['timestamp_ms'] if current is not None else None
        if held_since is not None:
            max_held = max(max_held, row['timestamp_ms']-held_since)
        previous = current
    counts = collections.Counter((event.get('stage'), event.get('result')) for event in events.values())
    return dict(session_tags=sessions, snapshots=len(rows), journal_sha256=digest(path),
        capture_local_span_ms=last['timestamp_ms']-first['timestamp_ms'],
        nl_carrier_tx_delta=last['tx']-first['tx'], nl_carrier_rx_delta=last['rx']-first['rx'],
        carrier_bytes_are_not_retry_bytes=True, nl_reverse_receive_assembly_delta=assembly,
        sampled_max_pending=max(flow.get('pending', 0) for flow in flows),
        sampled_max_head_retries=max(flow.get('head_retries', 0) for flow in flows),
        sampled_max_buffered=max(flow.get('buffered', 0) for flow in flows),
        sampled_unchanged_pending_head_max_wall_ms=max_held,
        sampled_head_span_not_exact_window_stall_time=True,
        final_flow=last['delivery']['flow'], observed_boundary_events=len(events),
        missing_indices_within_observed_span=max(events)-min(events)+1-len(events),
        nl_observed_old_rtp=counts['rtp_received', 'old_rtp'],
        nl_observed_frame_discard=counts['vp8_reassembled', 'frame_discard'],
        nl_observed_retry_submissions=sum(event.get('stage') == 'reliable_send' and event.get('attempt_known', False)
                                          and event.get('attempt', 0)>0 for event in events.values()),
        boundary_counts_are_lower_bounds=True,
        observed_lifecycle_errors=sorted({(row.get('stage'), row.get('state'), row.get('reason')) for row in rows if row.get('reason', 'NONE')!='NONE'}))


def phase_result(phase):
    directory = WORK / ('physical-'+phase)
    result = json.loads((directory/'baseline/result.json').read_text())
    preflight = json.loads((directory/'baseline/preflight.json').read_text())
    requests = [json.loads(line) for line in (directory/'baseline/requests.jsonl').read_text().splitlines()]
    control = json.loads((directory/'small/requests.jsonl').read_text().splitlines()[0])
    return dict(phase=phase, version=dict(A1=92, B=93, A2=94)[phase], policy='B125' if phase=='B' else 'A0',
        preflight_utc=preflight['utc'],
        single_mbit_s=requests[0].get('mbit_s'), aggregate_mbit_s=result['parallel'][0]['aggregate_mbit_s'] if result['parallel'] else None,
        completed=sum(row['valid'] for row in requests), attempted=len(requests),
        requested_application_bytes=sum(row['intended_bytes'] for row in requests)+control['intended_bytes'],
        control_ttfb_seconds=float(control['metrics']['time_starttransfer']), control_full_seconds=float(control['metrics']['time_total']),
        control_is_application_transfer_not_rtt=True, topology=preflight['topology'], nl=preflight['nl'],
        topology_stable=result['topology_stable'], matched_tcp_connections=result['matched_requests'],
        actual_mux_stream_ids='NOT_EXPOSED_BY_ORDINARY_TRACE',
        requests=[dict(name=row['name'], valid=row['valid'], intended_bytes=row['intended_bytes'],
                       start_epoch=row['start_epoch'], end_epoch=row['end_epoch'],
                       observed_hash_not_origin_acceptance=row['observed_hash_not_origin_acceptance'],
                       bytes=int(row['metrics'].get('BODY_BYTES', 0)), seconds=float(row['metrics']['time_total']),
                       ttfb_seconds=float(row['metrics']['time_starttransfer']), http=row['metrics'].get('http_code'),
                       curl_exit=row['metrics'].get('CURL_EXIT'), body_sha256=row['metrics'].get('BODY_SHA256')) for row in requests],
        trace=normal_trace(directory/'baseline/capture/NL-raw.jsonl'),
        android_late_recovered_discard_counts='UNAVAILABLE_IN_CAPTURE',
        android_hold_and_data_ack_delay='UNAVAILABLE_IN_CAPTURE', exact_rs_retry_new_bytes='UNAVAILABLE_IN_CAPTURE',
        paired_performance_gate=result['small_gate_pass'],
        meter_authorization='EXPLICIT_FINITE_DEADLINE_ABA; ordinary HTTP/topology/socket gate, not prior PERF gate')


def owner_export(phases):
    path = WORK/'owner94-export.json'
    export = json.loads(path.read_text())
    ring, incident = export['ring'], export['incident']
    session = ring['restricted_session']
    lifecycle = session['lifecycle']
    assert ring['version_code'] == 94
    assert phases[-1]['trace']['session_tags'] == [session['session_tag']]
    trace = lifecycle['trace']
    delivery = [row for row in trace if row.get('delivery')]
    scalar_fields = ('native_state', 'authorization_denied', 'session_tag', 'correlation_status',
                     'terminal_reason', 'reliable_terminal', 'signaling_failure', 'ice_failure',
                     'subscriber_state', 'publisher_state', 'terminal_at_ms', 'observed_at_ms',
                     'retransmissions', 'recovery_timeouts', 'received_frames', 'sent_frames',
                     'protocol_errors', 'dns_responses', 'dns_errors', 'tcp_open_ok', 'tcp_open_errors',
                     'tcp_admission_waits', 'tcp_admission_rejected', 'tcp_admission_timeouts',
                     'tcp_admission_cancelled', 'tcp_admission_waiting', 'lease_admission_rejected',
                     'sent_bytes', 'received_bytes', 'evidence_dropped')
    phases[-1]['android_export'] = 'A2_ONLY_CUMULATIVE; not request-window deltas'
    return dict(sha256=digest(path), version=ring['version_code'], state=ring['state'],
        observed_utc=datetime.datetime.fromtimestamp(session['observed_at_ms']/1000, datetime.timezone.utc).isoformat(),
        session={key:session[key] for key in scalar_fields}, counters=ring['counters'],
        matched_phase='A2', history_count=len(ring['restricted_history']),
        historical_incident_version=incident['version_code'], historical_incident_excluded=True,
        trace_count=len(trace), trace_span_ms=[trace[0]['timestamp_ms'], trace[-1]['timestamp_ms']],
        retained_delivery_snapshots=len(delivery), delivery_span_ms=[delivery[0]['timestamp_ms'], delivery[-1]['timestamp_ms']],
        last_receive_assembly=delivery[-1]['delivery']['assembly'], last_flow=delivery[-1]['delivery']['flow'],
        boundaries_retained=len(lifecycle['boundaries']['events']), boundaries_dropped=lifecycle['boundaries']['dropped'],
        observed_reconnect_events=sum(row['state_from']=='CONNECTED' and row['state_to']!='CONNECTED' for row in ring['events']),
        dns_probe_failure_timestamps=[row['timestamp'] for row in ring['events'] if row['reason_code']=='DNS_PROBE_FAILED'],
        session_errors_not_zero=session['protocol_errors']!=0,
        recovery_timeouts_mean='ReliableStream timeout counter, not automatic reconnect count',
        protocol_error_cause='not identified by retained ordinary export',
        missing_comparison='No A1/B Android export; no paired old_rtp/discard/recovered/hold or DATA/ACK delay delta')


def main():
    replay = json.loads((WORK/'deadline-results.json').read_text())
    old = json.loads((ROOT/'state-client-build/rtp-late-arrival-20261020/sweep.json').read_text())
    for row in replay:
        baseline = next(value for value in old if value['Sequence']==row['Sequence'] and value['BudgetMS']==100)
        delays = [row['Messages'][key]-value for key,value in baseline['Messages'].items() if key in row['Messages']]
        row['vs_A0_following_delay_ms_range'] = [min(delays)/1e6, max(delays)/1e6]
        row['vs_A0_messages_missing'] = len(baseline['Messages'].keys()-row['Messages'].keys())
    phases = [phase_result(phase) for phase in ('A1', 'B', 'A2')]
    android_export = owner_export(phases)
    pins = {}
    for name in ('telemost/rtp.go', 'telemost/rtp_reader.go', 'telemost/signaling.go', 'telemost/rtp_gap_test.go', 'go.mod', 'go.sum', 'telemost/session.go', 'telemost/msg.go', 'telemost/vp8.go'):
        before = SAVED/'normal92/android-source/carrier'/name
        after = WORK/'android-source/carrier'/name
        pins[name] = dict(before=digest(before) if before.exists() else None, after=digest(after))
    proofs = [json.loads((WORK/name).read_text()) for name in ('identity-before.json', 'identity-after.json', 'normal94/identity-before.json', 'normal94/identity-after.json')]
    identity = {key:len({row[key] for row in proofs})==1 for key in ('identity_bindings_sha256', 'support_id_sha256', 'owner_record_count')}
    identity.update(owner_revoked=any(row['owner_revoked'] for row in proofs), readiness93=proofs[1].get('beta93_readiness'), readiness94=proofs[-1].get('beta94_readiness'),
                    handoff_phases_unchanged=all(row['handoff_phases']==proofs[0]['handoff_phases'] for row in proofs))
    receipts = {label:json.loads(path.read_text()) for label,path in {
        'candidate93':WORK/'delivery/signing-receipt.json', 'baseline94':WORK/'normal94/delivery/signing-receipt.json'}.items()}
    scheduler_ms = []
    for line in (WORK/'stress-1.jsonl').read_text().splitlines():
        match = re.search(r'scheduler_lateness=([\d.]+)(µs|ms)', json.loads(line).get('Output', ''))
        if match:
            scheduler_ms.append(float(match[1])/(1000 if match[2]=='µs' else 1))
    evidence = dict(schema=1, source_base='exact beta92/dd722ead; b9/1011 unchanged',
        finite_deadline_correctness='PASS', late_arrival_recovery='CONDITIONAL_SYNTHETIC_1294_ONLY',
        physical_speed_acceptance='NOT_ACCEPTED_SINGLE_B_SAMPLE_AND_MISSING_ANDROID_MECHANISM_COUNTERS',
        selected_local_candidate='B125', current_policy='A0_ON_FORWARD94',
        input_sha256=digest(FIXTURE/'late-arrival-input.json'), patch_sha256=digest(FIXTURE/'finite-deadline.patch'), sources=pins,
        a0_replay=[row for row in old if row['BudgetMS']==100], replay=replay,
        physical=phases, owner94_export=android_export,
        application_bytes=sum(row['requested_application_bytes'] for row in phases),
        unchanged_checks_reused=450, new_checks={path.name:tests(path) for pattern in ('delta-*.jsonl','integration-*.jsonl','stress-*.jsonl','a0-tradeoff.jsonl','clean-reapply.jsonl') for path in sorted(WORK.glob(pattern))},
        local_scheduler_lateness_ms=dict(samples=len(scheduler_ms), minimum=min(scheduler_ms), maximum=max(scheduler_ms), android_guarantee=False),
        android_builds={label:dict(tests=json.loads(path.read_text())['tests'], receipt_sha256=digest(path)) for label,path in
                        [('93',WORK/'build/receipt.json'), ('94',WORK/'normal94/android-build/receipt.json')]},
        artifacts=receipts,
        installations={label:dict(receipt_sha256=digest(path), before=json.loads(path.read_text())['before'],
                                  after=json.loads(path.read_text())['after'], identity_verified_after_install=True)
                       for label,path in [('candidate93',WORK/'upgrade-receipt.json'), ('baseline94',WORK/'normal94/upgrade-receipt.json')]},
        signing_receipts_describe_pre_install_state=True,
        identity=identity, current=json.loads((WORK/'runtime-final.json').read_text()),
        bootstrap1011='unchanged exact b9; prior177 race checks reused', nack='default100ms unchanged; actual negotiation/RTX and origin9909 unknown',
        old597='trigger unknown; missing final6s unchanged',
        arbitrary_late_packet_tradeoff='A0 can accept a hole packet even at500ms with no intervening arrivals; autonomous100/125 intentionally cannot after deadline',
        diagnostics='ordinary identical trace; no performance logger or owner fault schema; no removal-only build',
        side_effects=dict(gateway_restart=False, security_state_restore=False, uninstall=False, clear_data=False, push=False, public_release=False),
        fixtures={path.name:digest(path) for path in sorted(FIXTURE.glob('deadline*.py'))}|{'deadline_test.go':digest(FIXTURE/'deadline_test.go'),'arrival_tradeoff_test.go':digest(FIXTURE/'arrival_tradeoff_test.go')})
    destination = ROOT/'docs/releases/2026-10-20-mesh-receive-path.deadline.json'
    text = json.dumps(evidence, indent=2)+'\n'
    operation = ('*** Update File: '+str(destination)+'\n@@\n'+''.join('-'+line+'\n' for line in destination.read_text().splitlines())) if destination.exists() else '*** Add File: '+str(destination)+'\n'
    subprocess.run(['apply_patch','*** Begin Patch\n'+operation+''.join('+'+line+'\n' for line in text.splitlines())+'*** End Patch\n'],check=True)
    print(json.dumps(dict(phases=[{key:row[key] for key in ('phase','single_mbit_s','aggregate_mbit_s','control_ttfb_seconds','control_full_seconds','completed')} for row in phases], application_bytes=evidence['application_bytes'], identity_preserved=identity['identity_bindings_sha256'] and identity['support_id_sha256'])))


if __name__ == '__main__':
    main()
