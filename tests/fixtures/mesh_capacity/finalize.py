"""Readback and seal completed evidence; never deploy or change production."""
import datetime
import json
import os
from pathlib import Path
import re
import subprocess
import tarfile

from prepare import ROOT, WORK, FIX, SOURCE, digest, patch_file
from run import production_state, ssh, HOST


def main():
    expected={'C1','R816a','T816','P816','C05','R832a','R1632a','R3232a','R3232b','R1632b','R832b','P3232','P816b','Rmatch','C1b','Rmix','Reverse','R32long','R32sustain'}
    summary=json.loads((WORK/'summary.json').read_text())
    assert set(summary['phases'])==expected
    manifest=json.loads((WORK/'build.json').read_text())
    assert digest(WORK/'telemost-capacity')==manifest['binary_sha256']
    assert all(digest(SOURCE/name)==value for name,value in manifest['source_inventory'].items())
    assert {str(path.relative_to(SOURCE)) for path in SOURCE.rglob('*') if path.is_file()}==set(manifest['source_inventory'])
    source_total,media,wire,closed=0,0,0,0
    rows=[]
    protocol_warnings=[]
    all_paths=set()
    for phase,item in summary['phases'].items():
        directory=WORK/phase
        result=item['result'];reservation=item['reservation']
        assert result['completed'] and result['error'] is None
        assert result['production_equal']
        assert reservation['binary_sha256']==manifest['binary_sha256']==digest(directory/'telemost-capacity')
        assert not any((directory/name).exists() for name in ['family.json','room.input','isolated-identities'])
        assert json.loads((directory/'cleanup.json').read_text())['stage_removed']
        if item['config']['Mode']=='P':
            assert len(item['requests'])==5 and all(row['passed'] for row in item['requests'])
            counters=[dict(request=row['name'],before=row['mux_before']['ProtocolErrors'],after=row['mux_after']['ProtocolErrors']) for row in item['requests']]
            if any(row['before'] or row['after'] for row in counters):
                assert phase=='P816' and counters==[dict(request=name,before=0 if name=='control_echo' else 1,after=0 if name=='control_echo' else 1) for name in ['control_echo','single','parallel_0','parallel_1','reverse_control']]
                warning=dict(phase=phase,detected='postflight, not at the phase boundary',counters=counters,cause='not established by exported counters; transition is between echo completion and single-download before snapshot',classification='EXCLUDED_FROM_CLEAN_P_COMPARISON',data_bodies='5/5 exact, not a clean protocol pass',workflow_gap='new wrapper omitted previous harness protocol stop gate; subsequent independent sessions already completed before discovery',repair='future runner rejects any nonzero P before/after counter; no production or binary change; use already completed clean P3232/P816b only')
                protocol_warnings.append(warning)
                patch_file(directory/'postflight-protocol-warning.json',json.dumps(warning,indent=2))
        else:
            received=item['received']
            assert received['count']+len(received['missing_ids'])==received['expected']==item['config']['Count']
            assert received['corrupt']==0
            if item['config']['Mode']!='C':assert received['count']==received['expected'] and item['complete']['complete']
        source_total+=reservation['application_reserved'];wire+=result['wire_charged']
        for name,endpoint in item['endpoints'].items():
            carrier=endpoint['carrier']
            assert carrier['PublisherState']=='closed' and carrier['SubscriberState']=='closed'
            assert not endpoint['wire']['stopped']
            closed+=1
            media+=endpoint['wire']['rtp_bytes']+endpoint['wire']['rtcp_bytes']
            for pair in endpoint['selected_paths']:
                if pair.get('remote'):all_paths.add(pair['remote']['ip'])
        for path in directory.glob('*'):
            if path.suffix not in ['.json','.jsonl','.stderr','.log']:continue
            text=path.read_text()
            assert not re.search(r'-----BEGIN (?:[A-Z ]+)?PRIVATE KEY-----|https://telemost\.yandex\.ru/j/[A-Za-z0-9_-]+|OAuth [A-Za-z0-9_-]{8,}',text),str(path)
        rows.append(dict(phase=phase,application_reserved=reservation['application_reserved'],media_charge=result['wire_charged'],closed=True,complete=item['config']['Mode']=='P' or item['complete']['complete']))
    assert source_total==summary['application_reserved']<=128*1024*1024
    assert wire==summary['wire_charged']<=256*1024*1024
    local=[]
    for process in Path('/proc').iterdir():
        if not process.name.isdigit() or int(process.name)==os.getpid():continue
        try:
            target=os.readlink(process/'exe')
            args=(process/'cmdline').read_bytes().split(b'\0')
        except (FileNotFoundError,PermissionError,ProcessLookupError):continue
        if target.endswith('/telemost-capacity') or str(FIX/'worker.py').encode() in args:local.append(int(process.name))
    assert not local
    remote=json.loads(ssh(HOST,"""import json,os
from pathlib import Path
found=[]
for process in Path('/proc').iterdir():
 if not process.name.isdigit() or int(process.name)==os.getpid():continue
 try:
  target=os.readlink(process/'exe')
  args=(process/'cmdline').read_bytes().split(b'\\0')
 except (FileNotFoundError,PermissionError,ProcessLookupError):continue
 if target.endswith('/telemost-capacity') or any(arg.startswith(b'/opt/apps/family_connect/capacity-20261020-') for arg in args):found.append(int(process.name))
print(json.dumps({'owned_pids':found,'stages':[str(path) for path in Path('/opt/apps/family_connect').glob('capacity-20261020-*')]}))
"""))
    assert not remote['owned_pids'] and not remote['stages']
    production=production_state()
    first=summary['phases']['C1']['reservation']['production_before']
    assert production==first
    routes={}
    for address in sorted(all_paths):
        result=subprocess.run(['ip','-j','route','get',address],capture_output=True,text=True,check=True,timeout=5)
        routes[address]=json.loads(result.stdout)
    verification=dict(status='COMPLETED_WITH_P816_PROTOCOL_WARNING_NOT_PRODUCT_ADMISSION',protocol_warnings=protocol_warnings,utc=datetime.datetime.now(datetime.UTC).isoformat(),phases=len(rows),closed_peers=closed,application_reserved=source_total,application_limit=128*1024*1024,outgoing_rtp_rtcp_bytes=media,conservative_wire_charge=wire,wire_limit=256*1024*1024,production=production,production_equals_initial=True,local_owned_pids=local,remote=remote,routes_postflight=routes,source_inventory_sha256=__import__('hashlib').sha256(json.dumps(manifest['source_inventory'],sort_keys=True).encode()).hexdigest(),build_manifest_sha256=digest(WORK/'build.json'),binary_sha256=manifest['binary_sha256'],fixture_inventory={path.name:digest(path) for path in FIX.iterdir() if path.is_file()},original_operator_sha256=digest(WORK/'operator-used/run.py'),results=rows,provider_metadata_deletion='not confirmed; normal participant departure and both PeerConnections closed')
    patch_file(WORK/'verification.json',json.dumps(verification,indent=2))
    archive=WORK/'mesh-capacity-kit.tar.gz'
    assert not archive.exists()
    with tarfile.open(archive,'w:gz') as bundle:
        for path in [SOURCE,WORK/'telemost-capacity',FIX,WORK/'operator-used']:
            bundle.add(path,arcname=path.name,filter=lambda item:None if '__pycache__' in item.name else item)
        for path in WORK.iterdir():
            if path.is_file() and path.suffix in ['.json','.log','.patch']:bundle.add(path,arcname=path.name)
        for phase in expected:
            for path in (WORK/phase).iterdir():
                if path.is_file() and path.suffix in ['.json','.jsonl','.log','.stderr']:bundle.add(path,arcname=phase+'/'+path.name)
    patch_file(WORK/'kit.json',json.dumps(dict(path=str(archive.relative_to(ROOT)),sha256=digest(archive),bytes=archive.stat().st_size),indent=2))
    print(json.dumps({key:verification[key] for key in ['status','phases','closed_peers','application_reserved','outgoing_rtp_rtcp_bytes','conservative_wire_charge','production_equals_initial']}))


if __name__=='__main__':main()
