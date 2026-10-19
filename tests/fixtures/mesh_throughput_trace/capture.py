"""Bounded read-only live capture; no service/app mutation or journal rescans."""

import os
from pathlib import Path
import shlex
import subprocess
import threading
import time

REMOTE = r'''
import os,select,subprocess,sys,time
duration=int(sys.argv[1]);assert 1<=duration<=900
unit='family-connect-restricted-bootstrap.service'
invocation=subprocess.check_output(['systemctl','show',unit,'--value','-p','InvocationID'],text=True).strip()
assert invocation and len(invocation)==32
command=['journalctl','--file=/var/log/journal/*/system.journal','--since','2 seconds ago','--no-pager','--all','-f','-o','json','_SYSTEMD_INVOCATION_ID='+invocation]
process=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=sys.stderr,bufsize=0)
deadline=time.monotonic()+duration;written=0
try:
 while time.monotonic()<deadline and written<64*1024*1024:
  readable,_,_=select.select([process.stdout,sys.stdin],[],[],1)
  if sys.stdin in readable and not sys.stdin.readline():break
  if process.stdout not in readable:continue
  chunk=os.read(process.stdout.fileno(),min(65536,64*1024*1024-written))
  if not chunk:break
  sys.stdout.buffer.write(chunk);sys.stdout.buffer.flush();written+=len(chunk)
finally:
 process.terminate()
 try:process.wait(timeout=5)
 except subprocess.TimeoutExpired:process.kill();process.wait()
'''


class Capture:
    def __init__(self, directory, seconds=300):
        assert 1 <= seconds <= 900
        os.umask(0o077)
        self.directory = Path(directory)
        self.directory.mkdir(mode=0o700, exist_ok=False)
        self.handles, self.processes, self.threads = [], [], []
        self.cap_reached = []
        commands = dict(NL=['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=8',
            '-o', 'StrictHostKeyChecking=yes', 'root@186.246.45.246',
            'python3 -B -c ' + shlex.quote(REMOTE) + ' ' + str(seconds)],
            Android=['adb', 'logcat', '-T', '1', '-v', 'raw', 'FamilyConnectPerf:I', '*:S'])
        for node, command in commands.items():
            handle = (self.directory / (node + '.stderr')).open('xb')
            self.handles.append(handle)
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=handle, bufsize=0)
            self.processes.append(process)
            thread = threading.Thread(target=self.copy, args=(node, process), daemon=False)
            thread.start()
            self.threads.append(thread)

    def copy(self, node, process):
        written, cap = 0, 64 * 1024 * 1024
        with (self.directory / (node + '-raw.jsonl')).open('xb') as handle:
            while written < cap:
                chunk = process.stdout.read(min(65536, cap - written))
                if not chunk:
                    break
                handle.write(chunk)
                written += len(chunk)
        if written == cap:
            self.cap_reached.append(node)
            process.terminate()

    def stop(self):
        self.processes[0].stdin.close()
        self.processes[1].terminate()
        for process in self.processes:
            try:
                process.wait(timeout=12)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        for thread in self.threads:
            thread.join(timeout=5)
            assert not thread.is_alive(), 'capture thread remains'
        for handle in self.handles:
            handle.close()
        return dict(cap_reached=self.cap_reached, limit_bytes_per_node=64 * 1024 * 1024,
                    exit_codes=[process.returncode for process in self.processes])
