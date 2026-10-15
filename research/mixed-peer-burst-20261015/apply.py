import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

parser = argparse.ArgumentParser()
parser.add_argument("--retained", type=Path, required=True)
parser.add_argument("--out", type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parent
manifest = json.loads((root / "source-manifest.json").read_text())
subprocess.run([sys.executable, str(root.parent / "receive-queue-stall-20261015/apply.py"), "--retained", str(args.retained.resolve()), "--out", str(args.out.resolve())], check=True)
digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
assert digest(root / "source.patch") == manifest["patch_sha256"]
for entry in manifest["files"]:
    target = args.out / entry["path"]
    if entry["before_sha256"]:
        assert digest(target) == entry["before_sha256"], entry["path"]
    else:
        assert not target.exists(), entry["path"]
    source = root / "changed" / entry["path"]
    assert digest(source) == entry["after_sha256"], entry["path"]
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(source.read_bytes())
inventory = json.loads((root / "results/cumulative-source.json").read_text())
for name, expected in inventory["files"].items():
    assert digest(args.out / name) == expected, name
assert hashlib.sha256(json.dumps(inventory["files"], sort_keys=True, separators=(",", ":")).encode()).hexdigest() == manifest["new_cumulative"]
print("Exact cumulative source reconstructed: " + manifest["new_cumulative"])
