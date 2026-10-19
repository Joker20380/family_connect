"""Summarize local intervals and counter deltas without cross-host timing claims."""

import collections
import json
from pathlib import Path
import sys


def distribution(values):
    values = sorted(values)
    if not values:
        return dict(count=0)
    return dict(count=len(values), p50_ms=values[len(values)//2]/1e6,
                p90_ms=values[min(len(values)-1, int(len(values)*.9))]/1e6,
                max_ms=values[-1]/1e6)


def summarize(result):
    summary = dict(completeness=result['completeness'], errors=result['errors'], nodes={})
    for node in ('NL', 'Android'):
        samples = [value for value in result['counter_samples'] if value['node'] == node]
        if not samples:
            continue
        origins = {(value['origin'], value['session_tag']) for value in samples}
        assert len(origins) == 1, 'Summarize separate sessions independently'
        first, last = samples[0], samples[-1]
        before, after = first['window'], last['window']
        intervals = collections.defaultdict(list)
        events = {}
        selected = []
        for block in result['logical_data']:
            for interval in block['local_intervals']:
                if interval['node'] == node:
                    intervals[interval['kind']].append(interval['ns'])
            for event in block['events']:
                if event['node'] == node:
                    events[event['point']['i']] = event['point']
            if (node == 'NL' and block['retries'] and block['first_submission_observed']
                    and len(block['nodes']) == 2 and block['consumes'] == 1):
                selected.append(dict(sequence=block['sequence'], wire=block['wire'], retries=block['retries'],
                                     results=block['receive_results'], intervals=block['local_intervals']))
        local_acks = collections.defaultdict(dict)
        for event in result.get('ack_events', []):
            if event['node'] == node:
                point = event['point']
                events[point['i']] = point
                if point.get('token'):
                    local_acks[(event['origin'], event['tag'], point['token'])][point['kind']] = point
        for points in local_acks.values():
            created, written = points.get('ack_created'), points.get('ack_carrier_written')
            queued = points.get('ack_carrier_queued')
            if created and written and written.get('result') == 'ok':
                intervals['ack_created_to_local_write_ns'].append(written['ns']-created['ns'])
            if queued and written and written.get('result') == 'ok':
                intervals['ack_queued_to_local_write_ns'].append(written['ns']-queued['ns'])
        decoded = None
        for point in sorted(events.values(), key=lambda value: value['i']):
            if point['kind'] == 'ack_decode':
                decoded = point
            elif point['kind'] == 'ack_input':
                if decoded and all(decoded.get(key, 0) == point.get(key, 0) for key in ('wire', 'base', 'mask')):
                    intervals['ack_decode_to_engine_input_ns'].append(point['ns']-decoded['ns'])
                decoded = None
        streams = {}
        for sample in samples:
            mux = sample.get('mux') or {}
            for stream in (mux.get('Streams') or []) + (mux.get('Retired') or []):
                if stream['ID']:
                    previous = streams.get(stream['ID'])
                    if previous is None or sum(stream['HandedDATA']['Bytes']) >= sum(previous['HandedDATA']['Bytes']):
                        streams[stream['ID']] = stream
        high_volume = sorted(streams.values(), key=lambda value: sum(value['HandedDATA']['Bytes']), reverse=True)[:12]
        delta = {key: after[key]-before[key] if key in before and key in after else None for key in ('ReceiveReadyWaitNS', 'ReleasedBytes', 'ReleasedBlocks',
                  'FullNS', 'ReadyFullNS', 'WindowOnlyBlockedNS', 'HeadSACKedBlockedNS', 'HeadUnconfirmedLaterSACKedBlockedNS')}
        for key in ('NewDATA', 'RetryDATA', 'CarrierAcceptedDATA'):
            delta[key] = {field: [end-start for start, end in zip(before[key][field], after[key][field])]
                          for field in ('Count', 'Bytes')}
        summary['nodes'][node] = dict(sample_interval_seconds=(last['node_ns']-first['node_ns'])/1e9,
            delta=delta, intervals={key: distribution(values) for key, values in intervals.items()},
            high_volume_streams=[{key: stream[key] for key in ('ID', 'Credit', 'CreditUpdates', 'CreditBytes',
                'ZeroCreditReadyNS', 'QueueReadyNS', 'Closed', 'HandedDATA')} for stream in high_volume],
            repeat_examples=selected[:8], observed_event_kinds=dict(collections.Counter(point['kind'] for point in events.values())))
    return summary


if __name__ == '__main__':
    directory = Path(sys.argv[1])
    value = summarize(json.loads((directory / (sys.argv[2] if len(sys.argv) > 2 else 'correlation-private.json')).read_text()))
    with (directory / 'analysis.json').open('x') as handle:
        json.dump(value, handle, indent=2)
    print(json.dumps(value, indent=2))
