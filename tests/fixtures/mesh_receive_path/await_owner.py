"""Bounded read-only readiness watch; never presses Connect or accesses UI."""

import datetime
import json
import os
import subprocess
import time

from preserve import WORK


def main():
    os.umask(0o077)
    with (WORK/'owner-connect-watch.jsonl').open('x') as output:
        for attempt in range(24):
            result=subprocess.run(['adb','shell','dumpsys','connectivity'],text=True,capture_output=True,timeout=15)
            lines=[line for line in result.stdout.splitlines() if line.strip().startswith('NetworkAgentInfo{') and 'ni{VPN' in line and 'OwnerUid: 10283' in line]
            record=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),vpn_count=len(lines),read_exit=result.returncode)
            output.write(json.dumps(record)+'\n');output.flush()
            if result.returncode==0 and len(lines)==1 and '10.79.0.1' in lines[0]:
                print('OWNER_MESH_TUN_PRESENT_NO_CONNECT_COMMAND_SENT');return
            time.sleep(5)
    print('OWNER_CONNECT_NOT_OBSERVED_NO_TRAFFIC_STARTED')


if __name__=='__main__':main()
