"""Add conservative carrier/receiver boundaries to the existing RS correlator."""

import argparse
import collections
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/fixtures/queue_retry'))
from journal import reassemble, performance_lines
sys.path.insert(0, str(ROOT / 'tests/fixtures/mesh_throughput_trace'))
from correlate import reconstruct, correlate


def receive_evidence(nodes):
    points = {}
    errors = []
    coverage = {}
    for node, records in nodes.items():
        for record in records:
            trace = record['performance']['Trace']
            stream = (node, record['session_tag'], trace['origin'])
            received = trace.get('receive')
            if received is None:
                errors.append(dict(node=node, session=stream[1], error='missing_receive_trace'))
                continue
            coverage[stream] = max(coverage.get(stream, 0), received['count'])
            for point in received.get('points', []) + received.get('incident', []):
                key = (*stream, point['i'])
                if key in points and points[key] != point:
                    errors.append(dict(node=node, index=point['i'], error='conflicting_receive_point'))
                points[key] = point
    streams = []
    for stream, count in coverage.items():
        observed = sorted(key[-1] for key in points if key[:3] == stream)
        streams.append(dict(node=stream[0],session=stream[1],origin=stream[2],count=count,
                            observed=len(observed),missing=count-len(observed),
                            prefix_unobserved=observed[0]-1 if observed else count,
                            interior_missing=observed[-1]-observed[0]+1-len(observed) if observed else 0,
                            first=observed[0] if observed else None,last=observed[-1] if observed else None))
    messages = collections.defaultdict(list)
    frame_bindings = collections.defaultdict(set)
    for key, point in points.items():
        if point.get('total') and point.get('ts'):
            frame_bindings[(*key[:3],point.get('track'),point['ts'])].add((key[1],point.get('sender',0),point.get('message',0)))
    unidentified_frames = set()
    for key, point in points.items():
        if point.get('total'):
            message_key = (key[1], point.get('sender',0), point.get('message',0))
            messages[message_key].append(dict(node=key[0],origin=key[2],**point))
        elif point.get('ts'):
            frame_key=(*key[:3],point.get('track'),point['ts'])
            candidates=frame_bindings.get(frame_key,set())
            if len(candidates)==1:
                messages[next(iter(candidates))].append(dict(node=key[0],origin=key[2],binding='same_node_track_timestamp_header',**point))
            else:
                unidentified_frames.add(frame_key)
    lifecycles = []
    for key, observed in messages.items():
        sequences = sorted({item.get('seq',0) for item in observed if item.get('known')})
        attempts = sorted({item.get('attempt',0) for item in observed if item.get('attempt_known')})
        if not sequences:
            continue
        lifecycles.append(dict(session=key[0],sender=key[1],message=key[2],sequences=sequences,
                               attempts=attempts,events=sorted(observed,key=lambda item:(item['node'],item['ns'],item['i']))))
    return dict(coverage=streams, carrier_lifecycles=lifecycles, errors=errors,
                frames_without_unique_observed_header=len(unidentified_frames),
                absence_is_not_loss=True, cross_node_latency_computed=False,
                rtp_numbers_matched_across_sfu=False)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--nl',type=Path,required=True)
    parser.add_argument('--android',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    arguments=parser.parse_args()
    os.umask(0o077)
    journal, journal_errors = reassemble(arguments.nl.read_text().splitlines())
    nl, nl_errors = reconstruct(performance_lines(journal))
    android, android_errors = reconstruct(arguments.android.read_text().splitlines())
    nodes = dict(NL=nl,Android=android)
    result=dict(reliable=correlate(nodes),receive=receive_evidence(nodes),
                parser_errors=dict(journal=journal_errors,nl=nl_errors,android=android_errors))
    with arguments.output.open('x') as output:json.dump(result,output,indent=2)
    print(json.dumps(dict(receive_coverage=result['receive']['coverage'],
                          parser_errors={key:len(value) for key,value in result['parser_errors'].items()},
                          logical_data=len(result['reliable']['logical_data']))))


if __name__ == '__main__':
    main()
