"""One disposable automatic-room smoke; no manual room input or production writes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import shlex
import socket
import subprocess
import time

SSH = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10']
HOST = 'root@186.246.45.246'
PACKAGE = 'com.familyconnect.telemosttest'


def run(command, **kwargs):
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            timeout=kwargs.pop('timeout', 30), **kwargs)
    if result.returncode:
        raise RuntimeError('bounded external command failed (details redacted)')
    return result.stdout


def events(raw):
    return [json.loads(line) for line in raw.decode().splitlines() if line.strip()]


def validate(gateway, android):
    stages = [row['event'] for row in gateway]
    ordered = ['CREATING', 'CREATED', 'GATEWAY_JOINING', 'READY', 'CLIENT_ISSUED', 'family_auth', 'ACTIVE']
    if not all(stages.count(stage) == 1 for stage in ordered):
        raise RuntimeError('automatic broker lifecycle incomplete')
    if [stages.index(stage) for stage in ordered] != sorted(stages.index(stage) for stage in ordered):
        raise RuntimeError('gateway-first ordering failed')
    starts = [row for row in android if row.get('event') == 'start']
    if len(starts) != 1 or starts[0].get('room_method') != 'authenticated automatic broker':
        raise RuntimeError('manual room path detected')
    auth = [row for row in android if row.get('event') == 'family_auth']
    if len(auth) != 1 or not auth[0].get('accepted'):
        raise RuntimeError('Family admission missing')
    https = [row for row in android if row.get('event') == 'mux_https']
    if len(https) != 4 or not all(row.get('passed') and row.get('end_site_tls_verified') and row.get('http_status') == 200 for row in https):
        raise RuntimeError('existing short public HTTPS proof failed')
    result = [row for row in android if row.get('event') == 'mux_result']
    if len(result) != 1 or result[0].get('status') != 'PASS':
        raise RuntimeError('mux smoke failed')
    exits = [row for row in android if row.get('event') == 'android_exit']
    if len(exits) != 1 or exits[0].get('code') != 0:
        raise RuntimeError('native process did not exit cleanly')
    return {'automatic': True, 'provider_http_status': 201, 'gateway_ready': True,
            'family_tls': True, 'https_verified': len(https), 'manual_room': False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--adb', required=True)
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--apk', type=Path, required=True)
    parser.add_argument('--family-dir', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    token = os.environ.get('YANDEX_TELEMOST_OAUTH_TOKEN')
    if not token:
        raise RuntimeError('YANDEX_TELEMOST_OAUTH_TOKEN absent; live stopped')
    if '\n' in token or '\r' in token:
        raise RuntimeError('invalid token input (redacted)')
    args.out.mkdir(mode=0o700, parents=True, exist_ok=False)
    def adb(*command, **kwargs):
        return run([args.adb, *command], **kwargs)
    if adb('shell', 'pm', 'list', 'packages', PACKAGE).strip():
        raise RuntimeError('diagnostic APK already installed; preserve foreign installation')
    wifi = adb('shell', 'settings', 'get', 'global', 'wifi_on').strip()
    data = adb('shell', 'settings', 'get', 'global', 'mobile_data').strip()
    if wifi not in (b'0', b'1') or data not in (b'0', b'1'):
        raise RuntimeError('radio state not safely restorable')
    directory = '/tmp/fc-rb1-' + secrets.token_hex(8)
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        port = listener.getsockname()[1]
    remote = None
    installed = created = reversed_port = False
    gateway_log = None
    try:
        run([*SSH, HOST, 'umask 077; mkdir ' + directory])
        created = True
        for name, raw in [('room-broker', args.binary.read_bytes()), ('family.json', (args.family_dir / 'gateway.json').read_bytes())]:
            run([*SSH, HOST, f'umask 077; cat > {directory}/{name}; chmod ' + ('700' if name == 'room-broker' else '600') + f' {directory}/{name}'], input=raw, timeout=180)
        code = ('import os,sys; os.chdir(' + repr(directory) + '); '
                'os.environ["YANDEX_TELEMOST_OAUTH_TOKEN"]=sys.stdin.readline().rstrip("\\n"); '
                'open("pid","w").write(str(os.getpid())); '
                'os.execv("./room-broker",["./room-broker","--family-config","family.json","--duration","3m"])')
        gateway_log = (args.out / 'gateway.jsonl').open('wb')
        remote = subprocess.Popen([*SSH, '-o', 'ExitOnForwardFailure=yes', '-L', f'{port}:127.0.0.1:18443', HOST,
                                   'python3 -c ' + shlex.quote(code)], stdin=subprocess.PIPE, stdout=gateway_log, stderr=subprocess.DEVNULL)
        remote.stdin.write((token + '\n').encode())
        remote.stdin.close()
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            if remote.poll() is not None:
                raise RuntimeError('disposable broker startup failed')
            if b'control_ready' in (args.out / 'gateway.jsonl').read_bytes():
                break
            time.sleep(.2)
        else:
            raise RuntimeError('control startup timeout')
        adb('install', '-t', str(args.apk), timeout=90)
        installed = True
        adb('reverse', f'tcp:{port}', f'tcp:{port}')
        reversed_port = True
        adb('shell', 'svc', 'data', 'enable')
        adb('shell', 'svc', 'wifi', 'disable')
        for name, raw in [('family.input', (args.family_dir / 'valid.json').read_bytes()),
                          ('broker.input', f'https://127.0.0.1:{port}'.encode()),
                          ('mux.input', b'{"mode":"public"}')]:
            command = f'umask 077; mkdir -p files; cat > files/{name}'
            adb('shell', '-T', 'run-as', PACKAGE, 'sh', '-c', shlex.quote(command), input=raw)
        adb('shell', 'am', 'start', '-n', PACKAGE + '/.ProbeActivity', '--ez', 'run', 'true')
        deadline = time.monotonic() + 150
        while time.monotonic() < deadline:
            raw = adb('shell', '-T', 'run-as', PACKAGE, 'sh', '-c', shlex.quote('cat files/evidence.jsonl 2>/dev/null || true'))
            if token.encode() in raw:
                raise RuntimeError('secret boundary violation')
            (args.out / 'android.jsonl').write_bytes(raw)
            rows = events(raw)
            if any(row.get('event') == 'android_exit' for row in rows):
                break
            time.sleep(1)
        else:
            raise RuntimeError('short automatic smoke timeout')
        gateway = events((args.out / 'gateway.jsonl').read_bytes())
        evidence = validate(gateway, rows)
        evidence.update(broker_sha256=hashlib.sha256(args.binary.read_bytes()).hexdigest(),
                        apk_sha256=hashlib.sha256(args.apk.read_bytes()).hexdigest())
        (args.out / 'evidence.json').write_text(json.dumps(evidence, indent=2) + '\n')
        print(json.dumps(evidence), flush=True)
    finally:
        cleanup = []
        if installed:
            for command in [('shell', 'am', 'force-stop', PACKAGE), ('uninstall', PACKAGE)]:
                try: adb(*command)
                except Exception: cleanup.append('android')
        if reversed_port:
            try: adb('reverse', '--remove', f'tcp:{port}')
            except Exception: cleanup.append('reverse')
        for radio, value in [('wifi', wifi), ('data', data)]:
            try: adb('shell', 'svc', radio, 'enable' if value == b'1' else 'disable')
            except Exception: cleanup.append('radio')
        if installed and adb('shell', 'pm', 'list', 'packages', PACKAGE).strip():
            cleanup.append('apk_retained')
        if adb('shell', 'settings', 'get', 'global', 'wifi_on').strip() != wifi or adb('shell', 'settings', 'get', 'global', 'mobile_data').strip() != data:
            cleanup.append('radio_mismatch')
        if created:
            code = ('import os,signal,time,shutil; from pathlib import Path; root=Path(' + repr(directory) + '); '
                    'pid=int((root/"pid").read_text()) if (root/"pid").exists() else 0; '
                    'owned=lambda: pid>1 and Path("/proc/%s/exe"%pid).exists() and os.readlink("/proc/%s/exe"%pid)==str(root/"room-broker"); '
                    'os.kill(pid,signal.SIGTERM) if owned() else None; time.sleep(2); '
                    'os.kill(pid,signal.SIGKILL) if owned() else None; time.sleep(.2); '
                    'assert not owned(); shutil.rmtree(root)')
            try: run([*SSH, HOST, 'python3 -c ' + shlex.quote(code)], timeout=15)
            except Exception: cleanup.append('gateway')
        if remote is not None:
            try: remote.wait(timeout=5)
            except subprocess.TimeoutExpired:
                remote.terminate()
                try: remote.wait(timeout=5)
                except subprocess.TimeoutExpired: remote.kill(); remote.wait()
        if gateway_log is not None:
            gateway_log.close()
        (args.out / 'cleanup.json').write_text(json.dumps({'errors': cleanup, 'radios_restored': not cleanup}) + '\n')
        if cleanup:
            raise RuntimeError('cleanup requires attention: ' + ','.join(cleanup))


if __name__ == '__main__':
    main()
