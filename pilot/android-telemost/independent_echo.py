"""Temporary nobody echo with file-backed evidence, independent of an SSH stream."""
import json
import shlex
import subprocess
import time


class IndependentEcho:
    def __init__(self, ssh, directory, output):
        self.ssh = ssh
        self.directory = directory
        self.output = output
        self.returncode = None

    def start(self, room, arguments):
        code = f'''
import os, pathlib, subprocess, sys
os.chdir({self.directory!r})
os.umask(0o077)
room = sys.stdin.readline().rstrip("\\n")
reader, writer = os.pipe()
supervisor = os.fork()
if supervisor:
    os.close(writer)
    ready = os.read(reader, 1)
    os.close(reader)
    sys.exit(0 if ready == b"1" else 1)
os.close(reader)
os.setsid()
with open(os.devnull, "r+b", buffering=0) as quiet:
    for descriptor in (0, 1, 2):
        os.dup2(quiet.fileno(), descriptor)
pathlib.Path("supervisor.pid").write_text(str(os.getpid()))
environment = {{"PATH": os.defpath, "FC_TELEMOST_ROOM": room}}
with open("B.jsonl", "wb") as output, open("B.stderr", "wb") as errors:
    child = subprocess.Popen({arguments!r}, stdin=subprocess.DEVNULL, stdout=output, stderr=errors, env=environment)
pathlib.Path("pid").write_text(str(child.pid))
os.write(writer, b"1")
os.close(writer)
pathlib.Path("exit.code").write_text(str(child.wait()))
os._exit(0)
'''
        subprocess.run(self.ssh + ['runuser -u nobody -- python3 -c ' + shlex.quote(code)], input=room + '\n', text=True, capture_output=True, check=True, timeout=30)

    def collect(self):
        code = f'''
import json,pathlib
folder=pathlib.Path({self.directory!r})
result={{}}
for name in ("B.jsonl", "B.stderr", "exit.code"):
    path=folder/name
    if path.exists():
        if path.stat().st_size > 2*1024*1024:
            raise RuntimeError("bounded test output exceeded")
        result[name]=path.read_text()
print(json.dumps(result))
'''
        result = json.loads(subprocess.check_output(self.ssh + ['python3 -c ' + shlex.quote(code)], text=True, timeout=25))
        for name in ('B.jsonl', 'B.stderr'):
            if name in result:
                (self.output / name).write_text(result[name])
        if 'exit.code' in result:
            self.returncode = int(result['exit.code'])
        return self.returncode

    def cleanup(self):
        code = f'''
import os,pathlib,signal,time
folder=pathlib.Path({self.directory!r})
path=folder/"pid"
pid=int(path.read_text()) if path.exists() else 0
def alive():
    executable=pathlib.Path(f"/proc/{{pid}}/exe")
    return pid > 0 and executable.exists() and str(executable.resolve()) == str(folder/"telemost-live")
if alive():
    os.kill(pid,signal.SIGTERM)
for attempt in range(50):
    if not alive(): break
    time.sleep(0.1)
forced=alive()
if forced:
    os.kill(pid,signal.SIGKILL)
for attempt in range(50):
    if (folder/"exit.code").exists(): break
    time.sleep(0.1)
supervisor=folder/"supervisor.pid"
supervisor_pid=int(supervisor.read_text()) if supervisor.exists() else 0
process=pathlib.Path(f"/proc/{{supervisor_pid}}")
if process.exists() and (process/"cwd").exists() and str((process/"cwd").resolve()) == str(folder):
    for attempt in range(20):
        if not (process/"cwd").exists(): break
        time.sleep(0.1)
    if (process/"cwd").exists(): os.kill(supervisor_pid,signal.SIGTERM)
if alive(): raise RuntimeError("remote test still alive")
print("REMOTE_CHILD_STOPPED; FORCED_KILL="+str(forced))
'''
        subprocess.run(self.ssh + ['python3 -c ' + shlex.quote(code)], check=True, timeout=30)
        self.collect()
        code = f'import shutil; shutil.rmtree({self.directory!r}); print("REMOTE_TEMP_REMOVED")'
        subprocess.run(self.ssh + ['python3 -c ' + shlex.quote(code)], check=True, timeout=25)

