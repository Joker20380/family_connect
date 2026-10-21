"""Offline replay preparation against sealed beta92; never deploys or sends traffic."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
SAVED = ROOT / 'state-client-build/mesh-receive-path-20261020'
WORK = Path(os.environ.get('RTP_LATE_OUT', ROOT / 'state-client-build/rtp-late-arrival-20261020'))
FIXTURE = Path(__file__).resolve().parent
TOOLS = ROOT / 'state-client-build/field65-export16/diag-source-freeze-1/resume-tools'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare():
    WORK.mkdir(mode=0o700, exist_ok=False)
    inventory = json.loads((SAVED / 'normal92/android-build/source-inventory.json').read_text())
    source = SAVED / 'normal92/android-source'
    assert all(digest(source / name) == expected for name, expected in inventory.items())
    gateway_root = ROOT / 'state-client-build/tunnel-restart-20261019'
    gateway = json.loads((gateway_root / 'gateway-build.json').read_text())
    assert all(digest(gateway_root / 'gateway-source/carrier' / name) == expected
               for name, expected in gateway['files'].items())
    assert digest(SAVED / 'gateway-baseline-b9') == 'b9ae880731517753e456637e52dcc421b9f7d7b881b400c856989ae93193e9ba'
    assert digest(SAVED / 'normal92/delivery/FamilyConnect-0.1.18-beta92-stability.apk') == '1e73167c8bfdba68f96249088cf08ea3dfb9d3614d5bedb8a0a7bdd8716e4e7b'
    shutil.copytree(source / 'carrier', WORK / 'carrier')
    rtp_path = WORK / 'carrier/telemost/rtp.go'
    text = rtp_path.read_text()
    for old, new in [('time.Since(b.gapSince)', 'replayNow.Sub(b.gapSince)'),
                     ('100*time.Millisecond', 'replayBudget'), ('b.gapSince = time.Now()', 'b.gapSince = replayNow')]:
        assert text.count(old) == 1
        text = text.replace(old, new)
    text = text.replace('b.pkts[pkt.SequenceNumber] = b.clone(pkt)',
                        'b.pkts[pkt.SequenceNumber] = b.clone(pkt)\n\tif replayQueued != nil { replayQueued(b) }')
    rtp_path.write_text(text)
    (WORK / 'baseline.json').write_text(json.dumps(dict(
        inventory_sha256=digest(SAVED / 'normal92/android-build/source-inventory.json'),
        baseline_rtp_sha256=digest(source / 'carrier/telemost/rtp.go'),
        replay_rtp_sha256=digest(rtp_path), gateway_inventory=gateway['source_inventory'],
        substitutions='TEST_ONLY_CLOCK_BUDGET_AND_READ_ONLY_QUEUE_OBSERVER; no production candidate'), indent=2))
    sys.path.insert(0, str(ROOT / 'tests/fixtures/mesh_throughput_trace'))
    from correlate import reconstruct
    records, errors = reconstruct((SAVED / 'baseline/capture/Android-raw.jsonl').read_text().splitlines())
    assert not errors
    assert len({(record['session_tag'], record['performance']['Trace']['origin']) for record in records}) == 1
    points = {}
    for record in records:
        for point in record['performance']['Trace']['receive']['points']:
            assert point['i'] not in points or point == points[point['i']]
            points[point['i']] = point
    episodes = []
    for sequence, first, last, start in [(614, 28523, 28778, 28672), (1127, 57918, 58173, 57963),
                                         (1294, 68480, 68735, 68480)]:
        segment = [points[index] for index in range(first, last + 1)]
        assert len({point['track'] for point in segment if point.get('track')}) == 1
        arrivals = [dict(point, provenance='reader') for point in segment if point['stage'] == 'rtp_reader' and point['i'] >= start]
        if sequence == 1294:
            seen = {point['first'] for point in arrivals}
            prefix = [dict(point, ns=point['ns']-point['wait_ns'], provenance='enqueue_reconstructed_from_release_wait')
                      for point in segment if point['stage'] == 'reorder_released' and point['first'] not in seen
                      and point.get('wait_ns', 0) > 1_000_000]
            assert {point['first'] for point in prefix} == set(range(9910, 9936))
            arrivals += prefix
        arrivals.sort(key=lambda point: (point['ns'], point['i']))
        episodes.append(dict(sequence=sequence, first_index=first, last_index=last,
                             points=segment, arrivals=arrivals))
    output = FIXTURE / 'late-arrival-input.json'
    content = json.dumps(dict(schema=1, payload='NOT_CAPTURED_SYNTHETIC_ONLY',
                             packet_sizes_and_marker='NOT_IN_RECEIVE_RING; derived from accepted packetizer where possible',
                             origin='ONE_PROCESS_MONOTONIC_NS', episodes=episodes), separators=(',', ':'))
    if output.exists():
        assert output.read_text() == content
    else:
        with output.open('x') as handle:
            handle.write(content)
    print('EXACT92_B9_VERIFIED_OFFLINE_INPUT_PRESERVED')


def run():
    shutil.copyfile(FIXTURE / 'late_arrival_test.go', WORK / 'carrier/telemost/late_arrival_test.go')
    shutil.copyfile(FIXTURE / 'late-arrival-input.json', WORK / 'carrier/telemost/late-arrival-input.json')
    environment = {key: value for key, value in os.environ.items() if not key.startswith(('GO', 'CGO', 'FC_', 'YANDEX_'))}
    environment.update(GOTOOLCHAIN='local', GOWORK='off', GOPROXY='off', GOSUMDB='off', GOMAXPROCS='2',
                       GOPATH=str(TOOLS / 'gopath'), GOCACHE=str(SAVED / 'go-cache'), REPLAY_OUTPUT=str(WORK))
    index = len(list(WORK.glob('replay-*.jsonl'))) + 1
    with (WORK / f'replay-{index}.jsonl').open('xb') as output:
        result = subprocess.run([TOOLS / 'go/bin/go', 'test', '-race', '-json', '-count=1', '-timeout', '90s',
                                 '-run', '^TestLate', './telemost'], cwd=WORK / 'carrier', env=environment,
                                stdout=output, stderr=subprocess.STDOUT, timeout=180)
    print(json.dumps(dict(exit=result.returncode, log=f'replay-{index}.jsonl')))
    raise SystemExit(result.returncode)


def regressions(only=None):
    environment = {key: value for key, value in os.environ.items() if not key.startswith(('GO', 'CGO', 'FC_', 'YANDEX_'))}
    environment.update(GOTOOLCHAIN='local', GOWORK='off', GOPROXY='off', GOSUMDB='off', GOMAXPROCS='2',
                       GOPATH=str(TOOLS / 'gopath'), GOCACHE=str(SAVED / 'go-cache'), FC_EXPECT_SEED_OBSERVABILITY='1')
    sources = [('android92', SAVED / 'normal92/android-source/carrier',
                ['./telemost', './reliablestream', './familysession', './wholedevice', './restrictedowner']),
               ('gateway-b9', ROOT / 'state-client-build/tunnel-restart-20261019/gateway-source/carrier',
                ['./cmd/bootstrap-broker', './telemost', './sessiondiag'])]
    for label, source, packages in sources:
        if only is not None and label != only:
            continue
        target = WORK / ('regression-' + label)
        if not target.exists():
            shutil.copytree(source, target)
            shutil.copyfile(ROOT / 'tests/fixtures/tunnel_restart/peer_state_test.go', target / 'telemost/restart_audit_test.go')
        index = len(list(WORK.glob(label + '-*.jsonl'))) + 1
        with (WORK / f'{label}-{index}.jsonl').open('xb') as output:
            result = subprocess.run([TOOLS / 'go/bin/go', 'test', '-race', '-json', '-count=1', '-timeout', '120s', *packages],
                                    cwd=target, env=environment, stdout=output, stderr=subprocess.STDOUT, timeout=420)
        print(json.dumps(dict(label=label, exit=result.returncode)), flush=True)
        if result.returncode:
            raise SystemExit(result.returncode)


if __name__ == '__main__':
    os.umask(0o077)
    {'prepare': prepare, 'run': run, 'regressions': regressions,
     'gateway-regressions': lambda: regressions('gateway-b9')}[sys.argv[1]]()
