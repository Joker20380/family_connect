"""Summarize retained phase samples without inventing absent counter coverage."""

import ast
import collections
import datetime
import importlib.util
import json
from pathlib import Path
import re
import statistics
import sys

spec = importlib.util.spec_from_file_location('fc_speed_candidate_prepare', Path(__file__).with_name('prepare.py'))
inputs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inputs)
ROOT, WORK, digest = inputs.ROOT, inputs.WORK, inputs.digest


def body_accounting(requests, cells):
    received = sum(int(row['metrics'].get('BODY_BYTES', 0)) for row in requests)
    complete = sum(int(row['metrics'].get('BODY_BYTES', 0)) for row in requests if row['valid'])
    qualified = []
    for cell in cells:
        batch = [row for row in requests if row['name'].startswith('bulk-' + str(cell['flows']) + '-')]
        eligible = len(batch) == cell['flows'] and all(row['valid'] for row in batch) and cell['completed'] == cell['flows']
        qualified.append(dict(cell, body_complete=eligible, completed_goodput_mbit_s=cell['mbit_s'] if eligible else None))
    return dict(received_body_bytes=received, complete_response_bytes=complete,
                partial_response_bytes=received-complete, cells=qualified,
                incomplete_responses=[dict(name=row['name'],intended_bytes=row['intended_bytes'],
                    received_bytes=int(row['metrics'].get('BODY_BYTES',0)),curl_exit=row['metrics'].get('CURL_EXIT'))
                    for row in requests if not row['valid']])


def capture_messages(capture):
    source = ROOT / 'tests/fixtures/queue_retry/journal.py'
    text = source.read_text()
    node = next(node for node in ast.parse(text).body if isinstance(node,ast.FunctionDef) and node.name=='reassemble')
    namespace = dict(json=json)
    exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'),namespace)
    rows,errors = namespace['reassemble']([row['raw'] for row in capture if row['kind']=='journal'])
    messages = []
    for row in rows:
        try:
            messages.append(json.loads(row['MESSAGE']))
        except (ValueError,TypeError) as error:
            errors.append(dict(error=str(error)))
    return messages,errors


def summarize(phase):
    root = WORK / ('phase-' + phase)
    requests = [json.loads(line) for line in (root/'requests.jsonl').read_text().splitlines()]
    capture = [json.loads(line) for line in (root/'capture-private.jsonl').read_text().splitlines()]
    scope = json.loads((root/'scope.json').read_text())
    samples = [row for row in capture if row['kind'] == 'sample']
    origin = next(row for row in capture if row['kind'] == 'origin')
    ticks = origin['clock_ticks']
    def cpu(row):
        fields = row['stat'].rsplit(')',1)[1].split()
        return int(fields[11]) + int(fields[12])
    rss = [int(re.search(r'^VmRSS:\s+(\d+)', row['status'], re.M)[1]) for row in samples]
    traces = collections.defaultdict(list)
    messages,parse_errors = capture_messages(capture)
    terminals = []
    for message in messages:
        if message.get('event') == 'session_terminal':
            diagnostic = message.get('diagnostic',{})
            if diagnostic.get('session_tag') == scope.get('session_tag'):
                terminals.append(dict(utc=message.get('utc'),**{key:diagnostic.get(key) for key in
                    ('session_tag','protocol_errors','terminal_reason','reliable_terminal','retransmissions','retry_bytes')},
                    lifecycle={key:diagnostic.get('lifecycle',{}).get(key) for key in
                        ('first_failure','first_close','trace_dropped','export_dropped')}))
        trace = message.get('trace', {})
        if message.get('event') == 'restricted_trace':
            traces[trace['session_tag']].append(trace)
    sessions = []
    for tag, rows in traces.items():
        activity = [row for row in rows if row.get('delivery')]
        assembly_delta = None
        if len(activity) > 1:
            first, last = activity[0]['delivery']['assembly'], activity[-1]['delivery']['assembly']
            if all(last[key] >= first[key] for key in first if key != 'pending'):
                assembly_delta = {key:last[key]-first[key] for key in first if key != 'pending'}
        flows = [row['delivery']['flow'] for row in activity]
        sessions.append(dict(session_tag=tag, owner_attribution=tag == scope.get('session_tag'),
                             trace_count=len(rows), reasons=dict(collections.Counter(row.get('reason') for row in rows)),
                             observation_interval_ms=[rows[0]['timestamp_ms'], rows[-1]['timestamp_ms']],
                             flow_samples=len(flows), max_observed_pending=max((flow['pending'] for flow in flows),default=None),
                             max_observed_head_retries=max((flow['head_retries'] for flow in flows),default=None),
                             sampled_head_retry_nonzero=sum(flow['head_retries'] > 0 for flow in flows),
                             reverse_carrier_receive_assembly_delta=assembly_delta,
                             lease_events=[{key:row.get(key) for key in ('timestamp_ms','lease_action','lease_sequence','lease_deadline_ms')} for row in rows if row.get('lease_action')]))
    latency = {}
    for kind in ('idle','loaded'):
        values = [float(row['metrics']['time_total']) for row in requests if row['name'].startswith(kind)]
        latency[kind] = dict(n=len(values), median_seconds=statistics.median(values),max_seconds=max(values),p99=None)
    single = next(row for row in requests if row['name'] == 'bulk-1-0')
    accounting = body_accounting(requests,json.loads((root/'cells.json').read_text()))
    result = dict(phase=phase,profile=scope.get('android_diagnostic',{}).get('speed_profile','P0_SOURCE_FIXED'),
                  attempts=len(requests),valid=sum(row['valid'] for row in requests),
                  delivered_bytes=sum(int(row['metrics'].get('BODY_BYTES',0)) for row in requests),
                  delivered_bytes_scope='received body bytes including partial responses; not all completed delivery',
                  **accounting,latency=latency,
                  loaded_probes_fully_overlap_single=all(float(row['metrics']['BEGIN']) >= float(single['metrics']['BEGIN']) and float(row['metrics']['END']) <= float(single['metrics']['END']) for row in requests if row['name'].startswith('loaded')),
                  first_request_utc=datetime.datetime.fromtimestamp(min(row['start_epoch'] for row in requests),datetime.timezone.utc).isoformat(),
                  last_request_utc=datetime.datetime.fromtimestamp(max(row['end_epoch'] for row in requests),datetime.timezone.utc).isoformat(),
                  gateway_sample_count=len(samples),gateway_cpu_percent_one_core=(cpu(samples[-1])-cpu(samples[0]))/ticks/(samples[-1]['monotonic']-samples[0]['monotonic'])*100,
                  gateway_rss_kib=dict(first=rss[0],last=rss[-1],max_observed=max(rss)),
                  gateway_resource_pid=origin['pid'],gateway_resource_invocation=origin['invocation'],
                  gateway_resource_interval_epoch=[samples[0]['epoch'],samples[-1]['epoch']],
                  resources_scope='whole gateway process; not owner-only; Android CPU/RSS not sampled',
                  sessions=sessions,gateway_terminal_records=terminals,parse_errors=parse_errors,collector_end=capture[-1],
                  protocol_error_delta=None,retry_bytes=None,media_bytes=None,queue_age=None,mux_ready_wait=None,
                  clean_acceptance=False,local_clock_latency_only=True,
                  limitations=['sampled head retries are not a stall duration or packet-loss count',
                               'gateway receive RTP gaps describe reverse direction, not download losses',
                               'overlapping boundary rings are not summed as independent counters',
                               'body hash observed, no pre-known origin digest; post-load and terminal review required'],
                  hashes={name:digest(root/name) for name in ('scope.json','requests.jsonl','capture-private.jsonl','cells.json','summary.json')})
    (root/'phase-analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def main():
    results = {phase:summarize(phase) for phase in sys.argv[1:]}
    print(json.dumps({phase:{key:result[key] for key in ('valid','attempts','delivered_bytes','cells','latency','gateway_cpu_percent_one_core','gateway_rss_kib')} for phase,result in results.items()}))
    if 'original96' in results and 'P0a' in results:
        comparison = dict(single_percent=(results['P0a']['cells'][0]['mbit_s']/results['original96']['cells'][0]['mbit_s']-1)*100,
                          aggregate_percent=(results['P0a']['cells'][1]['mbit_s']/results['original96']['cells'][1]['mbit_s']-1)*100,
                          criterion_percent=15, status='REVIEW_REQUIRED_NOT_COMPARABLE_OR_CLEAN_ACCEPTANCE',
                          scope='one different-session original/new P0 pair, not isolated code causality')
        (WORK/'p0-consistency.json').write_text(json.dumps(comparison,indent=2)+'\n')
        print(json.dumps(comparison))


if __name__ == '__main__':
    main()
