"""Normal owner UI disconnect/connect, finite waits and network receipts only."""

import json
import re
import subprocess
import sys
import time
from prepare import WORK

def state():
    raw=subprocess.check_output(['adb','shell','dumpsys','connectivity'],text=True,timeout=15)
    return [line.strip() for line in raw.splitlines() if line.strip().startswith('NetworkAgentInfo{') and 'ni{VPN' in line and 'OwnerUid: 10283' in line]

def action(name, target):
    result=subprocess.run(['adb','shell','uiautomator','runtest','/system/framework/android.test.base.jar','/data/local/tmp/fc-mux-profile-ui.jar','-c','OwnerUi'],text=True,capture_output=True,timeout=30)
    (target/(name+'.log')).write_text(result.stdout+result.stderr)
    matches=re.findall(r'^OWNER_BUTTON  \| '+name+r' \| \[(\d+),(\d+)\]\[(\d+),(\d+)\]$',result.stdout,re.MULTILINE)
    assert result.returncode==0 and len(matches)==1,'ORDINARY_UI_BUTTON_NOT_FOUND'
    focus=subprocess.check_output(['adb','shell','dumpsys','window'],text=True,timeout=15)
    assert any('mCurrentFocus=' in line and 'com.familyconnect.app.friends/com.familyconnect.app.FriendsActivity' in line for line in focus.splitlines())
    left,top,right,bottom=map(int,matches[0])
    subprocess.run(['adb','shell','input','tap',str((left+right)//2),str((top+bottom)//2)],check=True,timeout=15)

def main():
    phase=sys.argv[1];assert phase in ('B1','B1r','B2','A2','A3','B3','return95')
    target=WORK/('session-'+phase);target.mkdir(mode=0o700,exist_ok=False)
    before=state()
    action('Disconnect',target)
    deadline=time.monotonic()+60
    while state():
        assert time.monotonic()<deadline,'DISCONNECT_TIMEOUT'
        time.sleep(2)
    action('Connect',target)
    deadline=time.monotonic()+120;stable=None;since=0
    while time.monotonic()<deadline:
        current=state();now=time.monotonic()
        network=current[0] if len(current)==1 else None
        key=re.search(r'network\{(\d+)\}',network)[1] if network and re.search(r'network\{(\d+)\}',network) else network
        if key!=stable:stable=key;since=now
        if network and '10.79.0.1' in network and now-since>=20:break
        time.sleep(2)
    else:raise RuntimeError('CONNECT_STABILITY_TIMEOUT')
    (target/'receipt.json').write_text(json.dumps(dict(before=before,after=state(),normal_ui_only=True,epoch=time.time()),indent=2))
    print('NEW_OWNER_SESSION_READY',phase,flush=True)

if __name__=='__main__':main()
