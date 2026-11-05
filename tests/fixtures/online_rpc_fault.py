import json
import os
from pathlib import Path
import subprocess
import sys


def main():
    raw = sys.stdin.buffer.read(1024*1024+1)
    result = subprocess.run([sys.executable, *sys.argv[1:]], input=raw, capture_output=True, timeout=120)
    request = json.loads(raw)
    config = Path(sys.argv[6])
    fault_path = config.parent/'rpc-fault.json'
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
                response = json.loads(result.stdout)
                response['payload']['slot'] = 'unknown-participant'
                sys.stdout.write(json.dumps(response, sort_keys=True, separators=(',', ':')))
                return 0
    sys.stdout.buffer.write(result.stdout)
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
