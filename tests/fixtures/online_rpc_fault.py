import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import time


def main():
    raw = sys.stdin.buffer.read(1024*1024+1)
    request = json.loads(raw)
    config = Path(sys.argv[6])
    fault_path = config.parent/'rpc-fault.json'
    if fault_path.exists():
        fault = json.loads(fault_path.read_bytes())
        if fault['kind'] == 'drop-before' and request['action'] == 'online' and request['payload']['command'] == fault['command']:
            try:
                descriptor = os.open(config.parent/'rpc-fault-consumed', os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o600)
            except FileExistsError:
                pass
            else:
                os.close(descriptor)
                os._exit(86)
    result = subprocess.run([sys.executable, *sys.argv[1:]], input=raw, capture_output=True, timeout=120)
    if fault_path.exists() and result.returncode == 0:
        fault = json.loads(fault_path.read_bytes())
        if request['action'] == 'online' and request['payload']['command'] == fault['command']:
            try:
                descriptor = os.open(config.parent/'rpc-fault-consumed', os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o600)
            except FileExistsError:
                pass
            else:
                os.close(descriptor)
                if fault['kind'] == 'drop':
                    os._exit(86)
                if fault['kind'] == 'stale-runtime':
                    settings = json.loads(config.read_bytes())
                    supervisor = runpy.run_path('/usr/bin/systemctl')['request']
                    unit = 'test-'+settings['gateway_slot']+'.service'
                    before = supervisor(dict(command='show', unit=unit))['state']
                    supervisor(dict(command='kill', unit=unit))
                    observer = Path(settings['online']['reader_socket'])
                    assert not observer.exists()
                    after = supervisor(dict(command='start', unit=unit))['state']
                    assert before['MainPID'] != after['MainPID'] and before['InvocationID'] != after['InvocationID']
                    deadline = time.monotonic()+5
                    while not observer.exists():
                        assert time.monotonic() < deadline
                        time.sleep(.02)
                    with (config.parent/'rpc-runtime-replaced.json').open('x') as output:
                        json.dump(dict(before=before, after=after, returned='receipt-from-dead-process'), output)
                    sys.stdout.buffer.write(result.stdout)
                    return 0
                response = json.loads(result.stdout)
                response['payload']['slot'] = 'unknown-participant'
                sys.stdout.write(json.dumps(response, sort_keys=True, separators=(',', ':')))
                return 0
    sys.stdout.buffer.write(result.stdout)
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
