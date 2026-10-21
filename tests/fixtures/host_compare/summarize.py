"""Offline projection of same-clock, byte-exact isolated host comparison records."""
import datetime
import json
from pathlib import Path
import subprocess

from prepare import WORK


def records(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []


def main():
    phases={}
    reserved=0
    for phase in ['A1','B1','B2','A2']:
        root=WORK/phase
        if not root.exists():
            phases[phase]=dict(status='NOT_RUN');continue
        reservation=json.loads((root/'reservation.json').read_text()) if (root/'reservation.json').exists() else {}
        reserved+=reservation.get('intended_application_bytes',0)
        client=records(root/'peer.jsonl');server=records(root/'server-peer.jsonl')
        requests=[]
        for row in client:
            if row.get('event')!='host_request':continue
            item={key:row.get(key) for key in ['name','operation','size','received','sha256','passed','error','start_ns','end_ns','full_seconds','open_seconds','first_byte_seconds','body_seconds']}
            item['stream']=row.get('stream')
            item['goodput_mbit_s']=row['received']*8/row['full_seconds']/1e6 if row['operation']=='D' else None
            item['protocol_errors_before_after']=[row['mux_before']['ProtocolErrors'],row['mux_after']['ProtocolErrors']]
            requests.append(item)
        parallel=[row for row in requests if row['name'].startswith('parallel_')]
        aggregate=None
        if len(parallel)==2:
            interval=(max(row['end_ns'] for row in parallel)-min(row['start_ns'] for row in parallel))/1e9
            aggregate=dict(seconds=interval,received=sum(row['received'] for row in parallel),mbit_s=sum(row['received'] for row in parallel)*8/interval/1e6,complete=all(row['passed'] for row in parallel))
        endpoints={}
        for name,events,resource_path in [('client',client,root/'resources.jsonl'),('server',server,root/'server-resources.jsonl')]:
            samples=[row for row in events if 'transport' in row]
            counter_bracket=None
            if len(samples)>1:
                first_sample,last_sample=samples[0],samples[-1]
                first_time=datetime.datetime.fromisoformat(first_sample['utc'].replace('Z','+00:00'))
                last_time=datetime.datetime.fromisoformat(last_sample['utc'].replace('Z','+00:00'))
                seconds=(last_time-first_time).total_seconds()
                first_rs=first_sample['transport']['reliability'];last_rs=last_sample['transport']['reliability']
                first_perf=first_rs['Performance'];last_perf=last_rs['Performance']
                waits={key:(last_perf[key]-first_perf[key])/1e9 for key in ['FullNS','ReadyFullNS','WindowOnlyBlockedNS','HeadSACKedBlockedNS','HeadUnconfirmedLaterSACKedBlockedNS']}
                counter_bracket=dict(first_utc=first_sample['utc'],last_utc=last_sample['utc'],seconds=seconds,retry_bytes=last_rs['RetransmittedBytes']-first_rs['RetransmittedBytes'],retries=last_rs['Retransmissions']-first_rs['Retransmissions'],new_data_bytes=sum(last_perf['NewDATA']['Bytes'])-sum(first_perf['NewDATA']['Bytes']),wait_seconds=waits,wait_fraction={key:value/seconds for key,value in waits.items()} if seconds>0 else {},scope='Same endpoint first/last transport snapshot bracket including close tail, not request-local; own UTC sample interval, no cross-machine subtraction. Overlapping waits are not summed.')
            media_path={}
            if samples:
                for side in ['publisher','subscriber']:
                    selected=next((sample for sample in reversed(samples) if any(row.get('type')=='candidate-pair' for row in sample['transport'].get(side,[]))),None)
                    media_path[side]=dict(observed_utc=selected.get('utc'),records=[row for row in selected['transport'][side] if row.get('type') in ['candidate-pair','local-candidate','remote-candidate','transport']]) if selected else None
            mux=[row['stats'] for row in events if row.get('event') in ['mux_sample','mux_result','mux_gateway']]
            process=[row for row in events if row.get('event') in ['resources','summary']]
            resource=records(resource_path)
            system={}
            if len(resource)>1:
                first=[int(value) for value in resource[0]['cpu'].split()[1:]]
                last=[int(value) for value in resource[-1]['cpu'].split()[1:]]
                delta=[after-before for before,after in zip(first,last)];total=sum(delta[:8])
                system=dict(interval_s=resource[-1]['monotonic']-resource[0]['monotonic'],busy_fraction=(total-delta[3]-delta[4])/total,steal_fraction=delta[7]/total,load_first_last=[resource[0]['load'],resource[-1]['load']],cgroup_cpu_first_last=[resource[0].get('cpu.stat'),resource[-1].get('cpu.stat')],memory_events_first_last=[resource[0].get('memory.events'),resource[-1].get('memory.events')],scope='whole host CPU/load/network; process RUSAGE separately; local cgroup may include other applications')
            retired={row['ID']:row for sample in samples if sample.get('mux_performance') for row in sample['mux_performance'].get('Retired',[]) if row['ID']!=0}
            endpoints[name]=dict(media_path=media_path,mux_first_last=[mux[0],mux[-1]] if mux else [],resources_last=process[-1] if process else None,system=system,counter_bracket=counter_bracket,stream_lifetime_counters=retired,reliability_last=samples[-1]['transport'].get('reliability') if samples else None,carrier_last=samples[-1]['transport'].get('carrier') if samples else None,setup_ms=next((row.get('stats',{}).get('SetupMs') for row in events if row.get('event')=='connected'),None),family_tls_accepted=any(row.get('event')=='family_auth' and row.get('accepted') is True for row in events))
        result=json.loads((root/'phase-result.json').read_text()) if (root/'phase-result.json').exists() else dict(error='phase receipt missing')
        phases[phase]=dict(status='COMPLETE' if result.get('completed') else 'FAILED',host=reservation.get('host'),error=result.get('error'),requests=requests,aggregate=aggregate,endpoints=endpoints,protocol_error_stop=(root/'protocol-error-stop.json').exists(),cleanup=json.loads((root/'cleanup.json').read_text()) if (root/'cleanup.json').exists() else None)
    data=dict(utc=datetime.datetime.now(datetime.UTC).isoformat(),phases=phases,reserved_application_bytes=reserved,application_limit=67108864,missing_phases=[phase for phase,row in phases.items() if row['status']!='COMPLETE'],android_tun=False,production_admission_tested=False,clock_scope='Each request/parallel interval uses the same client process monotonic clock. No inter-host clock subtraction.')
    path=WORK/'summary.json';assert not path.exists()
    subprocess.run(['apply_patch'],input='*** Begin Patch\n*** Add File: '+str(path)+'\n'+''.join('+'+line+'\n' for line in json.dumps(data,indent=2).splitlines())+'*** End Patch\n',text=True,check=True)
    for phase,row in phases.items():
        print(phase,row['status'],[(request['name'],request['passed'],request['full_seconds'],request['goodput_mbit_s']) for request in row.get('requests',[])],row.get('aggregate'),row.get('error'))


if __name__=='__main__':
    main()
