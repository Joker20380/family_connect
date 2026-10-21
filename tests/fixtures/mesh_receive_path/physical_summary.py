"""Small causal summary of saved paired evidence; no new traffic or clock mixing."""

import collections
import json
import os
import sys

from preserve import ROOT, WORK, digest
from correlate_receive import receive_evidence

sys.path.insert(0,str(ROOT/'tests/fixtures/mesh_throughput_trace'))
from correlate import reconstruct


def main():
    os.umask(0o077)
    directory=WORK/'baseline'
    correlation=json.loads((directory/'correlation-private.json').read_text())
    android,errors=reconstruct((directory/'capture/Android-raw.jsonl').read_text().splitlines())
    assert not errors and not correlation['errors'] and not any(correlation['parser_errors'].values())
    receive=receive_evidence(dict(Android=android))
    points={point['i']:point for record in android for point in record['performance']['Trace']['receive']['points']}
    results=[]
    for sequence,message in ((614,2969333433),(1127,2969334733),(1294,2969335140)):
        message_trace=next(value for value in correlation['receive_path']['carrier_lifecycles']
                           if value['message']==message and sequence in value['sequences'])
        received=[point for point in message_trace['events'] if point['node']=='Android']
        first,last=min(point['i'] for point in received),max(point['i'] for point in received)
        assert all(index in points for index in range(first,last+1))
        logical=next(value for value in correlation['logical_data'] if value['sequence']==sequence and
                     any(event['node']=='NL' and event['point']['kind']=='submission' for event in value['events']))
        results.append(dict(sequence=sequence,sender=message_trace['sender'],message=message,
                            android_complete_retained_index_range=[first,last],
                            initial_submission_observed=logical['first_submission_observed'],
                            nl_events=[event['point'] for event in logical['events'] if event['node']=='NL'],
                            android_events=received,android_consume_for_selected_sequence='UNOBSERVED_IN_RETAINED_RS_RING',
                            no_arrival_timer_cause_established=False))
    controls=[]
    for sequence,base,mask in ((649,650,127),(741,742,127)):
        logical=next(value for value in correlation['logical_data'] if value['sequence']==sequence and
                     any(event['node']=='NL' and event['point']['kind']=='submission' for event in value['events']))
        matching=[event for event in correlation['ack_events'] if event['point'].get('base',0)==base
                  and event['point'].get('mask',0)==mask and
                  ((event['node']=='Android' and event['point']['kind'] in ('ack_created','ack_carrier_queued','ack_carrier_written'))
                   or (event['node']=='NL' and event['point']['kind']=='ack_input'))]
        generated=[event for event in matching if event['node']=='Android' and event['point']['kind']=='ack_created']
        controls.append(dict(sequence=sequence,logical=logical,covering_ack_events=matching,
                             candidate_local_generations=len(generated),unique_wire_identifier=False,
                             earlier_android_attempt_rtp='INSUFFICIENT_RETAINED_CAPTURE'))
    samples=correlation['counter_samples']
    counters={}
    for node in ('NL','Android'):
        values=[value for value in samples if value['node']==node]
        assert len({(value['origin'],value['session_tag']) for value in values})==1
        first,last=values[0],values[-1]
        fields=('ReadyFullNS','WindowOnlyBlockedNS','HeadSACKedBlockedNS',
                'HeadUnconfirmedLaterSACKedBlockedNS','ReceiveReadyWaitNS','ReleasedBytes')
        counters[node]=dict(span_ns=last['node_ns']-first['node_ns'],
                            deltas={name:last['window'][name]-first['window'][name] for name in fields},
                            interval_overlap='NOT_ADDED_AS_INDEPENDENT_DELAYS')
    streams=collections.defaultdict(list)
    for sample in samples:
        if sample['node']=='NL':
            for stream in sample['mux']['Streams']:streams[stream['ID']].append(stream)
    bulk_streams=[dict(stream=key,observed_handed_bytes=max(sum(value['HandedDATA']['Bytes']) for value in values),
                       zero_credit_ready_ns=max(value['ZeroCreditReadyNS'] for value in values),
                       queue_ready_ns=max(value['QueueReadyNS'] for value in values))
                  for key,values in streams.items() if max(sum(value['HandedDATA']['Bytes']) for value in values)>1000000]
    receiver_counts=[record['performance']['Trace']['receive'] for record in android]
    assert all(not value.get('incident_at') and value['later_capacity']==0 for value in receiver_counts)
    requests=[json.loads(line) for line in (directory/'requests.jsonl').read_text().splitlines()]
    result=dict(session=android[0]['session_tag'],classification='FORWARD_RTP_GAP_AND_LATE_ARRIVAL_THEN_LOCAL_FRAME_DISCARD',
                selected_damaged_lifecycles=results,slow_reliable_controls=controls,
                android_capacity_events_cumulative=0,android_coverage=receive['coverage'],
                selected_interval_missing_record_is_not_loss=True,counters=counters,bulk_mux_streams=bulk_streams,
                requests=[dict(name=row['name'],valid=row['valid'],bytes=row['metrics']['BODY_BYTES'],
                               ttfb_s=row['metrics']['time_starttransfer'],full_s=row['metrics']['time_total'],
                               mbit_s=row.get('mbit_s'),observed_sha256=row['metrics']['BODY_SHA256']) for row in requests],
                result=json.loads((directory/'result.json').read_text()),
                targeted_candidate='LOCAL_VALIDATED_NOT_DEPLOYED_NO_CURRENT_CAPACITY_PRESSURE',
                packet_pacing_or_network_hop_attribution='NOT_ESTABLISHED',
                next_comparison='Same exact pair and IPv4 endpoint on an already authorized alternative placement; '
                                'no purchase, production migration or silent country change. Placement not selected.',
                source_files={str(path.relative_to(WORK)):digest(path) for path in
                              (directory/'correlation-private.json',directory/'capture/NL-raw.jsonl',
                               directory/'capture/Android-raw.jsonl',directory/'requests.jsonl')})
    with (WORK/'physical-receiver-summary.json').open('x') as output:json.dump(result,output,indent=2)
    print(json.dumps(dict(classification=result['classification'],damaged=len(results),reliable_controls=len(controls),
                          capacity=0,requests=len(requests),successful=sum(row['valid'] for row in requests),
                          mux_streams=[value['stream'] for value in bulk_streams])))


if __name__=='__main__':main()
