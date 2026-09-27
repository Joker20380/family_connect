#!/usr/bin/env python3
"""Disposable physical Android/Amsterdam synthetic VP8 run; room only from env."""
import argparse
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import tarfile
import time

PACKAGE = "com.familyconnect.telemosttest"
SSH = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=12", "root@186.246.45.246"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--adb", default="adb")
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--case", choices=["acceptance", "cancel", "process-death", "remote-exit", "activity-close"], default="acceptance")
    args = parser.parse_args()
    room = os.environ["FC_TELEMOST_ROOM"]
    if not room or len(room) > 2048 or "\n" in room or "\r" in room:
        raise SystemExit("Invalid room input (redacted)")
    args.out.mkdir(mode=0o700, parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[2]
    directory = subprocess.check_output(SSH + ["mktemp -d /tmp/fc-eu2-live.XXXXXXXX"], text=True).strip()
    if not re.fullmatch(r"/tmp/fc-eu2-live\.[a-zA-Z0-9]{8}", directory):
        raise SystemExit("Unexpected remote temporary directory")
    remote = None
    def adb(*command, **kwargs):
        return subprocess.run([args.adb, *command], capture_output=True, check=True, timeout=25, **kwargs)
    def events(path):
        return [json.loads(line) for line in path.read_text().splitlines() if line.endswith("}")]
    def stop_remote():
        code = f'import os,pathlib,signal; directory=pathlib.Path({directory!r}); pid=int((directory/"pid").read_text()); executable=pathlib.Path(f"/proc/{{pid}}/exe"); os.kill(pid,signal.SIGTERM) if executable.exists() and str(executable.resolve())==str(directory/"telemost-live") else None'
        subprocess.run(SSH + ["python3 -c " + shlex.quote(code)], check=True, timeout=25)
    try:
        archive = args.out / "artifact.tar"
        with tarfile.open(archive, "w") as bundle:
            bundle.add(args.binary, arcname="telemost-live")
            bundle.add(root / "carrier/licenses", arcname="licenses")
        with archive.open("rb") as source:
            subprocess.run(SSH + [f"tar -xf - -C {directory} && chown -R nobody:nogroup {directory}"], stdin=source, check=True, timeout=45)
        archive.unlink()
        code = f'import os,sys; os.chdir({directory!r}); os.environ["FC_TELEMOST_ROOM"]=sys.stdin.readline().rstrip("\\n"); open("pid","w").write(str(os.getpid())); os.execvpe("./telemost-live",["./telemost-live","--role","echo","--mode","vp8","--duration","25m","--metrics-interval","10s"],os.environ)'
        with (args.out / "B.jsonl").open("w") as output, (args.out / "B.stderr").open("w") as errors:
            remote = subprocess.Popen(SSH + ["runuser -u nobody -- python3 -c " + shlex.quote(code)], stdin=subprocess.PIPE, stdout=output, stderr=errors, text=True)
        remote.stdin.write(room + "\n")
        remote.stdin.close()
        deadline = time.monotonic() + 75
        while not any(event.get("event") == "connected" for event in events(args.out / "B.jsonl")):
            if remote.poll() is not None or time.monotonic() > deadline:
                raise RuntimeError("B_JOIN_FAILED: inspect sanitized evidence")
            time.sleep(0.5)
        print("B_CONNECTED", flush=True)
        adb("shell", "am", "force-stop", PACKAGE)
        script = "umask 077; mkdir -p files; rm -f files/evidence.jsonl; cat > files/room.input"
        adb("shell", "-T", "run-as", PACKAGE, "sh", "-c", shlex.quote(script), input=room.encode())
        del room
        adb("shell", "am", "start", "-n", PACKAGE + "/.ProbeActivity", "--ez", "run", "true")
        deadline = time.monotonic() + 1520
        milestone = 0
        fault_started = None
        while time.monotonic() < deadline:
            result = subprocess.run([args.adb, "exec-out", "run-as", PACKAGE, "cat", "files/evidence.jsonl"], capture_output=True, timeout=25)
            if result.returncode:
                time.sleep(1)
                continue
            (args.out / "A.jsonl").write_bytes(result.stdout)
            rows = events(args.out / "A.jsonl")
            checks = [event for event in rows if event.get("event") == "probe_result"]
            if len(checks) > milestone:
                milestone = len(checks)
                latest = checks[-1]
                print("A_RESULT", latest["phase"], latest["payload_bytes"], latest["count"], latest["byte_equal"], round(latest["mean_rtt_ms"], 3), flush=True)
            failures = [event for event in rows if event.get("event") == "android_failure"]
            exits = [event for event in rows if event.get("event") == "android_exit"]
            if failures:
                print("A_FAILURE", failures[-1]["reason"], flush=True)
                break
            if checks and args.case != "acceptance" and fault_started is None:
                fault_started = time.monotonic()
                if args.case == "remote-exit": stop_remote()
                elif args.case == "process-death": adb("shell", "am", "force-stop", PACKAGE)
                elif args.case == "activity-close": adb("shell", "am", "start", "-n", PACKAGE + "/.ProbeActivity", "--activity-clear-top", "--activity-single-top", "--ez", "close", "true")
                else: adb("shell", "am", "start", "-n", PACKAGE + "/.ProbeActivity", "--activity-clear-top", "--activity-single-top", "--ez", "disconnect", "true")
                print("FAULT_TRIGGERED", args.case, flush=True)
            if exits or (fault_started and args.case == "process-death"):
                elapsed = time.monotonic() - fault_started if fault_started else None
                print("A_EXIT", exits[-1] if exits else "process terminated", "fault_elapsed_s", elapsed, flush=True)
                break
            if fault_started and time.monotonic() - fault_started > 25:
                raise RuntimeError("ANDROID_SHUTDOWN_TIMEOUT")
            if not exits and any(event.get("event") == "start" for event in rows):
                alive = subprocess.run([args.adb, "shell", "pidof", PACKAGE], capture_output=True, timeout=10)
                if not alive.stdout.strip():
                    raise RuntimeError("ANDROID_PROCESS_LOST")
            time.sleep(2)
        else:
            raise RuntimeError("ANDROID_SUITE_DEADLINE")
        if args.case == "acceptance" and not (exits and exits[-1]["code"] == 0 and any(event.get("event") == "suite_complete" and event.get("gate_eligible_mode") for event in rows)):
            raise RuntimeError("ANDROID_ACCEPTANCE_INCOMPLETE: inspect sanitized evidence")
    finally:
        try:
            adb("shell", "am", "force-stop", PACKAGE)
            adb("exec-out", "run-as", PACKAGE, "rm", "-f", "files/room.input")
        except subprocess.SubprocessError:
            print("ANDROID_CLEANUP_UNCONFIRMED", flush=True)
        cleanup = f'import os,pathlib,signal,shutil,time; directory=pathlib.Path({directory!r}); pidfile=directory/"pid"; pid=int(pidfile.read_text()) if pidfile.exists() else 0; executable=pathlib.Path(f"/proc/{{pid}}/exe"); matched=pid>0 and executable.exists() and str(executable.resolve())==str(directory/"telemost-live"); os.kill(pid,signal.SIGTERM) if matched else None; time.sleep(3); alive=matched and executable.exists() and str(executable.resolve())==str(directory/"telemost-live"); os.kill(pid,signal.SIGKILL) if alive else None; shutil.rmtree(directory); print("REMOTE_TEMP_REMOVED; FORCED_KILL="+str(alive))'
        subprocess.run(SSH + ["python3 -c " + shlex.quote(cleanup)], check=True, timeout=30)
        if remote is not None:
            print("B_EXIT", remote.wait(timeout=15), flush=True)


if __name__ == "__main__":
    main()
