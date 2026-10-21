"""Read-only accepted96/734 control attribution; no fabricated new-format limits."""

import ast
import json
import os
import re
import subprocess
import sys
import time
from prepare import ROOT, WORK, APK_SHA, GATEWAY_SHA, digest


def main():
    os.umask(0o077)
    subprocess.run([sys.executable, ROOT/'tests/fixtures/speed_candidate/readback.py', 'original-preflight'], check=True)
    readback=json.loads((WORK/'original-preflight-readback.json').read_text())
    assert readback['phone']['code']==96 and readback['phone']['apk_sha256']==APK_SHA
    assert readback['gateway']['sha256']==GATEWAY_SHA and len(readback['vpn'])==1
    old=ROOT/'state-client-build/beta87-product-fix-20261019/identity_readback88.py'
    tree=ast.parse(old.read_text())
    remote=next(ast.literal_eval(node.value) for node in tree.body if isinstance(node,ast.Assign) and any(isinstance(item,ast.Name) and item.id=='remote' for item in node.targets))
    remote=remote.replace("version_code')=88", "version_code')=96").replace('beta88_readiness','beta96_readiness')
    remote=remote.replace('print(json.dumps(result))', '''import base64
public=base64.urlsafe_b64decode(row['public']+'='*(-len(row['public'])%4))
assert len(public)==64
result['target']=hashlib.sha256(public[32:]).hexdigest()[:32]
print(json.dumps(result))''')
    identity=json.loads(subprocess.check_output(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','root@185.251.89.19','python3 -B -'],input=remote,text=True,timeout=30))
    reference=json.loads((ROOT/'state-client-build/mobile-bootstrap-20261020/identity-after.json').read_text())
    assert all(identity[key]==reference[key] for key in ('identity_bindings_sha256','support_id_sha256','owner_record_count'))
    assert not identity['owner_revoked'] and identity['beta96_readiness']['result']=='READY'
    (WORK/'identity-original.json').write_text(json.dumps(identity,indent=2))
    meter=ROOT/'tests/fixtures/mesh_throughput_trace/measure.py'
    assert digest(meter)=='17e76fb9f3d8c46b5e7e4b5c55fa0f8098b59aef63e0e66c94cbce81b2c2a5ef'
    helpers=[node for node in ast.parse(meter.read_text()).body if isinstance(node,ast.FunctionDef) and node.name in ('adb','topology')]
    namespace=dict(subprocess=subprocess,re=re)
    exec(compile(ast.Module(body=helpers,type_ignores=[]),str(meter),'exec'),namespace)
    scope=dict(phase='original96',owner_verified=True,gateway_verified=True,observed_epoch=time.time(),
               limits_basis='EXACT_96_734_FIXED_DEFAULTS_NOT_LIVE_OPEN_EXPORT',readback=readback,
               topology=namespace['topology'](),vpn_network=re.search(r'network\{(\d+)\}',readback['vpn'][0])[1],
               phone_apk_sha256=APK_SHA,gateway_sha256=GATEWAY_SHA,
               gateway_pid=readback['gateway']['state']['MainPID'],gateway_invocation=readback['gateway']['state']['InvocationID'])
    destination=WORK/'scope-original96.json'
    with destination.open('x') as output:json.dump(scope,output,indent=2)
    print(json.dumps(dict(scope=str(destination),identity_preserved=True,ready='READY',mesh_tun_verified=True,transport_mutations=0)))


if __name__=='__main__':main()
