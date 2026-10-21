import collections
import importlib.util
import statistics
from lab import *
import interaction_analyze as prior

spec=importlib.util.spec_from_file_location('capacity_summary',ROOT/'tests/fixtures/mesh_capacity/summarize.py')
summary=importlib.util.module_from_spec(spec);spec.loader.exec_module(summary)


def distribution(values):
    return dict(n=len(values),median=statistics.median(values) if values else None,maximum=max(values) if values else None)


def main():
    phases={}
    for reservation in sorted(WORK.glob('*/reservation.json'),key=lambda path:path.stat().st_mtime):
        directory=reservation.parent
        if not (directory/'phase-result.json').exists():continue
        reserved=json.loads(reservation.read_text());result=json.loads((directory/'phase-result.json').read_text())
        sides={side:prior.records(directory/(prefix+'peer.jsonl')) for side,prefix in [('client',''),('server','server-')]}
        requests=[row for row in sides['client'] if row.get('event')=='host_request']
        single=next((row for row in requests if row['name']=='single'),None);parallel=[row for row in requests if row['name'].startswith('parallel_')]
        parallel_seconds=(max(row['end_ns'] for row in parallel)-min(row['start_ns'] for row in parallel))/1e9 if len(parallel)==2 and all('end_ns' in row for row in parallel) else None
        phase=dict(config=reserved['config'],source_reserved=reserved['application_reserved'],result=result,requests=[{key:row[key] for key in ['name','operation','passed','error','full_seconds','start_ns','end_ns','received','sha256','size','stream'] if key in row} for row in requests],single_seconds=single.get('full_seconds') if single else None,single_mbit_s=single.get('received',0)*8/single['full_seconds']/1e6 if single else None,parallel_seconds=parallel_seconds,parallel_mbit_s=sum(row.get('received',0) for row in parallel)*8/parallel_seconds/1e6 if parallel_seconds else None,small={},endpoints={},clean=False)
        for prefix in ['small_idle','small_loaded']:
            subset=[row for row in requests if row['name'].startswith(prefix)]
            phase['small'][prefix]=dict(latency=distribution([row['full_seconds'] for row in subset if row['passed']]),errors=sum(not row['passed'] for row in subset),fully_inside_single=sum(single is not None and 'end_ns' in single and 'end_ns' in row and row['start_ns']>=single['start_ns'] and row['end_ns']<=single['end_ns'] for row in subset))
        for side,prefix in [('client',''),('server','server-')]:
            events=sides[side];original=summary.endpoint(events,prior.records(directory/(prefix+'resources.jsonl')))
            endpoint={key:original.get(key) for key in ['wire','carrier','cpu_user_s','cpu_system_s','max_rss_kib','max_send_queue','max_receive_queue','waits_seconds','max_retained','max_sacked','max_unconfirmed','max_sampled_head_age_seconds','host_busy_percent','host_steal_percent','cgroup_delta']}
            snapshots=[row['transport'] for row in events if 'lab_rate' in row.get('transport',{})]
            for key in ['lab_rate','lab_fragments','quic','adapter']:endpoint[key]=next((row[key] for row in reversed(snapshots) if key in row),None)
            endpoint['quic_ready']=next((row for row in events if row.get('event')=='quic_ready'),None)
            endpoint['process_exit']=json.loads((directory/(prefix+'exit.json')).read_text()) if (directory/(prefix+'exit.json')).exists() else None
            endpoint['stderr']=(directory/(prefix+'peer.stderr')).read_text().splitlines() if (directory/(prefix+'peer.stderr')).exists() else []
            endpoint['startup_gate']=next((row for row in events if row.get('event')=='capacity_start_gate'),None)
            endpoint['completion_events']=[{key:row[key] for key in ['event','utc','error'] if key in row} for row in events if row.get('event') in ['p_workload_done','p_drained','quic_finished','summary']]
            metrics=[row['quic'] for row in snapshots if 'quic' in row]
            endpoint['quic_sampled']=dict(cwnd=distribution([row['CWND'] for row in metrics]),inflight=distribution([row['BytesInFlight'] for row in metrics]),srtt_ns=distribution([row['SmoothedRTTNS'] for row in metrics]),scope='one-second and final samples including idle/drain, not independent latency trials') if metrics else None
            endpoint['errors']=[row for row in events if row.get('event')=='error']
            endpoint['warnings']=[{key:row[key] for key in ['event','error','utc'] if key in row} for row in events if row.get('event') in ['packing_closed','quic_finished']]
            endpoint['trace']=next((row for row in events if row.get('event')=='media_trace_end'),None)
            endpoint['paths']=[dict(connection=path['connection'],local_type=path['local'].get('candidateType'),remote_type=path['remote'].get('candidateType'),remote_ip=path['remote'].get('ip'),protocol=path['remote'].get('protocol'),rtt=path['pair'].get('currentRoundTripTime')) for path in original.get('selected_paths',[])]
            endpoint['rs_retry']=prior.retries(events,original.get('reliability') or {}) if reserved['config']['Mode']=='P' else None
            proofs=[row for row in events if row.get('event')=='p_drained'];endpoint['drained']=bool(proofs and proofs[-1].get('error')=='<nil>')
            mux=[row['mux'] for row in events if row.get('mux')];endpoint['mux_final']=mux[-1] if mux else None
            endpoint['protocol_errors']=max([row.get('ProtocolErrors',0) for row in mux],default=0) if reserved['config']['Mode']!='QN' else None
            media=[row['entry'] for row in events if row.get('event')=='media'];tx=[row for row in media if row['stage']=='tx'];rtcp=[row for row in media if row['stage']=='rtcp_tx' and row.get('kind')!='RRblock']
            identities=collections.Counter((row.get('ssrc'),row.get('seq'),row.get('ts'),row.get('hash')) for row in tx)
            parts=collections.defaultdict(list)
            frames=collections.defaultdict(list)
            for row in tx:frames[(row.get('ssrc'),row.get('ts'))].append(row)
            for frame in frames.values():
                first=next((row for row in frame if row.get('kind')=='data' and row.get('start')),None)
                if first is not None:parts[(first.get('sender'),first.get('message'),first.get('fragment',0))].extend(frame)
            sizes=collections.Counter(len({(row.get('ssrc'),row.get('seq')) for row in rows}) for rows in parts.values() if any(row.get('start') for row in rows) and any(row.get('marker') for row in rows))
            clear=sum(row.get('size',0)+12 for row in tx)+sum(row.get('size',0) for row in rtcp)
            endpoint['packetization']=dict(identified_parts=len(parts),complete_part_rtp_counts=dict(sizes),group_scope='same local sender SSRC/timestamp for RTP continuation association; cross-host matching uses carrier IDs, never assumed SSRC preservation',max_clear_rtp=max((row.get('size',0)+12 for row in tx),default=0),rtp_packets=len(tx),rtcp_packets_upper=len(rtcp),rtp_repeats=sum(count-1 for count in identities.values()),full_clear=clear,ipv6_srtp16_srtcp20_upper=clear+64*len(tx)+68*len(rtcp),charged=result['wire_details'][side]['charged'])
            phase['endpoints'][side]=endpoint
        for side,opposite in [('client','server'),('server','client')]:
            def parts(rows,stage):return {(entry.get('sender'),entry.get('message'),entry.get('fragment',0)) for row in rows if row.get('event')=='media' for entry in [row['entry']] if entry['stage']==stage and entry.get('kind')=='data' and (stage=='assembled' or entry.get('start'))}
            complete=all(phase['endpoints'][endpoint]['trace'] and phase['endpoints'][endpoint]['trace']['overflow']==0 for endpoint in [side,opposite])
            sent=parts(sides[side],'tx');assembled=parts(sides[opposite],'assembled')
            phase['endpoints'][side]['lower_gaps']=dict(complete_trace=complete,identified_tx_parts=len(sent),unassembled=len(sent-assembled) if complete else None,scope='session endpoint IDs including shutdown tails; not physical packet-loss attribution')
        phase['clean']=result['completed'] and len(requests)==17 and all(row['passed'] for row in requests) and (directory/'two-end-proof.json').exists() and all(endpoint['drained'] and not endpoint['errors'] and not endpoint['protocol_errors'] for endpoint in phase['endpoints'].values())
        phase['proof_sha256']=digest(directory/'two-end-proof.json') if (directory/'two-end-proof.json').exists() else None
        phase['delivery_verified']=bool(phase['proof_sha256'] and len(requests)==17 and all(row['passed'] for row in requests))
        phases[directory.name]=phase
    result=dict(phases=phases,source_reserved_live=sum(row['source_reserved'] for row in phases.values()),media_charged_live=sum(row['result']['wire_charged'] for row in phases.values()))
    write(WORK/'analysis.json',json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(source_mib=result['source_reserved_live']/2**20,media_mib=result['media_charged_live']/2**20,phases={name:{key:row[key] for key in ['clean','single_seconds','single_mbit_s','parallel_seconds','parallel_mbit_s']} for name,row in phases.items()}),indent=2))


if __name__=='__main__':main()
