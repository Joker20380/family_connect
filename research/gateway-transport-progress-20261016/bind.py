import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("--prepared", type=Path, required=True)
parser.add_argument("--candidate", type=Path, required=True)
parser.add_argument("--client", type=Path, required=True)
parser.add_argument("--installed", type=Path, required=True)
parser.add_argument("--tools", type=Path, required=True)
parser.add_argument("--out", type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parent
canonical = "github.com/Joker20380/family_connect/carrier"
originals = {"candidate": args.candidate / "carrier", "new": args.client / "carrier", "oldclient": args.installed / "carrier", "oldgateway": root.parent / "supervisor-20261015/baseline/carrier"}
env = dict(os.environ, GOTOOLCHAIN="local", GOPROXY="off", GOSUMDB="off", GOPATH=str(args.tools / "gopath"), GOCACHE=str(args.prepared.parent / "go-cache"), TMPDIR=str(args.prepared.parent / "mixed-results/tmp"))
env.pop("GOFLAGS", None)
raw = subprocess.check_output([str(args.tools / "go/bin/go"), "list", "-deps", "-test", "-json", "-tags=fc_mixed_fixture", "."], cwd=args.prepared / "harness", env=env).decode()
decoder = json.JSONDecoder()
records = {}
while raw.strip():
    value, length = decoder.raw_decode(raw.lstrip())
    raw = raw.lstrip()[length:]
    directory = Path(value.get("Dir", "/nonexistent"))
    for variant, original in originals.items():
        stage = args.prepared / variant
        if not directory.is_relative_to(stage): continue
        for name in value.get("GoFiles", []) + value.get("CgoFiles", []):
            path = directory / name
            if name.endswith("_test.go"): continue
            relative = path.relative_to(stage)
            data = path.read_bytes()
            normalized = data if variant == "new" else data.replace(("fixture.invalid/" + variant).encode(), canonical.encode())
            expected = (root.parent / "mixed-peer-burst-20261015/adapter.go") if name == "mixed_fixture.go" else original / relative
            assert normalized == expected.read_bytes(), str(path)
            records[variant + "/" + str(relative)] = {"compiled_sha256": hashlib.sha256(data).hexdigest(), "original_sha256": hashlib.sha256(normalized).hexdigest(), "adapter": name == "mixed_fixture.go"}
args.out.write_text(json.dumps({"namespace_only_transformation_verified": True, "count": len(records), "files": records}, indent=2) + "\n")
print("Verified compiled source bindings", len(records))
