"""Sanitized late-arrival evidence and optional read-only current-runtime verification."""

import datetime
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from late_arrival import FIXTURE, ROOT, SAVED, TOOLS, WORK, digest

APK = '1e73167c8bfdba68f96249088cf08ea3dfb9d3614d5bedb8a0a7bdd8716e4e7b'
NATIVE = 'dd722eada0da7c890a8d71a72099cba5d0bbac1ce73377bbdbc8e7b85d820c23'
GATEWAY = 'b9ae880731517753e456637e52dcc421b9f7d7b881b400c856989ae93193e9ba'


def readback():
    specification = importlib.util.spec_from_file_location('existing_readonly', ROOT / 'tests/fixtures/mesh_throughput_trace/upgrade.py')
    existing = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(existing)
    phone = existing.snapshot()
    assert phone['code'] == 92 and phone['apk_sha256'] == APK and phone['native_sha256'] == NATIVE
    remote = '''
import datetime,hashlib,json,subprocess
unit='family-connect-restricted-bootstrap.service'
def state():
 return dict(line.split('=',1) for line in subprocess.check_output(['systemctl','show',unit,'-p','MainPID,InvocationID,NRestarts,ActiveState'],text=True).splitlines())
before=state()
with open('/proc/'+before['MainPID']+'/exe','rb') as handle: checksum=hashlib.file_digest(handle,'sha256').hexdigest()
assert before==state()
print(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),state=before,sha256=checksum)))
'''
    response = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=8', 'root@186.246.45.246', 'python3 -B -'],
                              input=remote, text=True, capture_output=True, timeout=20)
    response.check_returncode()
    gateway = json.loads(response.stdout)
    assert gateway['sha256'] == GATEWAY and gateway['state']['ActiveState'] == 'active'
    with (WORK / 'runtime-readback.json').open('x') as output:
        json.dump(dict(phone=phone, gateway=gateway, mutations=False), output, indent=2)
    print(json.dumps(dict(phone=phone, gateway=gateway, mutations=False)))


def tests(path):
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.startswith('{')]
    return dict(sha256=digest(path), passed=sum(row['Action'] == 'pass' and bool(row.get('Test')) for row in rows),
                failed=sum(row['Action'] == 'fail' and bool(row.get('Test')) for row in rows),
                skipped=sum(row['Action'] == 'skip' and bool(row.get('Test')) for row in rows),
                packages=sum(row['Action'] == 'pass' and not row.get('Test') for row in rows))


def summarize():
    source = SAVED / 'normal92/android-source/carrier'
    binary = SAVED / 'normal92/android-build/android/app/intermediates/merged_native_libs/privateBeta/mergePrivateBetaNativeLibs/out/lib/arm64-v8a/libfc_restricted.so'
    assert digest(binary) == NATIVE
    buildinfo = subprocess.check_output([TOOLS / 'go/bin/go', 'version', '-m', binary], text=True)
    assert 'github.com/pion/interceptor\tv0.1.45' in buildinfo and 'github.com/pion/webrtc/v4\tv4.2.15' in buildinfo
    assert '-tags=' not in buildinfo
    (WORK / 'native-buildinfo.txt').write_text(buildinfo)
    native_source = ROOT / 'state-client-build/transport-write-batching-1/source/carrier'
    relevant = ['go.mod', 'go.sum', 'telemost/rtp.go', 'telemost/session.go', 'telemost/signaling.go', 'telemost/msg.go', 'telemost/vp8.go']
    assert all(digest(source / name) == digest(native_source / name) for name in relevant)
    interceptor = TOOLS / 'gopath/pkg/mod/github.com/pion/interceptor@v0.1.45/pkg/nack/generator_interceptor.go'
    pion = TOOLS / 'gopath/pkg/mod/github.com/pion/webrtc/v4@v4.2.15/interceptor.go'
    assert 'interval:          time.Millisecond * 100' in interceptor.read_text()
    assert 'webrtc.RegisterDefaultInterceptors(mediaEngine, registry)' in (source / 'telemost/session.go').read_text()
    scan = {}
    for name in ['owner-beta90-export.json', 'owner-beta91-export.json', 'baseline/capture/Android-raw.jsonl',
                 'baseline/capture/NL-raw.jsonl', 'normal92/physical-baseline.json']:
        text = (SAVED / name).read_text()
        scan[name] = dict(sha256=digest(SAVED / name), counts={term: len(re.findall(term, text, re.I))
                          for term in ['a=rtcp-fb', 'a=rtpmap', 'NackCount', 'NACK', 'RTX', 'TransportLayerNack']})
    results = json.loads((WORK / 'sweep.json').read_text())
    for result in results:
        baseline = next(row for row in results if row['Sequence'] == result['Sequence'] and row['BudgetMS'] == 100)
        delays = [result['Messages'][message] - stamp for message, stamp in baseline['Messages'].items() if message in result['Messages']]
        result['FollowingMessagesDelayed'] = sum(delay > 0 for delay in delays)
        result['MaxFollowingDelayNS'] = max(delays, default=None)
        result['BaselineMessagesNotYetReleased'] = len(baseline['Messages'].keys() - result['Messages'].keys())
    successful = {name: tests(WORK / name) for name in ['replay-5.jsonl', 'android92-2.jsonl', 'gateway-b9-2.jsonl']}
    assert all(not result['failed'] and result['packages'] > 0 for result in successful.values())
    failures = {name: tests(WORK / name) for name in ['replay-1.jsonl', 'android92-1.jsonl', 'gateway-b9-1.jsonl']}
    pins = dict(baseline_apk=APK, baseline_native=NATIVE, baseline_gateway=GATEWAY,
                source_inventory_sha256=digest(SAVED / 'normal92/android-build/source-inventory.json'),
                exact_native_source={name: digest(source / name) for name in relevant},
                dependencies={str(path.relative_to(TOOLS)): digest(path) for path in [interceptor, pion]},
                fixture={name: digest(FIXTURE / name) for name in ['late-arrival-input.json', 'late_arrival.py', 'late_arrival_test.go', 'late_arrival_evidence.py']},
                replay_rtp_sha256=digest(WORK / 'carrier/telemost/rtp.go'))
    result = dict(schema='family_connect_rtp_late_arrival_replay_v1',
                  utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), pins=pins,
                  source='EXACT92_NATIVE_BUILD_SOURCE_VERIFIED_NOT_MAIN',
                  RTP_SKIP_TRIGGER=dict(DATA614='TIME; next2364 to2405; no window/track transition',
                                        DATA1127='TIME; next7900 to7943; no window/track transition',
                                        DATA1294='TIME; next9909 to9910; queued age109.444271ms; late after109.864063ms',
                                        DATA597='NOT_IDENTIFIABLE_FROM_AGGREGATE_WALL_BOUNDARIES; final6s still missing'),
                  NACK_NEGOTIATION_AND_TIMING=dict(interceptor='v0.1.45', webrtc='v4.2.15', default_interval_ms=100,
                      overrides=False, duplicate_generator_added=False, frequency_changed=False, retry_limits_changed=False,
                      actual_track_negotiation='NOT_SAVED', late_packet_source='UNKNOWN_NOT_PROVEN_NACK_OR_RTX', scan=scan),
                  REPLAY_RESULTS=results,
                  CHOSEN_RECEIVER_POLICY='KEEP_BASELINE100_ARRIVAL_DRIVEN; no shipping candidate passes finite-silence hold requirement',
                  smaller_budget_hypothesis='125ms conditionally recovers1294 with +24.901198ms max following delay near1127; not validated as bounded live policy',
                  PHYSICAL_GOODPUT_AND_LATENCY=dict(comparison='NOT_RUN', new_application_bytes=0, speed_acceptance=False),
                  RECOVERY_AND_IDENTITY_PRESERVED=dict(runtime_mutations=False, enrollment=False, recovery_source_changed=False,
                      credentials_floors_revocations_policy_written=False, identity_proof='NO_MUTATION; previous92 identity evidence retained, no new identity audit claimed'),
                  CURRENT_APK_AND_GATEWAY=json.loads((WORK / 'runtime-readback.json').read_text()),
                  REMAINING_LIMITATION=['No payload capture or full1294 reader prefix; synthetic seeded state and reconstructed enqueue times',
                      '614 and1127 no selected missing RTP returns in retained interval; later fate unknown',
                      '597 lacks process-local per-arrival timestamps and final6s',
                      'Deadline service would be a separate functional change requiring serialized ownership and close/cancel/arrival race checks',
                      'No physical A/B/A, no matched retry/new-byte or RS-stall deltas; tester/whitelists not tested'],
                  tests=successful, retained_failures=failures, pushed=False, public_release=False)
    destination = ROOT / 'docs/releases/2026-10-20-mesh-receive-path.late-arrival.json'
    with destination.open('x') as output:
        json.dump(result, output, indent=2)
    print(json.dumps(dict(result='REPLAY_COMPLETE_NO_LIVE_CANDIDATE', tests=successful, physical_bytes=0)))


if __name__ == '__main__':
    os.umask(0o077)
    {'readback': readback, 'summarize': summarize}[sys.argv[1]]()
