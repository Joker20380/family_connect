"""Wait for one user-initiated session restart; never inject input or change settings."""

import json
import re
import subprocess
import sys
import time
from prepare import WORK

def network():
    raw=subprocess.check_output(['adb','shell','dumpsys','connectivity'],text=True,timeout=15)
    for line in raw.splitlines():
        if line.strip().startswith('NetworkAgentInfo{') and 'ni{VPN' in line and 'OwnerUid: 10283' in line:
            found=re.search(r'network\{(\d+)\}',line)
            return found[1] if found else None
    return None

phase=sys.argv[1];assert phase=='B1m'
target=WORK/('manual-'+phase+'.json');assert not target.exists()
before=network();deadline=time.monotonic()+120;observations=[];stable=None;since=0
while time.monotonic()<deadline:
    current=network();now=time.monotonic()
    observations.append(dict(epoch=time.time(),network=current))
    if current!=stable:stable=current;since=now
    if current and current!=before and now-since>=20:break
    time.sleep(3)
else:
    target.write_text(json.dumps(dict(result='MANUAL_RESTART_NOT_OBSERVED',before=before,observations=observations),indent=2))
    raise SystemExit(2)
target.write_text(json.dumps(dict(result='USER_RESTART_OBSERVED',before=before,observations=observations),indent=2))
print('USER_RESTART_OBSERVED',current,flush=True)
