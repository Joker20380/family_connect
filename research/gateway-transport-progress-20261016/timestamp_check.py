import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("--candidate", type=Path, required=True)
parser.add_argument("--tools", type=Path, required=True)
parser.add_argument("--out", type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parent
vector = root.parents[1] / "tests/vectors/bootstrap-timestamps.json"
assert hashlib.sha256(vector.read_bytes()).hexdigest() == "a542d50e3b3645b9cd1813619ffb075fd3777d2a2473bd079d05ef83a8b2aca2"
args.out.mkdir(parents=True, exist_ok=False)
(args.out / "tmp").mkdir()
env = {key: value for key, value in os.environ.items() if not key.startswith(("FC_", "YANDEX_")) and key != "GOFLAGS"}
env.update(TMPDIR=str(args.out / "tmp"), GOTOOLCHAIN="local", GOPROXY="off", GOSUMDB="off", GOPATH=str(args.tools / "gopath"), GOCACHE=str(args.out.parent / "regression-cache"))
runs = []
for label, original in (("baseline", root.parent / "supervisor-20261015/baseline/carrier"), ("candidate", args.candidate / "carrier")):
    source = args.out / label
    shutil.copytree(original, source / "carrier")
    (source / "tests/vectors").mkdir(parents=True)
    shutil.copyfile(vector, source / "tests/vectors/bootstrap-timestamps.json")
    for mode, count, procs in (("normal", 1, "1"), ("race", 3, "1"), ("multicore", 1, "4")):
        command = [str(args.tools / "go/bin/go"), "test", "-json", "-run=^TestSharedTimestampContract$", "-count=" + str(count)]
        if mode == "race": command.append("-race")
        command.append("./bootstrap")
        logfile = args.out / (label + "-" + mode + ".jsonl")
        with logfile.open("wb") as output:
            result = subprocess.run(command, cwd=source / "carrier", env=dict(env, GOMAXPROCS=procs), stdout=output, stderr=subprocess.STDOUT, timeout=180).returncode
        runs.append({"suite": label, "mode": mode, "exit": result, "sha256": hashlib.sha256(logfile.read_bytes()).hexdigest(), "command": command})
        (args.out / "runs.json").write_text(json.dumps(runs, indent=2) + "\n")
        print(label, mode, result, flush=True)
