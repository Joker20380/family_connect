"""Postflight: inventory, all reservations, both-end proofs, owned process cleanup."""
import datetime
import importlib.util
import json
import os
from pathlib import Path
import shlex
import subprocess
from interaction_prepare import ROOT, WORK, FIX, SOURCE, inventory, digest, save
from interaction_proof import validate
from interaction_analyze import records


def main():
    assert (WORK/'live-complete.json').exists() or (WORK/'repair-stop.json').exists()
    build=json.loads((WORK/'build.json').read_text())
    assert inventory(SOURCE)==build['source_inventory']
    assert digest(WORK/'telemost-capacity')==build['binary_sha256']
    attempts=[]
    for path in sorted(WORK.glob('*/reservation.json'),key=lambda item:item.stat().st_mtime):
        directory=path.parent
        reservation=json.loads(path.read_text())
        result=json.loads((directory/'phase-result.json').read_text())
        assert result['production_equal'] and result['isolated_identities_removed']
        assert json.loads((directory/'cleanup.json').read_text())['stage_removed']
        assert digest(directory/'telemost-capacity')==build['binary_sha256']
        assert not any((directory/name).exists() for name in ['family.json','room.input','isolated-identities'])
        sides=[records(directory/name) for name in ['peer.jsonl','server-peer.jsonl']]
        for rows in sides:
            assert any(row.get('event')=='summary' and row.get('stats',{}).get('PublisherState')=='closed' for row in rows)
            assert not any(row.get('mux',{}).get('ProtocolErrors',0) for row in rows)
            trace=next(row for row in rows if row.get('event')=='media_trace_end')
            assert trace['overflow']==0 and trace['policy']=='A'
            assert not any(row.get('transport',{}).get('lab_wire',{}).get('stopped') for row in rows)
        if not result['error']:
            proof=json.loads((directory/'two-end-proof.json').read_text())
            validate([proof['client'],proof['server']],[row for row in sides[0] if row.get('event')=='host_request'],131072 if reservation['config']['MuxCredit128'] else 65536)
            assert (directory/'finish.input').exists()
        attempts.append(dict(phase=directory.name,error=result['error'],source=reservation['application_reserved'],media=result['wire_charged'],production_before=reservation['production_before'],production_after=result['production_after']))
    assert sum(row['source'] for row in attempts)<=64*1024**2
    assert sum(row['media'] for row in attempts)<=128*1024**2
    local=[]
    for process in Path('/proc').iterdir():
        if not process.name.isdigit():continue
        try:
            target=os.readlink(process/'exe')
            command=(process/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')
        except OSError:continue
        if 'p-stack-interaction-20261021/' in target or str(WORK/'worker.py') in command:local.append(int(process.name))
    assert not local
    remote=r'''
import hashlib,json,os,subprocess
from pathlib import Path
state=dict(line.split('=',1) for line in subprocess.check_output(['systemctl','show','family-connect-restricted-bootstrap.service','-p','MainPID,InvocationID,ActiveState'],text=True).splitlines())
state['binary']=hashlib.sha256((Path('/proc')/state['MainPID']/'exe').read_bytes()).hexdigest()
state['profile']=hashlib.sha256(Path('/opt/apps/family_connect/friends-restricted/gateway.json').read_bytes()).hexdigest()
state['flags']={name:Path('/opt/apps/family_connect/friends-restricted/diag67',name).read_text().strip() for name in ['rtp-pacing','mux-profile','mux-counters']}
peers=[]
for process in Path('/proc').iterdir():
 if not process.name.isdigit():continue
 try:target=os.readlink(process/'exe')
 except OSError:continue
 if '/pstack-20261021-' in target:peers.append(int(process.name))
units=subprocess.check_output(['systemctl','list-units','--all','--no-legend','--plain','family-connect-pstack-20261021-*'],text=True).strip()
print(json.dumps(dict(production=state,peers=peers,stages=[str(path) for path in Path('/opt/apps/family_connect').glob('pstack-20261021-*')],units=units)))
'''
    output=subprocess.check_output(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','root@186.246.45.246','python3 -B -c '+shlex.quote(remote)],timeout=45)
    remote_result=json.loads(output)
    assert not remote_result['peers'] and not remote_result['stages'] and not remote_result['units']
    network={}
    for name,command in [('addresses',['ip','-j','address']),('rules',['ip','-j','rule']),('routes',['ip','-j','route'])]:
        result=subprocess.run(command,capture_output=True,text=True,timeout=5)
        network[name]=json.loads(result.stdout) if result.returncode==0 else dict(error=result.returncode)
    first=json.loads((WORK/attempts[0]['phase']/'client-network.json').read_text())
    save(WORK/'verification.json',dict(utc=datetime.datetime.now(datetime.UTC).isoformat(),attempts=attempts,
         remote=remote_result,local_peers=local,client_network_equal=network==first,client_network_after=network,
         source_reserved=sum(row['source'] for row in attempts),media_charged=sum(row['media'] for row in attempts),
         binary_sha256=build['binary_sha256'],final_production_equal=remote_result['production']==attempts[-1]['production_after'],
         provider_metadata_deletion='not claimed; owned peers, ephemeral profiles and stages removed',product_admission=False))
    print(json.dumps(dict(attempts=len(attempts),source=sum(row['source'] for row in attempts),media=sum(row['media'] for row in attempts),local_peers=local,remote_peers=remote_result['peers'],client_network_equal=network==first)))


if __name__=='__main__':main()
