"""Reuse the accepted phone TUN meter and identical bounded64/128 counters."""

import json
import sys
from prepare import ROOT, WORK, APK, digest
from session_scope import select_session

phase=sys.argv[1]
assert phase in ('legacy94','smoke95','A1','B1','B1r','B1m','B2','A2','A3','B3','return95')
control=phase in ('legacy94','smoke95','return95')
window=131072 if phase.startswith('B') else 65536
profile='CREDIT128' if window==131072 else 'LEGACY64'
scope_path=WORK/('session-scope-'+phase+'.json')
scope=json.loads(scope_path.read_text()) if scope_path.exists() else None
assert phase!='B1m' or scope is not None,'OWNER_SCOPE_REQUIRED'
if scope:
    assert scope['phase']==phase and scope['profile']==profile and scope['window']==window
if phase!='legacy94':APK=json.loads((WORK/'delivery/signing-receipt.json').read_text())['signed']['sha256']
original=ROOT/'tests/fixtures/mux_credit/measure.py'
source=original.read_text()
assert digest(original)=='a936409c318246edcfaf15c7cfbee2b8b030091e8ab147da690748718d57ed67'
replacements={
    "target=WORK/'matrix'":"target=WORK/phase",
    "WORK/'observation-build.json'":"WORK/'negotiated-build.json'",
    "'/data/local/tmp/fc-mux-credit-matrix-20261020'":"'/data/local/tmp/fc-mux-profile-'+phase+'-20261020'",
    "reserved=WORK/'traffic-matrix-reservation.json'":"reserved=WORK/('traffic-'+phase+'-reservation.json')",
    'intended_bytes=24*1024*1024':'intended_bytes=(65536 if control else 8*1024*1024+65536)',
    'enumerate((1,2,4,4,2,1))':'enumerate((1,) if control else (1,1,2))',
    "4*1024*1024//flows":"(65536 if control or number==0 else 4*1024*1024//flows)",
    "assert len({row['session_tag'] for row in observed})==1":"assert all(row['performance']['Mux']['Profile']==profile and row['performance']['Mux']['Window']==window for row in observed),'NEGOTIATED_PROFILE_MISMATCH'\n        assert len({row['session_tag'] for row in observed})==1",
    "session_tag=session,snapshots=len(observed)":"session_tag=session,profile=profile,window=window,snapshots=len(observed)",
    "reserved.write_text(json.dumps(":"assert sum(json.loads(path.read_text())['intended_bytes'] for path in WORK.glob('traffic-*-reservation.json'))+(65536 if control else 8*1024*1024+65536)<=64*1024*1024\n        reserved.write_text(json.dumps(",
    "output.append(row)":"output.append(dict(row,observed_epoch=int(record['__REALTIME_TIMESTAMP'])/1e6))",
    "    return output":"    return select_session(output,scope,time.time()) if scope else output",
    "initial=topology()":"initial=topology()\n    if scope:\n        assert initial==scope['topology']\n        assert 'network{'+scope['vpn_network']+'}' in adb('dumpsys connectivity').stdout",
    "(target/'preflight.json').write_text":"if scope:\n        assert gateway['InvocationID']==scope['gateway_invocation'] and gateway['MainPID']==scope['gateway_pid']\n    (target/'preflight.json').write_text",
    "session_tag=session,profile=profile,window=window,snapshots=len(observed)":"session_tag=session,profile=profile,window=window,scope=scope,snapshots=len(observed)",
    "            if stop.is_set():break":"            if scope:\n                assert 'network{'+scope['vpn_network']+'}' in adb('dumpsys connectivity').stdout,'OWNER_VPN_CHANGED_STOP'\n                counters(target/'capture-private.jsonl')\n            if stop.is_set():break",
}
for old,new in replacements.items():
    assert old in source,old
    source=source.replace(old,new)
source=source.replace('from prepare import ROOT, WORK, APK, digest','')
namespace=dict(__name__='__main__',__file__=str(original),ROOT=ROOT,WORK=WORK,APK=APK,digest=digest,phase=phase,control=control,window=window,profile=profile,scope=scope,select_session=select_session)
exec(compile(source,str(original),'exec'),namespace)
