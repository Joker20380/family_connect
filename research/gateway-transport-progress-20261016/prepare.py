import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

parser = argparse.ArgumentParser()
parser.add_argument("--candidate", type=Path, required=True)
parser.add_argument("--client", type=Path, required=True)
parser.add_argument("--installed", type=Path, required=True)
parser.add_argument("--out", type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parent
previous = root.parent / "mixed-peer-burst-20261015"
canonical = "github.com/Joker20380/family_connect/carrier"
manifest = json.loads((root / "source-manifest.json").read_text())
client_manifest = json.loads((previous / "results/cumulative-source.json").read_text())
for name, digest in client_manifest["files"].items():
    assert hashlib.sha256((args.client / name).read_bytes()).hexdigest() == digest, name
for name, digest in manifest["candidate_files"].items():
    assert hashlib.sha256((args.candidate / "carrier" / name).read_bytes()).hexdigest() == digest, name
subprocess.run([sys.executable, str(previous / "prepare.py"), "--source", str(args.client.resolve()), "--old-client", str(args.installed.resolve()), "--out", str(args.out.resolve())], check=True)
stage = args.out / "candidate"
shutil.copytree(args.candidate / "carrier", stage)
(stage / "telemost/mixed_fixture.go").write_bytes((previous / "adapter.go").read_bytes())
for path in list(stage.rglob("*.go")) + [stage / "go.mod"]:
    path.write_text(path.read_text().replace(canonical, "fixture.invalid/candidate"))
harness = args.out / "harness"
with (harness / "go.mod").open("a") as output:
    output.write("\nrequire fixture.invalid/candidate v0.0.0\nreplace fixture.invalid/candidate => " + str(stage.resolve()) + "\n")
for name in ("mixed_test.go", "sustained_test.go", "installed_stall_test.go"):
    (harness / name).write_bytes((root / "tests" / name).read_bytes())
print("Four actual source namespaces; candidate is baseline plus guarded three-file delta")
