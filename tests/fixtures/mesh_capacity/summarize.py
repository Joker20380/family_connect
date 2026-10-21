"""Offline, receiver-monotonic results; retain every failure and reservation."""
import json
from pathlib import Path
import statistics

from prepare import WORK, patch_file


def records(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []


def median(values):
    return statistics.median(values) if values else None


def endpoint(events,resources):
    samples=[row['transport'] for row in events if 'transport' in row]
    summary=next((row for row in reversed(events) if row.get('event')=='summary'),{})
    if not samples:return dict(summary=summary)
    stats=samples[-1]
    reliability=next((row.get('reliability') for row in reversed(samples) if row.get('reliability')),None)
    perf=reliability.get('Performance',{}) if reliability else {}
    result=dict(wire=stats.get('lab_wire'),carrier=stats.get('carrier'),histograms=next((row['histograms'] for row in reversed(samples) if 'histograms' in row),{}),cpu_user_s=summary.get('cpu_user_s'),cpu_system_s=summary.get('cpu_system_s'),max_rss_kib=summary.get('max_rss_kib'),max_send_queue=max(row.get('send_queue_frames',0) for row in samples),max_receive_queue=max(row.get('receive_queue_messages',0) for row in samples),reliability=reliability,waits_seconds={name:perf[name]/1e9 for name in ['FullNS','ReadyFullNS','WindowOnlyBlockedNS','HeadSACKedBlockedNS','HeadUnconfirmedLaterSACKedBlockedNS'] if name in perf},max_retained=max([(row.get('reliability') or {}).get('Performance',{}).get('RetainedBytes',0) for row in samples]),max_unconfirmed=max([(row.get('reliability') or {}).get('Performance',{}).get('UnconfirmedBytes',0) for row in samples]),max_sacked=max([(row.get('reliability') or {}).get('Performance',{}).get('SACKedBytes',0) for row in samples]))
    result['selected_paths']=[]
    result['max_sampled_head_age_seconds']=max([(row.get('reliability') or {}).get('Performance',{}).get('HeadAgeNS',0) for row in samples])/1e9
    result['max_sampled_assembly_pending']=max([row.get('carrier',{}).get('Delivery',{}).get('assembly',{}).get('pending',0) for row in samples])
    for snapshot in reversed(samples):
        candidates=[]
        for connection in ['publisher','subscriber']:
            values=snapshot.get(connection,[])
            lookup={row.get('id'):row for row in values}
            for row in values:
                if row.get('type')=='candidate-pair' and row.get('nominated'):
                    candidates.append(dict(connection=connection,pair=row,local=lookup.get(row.get('localCandidateId')),remote=lookup.get(row.get('remoteCandidateId'))))
        if candidates:result['selected_paths']=candidates;break
    if len(resources)>1:
        first,last=resources[0],resources[-1]
        seconds=last['monotonic']-first['monotonic']
        result['resource_seconds']=seconds
        def counts(text):return {line.split()[0]:int(line.split()[1]) for line in text.splitlines() if len(line.split())==2}
        result['cgroup_delta']={name:counts(last.get('cpu.stat','')).get(name,0)-counts(first.get('cpu.stat','')).get(name,0) for name in ['usage_usec','nr_periods','nr_throttled','throttled_usec']}
        old=[int(value) for value in first['cpu'][0].split()[1:]];new=[int(value) for value in last['cpu'][0].split()[1:]]
        delta=[right-left for left,right in zip(old,new)];total=sum(delta[:8])
        result['host_steal_percent']=100*delta[7]/total if total else None
        result['host_busy_percent']=100*(total-delta[3]-delta[4])/total if total else None
        result['thread_peak_cpu_one_core_percent']=0
        result['thread_peak_wait_ms_per_second']=0
        for before,after in zip(resources,resources[1:]):
            interval=after['monotonic']-before['monotonic']
            for tid,thread in after.get('threads',{}).items():
                previous=before.get('threads',{}).get(tid)
                if not previous:continue
                old=[int(value) for value in previous['schedstat'].split()];new=[int(value) for value in thread['schedstat'].split()]
                result['thread_peak_cpu_one_core_percent']=max(result['thread_peak_cpu_one_core_percent'],100*(new[0]-old[0])/1e9/interval)
                result['thread_peak_wait_ms_per_second']=max(result['thread_peak_wait_ms_per_second'],(new[1]-old[1])/1e6/interval)
        result['gc_resources']=[row for row in events if row.get('event')=='resources']
    return result


def main():
    phases={}
    for receipt in sorted(WORK.glob('*/reservation.json'),key=lambda path:path.stat().st_mtime):
        directory=receipt.parent
        reservation=json.loads(receipt.read_text());config=reservation['config']
        client=records(directory/'peer.jsonl');server=records(directory/'server-peer.jsonl')
        events=client+server
        result=json.loads((directory/'phase-result.json').read_text()) if (directory/'phase-result.json').exists() else {}
        item=dict(config=config,result=result,reservation=reservation,endpoints={name:endpoint(rows,records(directory/filename)) for name,rows,filename in [('client',client,'resources.jsonl'),('server',server,'server-resources.jsonl')]})
        for event,name in [('capacity_received','received'),('capacity_sent','sent'),('capacity_confirmed','confirmed'),('capacity_complete','complete')]:
            item[name]=next((row for row in events if row.get('event')==event),None)
        if item['received']:
            received=item['received'];item['delivery_fraction']=received['count']/received['expected']
            item['received_mbit_s_to_last']=received['useful_bytes']*8/received['last_seconds']/1e6 if received['last_seconds'] else 0
            item['received_mbit_s_observation']=received['useful_bytes']*8/received['observation_seconds']/1e6
            if config['Mode']=='C':
                arrivals=received['arrivals_seconds'];size_sum=sum(config['Sizes'])/len(config['Sizes'])-32
                item['during_offered_interval_mbit_s']=sum(value<=config['Seconds'] for value in arrivals)*size_sum*8/config['Seconds']/1e6 if len(set(config['Sizes']))==1 else None
            item['loaded_rtt_median_s']=median(received.get('loaded_rtt_seconds') or [])
        item['idle_rtt_median_s']=median([row['rtt_seconds'] for row in events if row.get('event')=='capacity_probe'])
        item['requests']=[row for row in events if row.get('event')=='host_request']
        for row in item['requests']:row['goodput_mbit_s']=row['received']*8/row['full_seconds']/1e6
        parallel=[row for row in item['requests'] if row['name'].startswith('parallel_')]
        if len(parallel)==2:
            seconds=(max(row['end_ns'] for row in parallel)-min(row['start_ns'] for row in parallel))/1e9
            item['parallel']=dict(seconds=seconds,goodput_mbit_s=sum(row['received'] for row in parallel)*8/seconds/1e6,complete=all(row['passed'] for row in parallel))
        phases[directory.name]=item
    summary=dict(phases=phases,application_reserved=sum(row['reservation']['application_reserved'] for row in phases.values()),wire_charged=sum(row['result'].get('wire_charged',row['reservation']['wire_reserved']) for row in phases.values()))
    patch_file(WORK/'summary.json',json.dumps(summary,indent=2))
    for name,item in phases.items():
        sender=item['endpoints']['client' if item['config']['Reverse'] else 'server']
        rs=sender.get('reliability') or {}
        print(json.dumps(dict(phase=name,error=item['result'].get('error'),mode=item['config']['Mode'],fraction=item.get('delivery_fraction'),mbit_s=item.get('received_mbit_s_to_last'),retry_bytes=rs.get('RetransmittedBytes'),effective=(rs.get('Performance') or {}).get('EffectiveWindow'),ready_full=sender.get('waits_seconds',{}).get('ReadyFullNS'),assembly=item['endpoints']['client' if not item['config']['Reverse'] else 'server'].get('carrier',{}).get('Delivery',{}).get('assembly'),single=[row['goodput_mbit_s'] for row in item['requests'] if row['name']=='single'],parallel=item.get('parallel')),default=str))
    print(json.dumps({key:value for key,value in summary.items() if key!='phases'}))


if __name__=='__main__':main()
