"""Explicit owner-authorized in-place update; Android may end the current VPN session."""
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[3]
WORK=ROOT/'state-client-build/support-automation-20261021'


def main():
    assert sys.argv[1:]==['--allow-owner-vpn-interruption']
    os.umask(0o077)
    helpers=runpy.run_path(str(ROOT/'tests/fixtures/mesh_throughput_trace/upgrade.py'))
    before=helpers['snapshot']()
    signing=json.loads((WORK/'delivery/signing-receipt.json').read_text())
    assert before['code']==97 and before['apk_sha256']==signing['baseline']['sha256']
    assert before['native_sha256']=='1fa75ee968ae75ad6446000e1907c35ae39a3993625220c51c76bf607f71ee82'
    assert not (WORK/'install-intent.json').exists(), 'Reconcile previous install before another attempt'
    apk=WORK/'delivery/FamilyConnect-0.1.18-beta98-support.apk'
    assert hashlib.sha256(apk.read_bytes()).hexdigest()==signing['signed']['sha256']
    with (WORK/'install-intent.json').open('x') as output:
        json.dump(dict(before=before,apk_sha256=signing['signed']['sha256'],owner_vpn_interruption_authorized=True,method='adb install -r',force_stop=False,uninstall=False,clear_data=False),output,indent=2)
        output.flush();os.fsync(output.fileno())
    result=subprocess.run(['adb','-s','31ce63ba','install','-r',str(apk)],capture_output=True,text=True,timeout=180)
    after=helpers['snapshot']()
    receipt=dict(exit=result.returncode,stdout=result.stdout,stderr=result.stderr,before=before,after=after,identity_not_rotated=True,actual_profile='AWAITING_APP_SNAPSHOT')
    (WORK/'install-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    assert result.returncode==0 and result.stdout.strip().endswith('Success')
    assert after['code']==98 and after['uid']==before['uid'] and after['apk_sha256']==signing['signed']['sha256']
    assert after['native_sha256']==signing['native_sha256']
    subprocess.run(['adb','-s','31ce63ba','shell','am','start','-n','com.familyconnect.app.friends/com.familyconnect.app.FriendsActivity','--ei','tab','3'],check=True,capture_output=True,timeout=15)
    print(json.dumps(dict(status='INSTALLED98_SETTINGS_OPEN',apk_sha256=after['apk_sha256'],uid=after['uid'],requires_once='ENABLE_USB_SUPPORT_IN_APP',online_default='OFF')))


if __name__=='__main__':main()
