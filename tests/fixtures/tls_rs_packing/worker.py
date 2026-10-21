"""Observe only the owned test child and its cgroup; no production profiling."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


def main():
    os.umask(0o077)
    root=Path(sys.argv[1]).resolve()
    role=sys.argv[2]
    config=json.loads((root/'capacity.json').read_text())
    stopped=False
    def stop(signum,frame):
        nonlocal stopped
        stopped=True
    signal.signal(signal.SIGTERM,stop)
    signal.signal(signal.SIGINT,stop)
    environment={'PATH':os.defpath,'GOMAXPROCS':'2','FC_TELEMOST_ROOM':(root/'room.input').read_text().strip(),'FC_LAB_WIRE_LIMIT':(root/'wire-limit.input').read_text().strip()}
    command=[str(root/'telemost-capacity'),'--role',role,'--mode','vp8','--family-config',str(root/'family.json'),'--capacity-config',str(root/'capacity.json'),'--duration','8m' if config['Mode']=='P' else '210s','--metrics-interval','5s']
    if config['Mode']=='P' and role=='echo':
        environment['FC_HOST_COMPARE_FIXTURE']='1'
        command+=['--mux-gateway','--mux-test-loopback-port','18764']
    started=time.monotonic()
    with (root/'peer.jsonl').open('x') as output,(root/'peer.stderr').open('x') as errors,(root/'resources.jsonl').open('x') as resources:
        child=subprocess.Popen(command,env=environment,stdout=output,stderr=errors)
        try:
            while child.poll() is None and not stopped and time.monotonic()-started<490:
                record=dict(monotonic=time.monotonic(),cpu=[line for line in Path('/proc/stat').read_text().splitlines() if line.startswith('cpu')],load=os.getloadavg(),threads={})
                process=Path('/proc')/str(child.pid)
                for name in ['stat','schedstat','status']:
                    try:
                        value=(process/name).read_text()
                        record[name]=value if name!='status' else [line for line in value.splitlines() if line.startswith(('VmRSS:','VmHWM:','Threads:'))]
                    except FileNotFoundError: pass
                try:
                    for thread in (process/'task').iterdir():
                        try: record['threads'][thread.name]=dict(stat=(thread/'stat').read_text(),schedstat=(thread/'schedstat').read_text())
                        except FileNotFoundError: pass
                except FileNotFoundError: pass
                group=Path('/proc/self/cgroup').read_text().strip().split('::')[-1]
                for name in ['cpu.stat','cpu.max','memory.current','memory.events']:
                    location=Path('/sys/fs/cgroup')/group.lstrip('/')/name
                    if location.exists(): record[name]=location.read_text()
                resources.write(json.dumps(record)+'\n');resources.flush()
                if (root/'peer.jsonl').stat().st_size>32*1024*1024: stopped=True
                time.sleep(1)
        finally:
            terminated=child.poll() is None
            if terminated:child.terminate()
            try:child.wait(timeout=10)
            except subprocess.TimeoutExpired:child.kill();child.wait(timeout=5)
            (root/'exit.json').write_text(json.dumps(dict(exit=child.returncode,terminated=terminated,stopped=stopped,seconds=time.monotonic()-started)))


if __name__=='__main__':main()
