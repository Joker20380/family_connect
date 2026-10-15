import argparse
import hashlib
import json
from pathlib import Path
import shutil

parser = argparse.ArgumentParser()
parser.add_argument("--out", type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parent
manifest = json.loads((root / "source-manifest.json").read_text())
base = root.parent / "supervisor-20261015/baseline/carrier"
assert not args.out.exists()
for name, digest in manifest["baseline_files"].items():
    assert hashlib.sha256((base / name).read_bytes()).hexdigest() == digest, name
assert hashlib.sha256((root / "source.patch").read_bytes()).hexdigest() == manifest["patch_sha256"]
shutil.copytree(base, args.out / "carrier")
for name in manifest["product_paths"]:
    data = (root / "changed" / name).read_bytes()
    assert hashlib.sha256(data).hexdigest() == manifest["candidate_files"][name.removeprefix("carrier/")]
    (args.out / name).write_bytes(data)
for name, digest in manifest["candidate_files"].items():
    assert hashlib.sha256((args.out / "carrier" / name).read_bytes()).hexdigest() == digest, name
print(manifest["candidate_inventory_sha256"])
