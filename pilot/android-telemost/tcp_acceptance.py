"""Run single-stream cases; room only in environment, no automatic gate promotion."""
import argparse
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time


class Fixture:
    def __init__(self, host, output, source=None):
        self.ssh = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=12', 'root@' + host]
        self.output = output
        self.directory = None
        self.source = source or Path(__file__).with_name('tcp_fixture.py')

    def start(self, mode, public):
        self.directory = subprocess.check_output(self.ssh + ['mktemp -d /tmp/fc-eu4-fixture.XXXXXXXX'], text=True).strip()
        if not re.fullmatch(r'/tmp/fc-eu4-fixture\.[a-zA-Z0-9]{8}', self.directory):
            self.directory = None
            raise RuntimeError('invalid fixture directory')
        source = self.source.read_bytes()
        command = f'cat > {self.directory}/fixture.py; chown -R nobody:nogroup {self.directory}'
        subprocess.run(self.ssh + [command], input=source, check=True, timeout=30)
        code = f'''
import os,pathlib,subprocess
folder=pathlib.Path({self.directory!r})
os.chdir(folder)
os.umask(0o077)
with open('fixture.log','wb') as output:
    child=subprocess.Popen(['python3',str(folder/'fixture.py'),'--mode',{mode!r},'--bind',{'0.0.0.0' if public else '127.0.0.1'!r}],stdout=output,stderr=output,stdin=subprocess.DEVNULL,start_new_session=True)
pathlib.Path('pid').write_text(str(child.pid))
'''
        subprocess.run(self.ssh + ['runuser -u nobody -- python3 -c ' + shlex.quote(code)], check=True, timeout=30)
        for _ in range(30):
            rows = self.collect()
            if rows and rows[0].get('event') == 'fixture_ready':
                return rows[0]['port']
            time.sleep(0.2)
        raise RuntimeError('fixture not ready')

    def collect(self):
        if not self.directory:
            return []
        raw = subprocess.check_output(self.ssh + [f'head -c 65536 {self.directory}/fixture.log'], timeout=20)
        self.output.write_bytes(raw)
        return [json.loads(line) for line in raw.splitlines() if line.startswith(b'{')]

    def close(self):
        if not self.directory:
            return
        self.collect()
        code = f'''
import os,pathlib,signal,shutil,time
folder=pathlib.Path({self.directory!r})
path=folder/'pid'
pid=int(path.read_text()) if path.exists() else 0
def alive():
    process=pathlib.Path('/proc')/str(pid)
    return pid>0 and (process/'cwd').exists() and (process/'cwd').resolve()==folder and str(folder/'fixture.py').encode() in (process/'cmdline').read_bytes().split(b'\\0')
if alive(): os.kill(pid,signal.SIGTERM)
for _ in range(30):
    if not alive(): break
    time.sleep(0.1)
if alive(): raise RuntimeError('fixture still alive')
shutil.rmtree(folder)
print('FIXTURE_REMOVED')
'''
        subprocess.run(self.ssh + ['python3 -c ' + shlex.quote(code)], check=True, timeout=30)


def validate_tcp_evidence(case, android, gateway):
    closes = [row for row in gateway if row.get('event') == 'tcp_gateway']
    if len(closes) != 1 or closes[0]['stats']['active_sockets'] != 0 or closes[0]['stats']['retained_bytes'] != 0:
        raise RuntimeError('gateway socket/buffer cleanup unproven')
    if closes[0]['stats']['open_requests'] != 1:
        raise RuntimeError('unexpected OPEN count')
    if case in ('cancel', 'remote-exit', 'network-loss'):
        exits = [row for row in android if row.get('event') == 'android_exit']
        if len(exits) != 1 or exits[0]['code'] == 0 or exits[0]['cancelled'] != (case == 'cancel'):
            raise RuntimeError('expected interruption not proven')
        if not any(row.get('event') == 'tcp_open' for row in android):
            raise RuntimeError('no stream before fault')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--adb', required=True)
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--family-dir', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--case', choices=['local', 'https', 'download', 'multi', 'sustained', 'remote_close', 'remote_half_close', 'remote_reset', 'timeout', 'refused', 'cancel', 'remote-exit', 'network-loss'], required=True)
    parser.add_argument('--public-fixture', action='store_true')
    args = parser.parse_args()
    if not os.environ.get('FC_TELEMOST_ROOM'):
        raise RuntimeError('room environment required (redacted)')
    args.out.mkdir(mode=0o700, parents=True, exist_ok=False)
    fixture = None
    config = {'host': 'example.com', 'port': 443, 'mode': 'https', 'path': '/', 'timeout_ms': 10000}
    public = args.public_fixture or args.case in ('https', 'download')
    try:
        if args.case == 'download':
            config.update(host='speed.cloudflare.com', path='/__down?bytes=10485760')
        if args.case not in ('https', 'download'):
            fixture = Fixture('185.251.89.19' if public else '186.246.45.246', args.out / 'fixture.jsonl')
            mode = args.case if args.case in ('remote_close', 'remote_half_close', 'remote_reset', 'timeout') else 'echo'
            port = fixture.start(mode, public)
            config = {'host': '185.251.89.19' if public else '127.0.0.1', 'port': port, 'mode': mode, 'bytes': 10 * 1024 * 1024 if args.case == 'multi' else 65536, 'timeout_ms': 3000}
            if args.case in ('sustained', 'cancel', 'remote-exit', 'network-loss'):
                config.update(seconds=300, mbit=0.6)
            if args.case in ('timeout', 'refused'):
                config.update(mode='open_error', expected_error='timeout' if args.case == 'timeout' else 'connection_refused')
            if args.case == 'refused':
                fixture.close()
                fixture = None
        path = args.out / 'request.json'
        path.write_text(json.dumps(config))
        command = [sys.executable, str(Path(__file__).with_name('live.py')), '--adb', args.adb, '--binary', str(args.binary), '--family-dir', str(args.family_dir), '--independent-observer', '--tcp-config', str(path), '--out', str(args.out / 'flow')]
        if not public:
            command += ['--tcp-test-loopback-port', str(config['port'])]
        if args.case in ('cancel', 'remote-exit', 'network-loss'):
            command += ['--case', args.case]
        with (args.out / 'runner.log').open('wb') as output:
            run = subprocess.run(command, stdout=output, stderr=output, timeout=1600)
        if fixture:
            fixture.collect()
        if run.returncode:
            raise RuntimeError('TCP case failed: ' + args.case)
        android = [json.loads(line) for line in (args.out / 'flow/A.jsonl').read_text().splitlines() if line.endswith('}')]
        gateway = [json.loads(line) for line in (args.out / 'flow/B.jsonl').read_text().splitlines() if line.endswith('}')]
        validate_tcp_evidence(args.case, android, gateway)
        proofs = [row for row in android if row.get('event') == 'tcp_result']
        if args.case not in ('cancel', 'remote-exit', 'network-loss') and (len(proofs) != 1 or proofs[0]['status'] != 'PASS'):
            raise RuntimeError('TCP proof missing')
        if args.case == 'download' and proofs[0]['download_bytes'] != 10485760:
            raise RuntimeError('download exact length failed')
        if fixture and args.case in ('local', 'multi', 'sustained'):
            target = [row for row in fixture.collect() if row.get('event') == 'fixture_result']
            if len(target) != 1 or target[0]['bytes'] != proofs[0]['upload_bytes'] or target[0]['sha256'] != proofs[0]['upload_sha256']:
                raise RuntimeError('target exact validation failed')
        print(json.dumps({'case': args.case, 'result': proofs, 'runner_exit': run.returncode}), flush=True)
    finally:
        if fixture:
            fixture.close()


if __name__ == '__main__':
    main()
