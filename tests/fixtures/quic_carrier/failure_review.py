from lab import *

directory=WORK/'A1G'
result=json.loads((directory/'phase-result.json').read_text())
analysis=json.loads((WORK/'analysis.json').read_text())['phases']['A1G']
sides={}
for side,prefix in [('client',''),('server','server-')]:
    events=[json.loads(line) for line in (directory/(prefix+'peer.jsonl')).read_text().splitlines()]
    reliable=next(row['transport']['reliability'] for row in reversed(events) if row.get('transport',{}).get('reliability'))
    resource=analysis['endpoints'][side]
    sides[side]=dict(exit=json.loads((directory/(prefix+'exit.json')).read_text()),terminal=reliable['Terminal'],retries=reliable['Retransmissions'],retry_bytes=reliable['RetransmittedBytes'],event_ring_dropped=reliable['EventsDropped'],resources={key:resource[key] for key in ['cpu_user_s','cpu_system_s','max_rss_kib','host_busy_percent','host_steal_percent','cgroup_delta']},lower_gaps=resource['lower_gaps'])
save(WORK/'A1G-causal-review.json',dict(controller_error=result['error'],endpoints=sides,first_data_path_cause='server RS recovery_exhausted; client reset/carrier_closed, before full workload or two-end proof',not_caused_by_cleanup='both workers exited1 themselves, terminated=false stopped=false',single='received and SHA verified but no full phase admission',production_equal=result['production_equal'],scope='owned lab child/cgroup only; low average host busy, one15.82ms throttle, no demonstrated production influence; readback timeout is separate and final read succeeds',decision='do not tune RS or retry A1G; continue only the three remaining preplanned QN1/QN2/A2 phases after fresh safety readback; all failures retained'))
