import hashlib
import json
import os
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[3]
ACCEPTED = ROOT / 'state-client-build/transport-write-batching-1'
OUT = Path(os.environ.get('MESH_PERF3_OUT', ROOT / 'state-client-build/mesh-perf-3'))
assert OUT.is_absolute()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


manifest = json.loads((ACCEPTED / 'gateway-source.json').read_text())
source = ACCEPTED / 'gateway-source/carrier'
actual = {str(path.relative_to(source)): digest(path)
          for path in source.rglob('*') if path.is_file()}
assert actual == manifest['files']
assert hashlib.sha256(json.dumps(actual, sort_keys=True, separators=(',', ':')).encode()).hexdigest() == manifest['source_inventory']
binary = ACCEPTED / 'build/bootstrap-broker-batch1'
assert digest(binary) == '4b722d2d7f2159b96953e27777494bf596768f860ee8da7e634fb1100b08fab7'
OUT.mkdir(mode=0o700, exist_ok=False)
shutil.copytree(source, OUT / 'source/carrier')
shutil.copyfile(ACCEPTED / 'gateway-source.json', OUT / 'accepted-source.json')
(OUT / 'receipts').mkdir(mode=0o700)
print(json.dumps(dict(files=len(actual), inventory=manifest['source_inventory'], baseline_binary=digest(binary))))
