import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(os.environ.get('MESH_PERF3_OUT', ROOT / 'state-client-build/mesh-perf-3'))
assert OUT.is_absolute()
TOOLS = ROOT / 'state-client-build/field65-export16/diag-source-freeze-1/resume-tools'
GO = TOOLS / 'go/bin/go'
environment = {key: value for key, value in os.environ.items()
               if not key.startswith(('FC_', 'YANDEX_', 'GO', 'CGO_'))}
environment.update(GOTOOLCHAIN='local', GOWORK='off', GOPROXY='off', GOSUMDB='off',
                   GOPATH=str(TOOLS / 'gopath'), GOCACHE=str(OUT / 'cache'),
                   GOMAXPROCS='2', GOOS='linux', GOARCH='amd64', GOAMD64='v1', CGO_ENABLED='1')
label, mode, *arguments = sys.argv[1:]
if label.startswith('layer-'):
    environment.update(MESH_PERF='1', MESH_PERF_TRACE='1', MESH_PERF_TCP_KIB='256', MESH_PERF_DELAY_MS='40', MESH_PERF_SOURCE=label)
directory = OUT / 'source/carrier'
if mode == 'baseline':
    directory = ROOT / 'state-client-build/transport-write-batching-1/gateway-source/carrier'
elif mode == 'baseline-test':
    directory = OUT / 'baseline-test'
elif mode != 'candidate':
    raise SystemExit('mode must be baseline or candidate')
log = OUT / 'receipts' / (label + '.log')
receipt = OUT / 'receipts' / (label + '.json')
assert not receipt.exists()
started = time.time()
def source_inventory():
    files = {str(path.relative_to(directory)): hashlib.sha256(path.read_bytes()).hexdigest()
             for path in directory.rglob('*') if path.is_file()}
    return hashlib.sha256(json.dumps(files, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


before = source_inventory()
command = [str(GO), *arguments]
with log.open('xb') as handle:
    completed = subprocess.run(command, cwd=directory, env=environment, stdout=handle, stderr=subprocess.STDOUT, timeout=600)
record = dict(command=command, cwd=str(directory.relative_to(ROOT)) if directory.is_relative_to(ROOT) else str(directory), mode=mode, started_unix=started,
              seconds=time.time()-started, exit=completed.returncode,
              log_sha256=hashlib.sha256(log.read_bytes()).hexdigest(), environment=environment | {'PATH': '<host PATH>'})
record['environment'] = {key: environment[key] for key in environment if key.startswith(('GO', 'CGO'))}
record.update(source_before=before, source_after=source_inventory(), toolchain_sha256=hashlib.sha256(GO.read_bytes()).hexdigest())
with receipt.open('x') as handle:
    json.dump(record, handle, indent=2)
print(json.dumps({key: record[key] for key in ('mode', 'seconds', 'exit', 'log_sha256')}))
sys.exit(completed.returncode)
