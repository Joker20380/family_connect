"""Post-run bounded trace correlation; no wall-clock one-way subtraction."""
import collections
import importlib.util
import json
import statistics
from prepare import ROOT, BASE, WORK, FIX, patch_file


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []


def key(event):
    return tuple(event.get(name,0) for name in ['sender','message','fragment'])


def signed(value):
    return (value+2**31)%2**32-2**31


def analyze(directory):
    endpoints={side:rows(directory/(prefix+'peer.jsonl')) for side,prefix in [('client',''),('server','server-')]}
    media={side:[row['entry'] for row in events if row.get('event')=='media'] for side,events in endpoints.items()}
    sender,receiver=media['server'],media['client']
    tx={}
    for event in sender:
        if event['stage']=='tx' and event.get('kind')=='data' and event.get('start'):
            tx.setdefault(key(event),event)
    boundaries={stage:{} for stage in ['rx','ordered','assembled']}
    for event in receiver:
        stage=event['stage']
        if stage in boundaries and event.get('kind')=='data' and (event.get('start') or stage=='assembled'):
            boundaries[stage].setdefault(key(event),event)
    keep=[];seen=set()
    for event in sender:
        identity=(event.get('ssrc'),event.get('seq'),event.get('ts'))
        if event['stage']=='tx' and event.get('kind')=='keepalive' and identity not in seen:
            keep.append(event);seen.add(identity)
    complete=next((row for row in endpoints['client'] if row.get('event')=='capacity_received'),{})
    missing=set(complete.get('missing_ids',[]))
    messages={event.get('app_id',0):identity[:2] for identity,event in tx.items() if event.get('app_kind')==3 and identity[2]==0}
    results=[]
    for app_id,identity in sorted(messages.items()):
        fragments=[(item,event) for item,event in tx.items() if item[:2]==identity]
        first=min(event['ns'] for _,event in fragments)
        previous=max((event['ns'] for event in keep if event['ns']<=first),default=None)
        results.append(dict(app_id=app_id,missing=app_id in missing,first_tx_ns=first,since_keepalive_ms=(first-previous)/1e6 if previous else None,fragments=[dict(fragment=item[2],tx_ns=event['ns'],tx_timestamp=event.get('ts'),tx_first_sequence=event.get('seq'),**{stage:boundaries[stage].get(item) for stage in boundaries}) for item,event in sorted(fragments)]))
    timestamps=collections.Counter()
    for identity,event in tx.items():
        if identity in boundaries['rx']:
            timestamps[(boundaries['rx'][identity].get('ts',0)-event.get('ts',0))%2**32]+=1
    sequence_offsets=collections.Counter((boundaries['rx'][identity].get('seq',0)-event.get('seq',0))%65536 for identity,event in tx.items() if identity in boundaries['rx'])
    packet_index={}
    for side,events,stage in [('tx',sender,'tx'),('rx',receiver,'rx')]:
        packet_index[side]={}
        for event in events:
            if event['stage']==stage:packet_index[side].setdefault(event.get('ts',0),{}).setdefault(event.get('seq',0),event)
    if len(timestamps)==1 and sum(timestamps.values())>=20:
        stamp_offset=next(iter(timestamps))
        for row in results:
            for fragment in row['fragments']:
                stamp=fragment['tx_timestamp']
                sent_packets=packet_index['tx'].get(stamp,{})
                read_packets=packet_index['rx'].get((stamp+stamp_offset)%2**32,{})
                fragment['local_written_unique_packets']=len(sent_packets)
                fragment['reader_packets_by_learned_timestamp_offset']=len(read_packets)
                fragment['timestamp_match_inferred_not_identity_proof']=True
                fragment['payload_multiset_equal']=collections.Counter(item.get('hash') for item in sent_packets.values())==collections.Counter(item.get('hash') for item in read_packets.values())
                fragment['tx_markers']=sum(item.get('marker',False) for item in sent_packets.values())
                fragment['rx_markers']=sum(item.get('marker',False) for item in read_packets.values())
                for side,packets in [('tx',sent_packets),('rx',read_packets)]:
                    fragment[side+'_span_ms']=(max(item['ns'] for item in packets.values())-min(item['ns'] for item in packets.values()))/1e6 if packets else None
    spans={}
    for period,predicate in [('first30',lambda number:number<30),('last30',lambda number:number>=complete.get('expected',0)-30)]:
        fragments=[fragment for row in results if predicate(row['app_id']) for fragment in row['fragments'] if fragment.get('payload_multiset_equal') and fragment.get('local_written_unique_packets',0)>1]
        spans[period]={side+'_median_ms':statistics.median(fragment[side+'_span_ms'] for fragment in fragments) if fragments else None for side in ['tx','rx']}
        spans[period]['matched_complete_frames']=len(fragments)
    reports=[event for event in sender if event['stage']=='rtcp_tx' and event.get('kind')=='*rtcp.SenderReport' and event.get('count',0)]
    report_jumps=[]
    for before,after in zip(reports,reports[1:]):
        if before.get('ssrc')!=after.get('ssrc'):continue
        elapsed=(after['ns']-before['ns'])/1e9
        report_jumps.append(dict(ns=after['ns'],elapsed=elapsed,rtp_elapsed=signed(after.get('ts',0)-before.get('ts',0))/90000,ntp_elapsed=(after.get('ntp',0)-before.get('ntp',0))/2**32))
    local_stages=collections.Counter(event['stage'] for event in receiver)
    result=dict(phase=directory.name,complete=complete,tx_fragments=len(tx),boundary_fragments={name:len(set(tx)&set(value)) for name,value in boundaries.items()},missing_messages=[row for row in results if row['missing']],messages=results,keepalive_tx=keep,keepalive_rx=[event for event in receiver if event['stage']=='rx' and event.get('kind')=='keepalive'],timestamp_rewrite_offsets=[dict(offset=offset,count=count) for offset,count in timestamps.most_common()],sequence_rewrite_offsets=[dict(offset=offset,count=count) for offset,count in sequence_offsets.most_common()],sender_reports=report_jumps,receiver_stages=dict(local_stages),trace_end={side:[row for row in events if row.get('event')=='media_trace_end'] for side,events in endpoints.items()},mux={side:[row for row in events if row.get('event','').startswith('mux_lab_') and (row.get('mux',{}).get('ProtocolErrors') or row['event']!='mux_lab_sample')] for side,events in endpoints.items()})
    result['complete_frame_spans']=spans
    result['bulk_boundaries']={stage:sum(fragment[stage] is not None for row in results for fragment in row['fragments']) for stage in ['rx','ordered','assembled']}
    result['bulk_locally_written_messages']=sum(len(row['fragments'])==3 and all(fragment.get('local_written_unique_packets')==(7 if fragment['fragment']<2 else 1) and fragment.get('tx_markers')==1 for fragment in row['fragments']) for row in results)
    patch_file(directory/'media-analysis.json',json.dumps(result,indent=2))
    print(json.dumps(dict(phase=directory.name,count=complete.get('count'),expected=complete.get('expected'),missing=complete.get('missing_ids'),boundary=result['boundary_fragments'],missing_phase_ms=[round(row['since_keepalive_ms'],2) for row in results if row['missing'] and row['since_keepalive_ms'] is not None],sr_negative=sum(row['rtp_elapsed']<0 for row in report_jumps),sr_max_error=max([abs(row['rtp_elapsed']-row['elapsed']) for row in report_jumps],default=0),rx_stages=dict(local_stages),overflow={side:result['trace_end'][side][-1]['overflow'] if result['trace_end'][side] else None for side in endpoints})))
    return result


def previous():
    old=json.loads((BASE/'summary.json').read_text())
    results={}
    for name,phase in old['phases'].items():
        received=phase.get('received')
        result=dict(mode=phase['config']['Mode'],completed=phase['result']['completed'],clean_protocol=name!='P816')
        if received:
            result.update(bytes=received['useful_bytes'],count=received['count'],expected=received['expected'],receiver_seconds=received['last_seconds'],mbit=received['useful_bytes']*8/received['last_seconds']/1e6)
            if name.startswith('C'):
                missing=received['missing_ids'];groups=[]
                for number in missing:
                    if not groups or number!=groups[-1][-1]+1:groups.append([])
                    groups[-1].append(number)
                rate=phase['config']['Rate'];size=phase['config']['Sizes'][0]
                starts=[group[0]*size/rate for group in groups]
                result.update(missing_groups=groups,scheduled_group_starts=starts,scheduled_group_intervals=[right-left for left,right in zip(starts,starts[1:])],limitation='scheduled offer offsets, NOT actual loss timestamps; original trace lacks packet identities')
        if phase['requests']:result['P_requests']=[dict(name=row['name'],bytes=row['received'],seconds=row['full_seconds'],mbit=row['received']*8/row['full_seconds']/1e6,protocol_before=row['mux_before']['ProtocolErrors'],protocol_after=row['mux_after']['ProtocolErrors']) for row in phase['requests']]
        results[name]=result
    patch_file(WORK/'parent-recalculation.json',json.dumps(results,indent=2))


if __name__=='__main__':
    previous()
    for path in sorted(WORK.glob('*/phase-result.json'),key=lambda path:path.stat().st_mtime):analyze(path.parent)
    spec=importlib.util.spec_from_file_location('summary',ROOT/'tests/fixtures/mesh_capacity/summarize.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.main()
