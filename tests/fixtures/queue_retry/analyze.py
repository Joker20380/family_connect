"""Local-only bounded capture analysis; no cross-host latency subtraction."""

import collections
import json
import os
import re
import sys

from prepare import ROOT, WORK
from journal import reassemble, performance_lines

sys.path.insert(0,str(ROOT/'tests/fixtures/mesh_throughput_trace'))
from correlate import reconstruct, correlate


def distribution(values):
    values=sorted(values)
    return dict(count=len(values),median_ms=values[len(values)//2]/1e6 if values else None,
                p95_ms=values[min(len(values)-1,int(len(values)*.95))]/1e6 if values else None,
                max_ms=max(values)/1e6 if values else None)


def analyze(label):
    os.umask(0o077)
    folder=WORK/label
    result=json.loads((folder/'result.json').read_text())
    rows=[];raw_errors=[]
    for number,line in enumerate((folder/'capture-private.jsonl').read_text().splitlines(),1):
        try: rows.append(json.loads(line))
        except ValueError as error:raw_errors.append(dict(line=number,error=str(error)))
    journal,join_errors=reassemble(row['raw'] for row in rows if row['kind']=='journal')
    records,errors=reconstruct(performance_lines(journal))
    joined=correlate({'NL':records})
    events={}
    sessions=collections.defaultdict(list)
    for record in records:
        trace=record['performance']['Trace']
        key=(record['session_tag'],trace['origin'])
        sessions[key].append(record)
        for point in trace['points']:events[(*key,point['i'])]=point
    attempts=collections.defaultdict(dict);logical=collections.defaultdict(list)
    for key,point in events.items():
        if point['kind'].startswith('data_') and point.get('wire'):
            attempt_key=(*key[:2],point['wire'],point['seq'],point.get('attempt',0))
            if point['kind']!='data_carrier_written' or point.get('result')=='ok':
                attempts[attempt_key][point['kind']]=point['ns']
        if point.get('wire'):logical[(*key[:2],point['wire'],point['seq'])].append(point)
    queued_to_start=[];queued_to_done=[];overlap_examples=[];max_pending=0
    for key,points in attempts.items():
        queued=points.get('data_carrier_queued');started=points.get('data_writing');done=points.get('data_carrier_written')
        if queued is not None and started is not None and started>=queued:queued_to_start.append(started-queued)
        if queued is not None and done is not None and done>=queued:queued_to_done.append(done-queued)
    for key,points in logical.items():
        spans=[]
        for attempt_key,attempt in attempts.items():
            if attempt_key[:-1]!=key:continue
            if 'data_carrier_queued' in attempt and 'data_carrier_written' in attempt:
                spans.append((attempt['data_carrier_queued'],attempt['data_carrier_written'],attempt_key[-1]))
        for queued,done,attempt in spans:
            overlap=[other for start,end,other in spans if start<=queued<end]
            max_pending=max(max_pending,len(overlap))
            if len(overlap)>1 and len(overlap_examples)<8:
                overlap_examples.append(dict(session=key[0],sequence=key[-1],attempts=overlap,queued_ns=queued))
    counters=[]
    for key,snapshots in sessions.items():
        first,last=snapshots[0]['performance'],snapshots[-1]['performance']
        start,end=first['Window'],last['Window']
        entry=dict(session=key[0],origin=key[1],snapshot_count=len(snapshots),
                   carrier_queue_frames_max=max(row['performance']['CarrierQueueFrames'] for row in snapshots))
        for name in ('ReadyFullNS','FullNS','WindowOnlyBlockedNS','HeadSACKedBlockedNS','HeadUnconfirmedLaterSACKedBlockedNS','ReleasedBytes','ReleasedBlocks'):
            entry[name+'_delta']=end[name]-start[name]
        for name in ('NewDATA','RetryDATA'):
            entry[name+'_bytes_delta']=sum(end[name]['Bytes'])-sum(start[name]['Bytes'])
            entry[name+'_count_delta']=sum(end[name]['Count'])-sum(start[name]['Count'])
        for name in ('FirstACKNoRetry','FirstACKRecovery','ReleaseNoRetry','ReleaseRecovery'):
            entry[name]=dict(count_delta=sum(end[name]['Count'])-sum(start[name]['Count']),total_ns_delta=end[name]['TotalNS']-start[name]['TotalNS'],max_ns=end[name]['MaxNS'])
        streams={}
        for record in snapshots:
            mux=record['performance']['Mux']
            for stream in mux['Streams']+mux['Retired']:
                if stream['ID']==0:continue
                streams.setdefault(stream['ID'],[]).append(stream)
        entry['mux']=dict(observed_ids=len(streams),max_active=max(len(row['performance']['Mux']['Streams']) for row in snapshots),
            zero_credit_ready_ns_delta=sum(max(row['ZeroCreditReadyNS'] for row in values)-values[0]['ZeroCreditReadyNS'] for values in streams.values()),
            ready_bytes_max=max((row['ReadyBytes'] for values in streams.values() for row in values),default=0),
            retired_count=end.get('RetiredCount',last['Mux']['RetiredCount']))
        entry['mux']['large_streams']=[dict(id=stream_id,handed_bytes_delta=sum(values[-1]['HandedDATA']['Bytes'])-sum(values[0]['HandedDATA']['Bytes']),
            credit_min=min(row['Credit'] for row in values),ready_bytes_max=max(row['ReadyBytes'] for row in values),
            zero_credit_ready_ns_delta=values[-1]['ZeroCreditReadyNS']-values[0]['ZeroCreditReadyNS'])
            for stream_id,values in streams.items() if sum(values[-1]['HandedDATA']['Bytes'])-sum(values[0]['HandedDATA']['Bytes'])>100000]
        counters.append(entry)
    samples=[row for row in rows if row['kind']=='sample']
    cpu=[];memory=[]
    for row in samples:
        fields=row['stat'].split(') ',1)[1].split()
        cpu.append((row['monotonic'],int(fields[11])+int(fields[12])))
        match=re.search(r'VmRSS:\s+(\d+)',row['status'])
        if match:memory.append(int(match[1]))
    request_summary=[]
    for request in result['requests']:
        values=request['metrics'];remote=values.get('remote_ip')
        active=[row for row in samples if request['start_epoch']<=row['epoch']<=request['end_epoch']]
        sockets={line for row in active for line in row['sockets'] if remote and remote+':443' in line}
        request_summary.append(dict(name=request['name'],valid=request['valid'],body_bytes=int(values.get('BODY_BYTES',0)),
            seconds=values.get('time_total'),ttfb_seconds=values.get('time_starttransfer'),mbit_s=request.get('mbit_s'),
            gateway_cloudflare_tcp_connections_observed=len({tuple(line.split()[3:5]) for line in sockets}),
            peak_gateway_cloudflare_sockets=max((sum(bool(remote) and remote+':443' in line for line in row['sockets']) for row in active),default=0)))
    failures=[]
    for value in journal:
        try:
            message=value.get('MESSAGE','')
            if message.startswith('{'):
                event=json.loads(message)
                event=event.get('trace',event)
                if event.get('state')=='FAILED' or 'EXHAUST' in event.get('reason','') or event.get('reason')=='CARRIER_CLOSED':
                    failures.append({key:event[key] for key in ('state','reason','event','stage','timestamp_ms') if key in event})
        except ValueError:pass
    report=dict(label=label,gateway_sha256=result['gateway_sha256'],requests=request_summary,parallel=result['parallel'],
        failures=sum(not row['valid'] for row in result['requests']),application_bytes=result['application_bytes'],
        topology_stable=result['topology_stable'],capture_exit=result['capture_exit'],raw_errors=raw_errors,parser_errors=errors,journal_errors=join_errors,
        correlation_errors=joined['errors'],coverage=joined['completeness'],counter_deltas=counters,
        queued_to_writing=distribution(queued_to_start),queued_to_completed=distribution(queued_to_done),
        max_simultaneous_pending_complete_spans=max_pending,overlap_examples=overlap_examples,
        cpu_ticks_delta=cpu[-1][1]-cpu[0][1] if len(cpu)>1 else None,
        sample_seconds=cpu[-1][0]-cpu[0][0] if len(cpu)>1 else None,rss_max_kib=max(memory,default=0),
        natural_failure_events=failures,cap_records=[row for row in rows if row['kind']=='end'],
        caveats=['Missing ring prefix/interior is not absence of retries.','Durations overlap; do not add layer waits.',
                 'Only matched complete attempt spans count; pending maximum is a lower bound.',
                 'Counter deltas exclude intervals before first snapshot; background streams included.',
                 'No Android trace; no cross-host one-way latency or unique ACK matching.'])
    (folder/'analysis.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({key:report[key] for key in ('label','requests','parallel','failures','queued_to_completed','max_simultaneous_pending_complete_spans','parser_errors')}))


if __name__=='__main__':
    for label in sys.argv[1:]:analyze(label)
