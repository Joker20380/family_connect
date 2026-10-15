import argparse
import collections
import hashlib
import json
from pathlib import Path
import re

parser = argparse.ArgumentParser()
parser.add_argument("--work", type=Path, required=True)
parser.add_argument("--out", type=Path, required=True)
args = parser.parse_args()
args.out.mkdir(parents=True, exist_ok=False)
summary = {}
observations = []
for group in ("mixed-results", "installed-stall-control"):
    runs = json.loads((args.work / group / "runs.json").read_text())
    results = []
    for run in runs:
        path = args.work / group / (run["mode"] + ".log")
        assert hashlib.sha256(path.read_bytes()).hexdigest() == run["log_sha256"]
        current = ""
        outcomes = []
        failures = []
        for line in path.read_text().splitlines():
            if line.startswith("=== RUN   "): current = line.split("=== RUN   ")[1]
            match = re.search(r"--- (PASS|FAIL|SKIP): (\S+)", line)
            if match: outcomes.append({"status": match[1], "test": match[2]})
            if "MIXED " not in line:
                if ".go:" in line: failures.append(line.strip()[:240])
                continue
            kind, raw = line.split("MIXED ", 1)[1].split(" ", 1)
            value = json.loads(raw)
            if kind in ("burst", "remainder"):
                for snapshot in ("before", "after"):
                    failure = value[snapshot].get("first_failure")
                    value[snapshot]["first_failure"] = {key: failure.get(key) for key in ("stage", "state", "reason", "close_source")} if failure else None
            elif kind == "sustained_real_peer_overload":
                value = {"elapsed_ms": value["elapsed_ms"], "injected_replays": value["injected_replays"], "queue": {key:value["queue"].get(key) for key in ("depth", "capacity", "closed", "sampled_high_water", "active_calls")}, "terminals": {side:value[side].get("Terminal") for side in ("client","gateway")}}
            elif kind == "family_tls": pass
            else: continue
            observations.append({"group":group, "mode":run["mode"], "test":current, "kind":kind, "value":value})
        results.append({key:run[key] for key in ("mode","exit","elapsed_seconds","log_sha256")} | {"outcomes":outcomes,"failure_lines":failures})
    summary[group] = results
for group in ("regressions", "timestamp-fixture"):
    runs = json.loads((args.work / group / "runs.json").read_text())
    expected = 9 if group == "regressions" else 6
    assert len(runs) == expected, "unfinished " + group
    results = []
    for run in runs:
        path = args.work / group / (run["suite"] + "-" + run["mode"] + ".jsonl")
        counts = collections.Counter()
        failed = set()
        skipped = set()
        passed = set()
        failure_output = collections.defaultdict(list)
        outputs = collections.defaultdict(list)
        resource_output = []
        for line in path.read_text().splitlines():
            try: event = json.loads(line)
            except ValueError: continue
            name = event.get("Test", "")
            action = event.get("Action")
            if action == "output" and name:
                output = event.get("Output", "").strip()
                if ".go:" in output and "MIXED" not in output: outputs[name].append(output[:300])
                if "retained_payload_before_fixture_drain" in output: resource_output.append(output)
            if name and action in ("pass","fail","skip"):
                if "/" not in name: counts[action] += 1
                key = event["Package"].split("/carrier/")[-1] + "/" + name
                if action == "fail":
                    failed.add(key)
                    failure_output[key].extend(outputs[name][-2:])
                elif action == "skip": skipped.add(key)
                else: passed.add(key)
        results.append({key:run[key] for key in ("suite","mode","exit","sha256")} | {"top_level_counts":dict(counts),"failed":sorted(failed),"skipped":sorted(skipped),"passed_top_level": sorted(name for name in passed if name.count("/")==1),"failure_examples":{key:sorted(set(value)) for key,value in failure_output.items()},"retained_resource":resource_output})
    summary[group] = results
for name in ("receipt", "abi-receipt"):
    value = json.loads((args.work / "build" / (name + ".json")).read_text())
    if "command" in value:
        value["command"] = ["$TOOLS/go/bin/go", "build", "-trimpath", "-buildvcs=false", "-o", "$WORK/build/bootstrap-broker-transport-progress", "./cmd/bootstrap-broker"]
    summary["build-"+name] = value
(args.out / "summary.json").write_text(json.dumps(summary,indent=2)+"\n")
(args.out / "observations.json").write_text(json.dumps(observations,indent=2)+"\n")
print("Safe results written; raw logs/fixtures remain private")
