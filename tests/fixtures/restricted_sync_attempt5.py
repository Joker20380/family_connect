
import contextlib,io,json,os,runpy,subprocess,sys,time
from pathlib import Path
root=Path('/opt/apps/family_connect');destination=root/'friends-restricted';stage=root/'restricted-materials-stage-20261001';backup=Path(BACKUP)
def persist(name,value):
    descriptor=os.open(backup/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(descriptor,'w') as stream:json.dump(value,stream);stream.flush();os.fsync(stream.fileno())
    descriptor=os.open(backup,os.O_RDONLY|os.O_DIRECTORY);os.fsync(descriptor);os.close(descriptor)
receipt=dict(generation='attempt5-ru-sync',timestamp=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),live_sync_pass=False)
try:
    sys.argv=[str(root/'friends-access/restricted-sync.pyz'),'--help']
    with contextlib.redirect_stdout(io.StringIO()):
        try:runpy.run_path(sys.argv[0],run_name='__main__')
        except SystemExit as status:assert status.code==0
    from control.friends.access import Access
    from control.friends.restricted import DirectoryValidationError,from_env,directory
    os.environ['FC_FRIENDS_RESTRICTED_DIR']=str(destination)
    service=from_env(Access(root/'friends-access/access.db'))
    trust,authority,crl,_,number=service._trust(int(time.time()))
    assert crl.next_update_utc.timestamp()-time.time()>480
    subprocess.run(['systemctl','daemon-reload'],capture_output=True,check=True)
    start=int(time.time())
    process=subprocess.run(['systemctl','start','family-connect-restricted-sync.service'],capture_output=True,timeout=45)
    logs=subprocess.run(['journalctl','-u','family-connect-restricted-sync.service','--since','@'+str(start),'-o','cat','--no-pager'],capture_output=True,text=True,check=True,timeout=10).stdout
    observation=dict(exit=process.returncode,module_import_error='ModuleNotFoundError' in logs,value_error='ValueError' in logs,classified_directory_error='directory_validation_failed' in logs)
    persist('ru-service-observation.json',observation)
    assert process.returncode==0 and not any(observation[name] for name in ('module_import_error','value_error','classified_directory_error'))
    trust,authority,crl,_,synced=service._trust(int(time.time()))
    assert synced==number+1
    seeds=directory(service.seed_source(),trust['family'],trust['gateway'])
    assert seeds['issued_at'].endswith('Z') and seeds['expires_at'].endswith('Z')
    ssh=['/usr/bin/ssh','-i',str(destination/'sync.key'),'-o','IdentitiesOnly=yes','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','UserKnownHostsFile='+str(destination/'known_hosts'),'-o','ConnectTimeout=5','family-restricted@186.246.45.246']
    probe=subprocess.run(ssh+['id'],capture_output=True,timeout=15)
    persist('generic-shell.json',dict(exit=probe.returncode,stdout_empty=not probe.stdout))
    assert probe.returncode==126 and not probe.stdout
    stale=json.dumps({'revocations':(stage/'revocations.pem').read_text()}).encode()
    probe=subprocess.run(ssh+['restricted-sync'],input=stale,capture_output=True,timeout=15)
    persist('stale-crl.json',dict(exit=probe.returncode,stdout_empty=not probe.stdout))
    assert probe.returncode==1 and not probe.stdout
    assert not any(marker in logs for marker in ('https://','PRIVATE KEY','OAuth ','YANDEX_TELEMOST_OAUTH_TOKEN=','y0_'))
    receipt.update(live_sync_pass=True,previous_crl_sequence=number,crl_sequence=synced,crl_expiry=int(crl.next_update_utc.timestamp()),directory_expires=seeds['expires_at'],canonical_utc=True,generic_shell_denied=True,stale_crl_rejected=True,module_import_error=False,strict_host_verification=True)
except BaseException as error:
    receipt['failure_type']=type(error).__name__
    if hasattr(error,'predicate'):receipt.update(stage=error.stage,predicate=error.predicate,field=error.field)
persist('ru-sync.json',receipt)
print(json.dumps(receipt))
