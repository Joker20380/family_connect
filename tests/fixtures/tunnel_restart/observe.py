"""Five-minute passive observation; no connect, traffic or intentional fault."""

import datetime
import json
import os
import subprocess
import time

from preserve import WORK

REMOTE = r'''
import json,os,select,subprocess,sys,time
unit='family-connect-restricted-bootstrap.service'
def state():return dict(line.split('=',1) for line in subprocess.check_output(['systemctl','show',unit,'-p','MainPID,InvocationID,NRestarts,ActiveState'],text=True).splitlines())
before=state();print(json.dumps(dict(observation_start=before)),flush=True)
assert before['MainPID']!='0'
assert subprocess.check_output(['sha256sum','/proc/'+before['MainPID']+'/exe'],text=True).split()[0]=='b9ae880731517753e456637e52dcc421b9f7d7b881b400c856989ae93193e9ba'
process=subprocess.Popen(['journalctl','--file=/var/log/journal/*/system.journal','--since','2026-10-19 17:50:13 UTC','--no-pager','--all','-n','100','-f','-o','json','_SYSTEMD_INVOCATION_ID='+before['InvocationID']],stdout=subprocess.PIPE,stderr=sys.stderr,bufsize=0)
stop=time.monotonic()+300;size=0
try:
 while time.monotonic()<stop and size<4*1024*1024:
  readable,_,_=select.select([process.stdout],[],[],1)
  if not readable:continue
  data=os.read(process.stdout.fileno(),min(65536,4*1024*1024-size))
  if not data:break
  sys.stdout.buffer.write(data);sys.stdout.buffer.flush();size+=len(data)
finally:
 process.terminate()
 try:process.wait(timeout=5)
 except subprocess.TimeoutExpired:process.kill();process.wait()
print(json.dumps(dict(observation_end=state(),cap_reached=size>=4*1024*1024)),flush=True)
'''


def main():
    os.umask(0o077)
    target = WORK / 'passive'
    target.mkdir(mode=0o700, exist_ok=False)
    with (target / 'NL.jsonl').open('xb') as output, (target / 'NL.stderr').open('xb') as error, (target / 'phone.jsonl').open('x') as phone:
        process = subprocess.Popen(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=8','root@186.246.45.246','python3 -B -'],
            stdin=subprocess.PIPE, stdout=output, stderr=error)
        process.stdin.write(REMOTE.encode()); process.stdin.close()
        try:
            for index in range(31):
                commands = dict(pid=['pidof','com.familyconnect.app.friends'], interfaces=['ip','-o','addr','show'])
                snapshot = dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
                for name, command in commands.items():
                    response = subprocess.run(['adb','shell',*command], capture_output=True, text=True, timeout=10)
                    snapshot[name] = dict(exit=response.returncode, value=response.stdout.strip() if name=='pid' else
                        [line for line in response.stdout.splitlines() if 'tun' in line])
                phone.write(json.dumps(snapshot)+'\n');phone.flush()
                if index < 30: time.sleep(10)
            process.wait(timeout=25)
        finally:
            if process.poll() is None:
                process.terminate();process.wait(timeout=15)
    print(json.dumps(dict(result='PASSIVE_OBSERVATION_SAVED', gateway_capture_exit=process.returncode)))


if __name__ == '__main__':
    main()
