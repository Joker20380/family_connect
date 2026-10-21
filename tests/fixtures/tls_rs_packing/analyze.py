"""Raw-derived receiver/application timing and per-direction ciphertext accounting."""
import importlib.util
import json
from pathlib import Path
from prepare import ROOT,WORK,patch_file

spec=importlib.util.spec_from_file_location('capacity_summary',ROOT/'tests/fixtures/mesh_capacity/summarize.py')
summary=importlib.util.module_from_spec(spec);spec.loader.exec_module(summary)

def analyze():
    summary.main()
    result=json.loads((WORK/'summary.json').read_text())
    for name,phase in result['phases'].items():
        if not phase['result']:continue
        records={side:summary.records(WORK/name/(prefix+'peer.jsonl')) for side,prefix in [('client',''),('server','server-')]}
        phase['packing']={}
        for side,events in records.items():
            snapshots=[row['packing'] for row in events if 'packing' in row]
            packing=snapshots[-1] if snapshots else next((row['transport']['packing'] for row in reversed(events) if row.get('transport',{}).get('packing')),None)
            if not packing:continue
            hist={}
            for size,count in packing['DataSizes'].items():
                size=int(size)
                if size<0:continue
                full,tail=divmod(size,16384)
                if full:hist[16384]=hist.get(16384,0)+full*count
                if tail:hist[tail]=hist.get(tail,0)+count
            data_count=sum(hist.values());data_bytes=sum(size*count for size,count in hist.items())
            rs=phase['endpoints'][side].get('reliability',{})
            perf=rs.get('Performance') or {}
            counters=perf.get('NewDATA',{})
            phase['packing'][side]=dict(stats=packing,derived_unique_data_histogram=hist,data_count=data_count,data_bytes=data_bytes,bytes_per_slot=data_bytes/data_count if data_count else None,short_count=sum(count for size,count in hist.items() if size<16384),small_256_count=sum(count for size,count in hist.items() if size<=256),small_256_bytes=sum(size*count for size,count in hist.items() if size<=256),rs_new_count=sum(counters.get('Count',[])),rs_new_bytes=sum(counters.get('Bytes',[])),drains=[row for row in events if row.get('event')=='packing_drain'])
        for side,other in [('client','server'),('server','client')]:
            if side not in phase['packing'] or other not in phase['packing']:continue
            sender=phase['packing'][side]['stats'];receiver=phase['packing'][other]['stats']
            phase['packing'][side]['accepted_equals_ordered_peer']=sender['Accepted']==receiver['Received'] and sender['InputSHA256']==receiver['ReceiveSHA256']
            phase['packing'][side]['accepted_equals_submitted']=sender['Accepted']==sender['Sent'] and sender['InputSHA256']==sender['OutputSHA256']
        phase['protocol_errors']={side:max([row.get('mux',{}).get('ProtocolErrors',0) for row in events if row.get('event','').startswith('mux_lab_')],default=0) for side,events in records.items()}
        phase['protocol_categories']={side:[row for row in events if row.get('mux',{}).get('ProtocolErrors',0)>0] for side,events in records.items()}
        phase['mux_final']={side:next((row['mux'] for row in reversed(events) if row.get('event')=='mux_lab_final'),{}) for side,events in records.items()}
        phase['reliable_final']={side:dict(terminal=endpoint.get('reliability',{}).get('Terminal'),sent=endpoint.get('reliability',{}).get('DataSent'),released=(endpoint.get('reliability',{}).get('Performance') or {}).get('ReleasedBlocks')) for side,endpoint in phase['endpoints'].items()}
        phase['shutdown_ack_proven']=all(row['sent']==row['released'] and row['terminal']!='recovery_exhausted' for row in phase['reliable_final'].values())
        phase['clean_acknowledged_completion']=not phase['result'].get('error') and phase['shutdown_ack_proven'] and not any(phase['protocol_errors'].values())
        phase['shutdown_warning']='recovery_exhausted' if any(row['terminal']=='recovery_exhausted' for row in phase['reliable_final'].values()) else 'unconfirmed_at_cancel' if not phase['shutdown_ack_proven'] else None
        print(json.dumps(dict(phase=name,packing={side:{key:values[key] for key in ['data_count','bytes_per_slot','small_256_count','accepted_equals_ordered_peer','accepted_equals_submitted']} for side,values in phase['packing'].items()},protocol=phase['protocol_errors'])))
    patch_file(WORK/'analysis.json',json.dumps(result,indent=2))
    return result

if __name__=='__main__':analyze()
