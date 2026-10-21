"""Finite observer for one existing CLI peer; no listener or credentials issuer."""
import datetime
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


def main():
    os.umask(0o077)
    root = Path(sys.argv[1]).resolve()
    role = sys.argv[2]
    assert role in ('probe', 'echo')
    stopped = False

    def stop(signum, frame):
        nonlocal stopped
        stopped = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    environment = {'PATH': os.defpath, 'GOMAXPROCS': '2', 'FC_TELEMOST_ROOM': (root/'room.input').read_text().strip()}
    command = [str(root/'telemost-host-compare'), '--role', role, '--mode', 'vp8', '--family-config', str(root/'family.json'), '--duration', '8m', '--metrics-interval', '5s']
    if role == 'echo':
        environment['FC_HOST_COMPARE_FIXTURE'] = '1'
        command += ['--mux-gateway', '--mux-test-loopback-port', '18764']
    else:
        command += ['--mux-config', str(root/'mux.json')]
    started = time.monotonic()
    with (root/'peer.jsonl').open('x') as output, (root/'peer.stderr').open('x') as errors, (root/'resources.jsonl').open('x') as resources:
        child = subprocess.Popen(command, env=environment, stdout=output, stderr=errors)
        try:
            while child.poll() is None and not stopped and time.monotonic()-started < 490:
                memory = {line.split(':')[0]:line.split(':')[1].strip() for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith(('MemAvailable:', 'SwapFree:'))}
                record = dict(utc=datetime.datetime.now(datetime.UTC).isoformat(),monotonic=time.monotonic(),cpu=Path('/proc/stat').read_text().splitlines()[0],load=os.getloadavg(),memory=memory,network=Path('/proc/net/dev').read_text())
                for name in ['stat','schedstat','status']:
                    try:
                        text=(Path('/proc')/str(child.pid)/name).read_text()
                        record[name]=text if name!='status' else [line for line in text.splitlines() if line.startswith(('VmRSS:', 'VmHWM:', 'Threads:'))]
                    except FileNotFoundError:
                        pass
                group=Path('/proc/self/cgroup').read_text().strip().split('::')[-1]
                for name in ['cpu.stat','memory.current','memory.events']:
                    location=Path('/sys/fs/cgroup')/group.lstrip('/')/name
                    if location.exists():record[name]=location.read_text()
                resources.write(json.dumps(record)+'\n');resources.flush()
                if (root/'peer.jsonl').stat().st_size > 32*1024*1024:
                    stopped=True
                time.sleep(2)
        finally:
            terminated=child.poll() is None
            if terminated:child.terminate()
            try:child.wait(timeout=10)
            except subprocess.TimeoutExpired:child.kill();child.wait(timeout=5)
            (root/'exit.json').write_text(json.dumps(dict(exit=child.returncode,terminated=terminated,stopped=stopped,seconds=time.monotonic()-started)))


if __name__ == '__main__':
    main()
