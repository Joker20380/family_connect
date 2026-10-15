import argparse
import collections
import hashlib
import json
import os
import pathlib
import platform
import shutil
import subprocess
import time


parser = argparse.ArgumentParser()
parser.add_argument("--go", required=True, type=pathlib.Path)
parser.add_argument("--work", required=True, type=pathlib.Path)
parser.add_argument("--race-count", type=int, default=3)
options = parser.parse_args()
if options.race_count < 1 or options.race_count > 10:
    parser.error("race count must be within 1..10")
root = pathlib.Path(__file__).resolve().parent
repository = root.parents[1]
options.work.mkdir(parents=True, exist_ok=False)
environment = dict(os.environ, GOTOOLCHAIN="local", GOPROXY="off", GOSUMDB="off")
environment["GOCACHE"] = str(options.work / "go-cache")
environment["PATH"] = str(options.go.parent) + os.pathsep + environment.get("PATH", "")
environment.pop("FC_FAMILY_TEST_FIXTURES", None)


def digest(filename):
    return hashlib.sha256(filename.read_bytes()).hexdigest()


def command(arguments, cwd, logfile, timeout):
    started = time.monotonic()
    with logfile.open("wb") as output:
        try:
            result = subprocess.run(arguments, cwd=cwd, env=environment, stdout=output, stderr=subprocess.STDOUT, timeout=timeout)
            status = result.returncode
        except subprocess.TimeoutExpired:
            status = "TIMEOUT"
    return {"command": [str(argument) for argument in arguments], "cwd": str(cwd), "log": logfile.name, "exit": status, "elapsed_s": round(time.monotonic() - started, 3), "log_sha256": digest(logfile)}


metadata = {"status": "SOURCE_CHARACTERIZATION", "starting_review_sha": "2843b88252728902b23ca62d8df8c25914cdc5c8", "go_version": subprocess.check_output([options.go, "version"], env=environment, text=True).strip(), "go_environment": json.loads(subprocess.check_output([options.go, "env", "-json", "GOOS", "GOARCH", "CGO_ENABLED", "GOTOOLCHAIN", "GOPROXY", "GOSUMDB"], env=environment, text=True)), "host": platform.platform(), "test_sources": {filename.name: digest(filename) for filename in root.glob("*_test.go")}, "runs": []}
summary = []
failed = False
bindings = json.loads((root / "source-bindings.json").read_text())
for row in bindings["files"]:
    for location in row["published"]:
        if digest(repository / location["path"]) != location["sha256"]:
            raise SystemExit("Source binding mismatch; no compilation")
for variant in ("baseline", "frozen-candidate"):
    original = repository / "research/supervisor-20261015" / variant / "carrier"
    stage = options.work / variant / "carrier"
    shutil.copytree(original, stage)
    for source in root.glob("*_test.go"):
        shutil.copy2(source, stage / "bootstrap" / source.name)
    for mode, count in (("normal", 1), ("race", options.race_count)):
        executable = options.work / f"{variant}-{mode}.test"
        build = [options.go, "test", "-c", "-tags=seedacceptance", "-o", executable]
        if mode == "race":
            build.append("-race")
        build.append("./bootstrap")
        receipt = {"variant": variant, "mode": mode, "build": command(build, stage, options.work / f"{variant}-{mode}-build.log", 240)}
        metadata["runs"].append(receipt)
        if receipt["build"]["exit"] != 0:
            failed = True
            break
        receipt["binary_sha256"] = digest(executable)
        receipt["binary_metadata"] = subprocess.check_output([options.go, "version", "-m", executable], text=True, env=environment)
        receipt["test"] = command([executable, "-test.run=^TestRepro", "-test.v", "-test.failfast", "-test.timeout=90s", f"-test.count={count}"], stage, options.work / f"{variant}-{mode}-test.log", 100)
        print(json.dumps({"variant": variant, "mode": mode, "exit": receipt["test"]["exit"]}), flush=True)
        for line in (options.work / receipt["test"]["log"]).read_text().splitlines():
            if "REPRO " not in line:
                continue
            kind, payload = line.split("REPRO ", 1)[1].split(" ", 1)
            summary.append({"variant": variant, "mode": mode, "kind": kind, "record": json.loads(payload)})
        if receipt["test"]["exit"] != 0:
            failed = True
            break
    (options.work / "build-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    (options.work / "observations.jsonl").write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in summary))
    if failed:
        break
metadata["result"] = "FAIL_STOPPED" if failed else "PASS"
(options.work / "build-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
variants = collections.Counter()
for row in summary:
    if row["kind"] != "classification":
        continue
    actual = row["record"]["actual_recv"]
    key = (row["variant"], row["mode"], row["record"]["scenario"], actual["go_type"], actual["os_deadline"], actual["closed_pipe"], actual["eof"], actual["ctx_deadline"], actual["ctx_canceled"], row["record"]["startup"]["cause"])
    variants[key] += 1
rows = [{"server": key[0], "mode": key[1], "scenario": key[2], "go_type": key[3], "os_deadline": key[4], "closed_pipe": key[5], "eof": key[6], "ctx_deadline": key[7], "ctx_canceled": key[8], "cause": key[9], "count": count} for key, count in sorted(variants.items())]
(options.work / "classification-counts.json").write_text(json.dumps(rows, indent=2) + "\n")
raise SystemExit(1 if failed else 0)
