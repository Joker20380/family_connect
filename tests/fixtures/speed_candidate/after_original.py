"""Summarize the retained original-P0 control and its later terminal records."""

import json
import ast
import re
import statistics
import subprocess
import datetime
from prepare import ROOT, WORK, digest


def main():
    root=WORK/'phase-original96'
    requests=[json.loads(line) for line in (root/'requests.jsonl').read_text().splitlines()]
    capture=[json.loads(line) for line in (root/'capture-private.jsonl').read_text().splitlines()]
    scope=json.loads((root/'scope.json').read_text())
    traces=[]
    for record in capture:
        if record['kind']=='journal':
            message=json.loads(json.loads(record['raw'])['MESSAGE'])
            if message.get('event')=='restricted_trace':traces.append(message['trace'])
    tags=sorted({trace['session_tag'] for trace in traces})
    parser_path=ROOT/'tests/fixtures/queue_retry/journal.py'
    parser_text=parser_path.read_text()
    parser_node=next(node for node in ast.parse(parser_text).body if isinstance(node,ast.FunctionDef) and node.name=='reassemble')
    parser_source=ast.get_source_segment(parser_text,parser_node)+'\n'
    remote=parser_source+'''
import json,subprocess
invocation=EXPECTED_INVOCATION
raw=subprocess.check_output(['journalctl','--file=/var/log/journal/*/system.journal','--no-pager','--all','-o','json','-n','8000','_SYSTEMD_INVOCATION_ID='+invocation],timeout=20)
assert len(raw)<32*1024*1024
selected=[]
rows,errors=reassemble(raw.decode().splitlines())
for record in rows:
 try:
  message=json.loads(record['MESSAGE'])
 except (ValueError,KeyError):continue
 if message.get('event')=='session_terminal' and message.get('diagnostic',{}).get('session_tag') in TAGS:
  selected.append(dict(journal_epoch_us=record['__REALTIME_TIMESTAMP'],**message))
print(json.dumps(dict(terminal_records=selected,selection='last8000 journal entries of the exact original invocation; existing bounded continuation parser',input_bytes=len(raw),parser_errors=errors)))
'''.replace('EXPECTED_INVOCATION',repr(scope['gateway_invocation'])).replace('TAGS',repr(tags))
    compile(remote,'<terminal-readback>','exec')
    terminal=json.loads(subprocess.check_output(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','root@186.246.45.246','python3 -B -'],input=remote,text=True,timeout=30))
    (root/'terminal-readback-reassembled.json').write_text(json.dumps(terminal,indent=2))
    terminal_summary=[]
    for record in terminal['terminal_records']:
        diagnostic=record['diagnostic']
        lifecycle=diagnostic.get('lifecycle',{})
        terminal_summary.append(dict(utc=record.get('utc'),**{key:diagnostic.get(key) for key in
            ('session_tag','protocol_errors','reliable_terminal','retransmissions','recovery_timeouts')},
            first_failure=lifecycle.get('first_failure'),trace_dropped=lifecycle.get('trace_dropped'),
            scope='whole session; owner attribution and pre-load counter value unproven'))
    samples=[record for record in capture if record['kind']=='sample']
    ticks=int((root/'gateway-clock-ticks.txt').read_text())
    def cpu(record):
        fields=record['stat'].rsplit(')',1)[1].split()
        return int(fields[11])+int(fields[12])
    rss=[int(re.search(r'^VmRSS:\s+(\d+)',row['status'],re.M)[1]) for row in samples]
    latency={}
    for kind in ('idle','loaded'):
        selected=[row for row in requests if row['name'].startswith(kind)]
        values=[float(row['metrics']['time_total']) for row in selected]
        latency[kind]=dict(n=len(values),median_seconds=statistics.median(values),max_seconds=max(values),p99=None)
    single=next(row for row in requests if row['name']=='bulk-1-0')
    loaded=[row for row in requests if row['name'].startswith('loaded')]
    result=dict(profile='original96_P0',phone_apk_sha256=scope['phone_apk_sha256'],gateway_sha256=scope['gateway_sha256'],
                topology=scope['topology'],body_validation_passed=sum(row['valid'] for row in requests),attempts=len(requests),
                delivered_body_bytes=sum(int(row['metrics']['BODY_BYTES']) for row in requests),
                cells=json.loads((root/'cells.json').read_text()),latency=latency,
                loaded_probes_fully_overlap_single=all(float(row['metrics']['BEGIN'])>=float(single['metrics']['BEGIN']) and float(row['metrics']['END'])<=float(single['metrics']['END']) for row in loaded),
                gateway_process_cpu_percent_one_core=(cpu(samples[-1])-cpu(samples[0]))/ticks/(samples[-1]['monotonic']-samples[0]['monotonic'])*100,
                gateway_rss_kib=dict(first=rss[0],last=rss[-1],max_observed=max(rss)),
                resource_scope='whole gateway process, not owner-only; Android CPU/RSS not sampled in original control',
                trace_session_tags=tags,trace_reasons=sorted({trace.get('reason','') for trace in traces}),
                gateway_terminal_record_count=len(terminal['terminal_records']),
                terminal_summary=terminal_summary,
                last_request_end_utc=datetime.datetime.fromtimestamp(max(row['end_epoch'] for row in requests),datetime.timezone.utc).isoformat(),
                protocol_error_delta=None,media_wire_bytes=None,retry_bytes=None,
                limits_basis=scope['limits_basis'],clean_acceptance=False,
                limitations=['legacy counters OFF','no independent Android live OPEN/Mux export','multiple trace tags, no assumed owner tag',
                             'observed SHA256, not pre-known origin SHA','terminal records retained separately; no absence-as-zero'],
                hashes={name:digest(root/name) for name in ('requests.jsonl','capture-private.jsonl','terminal-readback.json','terminal-readback-reassembled.json','scope.json')})
    (root/'normalized.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':main()
