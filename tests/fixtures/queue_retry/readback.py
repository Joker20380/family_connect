"""Bounded runtime readback without connecting or modifying any service."""

import datetime
import json
import os
import re
import shlex
import subprocess
import sys

from prepare import APK, GATEWAY, WORK


def run(command, **options):
    return subprocess.check_output(command, text=True, stderr=subprocess.PIPE, timeout=25, **options)


def main():
    os.umask(0o077)
    name = sys.argv[1]
    assert re.fullmatch('[a-z-]+',name)
    remote = """
import datetime,hashlib,json,subprocess
from pathlib import Path
from cryptography import x509
unit='family-connect-restricted-bootstrap.service'
state=dict(line.split('=',1) for line in subprocess.check_output(['systemctl','show',unit,'-p','MainPID,InvocationID,NRestarts,ActiveState,ExecMainStartTimestamp'],text=True).splitlines())
assert state['MainPID']!='0'
binary=Path('/proc')/state['MainPID']/'exe'
profile=Path('/opt/apps/family_connect/friends-restricted/gateway.json')
leaf=x509.load_pem_x509_certificate(json.loads(profile.read_text())['certificate'].encode())
print(json.dumps(dict(state=state,sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),leaf_expiry=leaf.not_valid_after_utc.isoformat(),profile_sha256=hashlib.sha256(profile.read_bytes()).hexdigest())))
"""
    gateway=json.loads(run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=8','root@186.246.45.246','python3 -B -'], input=remote))
    package='com.familyconnect.app.friends'
    metadata=run(['adb','shell','dumpsys','package',package])
    apk=run(['adb','shell','pm','path',package]).strip().removeprefix('package:')
    phone=dict(code=int(re.search(r'versionCode=(\d+)',metadata)[1]),
               apk_sha256=run(['adb','shell','sha256sum',apk]).split()[0],
               pid=run(['adb','shell','pidof',package]).strip(),uid=int(re.search(r'userId=(\d+)',metadata)[1]))
    native=run(['adb','shell','unzip -p '+shlex.quote(apk)+' lib/arm64-v8a/libfc_restricted.so | sha256sum']).split()[0]
    phone['apk_native_sha256']=native
    assert native=='dd722eada0da7c890a8d71a72099cba5d0bbac1ce73377bbdbc8e7b85d820c23'
    connectivity=run(['adb','shell','dumpsys','connectivity'])
    vpn=[line.strip() for line in connectivity.splitlines() if line.strip().startswith('NetworkAgentInfo{') and 'ni{VPN' in line and 'OwnerUid: 10283' in line]
    record=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),gateway=gateway,phone=phone,vpn=vpn)
    with (WORK/(name+'-readback.json')).open('x') as output:json.dump(record,output,indent=2)
    assert gateway['sha256']==GATEWAY and phone['apk_sha256']==APK and phone['code']==90
    print(json.dumps(dict(utc=record['utc'],gateway=gateway,phone=phone,vpn_count=len(vpn))))


if __name__=='__main__':
    main()
