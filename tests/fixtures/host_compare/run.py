"""A/B/B/A operator wrapper around the existing isolated Family/Mux CLI."""
import datetime
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tarfile
import time

from prepare import ROOT, WORK, digest

HOSTS = {'A1':'186.246.45.246', 'B1':'185.251.89.19', 'B2':'185.251.89.19', 'A2':'186.246.45.246'}
UNIT_PREFIX = 'family-connect-hostcompare-20261020-'


def ssh(host, source, data=None, timeout=35):
    result=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','root@'+host,'python3 -B -c '+shlex.quote(source)],input=data,capture_output=True,timeout=timeout)
    if result.returncode:
        index=len(list(WORK.glob('remote-error-*.stderr')))+1
        (WORK/('remote-error-'+str(index)+'.stderr')).write_bytes(result.stderr[:65536])
        raise RuntimeError('remote operation failed exit='+str(result.returncode)+' stderr_sha256='+hashlib.sha256(result.stderr).hexdigest())
    return result.stdout


def save(path, value):
    assert not path.exists(), str(path)
    subprocess.run(['apply_patch'],input='*** Begin Patch\n*** Add File: '+str(path)+'\n'+''.join('+'+line+'\n' for line in json.dumps(value,indent=2).splitlines())+'*** End Patch\n',text=True,check=True,stdout=subprocess.DEVNULL)


def production_state():
    source="""import hashlib,json,subprocess
from pathlib import Path
state=dict(line.split('=',1) for line in subprocess.check_output(['systemctl','show','family-connect-restricted-bootstrap.service','-p','MainPID,InvocationID,ActiveState'],text=True).splitlines())
state['binary']=hashlib.sha256((Path('/proc')/state['MainPID']/'exe').read_bytes()).hexdigest()
state['profile']=hashlib.sha256(Path('/opt/apps/family_connect/friends-restricted/gateway.json').read_bytes()).hexdigest()
state['flags']={name:Path('/opt/apps/family_connect/friends-restricted/diag67',name).read_text().strip() for name in ['rtp-pacing','mux-profile','mux-counters']}
print(json.dumps(state))
"""
    return json.loads(ssh('186.246.45.246',source))


def create_room():
    source="""import json,os,re,shlex,stat,urllib.request
from pathlib import Path
path=Path('/opt/apps/family_connect/friends-restricted/provider.env');info=path.lstat()
assert info.st_uid==0 and stat.S_IMODE(info.st_mode)==0o600 and stat.S_ISREG(info.st_mode)
lines=shlex.split(path.read_text(),comments=True);values=dict(line.split('=',1) for line in lines)
assert set(values)=={'YANDEX_TELEMOST_OAUTH_TOKEN'}
request=urllib.request.Request('https://cloud-api.yandex.net/v1/telemost-api/conferences',data=b'{"waiting_room_level":"PUBLIC"}',headers={'Authorization':'OAuth '+values['YANDEX_TELEMOST_OAUTH_TOKEN'],'Content-Type':'application/json'},method='POST')
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs):return None
with urllib.request.build_opener(NoRedirect).open(request,timeout=15) as response:
 assert response.status==201
 raw=response.read(16385);assert len(raw)<=16384
 result=json.loads(raw);assert re.fullmatch(r'https://telemost.yandex.ru/j/[A-Za-z0-9_-]{1,128}',result['join_url'])
 print(json.dumps({'room':result['join_url'],'id_sha256':__import__('hashlib').sha256(result['id'].encode()).hexdigest()}))
"""
    return json.loads(ssh('186.246.45.246',source,timeout=25))


def remote_snapshot(host, stage):
    source="""import json
from pathlib import Path
root=Path(STAGE)
print(json.dumps({name:(root/name).read_text() for name in ['peer.jsonl','peer.stderr','resources.jsonl','exit.json'] if (root/name).exists() and (root/name).stat().st_size<33554432}))
""".replace('STAGE',repr(stage))
    return json.loads(ssh(host,source,timeout=35))


def main():
    os.umask(0o077)
    build=json.loads((WORK/'build.json').read_text())
    assert digest(WORK/'telemost-host-compare')==build['binary_sha256']
    assert not (WORK/'run-start.json').exists()
    before=production_state()
    assert before['binary']=='734b6ca6eb42be0367b703b657be87c624f3500ae408bbd771309ffaeb86128e'
    assert before['flags']=={'rtp-pacing':'OFF','mux-profile':'LEGACY64','mux-counters':'OFF'}
    save(WORK/'run-start.json',dict(utc=datetime.datetime.now(datetime.UTC).isoformat(),production=before,binary=build['binary_sha256'],order=list(HOSTS),maximum_application_reservation=4*build['application_bytes_per_phase'],limit=64*1024*1024))
    fixture=WORK/'isolated-identities'
    python=ROOT/'state-client-build/field65-export16/telemost-admission-ownership-1/build/venv/bin/python'
    try:
        with (WORK/'issuer.log').open('x') as log:
            subprocess.run([python,'-m','pilot.telemost_family_fixture','--out',fixture],cwd=ROOT,check=True,timeout=30,stdout=log,stderr=subprocess.STDOUT)
    except BaseException:
        if fixture.exists():shutil.rmtree(fixture)
        raise
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes
    profile=json.loads((fixture/'valid.json').read_text())
    authority=x509.load_pem_x509_certificate(profile['authority'].encode())
    certificate=x509.load_pem_x509_certificate(profile['certificate'].encode())
    save(WORK/'isolated-authority.json',dict(authority_sha256=authority.fingerprint(hashes.SHA256()).hex(),leaf_expiry=certificate.not_valid_after_utc.isoformat(),issuer='pilot.telemost_family_fixture',new_temporary_product_store=True,production_trust_import=False,production_credentials_copied=False))
    completed=[]
    try:
        for phase,host in HOSTS.items():
            assert production_state()==before,'PRODUCTION_CHANGED_STOP'
            directory=WORK/phase;directory.mkdir(mode=0o700)
            stage='/opt/apps/family_connect/hostcompare-20261020-'+phase.lower()
            unit=UNIT_PREFIX+phase.lower()
            local=None;staged=False;unit_started=False
            phase_error=None
            try:
                room=create_room()
                save(directory/'reservation.json',dict(phase=phase,host=host,room_id_sha256=room['id_sha256'],intended_application_bytes=build['application_bytes_per_phase'],production_before=before,maximum_request_seconds=150,server_resource_limits=dict(cpu_percent_one_core=50,memory_max_bytes=230686720,tasks_max=96,hard_seconds=510)))
                (directory/'room.input').write_text(room['room']);(directory/'room.input').chmod(0o600)
                shutil.copyfile(fixture/'valid.json',directory/'family.json');(directory/'family.json').chmod(0o600)
                shutil.copyfile(WORK/'telemost-host-compare',directory/'telemost-host-compare');(directory/'telemost-host-compare').chmod(0o700)
                (directory/'mux.json').write_text(json.dumps(dict(mode='host-compare',port=18764,seconds=0)))
                archive=io.BytesIO()
                with tarfile.open(fileobj=archive,mode='w:gz') as bundle:
                    for name,source in [('telemost-host-compare',WORK/'telemost-host-compare'),('family.json',fixture/'gateway.json'),('room.input',directory/'room.input'),('worker.py',ROOT/'tests/fixtures/host_compare/worker.py')]:
                        bundle.add(source,arcname=name)
                stage_source="""import hashlib,io,json,os,tarfile,sys
from pathlib import Path
root=Path(STAGE);root.mkdir(mode=0o700)
raw=sys.stdin.buffer.read(33554433);assert len(raw)<=33554432
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as archive:
 assert {member.name for member in archive.getmembers()}=={'telemost-host-compare','family.json','room.input','worker.py'}
 archive.extractall(root,filter='data')
assert hashlib.sha256((root/'telemost-host-compare').read_bytes()).hexdigest()==BINARY
for path in root.iterdir():path.chmod(0o700 if path.name=='telemost-host-compare' else 0o600);os.chown(path,65534,65534)
os.chown(root,65534,65534)
print(json.dumps({'staged':True}))
""".replace('STAGE',repr(stage)).replace('BINARY',repr(build['binary_sha256']))
                ssh(host,stage_source,archive.getvalue(),timeout=90);staged=True
                command=['systemd-run','--quiet','--collect','--unit='+unit,'--uid=nobody','--gid=nogroup','--working-directory='+stage,'--property=RuntimeMaxSec=510','--property=TimeoutStopSec=15','--property=MemoryMax=220M','--property=MemorySwapMax=0','--property=CPUQuota=50%','--property=TasksMax=96','--property=Nice=10','--property=NoNewPrivileges=yes','--property=ProtectSystem=strict','--property=ReadWritePaths='+stage,'--property=ProtectHome=yes','--property=PrivateTmp=yes','/usr/bin/python3',stage+'/worker.py',stage,'echo']
                ssh(host,'import subprocess;subprocess.run('+repr(command)+',check=True,capture_output=True,timeout=15)',timeout=25);unit_started=True
                gateway_ready=False
                for _ in range(35):
                    observed=remote_snapshot(host,stage)
                    rows=[json.loads(line) for line in observed.get('peer.jsonl','').splitlines() if line.strip()]
                    if any(row.get('event')=='connected' for row in rows):gateway_ready=True;break
                    if 'exit.json' in observed:break
                    time.sleep(2)
                assert gateway_ready,'ISOLATED_SERVER_MEDIA_NOT_CONNECTED'
                local=subprocess.Popen([sys.executable,str(ROOT/'tests/fixtures/host_compare/worker.py'),str(directory),'probe'])
                deadline=time.monotonic()+500
                while local.poll() is None and time.monotonic()<deadline:
                    time.sleep(5)
                    assert production_state()==before,'PRODUCTION_CHANGED_DURING_PHASE_STOP'
                assert local.poll() is not None,'LOCAL_PHASE_DEADLINE'
                exit_record=json.loads((directory/'exit.json').read_text())
                assert exit_record['exit']==0,'ISOLATED_CLIENT_FAILED'
            except Exception as error:
                phase_error=str(error)
            finally:
                if local is not None and local.poll() is None:
                    local.terminate()
                    try:local.wait(timeout=18)
                    except subprocess.TimeoutExpired:local.kill();local.wait(timeout=5)
                if unit_started:
                    ssh(host,'import subprocess;subprocess.run(["systemctl","stop",'+repr(unit)+'],check=False,capture_output=True,timeout=25)',timeout=30)
                if staged:
                    observed=remote_snapshot(host,stage)
                    for name,text in observed.items():(directory/('server-'+name)).write_text(text)
                    cleanup="""import json,os,shutil,subprocess
from pathlib import Path
root=Path(STAGE);assert root.parent==Path('/opt/apps/family_connect') and root.name.startswith('hostcompare-20261020-')
pids=[]
for process in Path('/proc').iterdir():
 if not process.name.isdigit() or int(process.name)==os.getpid():continue
 try:target=os.readlink(process/'exe')
 except (FileNotFoundError,PermissionError,ProcessLookupError):continue
 if target==str(root/'telemost-host-compare'):pids.append(int(process.name))
assert not pids
shutil.rmtree(root)
print(json.dumps({'owned_peer_pids':pids,'stage_removed':not root.exists(),'participant_leave':'CLI SIGTERM/context cancellation closes WebSocket and both peer connections; no provider conference-delete API used'}))
""".replace('STAGE',repr(stage))
                    save(directory/'cleanup.json',json.loads(ssh(host,cleanup)))
                for name in ['room.input','family.json']:
                    (directory/name).unlink(missing_ok=True)
                save(directory/'phase-result.json',dict(phase=phase,error=phase_error,completed=phase_error is None,production_after=production_state(),utc=datetime.datetime.now(datetime.UTC).isoformat()))
            completed.append(phase)
            print(json.dumps(dict(phase=phase,error=phase_error,finished=True)),flush=True)
            if phase_error:break
            client_rows=[json.loads(line) for line in (directory/'peer.jsonl').read_text().splitlines()]
            server_rows=[json.loads(line) for line in (directory/'server-peer.jsonl').read_text().splitlines()]
            counters=[row['stats'].get('ProtocolErrors',0) for row in client_rows+server_rows if row.get('event') in ['mux_sample','mux_result','mux_gateway']]
            if any(counters):
                save(directory/'protocol-error-stop.json',dict(counters=counters,decision='STOP_NO_FURTHER_PHASES',cause='Detailed category not exposed by existing CLI counters; do not dismiss because requests completed'))
                break
    finally:
        if fixture.exists():shutil.rmtree(fixture)
        save(WORK/'run-end.json',dict(utc=datetime.datetime.now(datetime.UTC).isoformat(),phases=completed,production=production_state(),isolated_identities_removed=not fixture.exists(),no_further_phases=True))


if __name__ == '__main__':
    main()
