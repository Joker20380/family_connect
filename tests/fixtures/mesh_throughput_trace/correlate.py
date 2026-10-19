"""Bounded metadata-only export reconstruction; never infer cross-host latency."""

import argparse
import base64
import hashlib
import json
from collections import defaultdict
from pathlib import Path

MAX_RECORD = 1024 * 1024
MAX_PENDING = 16


def reconstruct(lines):
    pending, records, errors = {}, [], []
    for number, line in enumerate(lines, 1):
        try:
            if not line.strip() or line.startswith('--------- beginning of '):
                continue
            if len(line) > MAX_RECORD * 2:
                raise ValueError('oversized input line')
            value = json.loads(line)
            stream = value.get('_STREAM_ID', value.get('stream', 'file'))
            if 'MESSAGE' in value:
                if not value['MESSAGE'].startswith('{'):
                    continue
                value = json.loads(value['MESSAGE'])
            if value.get('event') == 'restricted_performance_v1':
                records.append(value)
                continue
            if value.get('event') != 'restricted_performance_chunk_v1':
                continue
            count, part, size = value['parts'], value['part'], value['bytes']
            if not 1 <= count <= 600 or not 0 <= part < count or not 1 <= size <= MAX_RECORD:
                raise ValueError('invalid chunk bounds')
            key = (stream, value['origin'], value['session_tag'], value['capture'])
            if key not in pending and len(pending) == MAX_PENDING:
                evicted = next(iter(pending))
                errors.append(dict(line=number, error='incomplete_evicted', capture=list(evicted)))
                del pending[evicted]
            group = pending.setdefault(key, dict(parts=count, size=size, sha=value['sha256'], data={}))
            if (group['parts'], group['size'], group['sha']) != (count, size, value['sha256']):
                raise ValueError('chunk metadata conflict')
            data = base64.b64decode(value['data'], validate=True)
            if len(data) > 1800 or part in group['data'] and group['data'][part] != data:
                raise ValueError('chunk content conflict')
            group['data'][part] = data
            if len(group['data']) != count:
                continue
            raw = b''.join(group['data'][index] for index in range(count))
            del pending[key]
            if len(raw) != size or hashlib.sha256(raw).hexdigest() != group['sha']:
                raise ValueError('chunk checksum mismatch')
            record = json.loads(raw)
            if record.get('event') != 'restricted_performance_v1' or record.get('session_tag') != key[2]:
                raise ValueError('envelope binding mismatch')
            trace = record['performance'].get('Trace')
            if trace and trace['origin'] != key[1]:
                raise ValueError('origin binding mismatch')
            records.append(record)
        except (ValueError, TypeError, KeyError) as error:
            errors.append(dict(line=number, error=str(error)))
    for key, group in pending.items():
        errors.append(dict(error='incomplete', capture=list(key), missing=[index for index in range(group['parts']) if index not in group['data']]))
    return records, errors


def android_export(bundle):
    ring = bundle['ring']
    sessions = ring.get('restricted_history', []) + [ring.get('restricted_session', {})]
    return [dict(event='restricted_performance_v1', session_tag=session['session_tag'],
                 performance=session['restricted_performance_v1'])
            for session in sessions if 'restricted_performance_v1' in session]


def correlate(sources):
    events, errors, coverage, samples = {}, [], {}, []
    for node, records in sources.items():
        for record in records:
            performance = record['performance']
            trace = performance.get('Trace')
            if not trace:
                errors.append(dict(node=node, error='missing_transport_trace'))
                continue
            tag, origin = record['session_tag'], trace['origin']
            coverage_key = (node, origin, tag)
            entry = coverage.setdefault(coverage_key, dict(indices=set(), counts=[], overwritten=[]))
            entry['counts'].append(trace['count'])
            entry['overwritten'].append(trace['overwritten'])
            samples.append(dict(node=node, origin=origin, session_tag=tag, node_ns=trace['now_ns'],
                                window=performance.get('Window'), mux=performance.get('Mux')))
            for point in trace['points']:
                key = (node, origin, tag, point['i'])
                if key in events and events[key]['point'] != point:
                    errors.append(dict(node=node, error='event_index_conflict', index=point['i']))
                events[key] = dict(node=node, origin=origin, tag=tag, point=point)
                entry['indices'].add(point['i'])
    data, acks = defaultdict(list), defaultdict(list)
    for value in events.values():
        point = value['point']
        if not point.get('wire'):
            continue
        if point['kind'].startswith('ack_'):
            acks[(value['tag'], point['wire'], point.get('base', 0), point.get('mask', 0))].append(value)
        else:
            data[(value['tag'], point['wire'], point['seq'])].append(value)
    logical = []
    for key, points in sorted(data.items()):
        submissions = [value for value in points if value['point']['kind'] == 'submission']
        consumes = [value for value in points if value['point']['kind'] == 'consume']
        retries = [value for value in points if value['point']['kind'].startswith('retry_')]
        receives = [value for value in points if value['point']['kind'] == 'receive']
        summary = dict(session_tag=key[0], wire=key[1], sequence=key[2],
                       first_submission_observed=bool(submissions), retries=len(retries), consumes=len(consumes),
                       receive_results=[value['point']['result'] for value in receives],
                       nodes=sorted({value['node'] for value in points}), events=points,
                       receive_attempt_mapping='Wire has no retry attempt; arrivals cannot be uniquely assigned to submissions',
                       local_intervals=[])
        if len(consumes) > 1:
            errors.append(dict(error='multiple_consumes', key=list(key)))
        for value in points:
            point = value['point']
            if point['kind'] == 'data_decode' and point.get('carrier_ns', 0) > 0:
                summary['local_intervals'].append(dict(node=value['node'], origin=value['origin'],
                    kind='carrier_completion_to_decode_ns', ns=point['ns'] - point['carrier_ns']))
            if point['kind'] in ('consume', 'first_ack', 'release') and point.get('first_ns', 0) > 0:
                summary['local_intervals'].append(dict(node=value['node'], origin=value['origin'],
                    kind={'consume': 'head_ready_to_consume_ns', 'first_ack': 'submission_to_first_ack_ns',
                          'release': 'submission_to_release_ns'}[point['kind']],
                    recovery=bool(retries), ns=point['ns'] - point['first_ns']))
        logical.append(summary)
    matches = []
    for key, points in sorted(acks.items()):
        generated = [value for value in points if value['point']['kind'] == 'ack_created']
        for value in points:
            if value['point']['kind'] != 'ack_input':
                continue
            possible = [candidate for candidate in generated if candidate['node'] != value['node']]
            matches.append(dict(session_tag=key[0], wire=key[1], base=key[2], mask=key[3], received=value,
                possible_local_generations=possible, unique_wire_identifier=False,
                reason='ACK wire has no sender-local token; no cross-node timestamp subtraction'))
    completeness = []
    for key, entry in coverage.items():
        indices = sorted(entry['indices'])
        completeness.append(dict(node=key[0], origin=key[1], session_tag=key[2],
            observed=len(indices), prefix_unobserved=(indices[0]-1 if indices else max(entry['counts'])),
            interior_missing=(indices[-1]-indices[0]+1-len(indices) if indices else 0),
            max_reported_overwritten=max(entry['overwritten']), max_count=max(entry['counts'])))
    return dict(logical_data=logical, ack_correspondence=matches,
                ack_events=[value for points in acks.values() for value in points], completeness=completeness,
                counter_samples=samples, errors=errors, one_way_latency='NOT_COMPUTED',
                retries_are_logical_data_attempts=True, retained_bytes_are_physical_flight=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--nl', type=Path, required=True)
    parser.add_argument('--android', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    sources, errors = {}, {}
    for label, path in [('NL', args.nl), ('Android', args.android)]:
        with path.open() as handle:
            sources[label], errors[label] = reconstruct(handle)
    result = correlate(sources)
    result['parser_errors'] = errors
    with args.output.open('x') as handle:
        json.dump(result, handle, indent=2)
    print(json.dumps(dict(logical_blocks=len(result['logical_data']),
                          two_sided=sum(len(value['nodes']) == 2 for value in result['logical_data']),
                          errors=len(result['errors']) + sum(map(len, errors.values())))))


if __name__ == '__main__':
    main()
