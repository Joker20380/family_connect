#!/usr/bin/env python3
"""Offline PERF-2 evidence audit; completion is not an operating-envelope verdict."""
import argparse
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import statistics


def distribution(values):
    values = sorted(values)
    if not values:
        return {'count': 0}
    return {'count': len(values), 'avg': statistics.mean(values), 'min': values[0],
            'max': values[-1], **{f'p{percentile}': values[math.ceil(len(values) * percentile / 100) - 1]
                                 for percentile in (50, 95, 99)}}


def read_rows(path):
    if path.stat().st_size > 32 * 1024 * 1024:
        raise ValueError('evidence exceeds bound')
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def timestamp(row):
    return datetime.fromisoformat(row['utc'].replace('Z', '+00:00')).timestamp()


def reliability_events(snapshots, final):
    indexed = {}
    for stats in [snapshot.get('reliability', {}) for snapshot in snapshots] + [final]:
        for event in (stats.get('Events') or []) + (stats.get('RecentEvents') or []):
            index = event['index']
            if index in indexed and indexed[index] != event:
                raise ValueError('contradictory recovery evidence')
            indexed[index] = event
    count = len(final.get('Events') or []) + final.get('EventsDropped', 0)
    complete = set(indexed) == set(range(1, count + 1))
    return [indexed[index] for index in sorted(indexed)], complete


def endpoint_summary(rows, origin, finished):
    samples = [row for row in rows if 'snapshot' in row]
    snapshots = [row['snapshot'] for row in samples]
    final = next((row['stats'] for row in reversed(rows) if row.get('event') == 'reliability_final'), {})
    carrier = next((row['stats'] for row in reversed(rows) if row.get('event') == 'summary'), {})
    events, complete = reliability_events(snapshots, final)
    resource_rows = [row for row in rows if row.get('event') in ('resources', 'summary')]
    android_rows = [row for row in rows if row.get('event') == 'android_resources']
    numeric = lambda fields, records: {field: distribution([row[field] for row in records if field in row]) for field in fields}
    minutes = {}
    for row in samples:
        elapsed = timestamp(row) - origin
        if elapsed < 0:
            continue
        minute = int(elapsed // 60)
        snapshot = row['snapshot']
        reliability = snapshot.get('reliability', {})
        entry = minutes.setdefault(minute, {'carrier_queue': [], 'retained_bytes': [], 'send_depth': [], 'reorder_depth': [], 'application_queue': []})
        entry['carrier_queue'].append(snapshot['send_queue_frames'])
        entry['retained_bytes'].append(reliability.get('BufferedBytes', 0))
        entry['send_depth'].append(reliability.get('SendDepth', 0))
        entry['reorder_depth'].append(reliability.get('ReorderDepth', 0))
        if 'application_send_queue' in row:
            entry['application_queue'].append(row['application_send_queue'])
        entry['last_elapsed_s'] = elapsed
        entry['rtp_gaps_cumulative'] = snapshot['carrier']['Media']['SequenceGaps']
        entry['retransmissions_cumulative'] = reliability.get('Retransmissions', 0)
        entry['block_gaps_cumulative'] = reliability.get('Gaps', 0)
        entry['recovered_cumulative'] = reliability.get('RecoveredGaps', 0)
    for entry in minutes.values():
        for field in ('carrier_queue', 'retained_bytes', 'send_depth', 'reorder_depth', 'application_queue'):
            entry[field] = distribution(entry[field])
    stats = {key: value for key, value in final.items() if key not in ('Events', 'RecentEvents')}
    active = [row for row in samples if timestamp(row) <= finished]
    active_stats = active[-1]['snapshot'].get('reliability', {}) if active else {}
    active_stats = {key: value for key, value in active_stats.items() if key not in ('Events', 'RecentEvents')}
    ice = [pair['currentRoundTripTime'] for snapshot in snapshots for role in ('publisher', 'subscriber')
           for pair in snapshot.get(role, []) if pair.get('type') == 'candidate-pair' and 'currentRoundTripTime' in pair]
    return {'reliability': stats, 'carrier': {key: value for key, value in carrier.items() if key not in ('Evidence',)},
            'last_active_reliability': active_stats,
            'last_active_snapshot_utc': active[-1]['utc'] if active else None,
            'ice_rtt_seconds': distribution(ice),
            'events': events, 'event_coverage_complete': complete,
            'recovery_ms': distribution([event['delay_ms'] for event in events if event['kind'] == 'recovered']),
            'carrier_queue': distribution([snapshot['send_queue_frames'] for snapshot in snapshots]),
            'resources': numeric(('heap_bytes', 'heap_sys_bytes', 'max_rss_kib', 'rss_bytes', 'goroutines', 'cpu_user_s', 'cpu_system_s', 'gc_cycles', 'gc_pause_total_ns'), resource_rows),
            'android_resources': numeric(('app_pss_kib', 'java_used_bytes', 'app_cpu_ms'), android_rows),
            'battery_start_end': [android_rows[0]['battery_percent'], android_rows[-1]['battery_percent']] if android_rows else [],
            'minutes': minutes}


def summarize(directory):
    android = read_rows(directory / 'A.jsonl')
    gateway = read_rows(directory / 'B.jsonl')
    results = [row for row in android if row.get('event') == 'perf_result']
    if not results:
        return {'correctness_complete': False, 'reason': 'no_perf_result'}
    result = results[-1]
    warmup = next((row for row in android if row.get('event') == 'perf_warmup'), None)
    origin = timestamp(warmup or result)
    stages = [stage for row in android if row.get('event') == 'perf_blocks' and not row['warmup'] for stage in row['rows']]
    sequences = [int(stage[0]) for stage in stages]
    exact_rows = (len(stages) == result['blocks_received'] and bool(sequences) and warmup is not None
                  and sequences[0] == warmup['sent'] + 1
                  and sequences == list(range(sequences[0], sequences[0] + len(sequences))))
    auth = all(any(row.get('event') == 'family_auth' and row.get('accepted') is True for row in rows) for rows in (android, gateway))
    clean_exit = any(row.get('event') == 'android_exit' and row['code'] == 0 and not row.get('cancelled') for row in android)
    correct = (auth and clean_exit and exact_rows and not result['warmup'] and result['status'] == 'PASS'
               and not any(result['errors'].values()) and result['blocks_sent'] == result['blocks_received']
               and result['measurement_s'] >= result['config']['seconds'])
    endpoints = {name: endpoint_summary(rows, origin, timestamp(result)) for name, rows in (('android', android), ('amsterdam', gateway))}
    minutes = {}
    for stage in stages:
        entry = minutes.setdefault(int(stage[1] // 60000), {'rtt': [], 'count': 0})
        entry['rtt'].append(stage[4] - stage[1])
        entry['count'] += 1
    for entry in minutes.values():
        entry['rtt'] = distribution(entry['rtt'])
    stats = [entry['reliability'] for entry in endpoints.values()]
    retry_bytes = sum(entry.get('RetransmittedBytes', 0) for entry in stats)
    useful_bytes = result['useful_tx_bytes'] + result['useful_rx_bytes']
    return {'correctness_complete': correct, 'exact_timing_rows_complete': exact_rows,
            'result': {key: value for key, value in result.items() if key != 'snapshot'},
            'endpoints': endpoints, 'rtt_by_creation_minute': minutes,
            'delivery_efficiency': result['useful_rx_bytes'] / result['useful_tx_bytes'] if result['useful_tx_bytes'] else None,
            'session_retry_payload_bytes': retry_bytes,
            'session_retry_over_measured_bidirectional_useful_percent': retry_bytes * 100 / useful_bytes if useful_bytes else None,
            'session_ack_header_bytes': 64 * sum(entry.get('ACKSent', 0) for entry in stats),
            'session_data_header_bytes': 64 * sum(entry.get('DataSent', 0) + entry.get('Retransmissions', 0) for entry in stats),
            'sha256': {name: hashlib.sha256((directory / name).read_bytes()).hexdigest() for name in ('A.jsonl', 'B.jsonl')}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    summary = summarize(args.directory)
    args.out.write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({'correctness_complete': summary['correctness_complete'], 'result': summary.get('result')}))


if __name__ == '__main__':
    main()
