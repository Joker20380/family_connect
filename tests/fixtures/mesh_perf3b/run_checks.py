import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

root = Path(__file__).resolve().parents[3]
out = root / 'state-client-build/mesh-perf-3b'
tools = root / 'state-client-build/field65-export16/diag-source-freeze-1/resume-tools'
os.umask(0o077)
environment = {key: value for key, value in os.environ.items() if not key.startswith(('FC_', 'YANDEX_', 'GO', 'CGO_'))}
environment.update(GOTOOLCHAIN='local', GOWORK='off', GOPROXY='off', GOSUMDB='off',
                   GOPATH=str(tools / 'gopath'), GOCACHE=str(root / 'state-client-build/mesh-perf-3/cache'),
                   GOMAXPROCS='2', GOOS='linux', GOARCH='amd64', GOAMD64='v1', CGO_ENABLED='1',
                   FC_FAMILY_TEST_FIXTURES=str(out / 'fixtures-v2'), FC_PERF_OWNER_GUARD=str(out / 'fixtures-v2/owner.json'))
label, *arguments = sys.argv[1:]
command = [str(tools / 'go/bin/go'), *arguments]
receipt = out / 'receipts' / (label + '.json')
log = out / 'receipts' / (label + '.log')
assert not receipt.exists() and not log.exists()
started = time.time()
with log.open('xb') as handle:
    directory = root/'state-client-build/transport-write-batching-1/gateway-source/carrier' if label.startswith('baseline-') else out/'source/carrier'
    result = subprocess.run(command, cwd=directory, env=environment,
                            stdout=handle, stderr=subprocess.STDOUT, timeout=180)
record = dict(command=arguments, start_unix=started, seconds=time.time()-started,
              exit=result.returncode, log_sha256=hashlib.sha256(log.read_bytes()).hexdigest())
with receipt.open('x') as handle:json.dump(record, handle, indent=2)
print(json.dumps(record))
sys.exit(result.returncode)
