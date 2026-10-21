"""Bounded passive TUN watch and one existing <=4KiB post-update control."""

import datetime
import json
import os
import re
import subprocess
import time

from preserve import ROOT, WORK, digest
from normal import NORMAL, load


def main():
    os.umask(0o077)
    previous=None
    stable_since=0
    deadline=time.monotonic()+120
    with (NORMAL/'connect-watch.jsonl').open('x') as output:
        while time.monotonic()<deadline:
            reply=subprocess.run(['adb','shell','dumpsys','connectivity'],text=True,capture_output=True,timeout=15)
            lines=[line for line in reply.stdout.splitlines() if line.strip().startswith('NetworkAgentInfo{')
                   and 'ni{VPN' in line and 'OwnerUid: 10283' in line and '10.79.0.1' in line]
            topology=None
            if reply.returncode==0 and len(lines)==1:
                topology=dict(interface=re.search(r'InterfaceName: (\S+)',lines[0])[1],
                              underlay=re.search(r'UnderlyingNetworks: \[([^\]]*)\]',lines[0])[1])
            now=time.monotonic()
            if topology!=previous:stable_since=now
            previous=topology
            row=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),topology=topology,
                     stable_seconds=now-stable_since if topology else 0,read_exit=reply.returncode)
            output.write(json.dumps(row)+'\n');output.flush()
            if topology and now-stable_since>=35:break
            time.sleep(5)
        else:
            print('NO_STABLE_TUN_OBSERVED_NO_HTTP_NO_CONNECT_COMMAND')
            return
    runner=load(ROOT/'tests/fixtures/mesh_throughput_trace/upgrade.py',
                'cde4965c08308c14bf23175ad3af87cdcbdc72d5e3cfd03de1f4d2ffeb623301',{})
    phone=runner['snapshot']()
    signing=json.loads((NORMAL/'delivery/signing-receipt.json').read_text())
    assert phone['code']==92 and phone['apk_sha256']==signing['signed']['sha256']
    assert phone['native_sha256']==signing['native_sha256'] and phone['uid']==10283
    with (NORMAL/'final-device.json').open('x') as output:json.dump(phone,output,indent=2)
    helper=ROOT/'tests/fixtures/tunnel_restart/physical_control.py'
    assert digest(helper)=='c3fcb597b57dfb119eb5f58b8c92d0b3f84d50d0ac69768c1c37037a4d515787'
    source=helper.read_text()
    source=source.replace('beta90 unchanged recovery and seed containment production control only; no bulk or recurrent-loss acceptance',
                          'beta92 trace-off and exact b9/1011 production control; no speed or overnight acceptance')
    source=source.replace('fc-tunnel-restart-control-20261019','fc-receive-return-control-20261020')
    source=source.replace("'tunnel-restart-control-20261019'","'receive-return-control-20261020'")
    namespace=dict(__name__='normal92_control',__file__=str(helper))
    exec(compile(source,str(helper),'exec'),namespace)
    namespace.update(ROOT=ROOT,WORK=NORMAL)
    namespace['main']()


if __name__=='__main__':main()
