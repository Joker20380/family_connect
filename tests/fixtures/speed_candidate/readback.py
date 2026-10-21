"""Read-only owner/gateway receipt; never print credentials or control a session."""

import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
WORK = ROOT / 'state-client-build/speed-candidate-20261021'


def run(command, **options):
    return subprocess.check_output(command, text=True, stderr=subprocess.PIPE, timeout=30, **options)


def main():
    os.umask(0o077)
    label = sys.argv[1]
    assert re.fullmatch('[a-z0-9-]+', label)
    WORK.mkdir(mode=0o700, exist_ok=True)
    destination = WORK / (label + '-readback.json')
    assert not destination.exists()
    remote = """
import hashlib,json,subprocess
from pathlib import Path
unit='family-connect-restricted-bootstrap.service'
state=dict(line.split('=',1) for line in subprocess.check_output(['systemctl','show',unit,'-p','MainPID,InvocationID,NRestarts,ActiveState,ExecMainStartTimestamp'],text=True).splitlines())
assert state['MainPID']!='0'
root=Path('/opt/apps/family_connect/friends-restricted')
flags={name:(root/'diag67'/name).read_text().strip() if (root/'diag67'/name).exists() else None for name in ('rtp-pacing','mux-profile','mux-counters','speed-profile')}
print(json.dumps(dict(state=state,sha256=hashlib.sha256((Path('/proc')/state['MainPID']/'exe').read_bytes()).hexdigest(),profile_sha256=hashlib.sha256((root/'gateway.json').read_bytes()).hexdigest(),operator=flags)))
"""
    gateway = json.loads(run(['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=8', 'root@186.246.45.246', 'python3 -B -'], input=remote))
    devices = run(['adb', 'devices']).splitlines()[1:]
    if not any(line.endswith('\tdevice') for line in devices):
        record = dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), gateway=gateway,
                      phone={'status': 'UNAVAILABLE_ADB_NO_DEVICE'}, read_only=True)
        with destination.open('x') as output:
            json.dump(record, output, indent=2)
        print(json.dumps(record))
        return
    package = 'com.familyconnect.app.friends'
    metadata = run(['adb', 'shell', 'dumpsys', 'package', package])
    apk = run(['adb', 'shell', 'pm', 'path', package]).strip().removeprefix('package:')
    assert apk.startswith('/data/app/') and '\n' not in apk
    phone = dict(code=int(re.search(r'versionCode=(\d+)', metadata)[1]),
                 version=re.search(r'versionName=(\S+)', metadata)[1],
                 uid=int(re.search(r'userId=(\d+)', metadata)[1]),
                 apk_sha256=run(['adb', 'shell', 'sha256sum', apk]).split()[0],
                 native_sha256=run(['adb', 'shell', 'unzip -p ' + shlex.quote(apk) + ' lib/arm64-v8a/libfc_restricted.so | sha256sum']).split()[0])
    connectivity = run(['adb', 'shell', 'dumpsys', 'connectivity'])
    vpn = [line.strip() for line in connectivity.splitlines() if line.strip().startswith('NetworkAgentInfo{') and 'ni{VPN' in line and 'OwnerUid: ' + str(phone['uid']) in line]
    resources = dict(scope='point-in-time readback outside measured load; not phase peak or comparable to missing earlier phone samples')
    for kind, command in (('memory', ['adb','shell','dumpsys','meminfo',package]), ('cpu', ['adb','shell','dumpsys','cpuinfo'])):
        try:
            output = run(command)
            assert len(output) <= 256 * 1024
            resources[kind] = [line.strip() for line in output.splitlines() if
                               (kind == 'memory' and re.search(r'TOTAL PSS:|TOTAL RSS:|TOTAL SWAP PSS:|\*\* MEMINFO',line)) or
                               (kind == 'cpu' and (package in line or line.startswith('CPU usage from')))]
        except (subprocess.SubprocessError, AssertionError) as error:
            resources[kind] = dict(unavailable=type(error).__name__)
    record = dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), gateway=gateway, phone=phone, vpn=vpn, android_resources=resources, read_only=True)
    with destination.open('x') as output:
        json.dump(record, output, indent=2)
    print(json.dumps(dict(utc=record['utc'], gateway=gateway, phone=phone, vpn_count=len(vpn), android_resources=resources)))


if __name__ == '__main__':
    main()
