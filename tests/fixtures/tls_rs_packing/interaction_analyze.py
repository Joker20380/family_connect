"""Offline bounded-observation analysis; never sum overlapping waits or host clocks."""
import collections
import importlib.util
import json
import statistics
from interaction_prepare import ROOT, WORK, save, write


def records(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []


def distribution(values):
    return dict(n=len(values),median=statistics.median(values) if values else None,maximum=max(values) if values else None)


def lifecycle(observation):
    pending,selected={},{}
    queued,write_return=[],[]
    for event in observation.get('Events',[]):
        stream=event['ID']
        if event['Kind']=='read_credit_pending' and event['Pending']==event['Bytes']:
            pending[stream]=event['NS']
        if event['Kind']=='credit_selected':
            if stream in pending:queued.append((event['NS']-pending.pop(stream))/1e6)
            selected[stream]=event['NS']
        if event['Kind']=='writer_returned' and event['Bytes']==8 and stream in selected:
            write_return.append((event['NS']-selected.pop(stream))/1e6)
    return dict(credit_pending_to_select_ms=distribution(queued),select_to_family_write_return_ms=distribution(write_return),
                events=len(observation.get('Events',[])),dropped=observation.get('Dropped'),
                writer_send_seconds=observation.get('WriterSendNS',0)/1e9,
                writer_send_max_ms=observation.get('WriterSendMaxNS',0)/1e6,
                writer_lock_seconds=observation.get('WriterLockNS',0)/1e9,
                writer_lock_max_ms=observation.get('WriterLockMaxNS',0)/1e6)


def retries(events,stats):
    observed={}
    maximum=0
    for row in events:
        perf=(row.get('transport',{}).get('reliability') or {}).get('Performance',{})
        maximum=max(maximum,perf.get('EventCount',0))
        for event in perf.get('Events',[]):
            if event['Kind']:observed[(event['NodeNS'],event['Kind'],event['Sequence'],event['Retries'])]=event
    retried=[event for event in observed.values() if event['Kind']=='retry']
    first_ack={}
    for event in observed.values():
        if event['Kind']=='first_ack':first_ack[event['Sequence']]=event['NodeNS']
    after_ack=[event for event in retried if event['Sequence'] in first_ack and event['NodeNS']>first_ack[event['Sequence']]]
    unique={event['Sequence']:event['PayloadBytes'] for event in retried}
    media={}
    for row in events:
        event=row.get('entry',{})
        if event.get('stage')=='tx' and event.get('fragment',0)==0 and event.get('rs_seq',0)>0:
            media[(event.get('sender'),event.get('message'))]=event['rs_seq']
    counts=collections.Counter(media.values())
    payload=sum(stats.get('Performance',{}).get('NewDATA',{}).get('Bytes',[]))
    return dict(attempts=stats.get('Retransmissions'),retry_bytes=stats.get('RetransmittedBytes'),unique_ciphertext_bytes=payload,
                retry_to_unique_ratio=stats.get('RetransmittedBytes',0)/payload if payload else None,
                observed_retry_events=len(retried),observed_unique_retried=len(unique),observed_sizes=dict(collections.Counter(unique.values())),
                observed_retry_after_first_ack=len(after_ack),event_coverage=dict(unique=len(observed),total=maximum,complete=len(observed)==maximum),
                local_tx_retry_attempts_excluding_sequence0=sum(count-1 for count in counts.values()),local_tx_unique_repeated_excluding_sequence0=sum(count>1 for count in counts.values()),
                limitation='Q0 enqueue is not local-write completion. Bounded RS event ring may have gaps; post-ACK queued physical sends and ACK ingress/processing delay not fully observable. Do not infer packet loss from retry bytes.')


def local():
    result={}
    for path in sorted((WORK/'local-unrestricted').glob('*.json')):
        if path.name in ['inputs.json','result.json']:continue
        row=json.loads(path.read_text())
        samples=row['samples']
        active=[sample for sample in samples if any(stream['ID']==9 for stream in sample['mux']['Streams'] or []) and sample['ns']<=row['seconds']*1e9]
        ready=[sample for sample in active if any(stream['ID']==9 and stream['ReadyBytes']>0 for stream in sample['mux']['Streams'])]
        zero=[sample for sample in ready if any(stream['ID']==9 and stream['Credit']==0 for stream in sample['mux']['Streams'])]
        idle=[sample for sample in zero if not sample['rs']['Ready'] and sample['rs']['RetainedBlocks']<32]
        start=.1
        overlap=[]
        for duration in row['loaded']:
            if start<row['seconds']:overlap.append(duration)
            start+=duration
        result[path.stem]=dict(scenario=row['scenario'],variant=row['variant'],seconds=row['seconds'],mbit_s=row['mbit_s'],error=row['error'],
             source_bytes=row['source_bytes'],idle_seconds=distribution(row['idle']),concurrent_start_seconds=distribution(row['loaded']),started_during_bulk_seconds=distribution(overlap),
             selected_stream=9,samples=dict(active=len(active),source_ready=len(ready),zero_credit=len(zero),zero_credit_and_rs_not_full_or_ready=len(idle)),
             client_lifecycle=lifecycle(row['client_events']),server_lifecycle=lifecycle(row['server_events']),
             client_packing=row['client_packing'],server_packing=row['server_packing'],server_link=row['server_link'],
             rs_ready_full_ns=row['server_rs']['Performance']['ReadyFullNS'])
    return result


def live():
    spec=importlib.util.spec_from_file_location('capacity_summary',ROOT/'tests/fixtures/mesh_capacity/summarize.py')
    summary=importlib.util.module_from_spec(spec);spec.loader.exec_module(summary)
    phases={}
    for reservation in sorted(WORK.glob('*/reservation.json'),key=lambda path:path.stat().st_mtime):
        directory=reservation.parent
        if not (directory/'phase-result.json').exists():continue
        result=json.loads((directory/'phase-result.json').read_text())
        config=json.loads(reservation.read_text())
        sides={side:records(directory/(prefix+'peer.jsonl')) for side,prefix in [('client',''),('server','server-')]}
        requests=[row for row in sides['client'] if row.get('event')=='host_request']
        compact=[{key:row[key] for key in ['name','passed','full_seconds','start_ns','end_ns','received','sha256','size','stream']} for row in requests]
        single=next((row for row in requests if row['name']=='single'),None)
        parallel=[row for row in requests if row['name'].startswith('parallel_')]
        parallel_seconds=(max(row['end_ns'] for row in parallel)-min(row['start_ns'] for row in parallel))/1e9 if len(parallel)==2 else None
        controls={}
        for kind in ['small_idle','small_loaded']:
            values=[row for row in requests if row['name'].startswith(kind)]
            overlap=[row for row in values if single and row['start_ns']>=single['start_ns'] and row['end_ns']<=single['end_ns']]
            controls[kind]=dict(full_seconds=distribution([row['full_seconds'] for row in values if row['passed']]),errors=sum(not row['passed'] for row in values),fully_inside_single=len(overlap))
        phase=dict(result=result,config=config['config'],reservation=config['application_reserved'],requests=compact,small=controls,
             single_seconds=single['full_seconds'] if single else None,single_mbit_s=single['received']*8/single['full_seconds']/1e6 if single else None,
             parallel_seconds=parallel_seconds,parallel_mbit_s=sum(row['received'] for row in parallel)*8/parallel_seconds/1e6 if parallel_seconds else None,
             endpoints={},clean=False)
        for side,prefix in [('client',''),('server','server-')]:
            events=sides[side]
            endpoint=summary.endpoint(events,records(directory/(prefix+'resources.jsonl')))
            final=next((row for row in reversed(events) if row.get('event')=='mux_lab_final'),{})
            active=[]
            if single:
                stream_id=single['stream']['ID']
                for row in events:
                    if row.get('event')=='mux_lab_sample':
                        stream=next((stream for stream in row.get('performance',{}).get('Streams') or [] if stream['ID']==stream_id),None)
                        if stream:active.append((row,stream))
            ready=[pair for pair in active if pair[1]['ReadyBytes']>0]
            zero=[pair for pair in ready if pair[1]['Credit']==0]
            nonfull=[pair for pair in zero if not pair[0]['pressure']['ready'] and pair[0]['pressure']['depth']<32]
            retired=next((stream for stream in final.get('performance',{}).get('Retired',[]) if single and stream['ID']==single['stream']['ID']),None)
            packing=next((row['packing'] for row in events if row.get('event')=='p_drained'),None)
            endpoint.update(lifecycle=lifecycle(final.get('observation',{})),selected_stream=single['stream']['ID'] if single else None,
                            selected_retired=retired,selected_samples=dict(active=len(active),source_ready=len(ready),zero_credit=len(zero),zero_credit_and_rs_not_full_or_ready=len(nonfull)),
                            retry=retries(events,endpoint.get('reliability') or {}),packing=packing,
                            protocol_errors=max([row.get('mux',{}).get('ProtocolErrors',0) for row in events],default=0),
                            final_mux=final.get('mux'),trace=next((row for row in events if row.get('event')=='media_trace_end'),None))
            phase['endpoints'][side]=endpoint
        phase['clean']=not result['error'] and (directory/'two-end-proof.json').exists() and all(not endpoint['protocol_errors'] for endpoint in phase['endpoints'].values())
        phases[directory.name]=phase
    return phases


def main():
    result=dict(local=local(),live=live())
    result['source_reserved']=sum(row['reservation'] for row in result['live'].values())
    result['media_charged']=sum(row['result']['wire_charged'] for row in result['live'].values())
    write(WORK/'interaction-analysis.json',json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(source_reserved=result['source_reserved'],media_charged=result['media_charged'],phases={name:{key:row[key] for key in ['clean','single_seconds','single_mbit_s','parallel_seconds','parallel_mbit_s','small']} for name,row in result['live'].items()}),indent=2))


if __name__=='__main__':main()
