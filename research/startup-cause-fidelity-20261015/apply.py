import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

parser=argparse.ArgumentParser()
parser.add_argument('--retained',required=True,type=Path)
parser.add_argument('--out',required=True,type=Path)
args=parser.parse_args()
root=Path(__file__).resolve().parent
handoff=root.parent/'chat-vpn-handoff-20261015'
manifest=json.loads((root/'source-manifest.json').read_text())
assert hashlib.sha256((handoff/'source.patch').read_bytes()).hexdigest()==manifest['handoff_patch_sha256']
subprocess.run([sys.executable,str(handoff/'apply.py'),'--retained',str(args.retained),'--out',str(args.out)],check=True)
for row in manifest['files']:
    target=args.out/row['path']
    if row['before_sha256']:
        assert hashlib.sha256(target.read_bytes()).hexdigest()==row['before_sha256'],row['path']
    else:
        assert not target.exists(),row['path']
    raw=(root/'changed'/row['path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==row['after_sha256'],row['path']
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(raw)
print('Cumulative research84 + handoff + diagnostic delta reconstructed; no runtime/build action')
