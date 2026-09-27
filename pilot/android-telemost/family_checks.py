#!/usr/bin/env python3
"""Isolated physical native auth/lifecycle checks; only disposable credentials."""
import argparse
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import tarfile
import time

SSH = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=12', 'root@186.246.45.246']


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--adb', required=True)
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--native-test', type=Path, required=True)
    parser.add_argument('--family-dir', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--case', choices=['unit', 'ws-close', 'peer-close', 'replay'], required=True)
    args = parser.parse_args()
    args.out.mkdir(mode=0o700, parents=True, exist_ok=False)
    room = os.environ['FC_TELEMOST_ROOM']
    if not room or len(room) > 2048 or '\n' in room or '\r' in room:
        raise RuntimeError('invalid room (redacted)')
    root = Path(__file__).resolve().parents[2]

    def adb(*command, **options):
        return subprocess.run([args.adb, *command], capture_output=True, timeout=30, check=True, **options)

    directory = subprocess.check_output(SSH + ['mktemp -d /tmp/fc-eu3-check.XXXXXXXX'], text=True).strip()
    if not re.fullmatch(r'/tmp/fc-eu3-check\.[a-zA-Z0-9]{8}', directory):
        raise RuntimeError('unexpected remote path')
    android = None
    remote = None
    native = None
    generation = 0

    def events():
        path = args.out / f'B{generation}.jsonl'
        return [json.loads(line) for line in path.read_text().splitlines() if line.endswith('}')] if path.exists() else []

    def stop_remote():
        code = f'import os,pathlib,signal; folder=pathlib.Path({directory!r}); pid=int((folder/"pid").read_text()); executable=pathlib.Path(f"/proc/{{pid}}/exe"); os.kill(pid,signal.SIGTERM) if executable.exists() and str(executable.resolve())==str(folder/"telemost-live") else None'
        subprocess.run(SSH + ['python3 -c ' + shlex.quote(code)], check=True, timeout=25)
        remote.wait(timeout=20)

    def start_remote():
        nonlocal remote, generation
        generation += 1
        code = f'import os,sys; os.chdir({directory!r}); os.environ["FC_TELEMOST_ROOM"]=sys.stdin.readline().rstrip("\\n"); open("pid","w").write(str(os.getpid())); os.execvpe("./telemost-live",["./telemost-live","--role","echo","--mode","vp8","--family-config","family.input","--duration","3m"],os.environ)'
        with (args.out / f'B{generation}.jsonl').open('w') as output, (args.out / f'B{generation}.stderr').open('w') as errors:
            remote = subprocess.Popen(SSH + ['runuser -u nobody -- python3 -c ' + shlex.quote(code)], stdin=subprocess.PIPE, stdout=output, stderr=errors, text=True)
        remote.stdin.write(room + '\n')
        remote.stdin.close()
        deadline = time.monotonic() + 60
        while not any(row.get('event') == 'connected' for row in events()):
            if remote.poll() is not None or time.monotonic() > deadline:
                raise RuntimeError('remote join failed')
            time.sleep(0.25)

    try:
        android = adb('shell', 'mktemp', '-d', '/data/local/tmp/fc-eu3-check.XXXXXXXX').stdout.decode().strip()
        if not re.fullmatch(r'/data/local/tmp/fc-eu3-check\.[a-zA-Z0-9]{8}', android):
            android = None
            raise RuntimeError('unexpected Android path')
        archive = args.out / 'artifact.tar'
        with tarfile.open(archive, 'w') as bundle:
            bundle.add(args.binary, arcname='telemost-live')
            bundle.add(args.family_dir / 'gateway.json', arcname='family.input')
            bundle.add(root / 'carrier/licenses', arcname='licenses')
        with archive.open('rb') as source:
            subprocess.run(SSH + [f'tar -xf - -C {directory} && chown -R nobody:nogroup {directory}'], stdin=source, check=True, timeout=45)
        archive.unlink()
        adb('push', str(args.native_test), android + '/native.test')
        adb('push', str(root / 'carrier/licenses'), android + '/licenses')
        adb('shell', 'chmod', '700', android + '/native.test')
        adb('shell', '-T', 'sh', '-c', shlex.quote(f'umask 077; cat > {android}/family.input'), input=(args.family_dir / 'valid.json').read_bytes())
        if args.case != 'unit':
            start_remote()
        pattern = '^TestLiveFamilyHandshakeReplay$' if args.case == 'replay' else '^TestLiveSignalingClosure$'
        if args.case == 'unit':
            pattern = '^Test(CanonicalMatrixAndCancellation|AdmissionFailures|ExpiredLeaseAndBounds|TLSRecordReplayRejected|HandshakeProofReplayRejected)$'
        command = (f'read -r FC_TELEMOST_ROOM; export FC_TELEMOST_ROOM; '
                   f'export FC_FAMILY_TEST_PROFILE={android}/family.input; '
                   f'export FC_FAMILY_REPLAY_READY={android}/fresh.ready; '
                   f'export FC_TEST_LIVE_SIGNALING_CLOSE=1 FC_TEST_LIVE_FAMILY_REPLAY=1 FC_TEST_LIVE_PEER_CLOSE={int(args.case == "peer-close")}; '
                   'export SSL_CERT_DIR=/system/etc/security/cacerts:/apex/com.android.conscrypt/cacerts; '
                   f'echo $$ > {android}/pid; exec {android}/native.test -test.run {shlex.quote(pattern)} -test.v -test.timeout=120s')
        with (args.out / 'A.log').open('w') as output:
            native = subprocess.Popen([args.adb, 'shell', '-T', 'sh', '-c', shlex.quote(command)], stdin=subprocess.PIPE, stdout=output, stderr=subprocess.STDOUT, text=True)
        native.stdin.write(room + '\n')
        native.stdin.close()
        deadline = time.monotonic() + 135
        restarted = False
        while native.poll() is None and time.monotonic() < deadline:
            output = (args.out / 'A.log').read_text()
            if room in output:
                raise RuntimeError('sensitive output rejected')
            if args.case == 'replay' and not restarted and 'FAMILY_REPLAY_CAPTURE_READY' in output:
                if not any(row.get('event') == 'family_auth' and row.get('accepted') is True for row in events()):
                    raise RuntimeError('initial authentication evidence missing')
                stop_remote()
                start_remote()
                adb('shell', 'touch', android + '/fresh.ready')
                restarted = True
            time.sleep(0.25)
        if native.poll() is None:
            raise RuntimeError('native test deadline')
        output = (args.out / 'A.log').read_text()
        if native.returncode or '--- PASS:' not in output or room in output:
            raise RuntimeError('native test failed; inspect private sanitized test output')
        if args.case == 'replay':
            rejected = any(row.get('event') == 'family_auth' and row.get('accepted') is False for row in events())
            admitted = any(row.get('event') == 'family_auth' and row.get('accepted') is True for row in events())
            if not restarted or not rejected or admitted:
                raise RuntimeError('fresh server replay rejection not proven')
        print('PHYSICAL_NATIVE_CHECK_PASS', args.case, flush=True)
        for line in output.splitlines():
            if line.startswith(('=== RUN', '--- PASS', 'PASS')):
                print(line, flush=True)
    finally:
        cleanup_failed = False
        if android:
            cleanup = f'if [ -f {android}/pid ]; then pid=$(cat {android}/pid); if [ "$(readlink /proc/$pid/exe)" = "{android}/native.test" ]; then kill -TERM "$pid"; sleep 2; if [ "$(readlink /proc/$pid/exe)" = "{android}/native.test" ]; then kill -KILL "$pid"; sleep 1; fi; fi; fi; rm -rf {android}'
            try:
                adb('shell', '-T', 'sh', '-c', shlex.quote(cleanup))
            except subprocess.SubprocessError:
                cleanup_failed = True
                print('ANDROID_CLEANUP_UNCONFIRMED', flush=True)
        if native:
            try:
                native.wait(timeout=10)
            except subprocess.TimeoutExpired:
                cleanup_failed = True
        cleanup = f'import os,pathlib,signal,shutil,time; folder=pathlib.Path({directory!r}); pidfile=folder/"pid"; pid=int(pidfile.read_text()) if pidfile.exists() else 0; executable=pathlib.Path(f"/proc/{{pid}}/exe"); matched=pid>0 and executable.exists() and str(executable.resolve())==str(folder/"telemost-live"); os.kill(pid,signal.SIGTERM) if matched else None; time.sleep(2); alive=matched and executable.exists() and str(executable.resolve())==str(folder/"telemost-live"); os.kill(pid,signal.SIGKILL) if alive else None; shutil.rmtree(folder); print("REMOTE_TEMP_REMOVED; FORCED_KILL="+str(alive))'
        subprocess.run(SSH + ['python3 -c ' + shlex.quote(cleanup)], check=True, timeout=30)
        if remote:
            remote.wait(timeout=10)
        if cleanup_failed:
            raise RuntimeError('cleanup incomplete')


if __name__ == '__main__':
    main()
