"""Summarize available bounded measurements, including preflight failures."""

import collections
import json
import re
import sys
from prepare import ROOT, WORK, FIXTURE, digest
from session_scope import select_session

sys.path.insert(0,str(ROOT/'tests/fixtures/queue_retry'))
from journal import reassemble

def load(path):return json.loads(path.read_text())
def bytes_in(histogram):return sum(histogram['Bytes'])
def streams(snapshot):
    mux=snapshot['performance']['Mux']
    return {stream['ID']:stream for stream in (mux['Retired'] or [])+(mux['Streams'] or []) if stream['ID']}

def phase(name):
    directory=WORK/name
    if not (directory/'summary.json').exists():return dict(phase=name,status='NOT_RUN')
    raw=[json.loads(line) for line in (directory/'capture-private.jsonl').read_text().splitlines()]
    journal,errors=reassemble([row['raw'] for row in raw if row.get('kind')=='journal'])
    snapshots=[]
    for record in journal:
        try:row=json.loads(record['MESSAGE'])
        except (ValueError,TypeError):continue
        if row.get('event')=='restricted_performance_v1':
            row['epoch']=int(record['__REALTIME_TIMESTAMP'])/1e6;snapshots.append(row)
    observed_tags=sorted({row['session_tag'] for row in snapshots})
    observed_errors={tag:[group[0]['performance']['Mux']['ProtocolErrors'],group[-1]['performance']['Mux']['ProtocolErrors']] for tag in observed_tags for group in [[row for row in snapshots if row['session_tag']==tag]]}
    gate=load(directory/'counter-gate.json') if (directory/'counter-gate.json').exists() else {}
    if gate.get('scope'):
        snapshots=select_session(snapshots,gate['scope'])
    samples=[row for row in raw if row.get('kind')=='sample']
    requests=[json.loads(line) for line in (directory/'requests.jsonl').read_text().splitlines()] if (directory/'requests.jsonl').exists() else []
    result=dict(phase=name,status='MEASURED' if requests else 'PREFLIGHT_STOP_NO_TRAFFIC',summary=load(directory/'summary.json'),preflight=load(directory/'preflight.json'),journal_errors=errors,session_tags=sorted({row['session_tag'] for row in snapshots}),cells=[])
    result.update(observed_session_tags=observed_tags,observed_errors_by_session=observed_errors,owner_scope=gate.get('scope'),process_resource_scope='all gateway sessions, not only owner')
    if not snapshots:return result
    first,last=snapshots[0]['performance'],snapshots[-1]['performance']
    result.update(profile=last['Mux']['Profile'],window=last['Mux']['Window'],protocol_errors=[first['Mux']['ProtocolErrors'],last['Mux']['ProtocolErrors']],mux_retained_high_water=max(row['performance']['Mux']['RetainedHighWater'] for row in snapshots),rss_max_kib=max((int(re.search(r'VmRSS:\s+(\d+)',row['status'])[1]) for row in samples),default=0))
    result['errors_by_session']={tag:[group[0]['performance']['Mux']['ProtocolErrors'],group[-1]['performance']['Mux']['ProtocolErrors']] for tag in result['session_tags'] for group in [[row for row in snapshots if row['session_tag']==tag]]}
    if len(result['session_tags'])!=1:result['protocol_errors']=None
    origin=next(row for row in raw if row.get('kind')=='origin')
    if len(samples)>1:
        ticks=lambda row:sum(int(value) for value in row['stat'].split()[13:15])
        result['cpu_percent_one_core']=(ticks(samples[-1])-ticks(samples[0]))/origin['clock_ticks']/(samples[-1]['epoch']-samples[0]['epoch'])*100
    zero=free=full=0
    for row in snapshots:
        mux,window=row['performance']['Mux'],row['performance']['Window']
        if any(stream['ReadyBytes']>0 and stream['Credit']==0 for stream in mux['Streams'] or []):
            zero+=1
            free+=int(window['SlotSpan']<window['EffectiveWindow'] and not window['LocalWriterBusy'] and window['LocalQueuedFrames']==0)
            full+=int(window['SlotSpan']>=window['EffectiveWindow'])
    result['joint_samples']=dict(ready_zero=zero,rs_free_idle=free,rs_full=full,total=len(snapshots))
    for cell in result['summary']['cells']:
        selected=[row for row in requests if row['name'].startswith('cell-'+str(cell['cell'])+'-')]
        start,end=min(row['start_epoch'] for row in selected),max(row['end_epoch'] for row in selected)
        before=next((row for row in reversed(snapshots) if row['epoch']<start),snapshots[0])
        after=next((row for row in snapshots if row['epoch']>=end),snapshots[-1])
        previous,final=streams(before),streams(after)
        matches=[]
        for identifier,stream in final.items():
            handed=bytes_in(stream['HandedDATA'])-(bytes_in(previous[identifier]['HandedDATA']) if identifier in previous else 0)
            if handed>=selected[0]['intended_bytes']:
                matches.append(stream)
        item=dict(cell,kind='control' if selected[0]['intended_bytes']==65536 else ('single' if cell['flows']==1 else 'parallel'),requests=[dict(valid=row['valid'],intended_bytes=row['intended_bytes'],body_bytes=int(row['metrics'].get('BODY_BYTES',0)),ttfb_s=float(row['metrics']['time_starttransfer']),full_s=float(row['metrics']['time_total']),body_s=float(row['metrics']['time_total'])-float(row['metrics']['time_starttransfer']),connections=int(row['metrics']['num_connects'])) for row in selected],mux_streams=matches,mux_attribution_complete=len(matches)==cell['flows'],rs_scope='whole session bracket includes background and edges')
        older,newer=before['performance']['Window'],after['performance']['Window']
        item['rs_delta']={key:newer[key]-older[key] for key in ('ReadyFullNS','WindowOnlyBlockedNS','HeadUnconfirmedLaterSACKedBlockedNS','HeadSACKedBlockedNS','ReleasedBytes')}
        item['rs_delta'].update({key:bytes_in(newer[key])-bytes_in(older[key]) for key in ('NewDATA','RetryDATA')})
        item['socket_max']=max((sum(any(row['metrics']['remote_ip']+':443' in line for row in selected) for line in sample['sockets']) for sample in samples if start<=sample['epoch']<=end),default=0)
        result['cells'].append(item)
    return result

phases=[phase(name) for name in ('legacy94','smoke95','A1','B1','B1m','B2','A2','A3','B3','return95')]
seals=load(WORK/'final-source-seals.json')
result=dict(source_seals=seals,phases=phases,application_bytes=sum(row.get('summary',{}).get('bytes',0) for row in phases),reserved_bytes=sum(load(path)['intended_bytes'] for path in WORK.glob('traffic-*-reservation.json')),limit_bytes=64*1024*1024,per_request_limit_seconds=150,synthetic_byte_exact_not_physical_origin_integrity=True)
if (WORK/'off-control/summary.json').exists():
    result['off_control']=load(WORK/'off-control/summary.json')
    result['application_bytes']+=result['off_control']['bytes']
if (WORK/'final-off-readback.json').exists():
    runtime=load(WORK/'final-off-readback.json')
    result['final_runtime']={key:runtime[key] for key in ('utc','gateway','phone')}
result['decision']=dict(negotiation_and_legacy_compatibility='PASS',credit128_correctness='LOCAL_PASS_PHYSICAL_NOT_TESTED',physical_single_flow_gain='NOT_EVALUATED_EXTERNAL_UI_BLOCKER',credit128_enabled=False,required_action='User-operated ordinary Disconnect/Connect for each profile boundary; MIUI denies shell INJECT_EVENTS. No bypass attempted after explicit denial.',tester_version=94)
if (WORK/'manual-continuation-result.json').exists():
    continuation=load(WORK/'manual-continuation-result.json')
    result['manual_continuation']=continuation
    result['decision']=continuation['decision']
    runtime=load(WORK/continuation['final_readback'])
    result['final_runtime']={key:runtime[key] for key in ('utc','gateway','phone')}
destination=ROOT/'docs/releases/2026-10-20-mesh-mux-credit.negotiated.json'
text=json.dumps(result,indent=2)+'\n'
if destination.exists():
    import subprocess
    patch='*** Begin Patch\n*** Delete File: '+str(destination)+'\n*** Add File: '+str(destination)+'\n'+''.join('+'+line+'\n' for line in text.splitlines())+'*** End Patch\n'
else:
    import subprocess
    patch='*** Begin Patch\n*** Add File: '+str(destination)+'\n'+''.join('+'+line+'\n' for line in text.splitlines())+'*** End Patch\n'
subprocess.run(['apply_patch',patch],check=True,stdout=subprocess.DEVNULL)
print(json.dumps(dict(application_bytes=result['application_bytes'],phases=[dict(phase=row['phase'],status=row['status'],profile=row.get('profile'),protocol_errors=row.get('protocol_errors')) for row in phases])))
