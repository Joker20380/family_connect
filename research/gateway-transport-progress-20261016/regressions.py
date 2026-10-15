import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

parser = argparse.ArgumentParser()
parser.add_argument("--candidate", type=Path, required=True)
parser.add_argument("--tools", type=Path, required=True)
parser.add_argument("--fixture-source", type=Path, required=True)
parser.add_argument("--python", type=Path, required=True)
parser.add_argument("--out", type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parent
args.out.mkdir(parents=True, exist_ok=False)
(args.out / "tmp").mkdir()
env = {key: value for key, value in os.environ.items() if not key.startswith(("FC_", "YANDEX_")) and key != "GOFLAGS"}
env.update(TMPDIR=str(args.out / "tmp"), GOTOOLCHAIN="local", GOPROXY="off", GOSUMDB="off", GOPATH=str(args.tools / "gopath"), GOCACHE=str(args.out.parent / "regression-cache"), PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=str(args.fixture_source), CGO_ENABLED="1")
fixtures = args.out / "synthetic-private"
subprocess.run([str(args.python), str(args.fixture_source / "pilot/telemost_family_fixture.py"), "--out", str(fixtures)], env=env, check=True)
env["FC_FAMILY_TEST_FIXTURES"] = str(fixtures)
base = root.parent / "supervisor-20261015/baseline/carrier"
overlay = args.out / "test-overlay"
shutil.copytree(args.candidate / "carrier", overlay)
for name, source in (("receive_stall_test.go", root.parent / "mixed-peer-burst-20261015/changed/carrier/telemost/receive_stall_test.go"), ("receive_burst_test.go", root.parent / "mixed-peer-burst-20261015/changed/carrier/telemost/receive_burst_test.go"), ("gateway_resource_test.go", root / "tests/gateway_resource_test.go")):
    shutil.copyfile(source, overlay / "telemost" / name)
runs = []
packages = ["./reliablestream", "./telemost", "./familysession", "./tcpforward", "./bootstrap", "./roombroker", "./cmd/bootstrap-broker"]
for name, source, selected in (("baseline", base, packages), ("candidate", args.candidate / "carrier", packages), ("progress-resource", overlay, ["-run=^Test(ReceiveStall|ReceiveBurst|GatewayRetained)", "./telemost"])):
    for mode, count, procs in (("normal", 1, "1"), ("race", 3, "1"), ("multicore", 1, "4")):
        command = [str(args.tools / "go/bin/go"), "test", "-json", "-timeout=300s", "-count=" + str(count)]
        if mode == "race": command.append("-race")
        command += selected
        logfile = args.out / (name + "-" + mode + ".jsonl")
        started = time.monotonic()
        with logfile.open("wb") as output:
            try:
                result = subprocess.run(command, cwd=source, env=dict(env, GOMAXPROCS=procs), stdout=output, stderr=subprocess.STDOUT, timeout=900).returncode
            except subprocess.TimeoutExpired:
                result = "TIMEOUT"
        runs.append({"suite": name, "mode": mode, "exit": result, "elapsed_seconds": time.monotonic() - started, "command": command, "log": logfile.name, "sha256": hashlib.sha256(logfile.read_bytes()).hexdigest()})
        (args.out / "runs.json").write_text(json.dumps(runs, indent=2) + "\n")
        print(name, mode, result, flush=True)
