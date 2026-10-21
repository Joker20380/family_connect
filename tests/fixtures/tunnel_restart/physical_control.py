"""One existing <=4KiB HTTPS control through an already connected Android TUN."""

import datetime
import json
import os
import subprocess

from preserve import ROOT, WORK, digest


def main():
    os.umask(0o077)
    helper = ROOT / 'state-client-build/beta87-product-fix-20261019/physical_probe88.py'
    assert digest(helper) == 'd06aa28bbe8365ab3f3c6df244d1a935b3bf340c64407e0c1e3813388154da9d'
    remote = """
import json,subprocess
values=dict(line.split('=',1) for line in subprocess.check_output(['systemctl','show','family-connect-restricted-bootstrap.service','-p','MainPID,InvocationID,ActiveState'],text=True).splitlines())
assert values['MainPID']!='0' and values['ActiveState']=='active'
assert subprocess.check_output(['sha256sum','/proc/'+values['MainPID']+'/exe'],text=True).split()[0]=='b9ae880731517753e456637e52dcc421b9f7d7b881b400c856989ae93193e9ba'
print(json.dumps(values))
"""
    gateway = json.loads(subprocess.check_output(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=8','root@186.246.45.246','python3 -B -'],
                                                input=remote, text=True, timeout=20))
    phone = subprocess.check_output(['adb','shell','pidof','com.familyconnect.app.friends'], text=True, timeout=10).strip()
    baseline = WORK / 'physical-baseline.json'
    with baseline.open('x') as output:
        json.dump(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), nl=dict(service=gateway), phone=dict(process=phone)), output)
    namespace = dict(__name__='physical_probe_helper', __file__=str(helper))
    source = helper.read_text().replace('beta88 in-place update production control only; no bulk or recovery claim',
                                       'beta90 unchanged recovery and seed containment production control only; no bulk or recurrent-loss acceptance')
    exec(compile(source, str(helper), 'exec'), namespace)
    namespace.update(ROOT=ROOT, OUT=WORK / 'physical-control', REMOTE='/data/local/tmp/fc-tunnel-restart-control-20261019')
    namespace['main'](baseline, 'tunnel-restart-control-20261019')


if __name__ == '__main__':
    main()
