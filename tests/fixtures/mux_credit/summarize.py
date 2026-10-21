"""Reconcile retained matrix/model evidence without network access or new traffic."""

import collections
import json
import re

from measure import reassemble
from prepare import ROOT, WORK, APK, GATEWAY, digest


def read(name):
    return json.loads((WORK/name).read_text())


def histogram_bytes(histogram):
    return sum(histogram['Bytes'])


def streams(row):
    mux = row['performance']['Mux']
    return {stream['ID']: stream for stream in mux['Retired'] + mux['Streams'] if stream['ID']}


def main():
    raw = [json.loads(line) for line in (WORK/'matrix/capture-private.jsonl').read_text().splitlines()]
    journal, errors = reassemble([row['raw'] for row in raw if row['kind'] == 'journal'])
    assert not errors, errors
    snapshots = []
    for record in journal:
        try:
            row = json.loads(record['MESSAGE'])
        except (ValueError, TypeError):
            continue
        if row.get('event') == 'restricted_performance_v1':
            row['epoch'] = int(record['__REALTIME_TIMESTAMP'])/1e6
            snapshots.append(row)
    samples = [row for row in raw if row['kind'] == 'sample']
    requests = [json.loads(line) for line in (WORK/'matrix/requests.jsonl').read_text().splitlines()]
    cells = read('matrix/cells.json')
    for cell in cells:
        selected = [row for row in requests if row['name'].startswith(f'cell-{cell["cell"]}-')]
        start, end = min(row['start_epoch'] for row in selected), max(row['end_epoch'] for row in selected)
        before = next(row for row in reversed(snapshots) if row['epoch'] < start)
        after = next(row for row in snapshots if row['epoch'] >= end)
        prior, final = streams(before), streams(after)
        matches = []
        for identifier, stream in final.items():
            handed = histogram_bytes(stream['HandedDATA']) - histogram_bytes(prior[identifier]['HandedDATA']) if identifier in prior else histogram_bytes(stream['HandedDATA'])
            if handed >= selected[0]['intended_bytes']:
                assert identifier not in prior, 'ambiguous preexisting bulk stream'
                matches.append(stream)
        assert len(matches) == cell['flows'], 'ambiguous Mux attribution'
        cell['mux_streams'] = matches
        cell['counter_bracket'] = dict(before_epoch=before['epoch'], after_epoch=after['epoch'],
                                       request_start_epoch=start, request_end_epoch=end,
                                       scope='whole-session RS, bracketing samples include background and edges')
        cell['requests'] = [dict(name=row['name'], ttfb_s=float(row['metrics']['time_starttransfer']),
                                dns_s=float(row['metrics']['time_namelookup']), tcp_s=float(row['metrics']['time_connect']),
                                tls_s=float(row['metrics']['time_appconnect']), full_s=float(row['metrics']['time_total']),
                                body_s=float(row['metrics']['time_total'])-float(row['metrics']['time_starttransfer']),
                                connections=int(row['metrics']['num_connects']), valid=row['valid']) for row in selected]
        cell['bulk_socket_max'] = max(sum(any(address+':443' in line for address in {row['metrics']['remote_ip'] for row in selected}) for line in sample['sockets']) for sample in samples if start <= sample['epoch'] <= end)
        first, last = before['performance']['Window'], after['performance']['Window']
        cell['rs_delta'] = {key: last[key]-first[key] for key in ('ReadyFullNS', 'WindowOnlyBlockedNS', 'HeadUnconfirmedLaterSACKedBlockedNS', 'HeadSACKedBlockedNS', 'ReleasedBytes')}
        cell['rs_delta'].update({key: histogram_bytes(last[key])-histogram_bytes(first[key]) for key in ('NewDATA', 'RetryDATA')})
    zero, free, full = [], [], []
    for index, row in enumerate(snapshots):
        mux, window = row['performance']['Mux'], row['performance']['Window']
        if any(stream['ReadyBytes'] > 0 and stream['Credit'] == 0 for stream in mux['Streams']):
            zero.append(index)
            if window['SlotSpan'] < window['EffectiveWindow'] and not window['LocalWriterBusy'] and window['LocalQueuedFrames'] == 0:
                free.append(index)
            if window['SlotSpan'] >= window['EffectiveWindow']:
                full.append(index)
    first, last = snapshots[0]['performance'], snapshots[-1]['performance']
    origin = next(row for row in raw if row['kind'] == 'origin')
    ticks = lambda row: sum(int(value) for value in row['stat'].split()[13:15])
    cpu = (ticks(samples[-1])-ticks(samples[0]))/origin['clock_ticks']/(samples[-1]['epoch']-samples[0]['epoch'])*100
    models, checks = [], {}
    paths = sorted(WORK.glob('lab-*-*.jsonl')) + [WORK/'checks-2.jsonl', WORK/'checks-3.jsonl']
    for path in paths:
        records = [json.loads(line) for line in path.read_text().splitlines() if line.startswith('{')]
        checks[path.name] = dict(collections.Counter(row['Action'] for row in records if 'Test' in row and row['Action'] in ('pass', 'fail', 'skip')))
        text = ''.join(row.get('Output', '') for row in records)
        for line in text.splitlines():
            if 'CREDIT_MODEL ' in line:
                model = json.loads(line.split('CREDIT_MODEL ', 1)[1])
                model['mux_server']['Retired'] = [stream for stream in model['mux_server']['Retired'] if stream['ID']]
                model['rs']['Performance'].pop('Events', None)
                model['rs'].pop('Events', None)
                model['rs'].pop('RecentEvents', None)
                models.append(model)
    direct = read('direct-nl.json')
    direct['metrics'] = {key: direct['metrics'][key] for key in ('http_code', 'http_version', 'ssl_verify_result', 'num_connects', 'num_retries', 'size_download', 'time_namelookup', 'time_connect', 'time_appconnect', 'time_starttransfer', 'time_total', 'speed_download')}
    evidence = dict(
        status='COMPLETED_LAB_COMPATIBILITY_LIMIT_NO_FUNCTIONAL_ROLLOUT',
        application_bytes=read('matrix/summary.json')['bytes']+4194304+int(read('return-control/summary.json')['metrics']['BODY_BYTES']),
        session_tags=sorted({row['session_tag'] for row in snapshots}), preflight=read('matrix/preflight.json'),
        matrix=cells, snapshots=len(snapshots), samples=len(samples), journal_errors=errors,
        credit_joint_samples=dict(zero_ready=len(zero), rs_free_writer_idle=len(free), rs_full=len(full), free_indices=free,
                                  interpretation='point observations, not durations; do not add overlapping waits'),
        protocol_errors=dict(before=first['Mux']['ProtocolErrors'], after=last['Mux']['ProtocolErrors']),
        resources=dict(cpu_percent_one_core=cpu, rss_max_kib=max(int(re.search(r'VmRSS:\s+(\d+)', row['status'])[1]) for row in samples),
                       mux_retained_high_water=max(row['performance']['Mux']['RetainedHighWater'] for row in snapshots),
                       mux_active_range=[min(row['performance']['Mux']['ActiveStreams'] for row in snapshots), max(row['performance']['Mux']['ActiveStreams'] for row in snapshots)],
                       rs_retained_max=max(row['performance']['Window']['RetainedBytes'] for row in snapshots),
                       rs_local_queue_max=max(row['performance']['Window']['LocalQueuedBytes'] for row in snapshots)),
        model_input=read('model-input.json'), models=models, checks=checks, direct_nl=direct,
        counter_source_reapply=read('counter-source-reapply.json'),
        checks_sha256={path.name:digest(path) for path in paths},
        return_control=read('return-control/summary.json'), current=read('final-readback.json'),
        hashes=dict(apk=APK, gateway=GATEWAY, observer=read('observation-build.json')['sha256'],
                    capture=digest(WORK/'matrix/capture-private.jsonl'), model_test=digest(ROOT/'tests/fixtures/mux_credit/model_test.go'),
                    counter_patch=digest(ROOT/'tests/fixtures/mux_credit/counter-only.patch'),
                    android_source_inventory=digest(ROOT/'state-client-build/rtp-deadline-20261020/normal94/android-build/source-inventory.json'),
                    gateway_source_inventory=read('baseline-build.json')['source_inventory']))
    assert evidence['application_bytes'] <= 64*1024*1024
    assert len(models) == 24 and len(evidence['session_tags']) == 1
    assert not any(row.get('fail') for row in checks.values())
    destination = ROOT/'docs/releases/2026-10-20-mesh-mux-credit.evidence.json'
    destination.write_text(json.dumps(evidence, indent=2)+'\n')
    print(json.dumps(dict(bytes=evidence['application_bytes'], cells=[dict(cell=cell['cell'], ids=[stream['ID'] for stream in cell['mux_streams']], socket_max=cell['bulk_socket_max'], mbit_s=cell['aggregate_mbit_s']) for cell in cells], joint=evidence['credit_joint_samples'], resources=evidence['resources'])))


if __name__ == '__main__':
    main()
