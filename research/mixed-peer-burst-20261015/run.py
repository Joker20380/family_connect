import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

parser = argparse.ArgumentParser()
parser.add_argument("--prepared", type=Path, required=True)
parser.add_argument("--tools", type=Path, required=True)
parser.add_argument("--out", type=Path, required=True)
parser.add_argument("--modes", default="normal,race,multicore")
parser.add_argument("--match", default="^TestMixed")
args = parser.parse_args()
args.out.mkdir(parents=True, exist_ok=False)
(args.out / "tmp").mkdir()
records = []
for mode in args.modes.split(","):
    assert mode in ("normal", "race", "multicore")
    env = dict(os.environ, TMPDIR=str((args.out / "tmp").resolve()), GOTOOLCHAIN="local", GOPROXY="off", GOSUMDB="off", GOPATH=str(args.tools / "gopath"), GOCACHE=str(args.out.parent / "go-cache"), GOMAXPROCS="4" if mode == "multicore" else "1")
    for key in ("FC_FAMILY_TEST_FIXTURES", "YANDEX_TELEMOST_OAUTH_TOKEN", "FC_TELEMOST_ROOM", "GOFLAGS"):
        env.pop(key, None)
    command = [str(args.tools / "go/bin/go"), "test", "-mod=mod", "-tags=fc_mixed_fixture", "-v", "-timeout=300s", "-count=3" if mode == "race" else "-count=1", "-run=" + args.match]
    if mode == "race": command.append("-race")
    command.append(".")
    started = time.monotonic()
    logfile = args.out / (mode + ".log")
    with logfile.open("wb") as output:
        try:
            result = subprocess.run(command, cwd=args.prepared / "harness", env=env, stdout=output, stderr=subprocess.STDOUT, timeout=420).returncode
        except subprocess.TimeoutExpired:
            result = "TIMEOUT"
    records.append({"mode": mode, "exit": result, "elapsed_seconds": time.monotonic() - started, "log_sha256": hashlib.sha256(logfile.read_bytes()).hexdigest(), "command": command})
    (args.out / "runs.json").write_text(json.dumps(records, indent=2) + "\n")
    print(mode, result, flush=True)
raise SystemExit(0 if all(item["exit"] == 0 for item in records) else 1)
