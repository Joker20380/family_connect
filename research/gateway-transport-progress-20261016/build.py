import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("--source", type=Path, required=True)
parser.add_argument("--tools", type=Path, required=True)
parser.add_argument("--baseline-binary", type=Path, required=True)
parser.add_argument("--out", type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parent
manifest = json.loads((root / "source-manifest.json").read_text())
assert hashlib.sha256(args.baseline_binary.read_bytes()).hexdigest() == manifest["baseline"]["binary_sha256"]
actual = {str(path.relative_to(args.source / "carrier")): hashlib.sha256(path.read_bytes()).hexdigest() for path in (args.source / "carrier").rglob("*") if path.is_file()}
assert actual == manifest["candidate_files"], "not exact product source"
args.out.mkdir(parents=True, exist_ok=False)
(args.out / "tmp").mkdir()
env = {key: value for key, value in os.environ.items() if not key.startswith(("FC_", "YANDEX_")) and key not in ("GOFLAGS", "GOEXPERIMENT", "CGO_CFLAGS", "CGO_LDFLAGS")}
env.update(TMPDIR=str(args.out / "tmp"), GOTOOLCHAIN="local", GOPROXY="off", GOSUMDB="off", GOPATH=str(args.tools / "gopath"), GOCACHE=str(args.out.parent / "build-cache"), GOOS="linux", GOARCH="amd64", GOAMD64="v1", CGO_ENABLED="1")
go = str(args.tools / "go/bin/go")
binary = args.out / "bootstrap-broker-transport-progress"
command = [go, "build", "-trimpath", "-buildvcs=false", "-o", str(binary), "./cmd/bootstrap-broker"]
with (args.out / "build.log").open("wb") as output:
    subprocess.run(command, cwd=args.source / "carrier", env=env, stdout=output, stderr=subprocess.STDOUT, check=True)
info = subprocess.check_output([go, "version", "-m", str(binary)], env=env).decode()
old_info = subprocess.check_output([go, "version", "-m", str(args.baseline_binary)], env=env).decode()
assert [line for line in info.splitlines() if line.startswith("\tdep\t")] == [line for line in old_info.splitlines() if line.startswith("\tdep\t")]
assert "CGO_ENABLED=1" in info and "go1.26.1" in info and "-tags=" not in info
selected = subprocess.check_output([go, "list", "-deps", "-f", "{{.Dir}}:{{join .GoFiles \",\"}}", "./cmd/bootstrap-broker"], cwd=args.source / "carrier", env=env).decode()
assert "mixed_fixture" not in selected and "fixture.invalid" not in selected and "seedacceptance" not in info
(args.out / "candidate-buildinfo.txt").write_text(info)
(args.out / "baseline-buildinfo.txt").write_text(old_info)
receipt = {"source_inventory": manifest["candidate_inventory_sha256"], "command": command, "toolchain": subprocess.check_output([go, "version"], env=env).decode().strip(), "platform": {key:env[key] for key in ("GOOS", "GOARCH", "GOAMD64", "CGO_ENABLED")}, "tags": [], "build_delta": "buildvcs=false for manifest-addressed source projection; baseline recorded original git revision/dirty state. No compiler, CGO, dependencies, trimpath or tags delta.", "dependencies_equal_baseline": True, "test_adapters_in_build": False, "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(), "binary_size": binary.stat().st_size, "binary_executed": False}
(args.out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps(receipt, indent=2))
