import datetime
import hashlib
import inspect
import json
import os
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[3]
STATE = ROOT / 'state-client-build/mesh-perf-3b'
HOST = 'root@186.246.45.246'
STAGE = '/opt/apps/family_connect/friends-restricted/mesh-perf-3b-20261018-01'
os.umask(0o077)


def provider_options(path, uid, mode, keys, present):
    assert path == '/opt/apps/family_connect/friends-restricted/provider.env'
    assert uid == 0 and mode == 0o600
    assert keys == ['YANDEX_TELEMOST_OAUTH_TOKEN'] and present
    return ['--property=EnvironmentFile=' + path]


REMOTE = r'''
import datetime,hashlib,json,os,pwd,grp,re,socket,stat,subprocess,time
from pathlib import Path
from cryptography import x509
os.umask(0o077)
root=Path('/opt/apps/family_connect/friends-restricted')
stage=root/'mesh-perf-3b-20261018-01'
unit='family-connect-mesh-perf-3b-20261018-01.service'
prod='family-connect-restricted-bootstrap.service'
def run(args,timeout=15):return subprocess.check_output(args,text=True,stderr=subprocess.PIPE,timeout=timeout)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def state(name):return dict(line.split('=',1) for line in run(['systemctl','show',name,'--property=MainPID,InvocationID,ActiveState,SubState,NRestarts']).splitlines())
def save(name,value):
    with (stage/name).open('x') as handle:
        json.dump(value,handle,sort_keys=True);handle.flush();os.fsync(handle.fileno())
    descriptor=os.open(stage,os.O_RDONLY|os.O_DIRECTORY);os.fsync(descriptor);os.close(descriptor)
candidate=stage/'diagnostic-broker-owner-final'
assert sha(candidate)=='b5e6f5630e5f38575f82f8c1e0fa906b47a467290773d638ecb83b0872daa790'
before=state(prod)
assert before['ActiveState']=='active' and before['NRestarts']=='0'
assert sha(Path('/proc')/before['MainPID']/'exe')=='4b722d2d7f2159b96953e27777494bf596768f860ee8da7e634fb1100b08fab7'
assert run(['systemctl','show',unit,'--property=LoadState','--value']).strip()=='not-found'
profile_path=root/'gateway.json'
profile=json.loads(profile_path.read_bytes())
original=json.loads((root/'directory.json').read_bytes())
guard=json.loads((stage/'guard-input.json').read_bytes())
assert profile['family']==guard['family'] and profile['gateway']==original['seeds'][0]['gateway']
ca=x509.load_pem_x509_certificate(profile['authority'].encode());leaf=x509.load_pem_x509_certificate(profile['certificate'].encode());crl=x509.load_pem_x509_crl(profile['revocations'].encode())
leaf.verify_directly_issued_by(ca);assert crl.is_signature_valid(ca.public_key())
now=datetime.datetime.now(datetime.timezone.utc)
assert leaf.not_valid_before_utc<=now and ca.not_valid_before_utc<=now and crl.last_update_utc<=now
deadline=datetime.datetime.fromisoformat(guard['not_after'].replace('Z','+00:00'))
assert min(ca.not_valid_after_utc,leaf.not_valid_after_utc,crl.next_update_utc)>deadline
user=run(['systemctl','show',prod,'--property=User','--value']).strip() or 'root'
account=pwd.getpwnam(user)
group=run(['systemctl','show',prod,'--property=Group','--value']).strip()
gid=grp.getgrnam(group).gr_gid if group else account.pw_gid
assert profile_path.stat().st_uid==account.pw_uid and stat.S_IMODE(profile_path.stat().st_mode)==0o600
environment=dict(item.decode().split('=',1) for item in (Path('/proc')/before['MainPID']/'environ').read_bytes().split(b'\0') if item)
environment_files=run(['systemctl','show',prod,'--property=EnvironmentFiles','--value']).strip()
provider_paths=re.findall(r'(/[^ ]+) \(ignore_errors=(?:yes|no)\)',environment_files)
assert len(provider_paths)==1, 'PROVIDER_ENVIRONMENT_FILE_NOT_UNIQUE'
provider_file=Path(provider_paths[0]);provider_info=provider_file.lstat()
assert stat.S_ISREG(provider_info.st_mode) and provider_info.st_nlink==1
provider_keys=[line.strip().split('=',1)[0] for line in provider_file.read_text().splitlines() if line.strip() and not line.strip().startswith('#') and '=' in line]
provider=provider_options(str(provider_file),provider_info.st_uid,stat.S_IMODE(provider_info.st_mode),provider_keys,bool(environment.get('YANDEX_TELEMOST_OAUTH_TOKEN')))
transport_environment={key:value for key,value in environment.items() if key.startswith(('FC_','TELEMOST_','RELIABLESTREAM_'))}
assert set(transport_environment)<= {'FC_DIAGNOSTIC_CONTROL_DIR','FC_FATAL_RECEIPT_DIR'}, 'UNREVIEWED_TRANSPORT_ENVIRONMENT'
with socket.socket() as probe:probe.bind(('127.0.0.1',18445))
os.chown(stage,0,gid);os.chmod(stage,0o750)
os.chmod(candidate,0o555)
private=stage/'state';private.mkdir(mode=0o700);os.chown(private,account.pw_uid,gid)
for name in ('correlation','fatal'):
    (private/name).mkdir(mode=0o700);os.chown(private/name,account.pw_uid,gid)
guard_path=private/'owner-guard.json'
with guard_path.open('x') as handle:json.dump(guard,handle);handle.flush();os.fsync(handle.fileno())
os.chown(guard_path,account.pw_uid,gid);os.chmod(guard_path,0o600)
seconds=int((deadline-now).total_seconds())
assert 3600<seconds<=7200
arguments=['systemd-run','--unit='+unit,'--property=Type=exec','--property=Restart=no',
    '--property=User='+user,'--property=Group='+str(gid),'--property=RuntimeMaxSec='+str(seconds),
    '--property=TimeoutStopSec=20','--property=KillMode=control-group','--property=MemoryMax=1G',
    '--property=TasksMax=256','--property=NoNewPrivileges=yes','--property=ProtectSystem=strict',
    '--property=ReadWritePaths='+str(private),'--property=ReadOnlyPaths='+str(profile_path),
    '--property=PrivateTmp=yes','--working-directory='+str(private),
    '--setenv=FC_PERF_OWNER_GUARD='+str(guard_path),
    '--setenv=FC_DIAGNOSTIC_CONTROL_DIR='+str(private/'correlation'),
    '--setenv=FC_FATAL_RECEIPT_DIR='+str(private/'fatal')]
arguments += provider
for key in ('GOMAXPROCS','GODEBUG'):
    if key in environment:arguments.append('--setenv='+key+'='+environment[key])
arguments += [str(candidate),'--family-config',str(profile_path),'--directory-export',str(private/'directory.json'),
              '--listen','127.0.0.1:18445','--duration',str(seconds)+'s','--chat-services']
save('start-intent.json',dict(operation=guard['operation'],production=before,profile_sha256=sha(profile_path),
     production_directory_sha256=sha(root/'directory.json'),candidate_sha256=sha(candidate),deadline=guard['not_after'],
     uid=account.pw_uid,gid=gid,unit=unit,arguments=arguments,utc=now.isoformat()))
run(arguments,timeout=30)
limit=time.monotonic()+120
while True:
    current=state(unit)
    if current['ActiveState'] in ('failed','inactive'):raise RuntimeError('CANARY_NOT_RUNNING')
    if (private/'directory.json').exists():break
    assert time.monotonic()<limit,'CANARY_READY_TIMEOUT'
    time.sleep(2)
assert current['NRestarts']=='0' and current['ActiveState']=='active'
assert sha(Path('/proc')/current['MainPID']/'exe')==sha(candidate)
directory=json.loads((private/'directory.json').read_bytes())
issued=datetime.datetime.fromisoformat(directory['issued_at'].replace('Z','+00:00'))
assert issued>=now and directory['family']==profile['family']
assert all(seed['gateway']==profile['gateway'] for seed in directory['seeds'])
assert {seed['join_url'] for seed in directory['seeds']}.isdisjoint(seed['join_url'] for seed in original['seeds'])
assert stat.S_IMODE((private/'directory.json').stat().st_mode)==0o600
assert state(prod)==before and sha(profile_path)==json.loads((stage/'start-intent.json').read_bytes())['profile_sha256']
result=dict(result='STAGED_READY_NOT_ROUTED',operation=guard['operation'],state=current,loaded_sha256=sha(candidate),
    directory_sha256=sha(private/'directory.json'),issued_at=directory['issued_at'],expires_at=directory['expires_at'],
    production_unchanged=True,isolated_room=True,private_state=True,profile_read_only=True,owner_guard=True,unit=unit,
    runtime_max_seconds=seconds,resources=dict(memory_max='1G',tasks_max=256,cpu_quota='NOT_SET'))
save('ready-receipt.json',result)
print(json.dumps(result))
'''
REMOTE = inspect.getsource(provider_options) + '\n' + REMOTE


def main():
    local = STATE / 'canary-operation'
    local.mkdir(mode=0o700)
    config = json.loads((STATE/'api-operation/operation.json').read_bytes())
    assert json.loads((STATE/'api-operation/reconciled-prepare.json').read_bytes())['result'] == 'PREPARED_NOT_ARMED_RECONCILED'
    now = datetime.datetime.now(datetime.timezone.utc)
    guard = dict(config['owner_guard_identity'], operation=config['operation'],
                 not_before=now.isoformat(), not_after=(now+datetime.timedelta(hours=2)).isoformat())
    (local/'guard-input.json').write_text(json.dumps(guard))
    (local/'stage-remote.py').write_text(REMOTE)
    files = [local/'guard-input.json', local/'stage-remote.py', STATE/'diagnostic-broker-owner-final']
    expected = {path.name:hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
    (local/'upload-intent.json').write_text(json.dumps(dict(stage=STAGE,hashes=expected)))
    ssh = ['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10',HOST]
    subprocess.run(ssh+['mkdir','-m','700',STAGE],check=True,timeout=20)
    subprocess.run(['scp','-q','-o','BatchMode=yes',*map(str,files),HOST+':'+STAGE+'/'],check=True,timeout=45)
    output = subprocess.check_output(ssh+['sha256sum',*[STAGE+'/'+name for name in expected]],text=True,timeout=20)
    actual = {Path(line.split()[1]).name:line.split()[0] for line in output.splitlines()}
    assert actual==expected
    (local/'upload-receipt.json').write_text(json.dumps(actual))
    result = subprocess.run(ssh+['python3','-I','-B',STAGE+'/stage-remote.py'],capture_output=True,text=True,timeout=165)
    (local/'start.stderr').write_text(result.stderr)
    (local/'start.stdout').write_text(result.stdout)
    if result.returncode:
        raise RuntimeError('CANARY_START_FAILED_OR_UNCERTAIN; reconcile and stop only created canary, no retry')
    value = json.loads(result.stdout)
    (local/'ready-receipt.json').write_text(json.dumps(value,indent=2))
    subprocess.run(['scp','-q','-o','BatchMode=yes',HOST+':'+STAGE+'/state/directory.json',str(local/'canary-directory.json')],check=True,timeout=20)
    assert hashlib.sha256((local/'canary-directory.json').read_bytes()).hexdigest()==value['directory_sha256']
    print(json.dumps(value,indent=2))


if __name__ == '__main__':
    main()
