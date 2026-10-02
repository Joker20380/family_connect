"""Exact redacted attempt #8 NL flow; tests execute only with intercepted boundaries."""

FLOW_SHA256 = '640972d5fd9a5919a4e5ca0c4a35e3d9bb6c7f30d0c674040f6726191caa0649'
FLOW = r'''
import collections,json,os,subprocess,time
from pathlib import Path
root=Path('/opt/apps/family_connect');destination=root/'friends-restricted';backup=Path(BACKUP)
def persist(name,value):
    path=backup/name
    descriptor=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(descriptor,'w') as stream:json.dump(value,stream);stream.flush();os.fsync(stream.fileno())
    descriptor=os.open(backup,os.O_RDONLY|os.O_DIRECTORY);os.fsync(descriptor);os.close(descriptor)
def state():
    raw=subprocess.run(['systemctl','show',unit,'-p','ActiveState,SubState,MainPID,NRestarts,ExecMainStatus'],capture_output=True,text=True,check=True).stdout
    return dict(line.split('=',1) for line in raw.splitlines())
unit='family-connect-restricted-bootstrap.service';start=int(time.time());ready=False;failure=None;validation=None
try:
    from cryptography import x509
    profile=json.loads((destination/'gateway.json').read_bytes())
    crl=x509.load_pem_x509_crl(profile['revocations'].encode())
    assert crl.next_update_utc.timestamp()-time.time()>600
    assert state()['ActiveState']=='inactive'
    subprocess.run(['systemctl','start',unit],check=True,capture_output=True,timeout=30)
    for attempt in range(60):
        current=state()
        assert current['ActiveState']=='active' and int(current['NRestarts'])==0
        if (destination/'directory.json').is_file():
            command=[str(root/'friends-access/venv/bin/python'),'-I',str(root/'friends-access/restricted-sync.pyz'),'directory-check','--profile',str(destination/'gateway.json'),'--directory',str(destination/'directory.json'),'--receipt',str(backup/'live-directory-receipt.json'),'--generation','attempt8-nl-live']
            result=subprocess.run(command,cwd='/',capture_output=True,timeout=20)
            validation=json.loads((backup/'live-directory-receipt.json').read_bytes())
            assert result.returncode==0 and validation['result']=='passed'
            value=json.loads((destination/'directory.json').read_bytes())
            assert all(value[name].endswith('Z') for name in ('issued_at','expires_at'))
            assert len(value['seeds'])==1
            ready=True;break
        time.sleep(2)
    assert ready
    logs=subprocess.run(['journalctl','-u',unit,'--since','@'+str(start),'-o','json','-n','100','--no-pager'],capture_output=True,text=True,check=True,timeout=5).stdout
    events=collections.Counter();sensitive=False
    for line in logs.splitlines():
        message=json.loads(line).get('MESSAGE','')
        sensitive=sensitive or any(marker in message for marker in ('https://','http://','PRIVATE KEY','OAuth ','YANDEX_TELEMOST_OAUTH_TOKEN=','y0_'))
        try:
            event=json.loads(message).get('event','')
            if event.replace('_','').isalnum() and len(event)<80:events[event]+=1
        except (ValueError,AttributeError):pass
    assert not sensitive and events['bootstrap_seed_ready']==1
except BaseException as error:
    failure=type(error).__name__;ready=False
receipt=dict(timestamp=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),generation='attempt8-nl-live',bootstrap_ready=ready,start_utc=start,service_state=state(),failure_type=failure,directory_validation=validation)
if ready:receipt.update(directory_issued=value['issued_at'],directory_expires=value['expires_at'],seed_count=1,canonical_utc=True,python_live_directory_pass=True,log_events=dict(events),sensitive_log_markers=False)
persist('nl-live.json',receipt)
print(json.dumps(receipt))
'''
