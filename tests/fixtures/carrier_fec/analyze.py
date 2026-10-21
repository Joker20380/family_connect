import collections
import importlib.util
import json
import statistics
from lab import ROOT, WORK, save
import interaction_analyze as prior


def distribution(values):
    return dict(n=len(values),median=statistics.median(values) if values else None,maximum=max(values) if values else None)


def main():
    prior.WORK=WORK
    phases=prior.live()
    for phase,row in phases.items():
        directory=WORK/phase
        for side,prefix in [('client',''),('server','server-')]:
            events=prior.records(directory/(prefix+'peer.jsonl'))
            snapshots=[event['transport'] for event in events if 'lab_fragments' in event.get('transport',{})]
            endpoint=row['endpoints'][side]
            endpoint['fragment']=snapshots[-1]['lab_fragments'] if snapshots else None
            endpoint['rate']=snapshots[-1]['lab_rate'] if snapshots else None
            endpoint['capacity_events']=[event for event in events if event.get('event') in ['capacity_sent','capacity_received','capacity_complete','capacity_confirmed','capacity_probe','capacity_config']]
            endpoint['error_events']=[event for event in events if event.get('event')=='error']
            media=[event['entry'] for event in events if event.get('event')=='media']
            transmitted=[event for event in media if event['stage']=='tx']
            identities=collections.Counter((event.get('ssrc',0),event.get('seq',0)) for event in transmitted)
            endpoint['rtp_retransmitted_observed']=sum(count-1 for count in identities.values())
            source=[event for event in transmitted if event.get('kind')=='data' and event.get('start')]
            repairs=[event for event in transmitted if event.get('kind')=='repair' and event.get('start')]
            assembled=[event for event in media if event['stage']=='assembled']
            endpoint['observed_parts']=dict(tx_source=len(source),tx_repair=len(repairs),rx_assembled_source=sum(event.get('kind')=='data' for event in assembled),rx_assembled_repair=sum(event.get('kind')=='repair' for event in assembled),max_payload=max((event.get('size',0) for event in transmitted),default=0),one_packet_parts=sum(event.get('marker',False) for event in source+repairs),identified_parts=len(source)+len(repairs))
            endpoint['queue_samples']=dict(max_frames=max((snap['send_queue_frames'] for snap in snapshots),default=0),tail_frames=snapshots[-1]['send_queue_frames'] if snapshots else None)
            endpoint['srtcp_extra_upper_bytes']=4*sum(event['stage']=='rtcp_tx' and event.get('kind')!='RRblock' for event in media)
            if row['config']['FragmentMode']!='L':
                for key in ['local_tx_retry_attempts_excluding_sequence0','local_tx_unique_repeated_excluding_sequence0']:endpoint['retry'][key]=None
                endpoint['retry']['limitation']+=' FCF2 media events do not export RS sequence, so physical media-to-RS retry attribution is unknown, not zero.'
        for sender,receiver,prefix,other_prefix in [('server','client','server-',''),('client','server','','server-')]:
            sent=prior.records(directory/(prefix+'peer.jsonl'));received=prior.records(directory/(other_prefix+'peer.jsonl'))
            def parts(events,stage):
                return {(event.get('sender'),event.get('message'),event.get('fragment',0),event['kind']) for row in events if row.get('event')=='media' for event in [row['entry']] if event['stage']==stage and event.get('kind') in ['data','repair'] and (stage=='assembled' or event.get('start'))}
            transmitted=parts(sent,'tx');raw=parts(received,'rx');assembled=parts(received,'assembled')
            complete=all(endpoint.get('trace') and endpoint['trace'].get('overflow')==0 for endpoint in [row['endpoints'][sender],row['endpoints'][receiver]])
            row['endpoints'][sender]['matched_parts']=dict(coverage_complete=complete,tx_unique=len(transmitted),missing_at_raw_rx=len(transmitted-raw) if complete else None,not_assembled=len(transmitted-assembled) if complete else None,source_not_assembled=sum(part[-1]=='data' for part in transmitted-assembled) if complete else None,repair_not_assembled=sum(part[-1]=='repair' for part in transmitted-assembled) if complete else None,scope='whole session including shutdown tail; no one-way clock subtraction; L start-packet absence is not whole-RTP loss')
            if row['config']['FragmentMode']=='SF' and complete:
                groups=collections.defaultdict(set);counts={};received_groups=collections.defaultdict(set)
                for events,stage,target in [(sent,'tx',groups),(received,'rx',received_groups)]:
                    for record in events:
                        event=record.get('entry',{})
                        if record.get('event')!='media' or event.get('stage')!=stage or event.get('kind') not in ['data','repair'] or not event.get('start'):continue
                        key=(event.get('sender'),event.get('message'),event.get('fragment',0)//10)
                        target[key].add(event.get('fragment',0)%10)
                        if stage=='tx':counts[key]=event.get('total')
                histogram=collections.Counter();recoverable=0;unrecoverable=0
                for key,symbols in groups.items():
                    count=counts[key]
                    if count is None or symbols!=set(range(count+2)):continue
                    absent=symbols-received_groups[key]
                    histogram[len(absent)]+=1
                    if any(index<count for index in absent):
                        if len(absent)<=2:recoverable+=1
                        else:unrecoverable+=1
                row['endpoints'][sender]['matched_fec_groups']=dict(absent_symbol_histogram=dict(sorted(histogram.items())),source_missing_within_two=recoverable,source_missing_beyond_two=unrecoverable,scope='fully transmitted protected groups only, whole-session endpoint matching; not physical network loss provenance')
        if row['config']['Mode']!='P':
            received=[event for event in row['endpoints']['client']['capacity_events'] if event['event']=='capacity_received']
            complete=[event for event in row['endpoints']['server']['capacity_events'] if event['event']=='capacity_confirmed']
            row['raw_or_reliable']=dict(received=received,confirmed=complete)
            row['clean']=not row['result']['error'] and bool(received) and bool(complete) and not received[-1]['corrupt'] and received[-1]['count']==received[-1]['expected'] and complete[-1]['count']==complete[-1]['expected']
        print(phase,row['config']['FragmentMode'],row['clean'],row['single_mbit_s'],row['parallel_mbit_s'],row['result']['wire_charged'],flush=True)
    target=WORK/'analysis.json'
    if target.exists():target.rename(WORK/('analysis-'+str(len(list(WORK.glob('analysis*.json'))))+'.json'))
    save(target,dict(phases=phases,source=sum(row['reservation'] for row in phases.values()),media=sum(row['result']['wire_charged'] for row in phases.values())))


if __name__=='__main__':main()
