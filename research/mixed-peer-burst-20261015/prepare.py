import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("--source", type=Path, required=True)
parser.add_argument("--old-client", type=Path, required=True)
parser.add_argument("--out", type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parent
repo = root.parents[1]
args.out.mkdir(parents=True, exist_ok=False)
canonical = "github.com/Joker20380/family_connect/carrier"
baseline = repo / "research/supervisor-20261015/baseline/carrier"
inventory = json.loads((repo / "research/supervisor-20261015/source-inventory.json").read_text())
baseline_hashes = {item["path"]: item["sha256"] for item in inventory["files"]}
binding = {}
for directory in ("reliablestream", "familysession", "telemost", "sessiontrace"):
    for source in (baseline / directory).glob("*.go"):
        if source.name.endswith("_test.go"):
            continue
        key = str(source.relative_to(repo))
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        assert digest == baseline_hashes[key], key
        binding[key] = digest
old_inventory = json.loads((repo / "research/startup-cause-fidelity-20261015/results/gradle-final/cumulative-source.json").read_text())
for name, digest in old_inventory["files"].items():
    assert hashlib.sha256((args.old_client / name).read_bytes()).hexdigest() == digest, name
for variant, original in (("oldgateway", baseline), ("oldclient", args.old_client / "carrier"), ("new", args.source / "carrier")):
    stage = args.out / variant
    shutil.copytree(original, stage)
    (stage / "telemost/mixed_fixture.go").write_bytes((root / "adapter.go").read_bytes())
    if variant != "new":
        for path in list(stage.rglob("*.go")) + [stage / "go.mod"]:
            path.write_text(path.read_text().replace(canonical, "fixture.invalid/" + variant))
harness = args.out / "harness"
harness.mkdir()
module = (args.source / "carrier/go.mod").read_text().replace("module " + canonical, "module fixture.invalid/mixed")
module += "\nrequire (\n" + canonical + " v0.0.0\nfixture.invalid/oldgateway v0.0.0\nfixture.invalid/oldclient v0.0.0\n)\n"
for name, variant in ((canonical, "new"), ("fixture.invalid/oldgateway", "oldgateway"), ("fixture.invalid/oldclient", "oldclient")):
    module += "replace " + name + " => " + str((args.out / variant).resolve()) + "\n"
(harness / "go.mod").write_text(module)
shutil.copyfile(args.source / "carrier/go.sum", harness / "go.sum")
for source in root.glob("*_test.go"):
    shutil.copyfile(source, harness / source.name)
(args.out / "binding.json").write_text(json.dumps({"baseline_inputs": binding, "namespace_only_transformation": canonical + " to fixture.invalid/oldgateway or oldclient", "source": str(args.source)}, indent=2) + "\n")
print("Prepared separate old gateway, old client and new module namespaces; no production runtime")
