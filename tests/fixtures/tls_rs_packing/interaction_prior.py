"""Recover only claims actually present in sealed old evidence."""
import collections
import json
from interaction_prepare import PARENT, WORK, save, digest


def main():
    summary = json.loads((PARENT/'analysis.json').read_text())
    phases = {}
    for name in ['P32A1r','P32B1','P32B2','P32A2']:
        phase = summary['phases'][name]
        events = [json.loads(line) for line in (PARENT/name/'server-peer.jsonl').read_text().splitlines()]
        snapshots = [row['transport']['reliability']['Performance'] for row in events
                     if row.get('event')=='capacity_sample']
        endpoint = phase['endpoints']['server']
        phases[name] = dict(requests=phase['requests'], parallel=phase['parallel'],
                           rs_waits_seconds=endpoint['waits_seconds'],
                           zero_rs_ready_full=endpoint['reliability']['Performance']['ReadyFullNS']==0,
                           samples=len(snapshots),samples_with_rs_ready=sum(row['Ready'] for row in snapshots),
                           samples_below_full=sum(row['RetainedBlocks']<32 for row in snapshots),
                           mux_observation_scope='100ms aggregate Stats only; no sender per-stream ready/credit or WINDOW_UPDATE lifecycle',
                           shutdown_warning=phase['shutdown_warning'], clean=phase['clean_acknowledged_completion'])
    stalls=[]
    for line in (PARENT/'post-local-3.log').read_text().splitlines():
        if '"before_first_actual_carrier_write"' not in line:
            continue
        row=json.loads(line[line.index('{'):])
        stats=row['before_first_actual_carrier_write']
        events=[event for event in stats['Performance']['Events'] if event['Kind']=='enqueue_complete' and event['Retries']>0]
        sizes={event['Sequence']:event['PayloadBytes'] for event in events}
        stalls.append(dict(policy=row['policy'],window=row['window'],source='post-local-3.log TestPackingPreWriteRetryControl',
             direction='local client Family sender -> local server Family receiver, not NL live',
             application_bytes=64*16384,delivered_byte_exact=row['complete'],writer_hold_ms=2200,
             retry_attempts=stats['Retransmissions'],retry_bytes=stats['RetransmittedBytes'],
             ratio_to_delivered_application=stats['RetransmittedBytes']/(64*16384),
             unique_retried_observed=len(sizes),sizes_histogram=dict(collections.Counter(sizes.values())),
             attempts_before_first_write=stats['SendDepth']+stats['Retransmissions'],
             retained_bytes=stats['Performance']['RetainedBytes'],
             media_overhead=None,media_reason='queued PacketEndpoint fixture, not RTP; no complete carrier traffic capture',
             ack_classification='bulk actual writer held; no bulk ACK possible before release. Later ACK-processing latency not captured'))
    save(WORK/'prior-evidence.json',dict(phases=phases,stalls=stalls,source_log_sha256=digest(PARENT/'post-local-3.log')))
    print(json.dumps({'stalls':stalls,'phases':{name:{key:value for key,value in phase.items() if key not in ['requests','parallel']} for name,phase in phases.items()}},indent=2))


if __name__=='__main__':
    main()
