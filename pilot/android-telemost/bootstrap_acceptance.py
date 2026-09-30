"""Isolated BOOT-1 acceptance: direct mTLS preparation, cached Telemost recovery."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import shlex
import subprocess
import time

HOST = 'root@186.246.45.246'
SSH = ['ssh', '-T', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10']
PACKAGE = 'com.familyconnect.telemosttest'


def run(command, **options):
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            timeout=options.pop('timeout', 30), **options)
    if result.returncode:
        raise RuntimeError('bounded command failed (details redacted)')
    return result.stdout


def events(raw):
    if len(raw) > 4 * 1024 * 1024:
        raise RuntimeError('evidence limit')
    return [json.loads(line) for line in raw.decode().splitlines() if line.strip()]


def ordered(rows, names):
    stages = [row.get('event') for row in rows]
    if any(stages.count(name) != 1 for name in names):
        raise RuntimeError('missing or duplicate lifecycle event')
    positions = [stages.index(name) for name in names]
    if positions != sorted(positions):
        raise RuntimeError('lifecycle order rejected')


def validate(prepared, recovered, gateway, restarted):
    if not restarted:
        raise RuntimeError('process restart not established')
    ordered(prepared, ['bootstrap_cache_stored', 'android_exit'])
    if next(row for row in prepared if row.get('event') == 'android_exit').get('code') != 0:
        raise RuntimeError('cache preparation failed')
    ordered(recovered, ['bootstrap_normal_control_unavailable', 'bootstrap_cache_loaded',
                       'bootstrap_carrier_connected', 'bootstrap_family_auth',
                       'bootstrap_descriptor_received', 'bootstrap_closed_before_dedicated',
                       'connected', 'family_auth', 'mux_open', 'mux_result', 'android_exit'])
    if any(row.get('event') == 'bootstrap_cache_stored' for row in recovered):
        raise RuntimeError('cache refreshed during restricted recovery')
    ordered(gateway, ['bootstrap_seed_ready', 'bootstrap_family_auth', 'CREATING', 'CREATED',
                     'GATEWAY_JOINING', 'READY', 'CLIENT_ISSUED', 'bootstrap_handoff',
                     'family_auth', 'ACTIVE', 'dedicated_resources_closed'])
    starts = [row for row in recovered if row.get('event') == 'start']
    if len(starts) != 1 or starts[0].get('room_method') != 'cached bootstrap Telemost rendezvous':
        raise RuntimeError('non-bootstrap room acquisition')
    environment = [row for row in recovered if row.get('event') == 'android_start']
    if len(environment) != 1 or environment[0].get('network') != 'cellular' or environment[0].get('android') != '12' or environment[0].get('model') != 'Redmi Note 9 Pro' or environment[0].get('abi') != 'arm64-v8a':
        raise RuntimeError('physical cellular environment missing')
    auth = next(row for row in recovered if row.get('event') == 'family_auth')
    if auth.get('accepted') is not True:
        raise RuntimeError('dedicated admission failed')
    https = [row for row in recovered if row.get('event') == 'mux_https']
    if len(https) != 4 or len({row.get('stream_id') for row in https}) != 4 or not all(row.get('passed') and row.get('end_site_tls_verified') and row.get('http_status') == 200 for row in https):
        raise RuntimeError('dedicated HTTPS incomplete')
    dns = [row for row in recovered if row.get('event') == 'mux_dns']
    if len(dns) < 3 or not all(row.get('passed') for row in dns) or not {1, 28}.issubset({row.get('query_type') for row in dns}) or not any(row.get('nxdomain') and row.get('rcode') == 3 for row in dns):
        raise RuntimeError('dedicated DNS incomplete')
    result = next(row for row in recovered if row.get('event') == 'mux_result')
    exit_event = next(row for row in recovered if row.get('event') == 'android_exit')
    if result.get('status') != 'PASS' or exit_event.get('code') != 0 or exit_event.get('cancelled'):
        raise RuntimeError('dedicated smoke failed')
    return {'bootstrap': 'PASS', 'normal_control_unavailable': True, 'cached_before_restart': True,
            'manual_room': False, 'adb_control_forwarding': False, 'ssh_control_forwarding': False,
            'dedicated_https': 4, 'dedicated_dns': True, 'bootstrap_data_proxy': False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--adb', required=True)
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--apk', type=Path, required=True)
    parser.add_argument('--family-dir', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--port', type=int, default=18444)
    args = parser.parse_args()
    token = os.environ.get('YANDEX_TELEMOST_OAUTH_TOKEN', '')
    if not token or len(token) > 4096 or any(character in token for character in '\r\n\0'):
        raise RuntimeError('LIVE BLOCKED: provider credential unavailable (redacted)')
    if os.environ.get('FC_TELEMOST_ROOM') or not 1024 <= args.port <= 65535:
        raise RuntimeError('manual room or invalid port rejected')
    def adb(*command, **options):
        return run([args.adb, *command], **options)
    if adb('shell', 'pm', 'list', 'packages', PACKAGE).strip():
        raise RuntimeError('preserve existing diagnostic installation')
    if adb('shell', 'settings', 'get', 'global', 'wifi_on').strip() != b'0' or adb('shell', 'settings', 'get', 'global', 'mobile_data').strip() != b'1':
        raise RuntimeError('set cellular ON/Wi-Fi OFF before acceptance')
    args.out.mkdir(mode=0o700, parents=True, exist_ok=False)
    directory = '/tmp/fc-boot1-' + secrets.token_hex(8)
    remote = log = None
    created = installed = False
    evidence = None
    try:
        run([*SSH, HOST, 'umask 077; mkdir ' + directory]); created = True
        for name, raw in [('bootstrap-broker', args.binary.read_bytes()), ('family.json', (args.family_dir / 'gateway.json').read_bytes())]:
            mode = '700' if name == 'bootstrap-broker' else '600'
            run([*SSH, HOST, f'umask 077; cat > {directory}/{name}; chmod {mode} {directory}/{name}'], input=raw, timeout=180)
        code = ('import os,sys; os.chdir(' + repr(directory) + '); '
                'os.environ["YANDEX_TELEMOST_OAUTH_TOKEN"]=sys.stdin.readline().rstrip("\\n"); '
                'open("pid","w").write(str(os.getpid())); '
                'os.execv("./bootstrap-broker",["./bootstrap-broker","--family-config","family.json","--duration","8m","--listen",'
                + repr('186.246.45.246:' + str(args.port)) + '])')
        log = (args.out / 'gateway.jsonl').open('wb')
        remote = subprocess.Popen([*SSH, HOST, 'python3 -c ' + shlex.quote(code)], stdin=subprocess.PIPE, stdout=log, stderr=subprocess.DEVNULL)
        remote.stdin.write((token + '\n').encode()); remote.stdin.close()
        deadline = time.monotonic() + 75
        while time.monotonic() < deadline:
            if remote.poll() is not None: raise RuntimeError('seed process stopped')
            if any(row.get('event') == 'bootstrap_seed_ready' for row in events((args.out / 'gateway.jsonl').read_bytes())): break
            time.sleep(.25)
        else: raise RuntimeError('seed READY timeout')
        adb('install', '-t', str(args.apk), timeout=90); installed = True
        def write_input(name, raw):
            adb('shell', '-T', 'run-as', PACKAGE, 'sh', '-c', shlex.quote(f'umask 077; mkdir -p files; cat > files/{name}'), input=raw)
        write_input('family.input', (args.family_dir / 'valid.json').read_bytes())
        def phase(name, control):
            write_input('bootstrap.input', name.encode())
            write_input('broker.input', control.encode())
            adb('shell', 'am', 'start', '-n', PACKAGE + '/.ProbeActivity', '--ez', 'run', 'true')
            deadline = time.monotonic() + 210
            while time.monotonic() < deadline:
                raw = adb('shell', '-T', 'run-as', PACKAGE, 'sh', '-c', shlex.quote('head -c 4194305 files/evidence.jsonl 2>/dev/null || true'))
                if token.encode() in raw or b'telemost.yandex.ru/j/' in raw: raise RuntimeError('sensitive evidence rejected')
                rows = events(raw)
                (args.out / (name + '.jsonl')).write_bytes(raw)
                if any(row.get('event') == 'android_exit' for row in rows): return rows
                time.sleep(1)
            raise RuntimeError('diagnostic phase timeout')
        prepared = phase('refresh', f'https://186.246.45.246:{args.port}')
        ordered(prepared, ['bootstrap_cache_stored', 'android_exit'])
        if next(row for row in prepared if row.get('event') == 'android_exit').get('code') != 0:
            raise RuntimeError('preparation failed')
        adb('shell', 'am', 'force-stop', PACKAGE)
        if adb('shell', 'sh', '-c', shlex.quote('pidof ' + PACKAGE + ' || true'), timeout=10).strip(): raise RuntimeError('restart failed')
        write_input('mux.input', b'{"mode":"public"}')
        write_input('evidence.jsonl', b'')
        recovered = phase('recover', 'https://127.0.0.1:1')
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            gateway = events((args.out / 'gateway.jsonl').read_bytes())
            if any(row.get('event') == 'dedicated_resources_closed' for row in gateway): break
            time.sleep(.25)
        evidence = validate(prepared, recovered, gateway, restarted=True)
        evidence.update(binary_sha256=hashlib.sha256(args.binary.read_bytes()).hexdigest(), apk_sha256=hashlib.sha256(args.apk.read_bytes()).hexdigest())
    finally:
        cleanup = []
        if installed:
            for command in [('shell', 'am', 'force-stop', PACKAGE), ('uninstall', PACKAGE)]:
                try: adb(*command)
                except Exception: cleanup.append('android')
            try:
                if adb('shell', 'pm', 'list', 'packages', PACKAGE).strip(): cleanup.append('apk_retained')
                if adb('shell', 'sh', '-c', shlex.quote('pidof libfc_telemost.so || true')).strip(): cleanup.append('native_process_retained')
            except Exception: cleanup.append('android_cleanup_unverified')
        if created:
            code = ('import os,signal,time,shutil; from pathlib import Path; root=Path(' + repr(directory) + '); '
                    'pid=int((root/"pid").read_text()) if (root/"pid").exists() else 0; '
                    'owned=lambda: pid>1 and Path("/proc/%s/exe"%pid).exists() and os.readlink("/proc/%s/exe"%pid)==str(root/"bootstrap-broker"); '
                    'os.kill(pid,signal.SIGTERM) if owned() else None; time.sleep(3); '
                    'os.kill(pid,signal.SIGKILL) if owned() else None; time.sleep(.2); assert not owned(); shutil.rmtree(root)')
            try: run([*SSH, HOST, 'python3 -c ' + shlex.quote(code)], timeout=15)
            except Exception: cleanup.append('gateway')
        if remote is not None:
            try: remote.wait(timeout=5)
            except subprocess.TimeoutExpired:
                remote.terminate()
                try: remote.wait(timeout=5)
                except subprocess.TimeoutExpired: remote.kill(); remote.wait()
        if log is not None: log.close()
        (args.out / 'cleanup.json').write_text(json.dumps({'errors': cleanup, 'production_changed': False}) + '\n')
        if cleanup: raise RuntimeError('cleanup incomplete')
    (args.out / 'evidence.json').write_text(json.dumps(evidence, indent=2) + '\n')
    print(json.dumps(evidence))


if __name__ == '__main__':
    main()
