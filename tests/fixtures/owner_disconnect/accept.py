"""Bounded owner readback and HTTPS controls; never changes profile or connection."""
import argparse
import ast
import concurrent.futures
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import shlex
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[3]
WORK = ROOT / 'state-client-build/owner-disconnections-20261022'
SERIAL = '31ce63ba'
GATEWAY = '3a0804cd3da63135dce387d1dff9afdc4588562186abea2e5d00da1d9f5c31ae'
APKS = {
    102: 'bd7eab4920c7358c1343c0a4a6f425df7483301044e051fad3ee365b6a948427',
    103: '0d274fe5e0250301242d0307ae69c345bb27e935d79248d859afde817693fb04',
    104: '828ffe3534e22a61cecacd261f0875d5333682522d9533cb854cb11309436c1a',
}
LIMITS = dict(local_send=32, local_receive=32, peer_receive=32, effective_send=32, local_write_completion=False)
sys.path.insert(0, str(ROOT))
from scripts.owner_android_support import snapshot, save


def adb(command, timeout=25):
    return subprocess.run(['adb', '-s', SERIAL, 'shell', command], text=True, capture_output=True, timeout=timeout)


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def gateway(out):
    code = '''import json,subprocess,hashlib,time,glob
from pathlib import Path
unit='family-connect-restricted-bootstrap.service'
state=dict(line.split('=',1) for line in subprocess.check_output(['systemctl','show',unit,'-p','MainPID,InvocationID,ActiveState,NRestarts,ExecMainStartTimestamp'],text=True).splitlines())
paths=glob.glob('/var/log/journal/*/system.journal');assert len(paths)==1
raw=subprocess.check_output(['journalctl','--file='+paths[0],'-u',unit,'--utc','--no-pager','--all','--since','4 minutes ago','-o','json'],timeout=25)
assert len(raw)<8*1024*1024
root=Path('/opt/apps/family_connect/friends-restricted')
flags={name:(root/'diag67'/name).read_text().strip() for name in ('speed-profile','rtp-pacing','mux-profile')}
print(json.dumps(dict(epoch=time.time(),monotonic=time.monotonic(),state=state,binary_sha256=hashlib.sha256((Path('/proc')/state['MainPID']/'exe').read_bytes()).hexdigest(),profile_sha256=hashlib.sha256((root/'gateway.json').read_bytes()).hexdigest(),operator=flags,journal=raw.decode())))
'''
    started = utc()
    result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=8',
                             'root@186.246.45.246', 'python3 -B -'], input=code, text=True, capture_output=True, timeout=40)
    for suffix, data in [('json', result.stdout), ('stderr', result.stderr)]:
        path = out / ('gateway-raw.' + suffix)
        path.write_text(data)
        path.chmod(0o400)
    save(out / 'gateway-acquisition.json', dict(started=started, completed=utc(), returncode=result.returncode,
        sha256=hashlib.sha256(result.stdout.encode()).hexdigest()))
    result.check_returncode()
    value = json.loads(result.stdout)
    records, errors = runpy.run_path(str(ROOT / 'tests/fixtures/queue_retry/journal.py'))['reassemble'](value.pop('journal').splitlines())
    value['parser_errors'] = errors
    value['records'] = []
    for row in records:
        try:
            message = json.loads(row.get('MESSAGE', ''))
        except ValueError:
            continue
        value['records'].append(dict(at=row['__REALTIME_TIMESTAMP'], invocation=row.get('_SYSTEMD_INVOCATION_ID'), **message))
    save(out / 'gateway-analysis.json', value)
    return value


def healthy(phone, tag=None, candidate=102):
    original=json.loads((WORK/'raw-entry-20261022T095450Z/diagnostic.json').read_text())
    assert phone['version_code'] == candidate and phone['device_support_id'] == original['device_support_id']
    assert phone['state'] == 'CONNECTED' and phone['vpn_capture_open'] and phone['restricted_readiness'] == 'READY'
    current = phone['restricted_session']
    assert current['terminal_reason'] == 'NONE' and 'terminal_observed_at_ms' not in current
    assert current['speed_profile'] == 'P1' and current['reliable_limits'] == LIMITS
    assert current['mux_profile'] == 'CREDIT128' and current['mux_window'] == 131072
    assert tag is None or current['session_tag'] == tag, 'SESSION_CHANGED'
    return current['session_tag']


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('label')
    parser.add_argument('--mode', choices=['gate', 'probe', 'control'], default='gate')
    parser.add_argument('--wait-ready', type=int, default=0)
    parser.add_argument('--candidate', type=int, choices=sorted(APKS), default=102)
    args = parser.parse_args()
    assert re.fullmatch('[a-zA-Z0-9-]+', args.label)
    assert 0 <= args.wait_ready <= 180
    out = WORK / ('accept-' + args.label)
    out.mkdir(exist_ok=False)
    started = time.monotonic()
    phone = snapshot(SERIAL)
    observation = 0
    while phone['state'] != 'CONNECTED' and time.monotonic() - started < args.wait_ready:
        save(out / ('await-%04d.json' % observation), dict(utc=utc(), snapshot=phone))
        assert phone['state'] != 'DISCONNECTED', 'USER_INTENT_NOT_CONNECTED'
        assert not phone.get('restricted_session', {}).get('authorization_denied', False)
        time.sleep(5)
        phone = snapshot(SERIAL)
        observation += 1
    save(out / 'phone-before.json', dict(observed_utc=utc(), snapshot=phone))
    tag = healthy(phone, candidate=args.candidate)
    remote = gateway(out)
    assert remote['binary_sha256'] == GATEWAY and remote['state']['ActiveState'] == 'active' and not remote['parser_errors']
    matching = [row for row in remote['records'] if row.get('diagnostic', {}).get('session_tag') == tag]
    profiles = [row['diagnostic'] for row in matching if row.get('event') == 'session_profile' and row['invocation'] == remote['state']['InvocationID']]
    if not profiles:
        for prior in sorted(WORK.glob('accept-*/gate.json')):
            cached = json.loads(prior.read_text())
            if cached['tag'] != tag or cached['invocation'] != remote['state']['InvocationID'] or cached['gateway'] != GATEWAY:
                continue
            earlier = json.loads((prior.parent / 'gateway-analysis.json').read_text())
            profiles = [row['diagnostic'] for row in earlier['records'] if row.get('event') == 'session_profile'
                and row.get('diagnostic', {}).get('session_tag') == tag and row['invocation'] == remote['state']['InvocationID']]
            if profiles:
                save(out / 'profile-provenance.json', dict(path=str(prior), sha256=hashlib.sha256(prior.read_bytes()).hexdigest()))
                break
    assert len(profiles) == 1 and not any(row.get('event') == 'session_terminal' for row in matching)
    for profile in profiles:
        assert profile['speed_profile'] == 'P1' and profile['reliable_limits'] == LIMITS
        assert profile['mux_profile'] == 'CREDIT128' and profile['mux_window'] == 131072
    source = ROOT / 'tests/fixtures/mesh_throughput_trace/measure.py'
    syntax = ast.parse(source.read_text())
    helpers = [node for node in syntax.body if isinstance(node, ast.FunctionDef) and node.name == 'topology']
    namespace = dict(adb=adb, re=re)
    exec(compile(ast.Module(body=helpers, type_ignores=[]), str(source), 'exec'), namespace)
    topology = namespace['topology']
    initial = topology()
    package_path = adb('pm path com.familyconnect.app.friends').stdout.strip().removeprefix('package:')
    assert package_path.startswith('/data/app/') and '\n' not in package_path
    assert adb('sha256sum ' + shlex.quote(package_path)).stdout.split()[0] == APKS[args.candidate]
    healthy(snapshot(SERIAL), tag, args.candidate)
    save(out / 'gate.json', dict(utc=utc(), tag=tag, profile='P1', topology=initial, gateway=GATEWAY,
        invocation=remote['state']['InvocationID'], pid=remote['state']['MainPID'], apk=APKS[args.candidate], limits=LIMITS,
        version_code=args.candidate))
    print('BOTH_END_P1_GATE_PASS', args.label, flush=True)
    if args.mode == 'gate':
        return
    amount = 1024 if args.mode == 'probe' else (8 << 20) + 12 * 1024
    ledger_dir = WORK / 'traffic-reservations'
    ledger_dir.mkdir(exist_ok=True)
    reserved = sum(json.loads(path.read_text())['reserved_bytes'] for path in ledger_dir.glob('*.json'))
    assert reserved + amount <= 64 << 20
    save(ledger_dir / (args.label + '.json'), dict(utc=utc(), reserved_bytes=amount, previous_reserved=reserved,
        refundable=False, includes_failed_attempts=True))
    requests = []
    cells = []
    stop = threading.Event()
    finished = threading.Event()
    remote_root = '/data/local/tmp/fc-recovery%d-' % args.candidate + args.label
    namespace.update(out=out, remote_root=remote_root, stop=stop, lock=threading.Lock(), requests=requests,
        time=time, shlex=shlex, json=json, fields=('http_code', 'http_version', 'ssl_verify_result', 'remote_ip',
        'local_port', 'num_connects', 'size_download', 'time_namelookup', 'time_connect', 'time_appconnect', 'time_starttransfer', 'time_total'))
    request = next(node for node in ast.walk(syntax) if isinstance(node, ast.FunctionDef) and node.name == 'request')
    exec(compile(ast.Module(body=[request], type_ignores=[]), str(source), 'exec'), namespace)

    def monitor():
        for index in range(180):
            if finished.is_set():
                break
            try:
                current = snapshot(SERIAL)
                save(out / ('monitor-%04d.json' % index), dict(utc=utc(), snapshot=current))
                healthy(current, tag, args.candidate)
            except Exception as error:
                save(out / ('monitor-failure-%04d.json' % index), dict(utc=utc(), error=str(error), kind=type(error).__name__))
                stop.set()
                return
            finished.wait(2)

    def check():
        assert not stop.is_set() and time.monotonic() - started < 350, 'CONTROL_STOPPED'
        assert topology() == initial, 'TOPOLOGY_CHANGED'
        healthy(snapshot(SERIAL), tag, args.candidate)

    watcher = threading.Thread(target=monitor)
    watcher.start()
    failure = None
    try:
        adb('umask 077; mkdir ' + remote_root).check_returncode()
        check()
        if args.mode == 'probe':
            namespace['request']('probe', 1024)
        else:
            for index in range(6):
                check()
                namespace['request']('small-before-' + str(index), 1024)
            for flows in (1, 2):
                check()
                with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                    batch = list(pool.map(lambda index: namespace['request']('bulk-%d-%d' % (flows, index), (4 << 20) // flows), range(flows)))
                wall = max(float(row['metrics']['END']) for row in batch) - min(float(row['metrics']['BEGIN']) for row in batch)
                received = sum(int(row['metrics'].get('BODY_BYTES', 0)) for row in batch)
                cells.append(dict(flows=flows, seconds=wall, bytes=received, mbit_s=received * 8 / wall / 1e6,
                    completed=sum(row['valid'] for row in batch)))
                check()
            for index in range(6):
                check()
                namespace['request']('small-after-' + str(index), 1024)
        check()
    except BaseException as error:
        failure = type(error).__name__ + ': ' + str(error)
        raise
    finally:
        finished.set()
        watcher.join(timeout=15)
        adb('rmdir ' + remote_root)
        save(out / 'summary.json', dict(utc=utc(), mode=args.mode, duration_seconds=time.monotonic() - started,
            cells=cells, attempts=len(requests), completed=sum(row['valid'] for row in requests),
            reserved_bytes=amount, actual_requested=sum(row['intended_bytes'] for row in requests), failure=failure))
        save(out / 'phone-after.json', dict(utc=utc(), snapshot=snapshot(SERIAL)))


if __name__ == '__main__':
    main()
