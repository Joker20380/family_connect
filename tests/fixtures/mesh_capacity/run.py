"""One finite NL-only session; existing room/issuer/cleanup workflow, new namespace."""
import argparse
import datetime
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import time

from prepare import ROOT, WORK, FIX, digest

spec=importlib.util.spec_from_file_location('host_operator',ROOT/'tests/fixtures/host_compare/run.py')
host_operator=importlib.util.module_from_spec(spec)
spec.loader.exec_module(host_operator)
ssh,save,production_state,create_room,remote_snapshot=(getattr(host_operator,name) for name in ['ssh','save','production_state','create_room','remote_snapshot'])
HOST='186.246.45.246'


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []


def check_product_protocol(events):
    counters=[row[boundary]['ProtocolErrors'] for row in events if row.get('event')=='host_request' for boundary in ['mux_before','mux_after']]
    assert counters and not any(counters),'P_PROTOCOL_COUNTER_NONZERO_STOP'


def main():
    os.umask(0o077)
    parser=argparse.ArgumentParser()
    parser.add_argument('phase')
    parser.add_argument('--mode',choices=['C','R','T','P'],required=True)
    parser.add_argument('--rate',type=int,default=0)
    parser.add_argument('--seconds',type=int,default=20)
    parser.add_argument('--count',type=int,default=256)
    parser.add_argument('--sizes',default='16384')
    parser.add_argument('--send',type=int,default=8)
    parser.add_argument('--receive',type=int,default=16)
    parser.add_argument('--reverse',action='store_true')
    args=parser.parse_args()
    assert not list(WORK.glob('*/postflight-protocol-warning.json')),'POSTFLIGHT_PROTOCOL_WARNING_TASK_CLOSED'
    assert args.phase.isalnum() and len(args.phase)<25
    sizes=[int(value) for value in args.sizes.split(',')]
    count=args.count
    if args.mode=='C':
        assert args.rate>0 and args.seconds<=30
        count=int(args.rate*args.seconds/(sum(sizes)/len(sizes)))
    config=dict(Mode=args.mode,Run=int.from_bytes(args.phase.encode(),'little')%(2**63)+1,Count=count,Sizes=sizes,Rate=args.rate,Seconds=args.seconds if args.mode=='C' else 0,SendWindow=args.send,ReceiveWindow=args.receive,Reverse=args.reverse)
    app=sum(sizes[index%len(sizes)] for index in range(count))+65536
    if args.mode=='P':app=8585273
    previous=[json.loads(path.read_text()) for path in WORK.glob('*/reservation.json')]
    app_used=sum(item['application_reserved'] for item in previous)
    wire_used=0
    for item in previous:
        receipt=WORK/item['phase']/'phase-result.json'
        wire_used+=json.loads(receipt.read_text())['wire_charged'] if receipt.exists() else item['wire_reserved']
    server_limit=min(32*1024*1024,app*3+1024*1024)
    client_limit=2*1024*1024
    if args.reverse:server_limit,client_limit=client_limit,server_limit
    assert app_used+app<=128*1024*1024,'APPLICATION_BUDGET'
    assert wire_used+server_limit+client_limit<=256*1024*1024,'WIRE_BUDGET'
    build=json.loads((WORK/'build.json').read_text())
    assert digest(WORK/'telemost-capacity')==build['binary_sha256']
    before=production_state()
    assert before['binary']=='734b6ca6eb42be0367b703b657be87c624f3500ae408bbd771309ffaeb86128e'
    assert before['flags']=={'rtp-pacing':'OFF','mux-profile':'LEGACY64','mux-counters':'OFF'}
    directory=WORK/args.phase;directory.mkdir(mode=0o700)
    stage='/opt/apps/family_connect/capacity-20261020-'+args.phase.lower()
    unit='family-connect-capacity-20261020-'+args.phase.lower()
    fixture=directory/'isolated-identities'
    local=None;staged=False;unit_started=False;failure=None
    started=time.monotonic()
    save(directory/'reservation.json',dict(phase=args.phase,config=config,application_reserved=app,wire_reserved=server_limit+client_limit,server_wire_limit=server_limit,client_wire_limit=client_limit,application_previously_reserved=app_used,wire_previously_charged=wire_used,production_before=before,binary_sha256=build['binary_sha256'],host=HOST,utc=datetime.datetime.now(datetime.UTC).isoformat(),resource_limits=dict(cpu='50% of one core',memory='220MiB',tasks=96,runtime=510),session_scope='fresh disposable room and issuer, no production room or authority'))
    network={}
    for name,command in [('addresses',['ip','-j','address']),('rules',['ip','-j','rule']),('routes',['ip','-j','route'])]:
        result=subprocess.run(command,capture_output=True,text=True,timeout=5)
        network[name]=json.loads(result.stdout) if result.returncode==0 else dict(error=result.returncode)
    save(directory/'client-network.json',network)
    try:
        python=ROOT/'state-client-build/field65-export16/telemost-admission-ownership-1/build/venv/bin/python'
        with (directory/'issuer.log').open('x') as log:
            subprocess.run([python,'-m','pilot.telemost_family_fixture','--out',fixture],cwd=ROOT,check=True,timeout=30,stdout=log,stderr=subprocess.STDOUT)
        room=create_room()
        save(directory/'room-receipt.json',dict(id_sha256=room['id_sha256'],new_session=True))
        (directory/'room.input').write_text(room['room'])
        (directory/'capacity.json').write_text(json.dumps(config))
        (directory/'wire-limit.input').write_text(str(client_limit))
        shutil.copyfile(fixture/'valid.json',directory/'family.json');(directory/'family.json').chmod(0o600)
        shutil.copyfile(WORK/'telemost-capacity',directory/'telemost-capacity');(directory/'telemost-capacity').chmod(0o700)
        archive=io.BytesIO()
        with tarfile.open(fileobj=archive,mode='w:gz') as bundle:
            for name,source in [('telemost-capacity',WORK/'telemost-capacity'),('family.json',fixture/'gateway.json'),('room.input',directory/'room.input'),('capacity.json',directory/'capacity.json'),('worker.py',FIX/'worker.py')]:bundle.add(source,arcname=name)
        source="""import hashlib,io,json,os,tarfile,sys
from pathlib import Path
root=Path(STAGE);root.mkdir(mode=0o700)
raw=sys.stdin.buffer.read(33554433);assert len(raw)<=33554432
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as archive:
 assert {member.name for member in archive.getmembers()}=={'telemost-capacity','family.json','room.input','capacity.json','worker.py'}
 archive.extractall(root,filter='data')
assert hashlib.sha256((root/'telemost-capacity').read_bytes()).hexdigest()==BINARY
(root/'wire-limit.input').write_text(str(LIMIT))
for path in root.iterdir():path.chmod(0o700 if path.name=='telemost-capacity' else 0o600);os.chown(path,65534,65534)
os.chown(root,65534,65534)
print(json.dumps({'staged':True}))
""".replace('STAGE',repr(stage)).replace('BINARY',repr(build['binary_sha256'])).replace('LIMIT',str(server_limit))
        ssh(HOST,source,archive.getvalue(),timeout=90);staged=True
        command=['systemd-run','--quiet','--collect','--unit='+unit,'--uid=nobody','--gid=nogroup','--working-directory='+stage,'--property=RuntimeMaxSec=510','--property=TimeoutStopSec=15','--property=MemoryMax=220M','--property=MemorySwapMax=0','--property=CPUQuota=50%','--property=TasksMax=96','--property=Nice=10','--property=NoNewPrivileges=yes','--property=ProtectSystem=strict','--property=ReadWritePaths='+stage,'--property=ProtectHome=yes','--property=PrivateTmp=yes','/usr/bin/python3',stage+'/worker.py',stage,'echo']
        ssh(HOST,'import subprocess;subprocess.run('+repr(command)+',check=True,capture_output=True,timeout=15)',timeout=25);unit_started=True
        ready=False
        for attempt in range(35):
            observed=remote_snapshot(HOST,stage)
            events=[json.loads(line) for line in observed.get('peer.jsonl','').splitlines() if line.strip()]
            if any(row.get('event')=='connected' for row in events):ready=True;break
            if 'exit.json' in observed:break
            time.sleep(2)
        assert ready,'SERVER_MEDIA_NOT_CONNECTED'
        local=subprocess.Popen([sys.executable,str(FIX/'worker.py'),str(directory),'probe'])
        deadline=time.monotonic()+490
        while local.poll() is None and time.monotonic()<deadline:
            time.sleep(5)
            current=production_state()
            assert current==before,'PRODUCTION_READBACK_CHANGED_STOP_NO_ROLLBACK'
        assert local.poll() is not None,'LOCAL_DEADLINE'
        time.sleep(3)
        assert json.loads((directory/'exit.json').read_text())['exit']==0,'CLIENT_FAILED'
        if args.mode=='P':check_product_protocol(rows(directory/'peer.jsonl'))
    except Exception as error:failure=str(error)
    finally:
        if local is not None and local.poll() is None:
            local.terminate()
            try:local.wait(timeout=18)
            except subprocess.TimeoutExpired:local.kill();local.wait(timeout=5)
        if unit_started:ssh(HOST,'import subprocess;subprocess.run(["systemctl","stop",'+repr(unit)+'],check=False,capture_output=True,timeout=25)',timeout=30)
        if staged:
            observed=remote_snapshot(HOST,stage)
            for name,text in observed.items():(directory/('server-'+name)).write_text(text)
            cleanup="""import json,os,shutil
from pathlib import Path
root=Path(STAGE);assert root.parent==Path('/opt/apps/family_connect') and root.name.startswith('capacity-20261020-')
pids=[]
for process in Path('/proc').iterdir():
 if not process.name.isdigit() or int(process.name)==os.getpid():continue
 try:target=os.readlink(process/'exe')
 except (FileNotFoundError,PermissionError,ProcessLookupError):continue
 if target==str(root/'telemost-capacity'):pids.append(int(process.name))
assert not pids
shutil.rmtree(root)
print(json.dumps({'owned_peer_pids':pids,'stage_removed':not root.exists(),'provider_metadata_deletion':'not supported; normal session close only'}))
""".replace('STAGE',repr(stage))
            save(directory/'cleanup.json',json.loads(ssh(HOST,cleanup)))
        for name in ['room.input','family.json']:(directory/name).unlink(missing_ok=True)
        if fixture.exists():shutil.rmtree(fixture)
        wire=0;details={}
        for side,filename,limit in [('client','peer.jsonl',client_limit),('server','server-peer.jsonl',server_limit)]:
            events=rows(directory/filename)
            samples=[row['transport']['lab_wire'] for row in events if 'lab_wire' in row.get('transport',{})]
            closed=any(row.get('event')=='summary' and row.get('stats',{}).get('PublisherState')=='closed' for row in events)
            maximum=max([item['conservative_bytes'] for item in samples],default=0)
            charge=maximum+65536 if closed and samples else limit
            charge=min(charge,limit)
            wire+=charge
            details[side]=dict(maximum_observed=maximum,closed=closed,charged=charge,reserved=limit,tail_allowance=65536)
        after=production_state()
        save(directory/'phase-result.json',dict(phase=args.phase,error=failure,completed=failure is None,seconds_including_setup_drain_confirmation_cleanup=time.monotonic()-started,production_after=after,production_equal=after==before,wire_charged=wire,wire_details=details,isolated_identities_removed=not fixture.exists(),utc=datetime.datetime.now(datetime.UTC).isoformat()))
    print(json.dumps(dict(phase=args.phase,error=failure,application_reserved=app,wire_charged=wire)),flush=True)
    if failure:sys.exit(1)


if __name__=='__main__':main()
