"""Normalize one retained phase without network access or additional requests."""

import json
import re
import sys

from prepare import ROOT, WORK, digest

sys.path.insert(0, str(ROOT / 'tests/fixtures/queue_retry'))
from journal import reassemble


def histogram_bytes(value):
    return sum(value['Bytes'])


def streams(record):
    mux = record['performance']['Mux']
    return {stream['ID']: stream for stream in mux['Retired'] + mux['Streams'] if stream['ID']}


def delta(before, after, names):
    result = {name: after[name] - before[name] for name in names}
    assert all(value >= 0 for value in result.values()), 'COUNTER_SCOPE_RESET'
    return result


def histogram_delta(before, after):
    return dict(count=[last-first for first, last in zip(before['Count'], after['Count'])],
                total_ns=after['TotalNS']-before['TotalNS'],
                max_ns_scope='lifetime maxima cannot be subtracted',
                lifetime_max_before_ns=before['MaxNS'], lifetime_max_after_ns=after['MaxNS'])


def main():
    phase = sys.argv[1]
    assert phase in ('A1', 'B1', 'B2', 'A2')
    target = WORK / phase
    scope = json.loads((WORK / ('session-scope-'+phase+'.json')).read_text())
    raw = [json.loads(line) for line in (target / 'capture-private.jsonl').read_text().splitlines()]
    journal, errors = reassemble([row['raw'] for row in raw if row['kind'] == 'journal'])
    assert not errors, errors
    snapshots = []
    other_tags = set()
    diagnostics = []
    for entry in journal:
        try:
            record = json.loads(entry['MESSAGE'])
        except (ValueError, TypeError):
            continue
        if record.get('event') == 'restricted_performance_v1':
            if record['session_tag'] == scope['session_tag']:
                record['epoch'] = int(entry['__REALTIME_TIMESTAMP']) / 1e6
                snapshots.append(record)
            else:
                other_tags.add(record['session_tag'])
        elif record.get('event') in ('restricted_session_v1', 'restricted_session', 'restricted_failure'):
            diagnostics.append(record.get('event'))
    assert len(snapshots) > 2
    assert all(record['performance']['Mux']['Profile'] == 'LEGACY64' and
               record['performance']['Mux']['Window'] == 65536 and
               record['performance']['PacketPacing']['RateBytesPerSecond'] == (0 if phase.startswith('A') else 500000)
               for record in snapshots)
    assert any(row['kind'] == 'end' and not row['cap_reached'] and row['partial_bytes'] == 0 for row in raw)
    requests = [json.loads(line) for line in (target / 'requests.jsonl').read_text().splitlines()]
    cells = json.loads((target / 'cells.json').read_text())
    samples = [row for row in raw if row['kind'] == 'sample']
    for cell in cells:
        selected = [row for row in requests if row['name'].startswith('cell-'+str(cell['cell'])+'-')]
        start = min(row['start_epoch'] for row in selected)
        end = max(row['end_epoch'] for row in selected)
        before = next(row for row in reversed(snapshots) if row['epoch'] < start)
        after = next(row for row in snapshots if row['epoch'] >= end)
        interval_ns = after['node_ns'] - before['node_ns']
        assert interval_ns > 0
        prior, final = streams(before), streams(after)
        handed = {identifier: histogram_bytes(stream['HandedDATA']) -
                  (histogram_bytes(prior[identifier]['HandedDATA']) if identifier in prior else 0)
                  for identifier, stream in final.items()}
        matches = [identifier for identifier in final if identifier not in prior and
                   handed[identifier] >= selected[0]['intended_bytes']]
        attributable = len(matches) == cell['flows'] and all(row['valid'] for row in selected)
        measured = set(matches) if attributable else set()
        first, last = before['performance'], after['performance']
        bracketed = [row for row in snapshots if before['node_ns'] <= row['node_ns'] <= after['node_ns']]
        waits = delta(first['Window'], last['Window'],
                      ('ReadyFullNS', 'WindowOnlyBlockedNS', 'HeadUnconfirmedLaterSACKedBlockedNS',
                       'HeadSACKedBlockedNS', 'ReleasedBytes'))
        wait_percent = {name: value/interval_ns*100 for name, value in waits.items() if name.endswith('NS')}
        waits.update({name: histogram_bytes(last['Window'][name])-histogram_bytes(first['Window'][name])
                      for name in ('NewDATA', 'RetryDATA', 'CarrierAcceptedDATA')})
        pace_before, pace_after = first['PacketPacing'], last['PacketPacing']
        pacing = delta(pace_before, pace_after, ('Packets', 'RTPBytes', 'LocalWriteBytes', 'RTXPackets',
                                               'Errors', 'Rejected', 'RTCPBytes', 'RTCPWrittenBytes', 'RTCPWrittenPackets'))
        pacing.update(offered_rtp_mbit_s=pacing['RTPBytes']*8/(interval_ns/1e9)/1e6,
                      local_write_mbit_s=pacing['LocalWriteBytes']*8/(interval_ns/1e9)/1e6,
                      rtcp_types_delta=[last-first for first, last in zip(pace_before['RTCP'], pace_after['RTCP'])],
                      rtcp_order=['RR', 'NACK', 'TWCC', 'REMB', 'PLI', 'other'],
                      frame_packet_counts_delta=[last-first for first, last in zip(pace_before['FramePackets'], pace_after['FramePackets'])],
                      histograms={name: histogram_delta(pace_before[name], pace_after[name])
                                  for name in ('Spacing', 'Wait', 'SchedulerLate', 'CarrierQueueAge')},
                      peak_bins_lifetime_before=pace_before['Bins'], peak_bins_lifetime_after=pace_after['Bins'],
                      peak_bin_width_ms=[1, 5, 20],
                      pending_packet_sample_max=max(row['performance']['PacketPacing']['Pending'] for row in bracketed),
                      pending_bytes_sample_max=max(row['performance']['PacketPacing']['PendingBytes'] for row in bracketed),
                      carrier_frames_sample_max=max(row['performance']['CarrierQueueFrames'] for row in bracketed),
                      carrier_frames_lifetime_max=pace_after['CarrierQueueFramesMax'])
        stream_results = []
        for identifier in matches:
            stream = final[identifier]
            waiting = stream['ZeroCreditReadyNS']
            stream_results.append(dict(id=identifier, handed_bytes=handed[identifier],
                                       zero_credit_ready_ns=waiting, counter_interval_ns=interval_ns,
                                       zero_credit_percent=waiting/interval_ns*100,
                                       scope='new stream absent in before-snapshot; lifetime counter fully inside the stated bracket',
                                       closed=stream['Closed'], credit=stream['Credit'], queued_bytes=stream['QueuedBytes'],
                                       ready_bytes=stream['ReadyBytes'], receive_buffered=stream['ReceiveBuffered']))
        total_handed = histogram_bytes(last['Mux']['HandedDATA'])-histogram_bytes(first['Mux']['HandedDATA'])
        phone_requests = []
        for request in selected:
            metrics = request['metrics']
            full = float(metrics['time_total'])
            ttfb = float(metrics['time_starttransfer'])
            body = full - ttfb if ttfb > 0 and full >= ttfb else None
            phone_requests.append(dict(name=request['name'], valid=request['valid'], curl_exit=metrics.get('CURL_EXIT'),
                                       http_status=metrics.get('http_code'), bytes=int(metrics.get('BODY_BYTES', 0)),
                                       full_seconds=full, phone_wall_seconds=float(metrics['END'])-float(metrics['BEGIN']),
                                       phone_begin_uptime=metrics['BEGIN'], phone_end_uptime=metrics['END'],
                                       ttfb_seconds=ttfb, body_seconds=body,
                                       dns_seconds=float(metrics['time_namelookup']), tcp_seconds=float(metrics['time_connect']),
                                       tls_seconds=float(metrics['time_appconnect']), goodput_mbit_s=request.get('mbit_s'),
                                       body_mbit_s=int(metrics.get('BODY_BYTES', 0))*8/body/1e6 if body else None,
                                       new_connections=int(metrics['num_connects']), local_port=metrics['local_port']))
        joint = dict(zero_ready=0, zero_ready_rs_free_writer_idle=0, zero_ready_rs_full=0)
        for record in bracketed:
            mux, window = record['performance']['Mux'], record['performance']['Window']
            if any(stream['ReadyBytes'] > 0 and stream['Credit'] == 0 for stream in mux['Streams']):
                joint['zero_ready'] += 1
                if window['SlotSpan'] < window['EffectiveWindow'] and not window['LocalWriterBusy'] and window['LocalQueuedFrames'] == 0:
                    joint['zero_ready_rs_free_writer_idle'] += 1
                if window['SlotSpan'] >= window['EffectiveWindow']:
                    joint['zero_ready_rs_full'] += 1
        cell.update(requests=phone_requests, counter_bracket=dict(before_epoch=before['epoch'], after_epoch=after['epoch'],
                    before_node_ns=before['node_ns'], after_node_ns=after['node_ns'], interval_seconds=interval_ns/1e9,
                    request_start_epoch=start, request_end_epoch=end),
                    mux_attribution='unique new byte-volume-matching stream set' if attributable else 'AMBIGUOUS',
                    parallel_request_to_stream_mapping='not independently resolved' if cell['flows'] > 1 else 'single matching stream',
                    mux_streams=stream_results, rs_delta=waits, rs_wait_percent=wait_percent, pacing=pacing,
                    protocol_errors_before=first['Mux']['ProtocolErrors'], protocol_errors_after=last['Mux']['ProtocolErrors'],
                    joint_point_observations=joint,
                    background=dict(handed_download_bytes=total_handed-sum(handed[identifier] for identifier in measured) if attributable else None,
                        active_stream_range=[min(sum(stream['ID'] not in measured for stream in row['performance']['Mux']['Streams']) for row in bracketed),
                                             max(sum(stream['ID'] not in measured for stream in row['performance']['Mux']['Streams']) for row in bracketed)],
                        scope='other Mux handed download DATA including TLS overhead, not all bidirectional background traffic'),
                    matching_gateway_socket_max=max(sum(any(request['metrics']['remote_ip']+':443' in line for request in selected)
                                                        for line in sample['sockets']) for sample in samples if start <= sample['epoch'] <= end))
    first, last = snapshots[0]['performance'], snapshots[-1]['performance']
    origin = next(row for row in raw if row['kind'] == 'origin')
    ticks = lambda row: sum(int(value) for value in row['stat'].split()[13:15])
    result = dict(phase=phase, scope=scope, cells=cells,
                  summary=json.loads((target/'summary.json').read_text()), snapshots=len(snapshots), other_session_tags=sorted(other_tags),
                  protocol_errors=dict(at_establishment=None, first_observed=first['Mux']['ProtocolErrors'],
                                       before_bulk=cells[1]['protocol_errors_before'] if len(cells)>1 else None,
                                       after=last['Mux']['ProtocolErrors']),
                  local_write_errors=dict(before=first['PacketPacing']['Errors'], after=last['PacketPacing']['Errors']),
                  feedback=dict(negotiated={name:last['PacketPacing'][name] for name in ('NACK','TWCC','REMB')},
                                actual_rtcp_lifetime_before=first['PacketPacing']['RTCP'],actual_rtcp_lifetime_after=last['PacketPacing']['RTCP'],
                                scope='publisher to SFU leg, not full Android path; ordinary retransmissions not counted by RTX SSRC alone'),
                  resources=dict(cpu_percent_one_core=(ticks(samples[-1])-ticks(samples[0]))/origin['clock_ticks']/(samples[-1]['monotonic']-samples[0]['monotonic'])*100,
                                 rss_max_kib=max(int(re.search(r'VmRSS:\s+(\d+)', row['status'])[1]) for row in samples),
                                 mux_retained_sample_max=max(row['performance']['Mux']['RetainedBytes'] for row in snapshots),
                                 rs_retained_sample_max=max(row['performance']['Window']['RetainedBytes'] for row in snapshots),
                                 rs_local_queue_sample_max=max(row['performance']['Window']['LocalQueuedBytes'] for row in snapshots)),
                  collector_end=next(row for row in raw if row['kind']=='end'),journal_errors=errors,
                  retained_diagnostic_event_names=diagnostics,
                  limitations=['request groups matched to new stream sets, equal parallel streams not individually mapped',
                               'counter brackets include background and snapshot edges; overlapping waits are not added',
                               'peak bins and high-water values are lifetime maxima, not subtractable request-local peaks',
                               'no fresh Android per-frame gap/drop export; not inferred from publisher RTCP',
                               'no Android native byte-exact origin checksum; complete HTTPS body/length verified'],
                  capture_sha256=digest(target/'capture-private.jsonl'))
    with (target/'normalized.json').open('x') as output:
        json.dump(result, output, indent=2)
    print(json.dumps(dict(phase=phase, protocol_errors=result['protocol_errors'], resources=result['resources'],
                         cells=[dict(cell=cell['cell'], complete=cell['completed'], seconds=cell['wall_seconds'], mbit_s=cell['aggregate_mbit_s'],
                                     ids=[stream['id'] for stream in cell['mux_streams']], background=cell['background'], rs_wait_percent=cell['rs_wait_percent']) for cell in cells])))


if __name__ == '__main__':
    main()
