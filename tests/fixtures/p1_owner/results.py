"""Summarize the fixed four-phase contrast without changing acceptance thresholds."""
import argparse
import json
from pathlib import Path
import re
import statistics

from classify import classify
from observe import WORK
from scripts.owner_android_support import save


def latency(requests,prefix):
    values=[float(row['metrics']['time_total']) for row in requests if row['name'].startswith(prefix)]
    first=[float(row['metrics']['time_starttransfer']) for row in requests if row['name'].startswith(prefix)]
    return dict(count=len(values),median_seconds=statistics.median(values),max_seconds=max(values),
                ttfb_median_seconds=statistics.median(first),ttfb_max_seconds=max(first),p99_not_estimated=True)


def phase(label):
    directory=WORK/('traffic-'+label)
    load=lambda path:json.loads(path.read_text())
    summary=load(directory/'summary.json');gate=load(directory/'gate.json')
    requests=[json.loads(line) for line in (directory/'requests.jsonl').read_text().splitlines()]
    before=load(WORK/(label+'-close-control-before.json'));after=load(WORK/(label+'-close-control-after.json'))
    close=load(WORK/(label+'-close-control-receipt.json'));remote=close['gateway_terminal']['diagnostic']
    records=[load(path)['snapshot'] for path in directory.glob('monitor-*.json')]
    state_stable=all(record['state']=='CONNECTED' and record['restricted_session']['session_tag']==gate['session_tag'] for record in records)
    diagnostics=[record['restricted_session'] for record in records]+[before['restricted_session']]
    cleanup=[event for event in after['events'] if event.get('session_tag')==gate['session_tag'] and event.get('event') in ('cleanup_completed','cleanup_failed')]
    capture=[json.loads(line) for line in (directory/'capture-private.jsonl').read_text().splitlines()]
    samples=[row for row in capture if row['kind']=='sample']
    resources={}
    if len(samples)>1:
        ticks=[sum(int(value) for value in row['stat'].split(') ',1)[1].split()[11:13]) for row in samples]
        hz=next(row['clock_ticks'] for row in capture if row['kind']=='origin')
        resources=dict(gateway_cpu_percent_one_core=100*(ticks[-1]-ticks[0])/hz/(samples[-1]['monotonic']-samples[0]['monotonic']),
                       gateway_rss_max_kib=max(int(re.search(r'VmRSS:\s+(\d+)',row['status']).group(1)) for row in samples),samples=len(samples))
    return dict(profile=summary['profile'],session_tag=gate['session_tag'],single=summary['cells'][0],aggregate=summary['cells'][1],
                completed=summary['completed'],attempts=summary['attempts'],requested=summary['requested_bound'],failure=summary['failure'],
                idle=latency(requests,'idle'),loaded=latency(requests,'loaded'),both_limits=gate['limits'],mux_window=gate['mux_window'],
                stable_session=state_stable,network=before['network_class'],android_errors=classify(diagnostics),gateway_errors=classify([remote]),
                android_cleanup=bool(cleanup and cleanup[-1]['event']=='cleanup_completed'),
                gateway_terminal=remote['terminal_reason'],reliable_terminal=remote['reliable_terminal'],
                close_observation_seconds=close['seconds'],cleanup_counter_scope='Android final pre-stop snapshot; native stop success separately; gateway terminal counters',
                retry_bytes=dict(android=before['restricted_session'].get('retry_bytes'),gateway=remote.get('retry_bytes'),scope='whole session including background and gateway cleanup'),
                resources=resources,collector_end=next((row for row in reversed(capture) if row['kind']=='end'),None))


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('label');args=parser.parse_args()
    assert re.fullmatch('[a-z0-9-]+',args.label)
    phases={label:phase(label) for label in ('p0a','p1a','p1b','p0b')}
    contrasts=[]
    for baseline,candidate in [('p0a','p1a'),('p0b','p1b')]:
        left,right=phases[baseline],phases[candidate]
        single=right['single']['mbit_s']/left['single']['mbit_s'];aggregate=right['aggregate']['mbit_s']/left['aggregate']['mbit_s']
        small={kind:{measure:right[kind][measure]/left[kind][measure] for measure in ('median_seconds','max_seconds')} for kind in ('idle','loaded')}
        contrasts.append(dict(baseline=baseline,candidate=candidate,single_ratio=single,aggregate_ratio=aggregate,
                              single_pass=single>=1.2,aggregate_pass=aggregate>=.9,small_ratios=small,
                              latency_review_required=any(value>1.2 for group in small.values() for value in group.values())))
    result=dict(phases=phases,contrasts=contrasts,acceptance='PENDING_15MIN_AND_FINAL_ORDINARY_CONNECT',
                requested_total=sum(json.loads(path.read_text())['requested_bound'] for path in (WORK/'traffic-ledger').glob('*.json')))
    save(WORK/(args.label+'-results.json'),result)
    print(json.dumps(result))


if __name__=='__main__':main()
