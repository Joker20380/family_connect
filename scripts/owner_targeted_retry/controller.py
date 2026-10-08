from preparation import PreparationAborted, candidate
from contract import validate, verify_pair
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import select
import shlex
import socket
import subprocess
import time

os.umask(0o077)
output=Path(__file__).resolve().parent
def save(name,value):
    with (output/name).open('x') as stream:json.dump(value,stream,indent=2)
def adb(*args):
    result=subprocess.run(['adb','-s','31ce63ba',*args],capture_output=True,text=True,timeout=120)
    assert result.returncode==0,'ADB operation failed'
    return result.stdout
def receive(stream,timeout=20):
    assert select.select([stream],[],[],timeout)[0],'Operator bridge response timeout'
    line=stream.readline();assert line,'Operator bridge closed';return json.loads(line)
def remote_call(request):
    remote.stdin.write(json.dumps(request)+'\n');remote.stdin.flush()
    return receive(remote.stdout)
def phone_call(request):
    phone.write((json.dumps(request)+'\n').encode());phone.flush()
    return json.loads(phone.readline())
def diag(value):return value['stats']['packet']['diagnostic']
def latest_flow(value):
    events=diag(value)['lifecycle']['trace']
    flows=[event['delivery']['flow'] for event in events if event.get('delivery',{}).get('flow')]
    assert flows,'No sampled Reliable flow'
    return flows[-1]
preflight=json.loads((output/'fresh-preflight.json').read_text())
manifest=verify_pair(output/'accepted-pair.json')
validate(preflight['observed'],manifest)
assert preflight['result']=='PASS' and time.time()-datetime.datetime.fromisoformat(preflight['utc']).timestamp()<900
assert datetime.datetime.fromisoformat(preflight['leaf_expiry']).timestamp()-time.time()>1800
helper=output/'baseline-helper-beta71.apk'
assert hashlib.sha256(helper.read_bytes()).hexdigest()==json.loads((output/'helper-signature.json').read_text())['sha256']
assert 'Success' in adb('install','-r',str(helper))
gateway_source=r'''
import json,os,re,socket,stat,sys
from pathlib import Path
os.chdir('/opt/apps/family_connect/friends-restricted')
root=Path('diag67');info=root.stat();assert info.st_uid==info.st_gid==979 and stat.S_IMODE(info.st_mode)==0o700 and not list(root.iterdir())
os.setgroups([]);os.setgid(979);os.setuid(979)
print(json.dumps({'ready':True}),flush=True)
prearmed=False;bound=False
for line in sys.stdin:
    request=json.loads(line);session=request.pop('session');assert re.fullmatch('[0-9a-f]{64}',session)
    path=root/(session+'.sock')
    if request['operation']=='prearm':assert not prearmed;prearmed=True
    if request['operation']=='bind':assert not bound;bound=True
    assert request['operation'] in ('prearm','status','bind','cleanup')
    info=path.stat();assert info.st_uid==979 and stat.S_ISSOCK(info.st_mode) and stat.S_IMODE(info.st_mode)==0o600
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as connection:
        connection.settimeout(4);connection.connect(str(path));connection.sendall(json.dumps(request).encode());connection.shutdown(socket.SHUT_WR)
        data=b''
        while True:
            chunk=connection.recv(16384)
            if not chunk:break
            data+=chunk;assert len(data)<131072
    print(json.dumps(json.loads(data)),flush=True)
'''
remote=subprocess.Popen(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','root@186.246.45.246','python3 -u -c '+shlex.quote(gateway_source)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=(output/'gateway-operator.log').open('x'),text=True,bufsize=1)
assert receive(remote.stdout)=={'ready':True}
bridge='fc_selected71_'+secrets.token_hex(16)
port=int(adb('forward','tcp:0','localabstract:'+bridge).strip())
save('ONE-EXPERIMENT-STARTED.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),direction='owner_to_gateway',maximum_fault_arms=1,maximum_receiver_prearms=1))
instrument_log=(output/'instrumentation.log').open('x')
instrument=subprocess.Popen(['adb','-s','31ce63ba','shell','am','instrument','-w','-r','-e','class','com.familyconnect.app.OwnerSelectedRetryTest#singleExperiment','-e','owner_serial','31ce63ba','-e','expected_version','71','-e','bridge',bridge,'com.familyconnect.app.friends.test/androidx.test.runner.AndroidJUnitRunner'],stdout=instrument_log,stderr=subprocess.STDOUT)
connection=None;phone=None;key=None;session=None;proof=False
try:
    deadline=time.monotonic()+25
    while time.monotonic()<deadline:
        try:
            connection=socket.create_connection(('127.0.0.1',port),timeout=2)
            connection.settimeout(90);phone=connection.makefile('rwb',buffering=0)
            first=phone.readline()
            if first:break
            phone.close();connection.close();phone=None
        except (OSError,ValueError):pass
        time.sleep(.25)
    assert phone and first,'Test bridge unavailable; no retry'
    baseline=json.loads(first);save('baseline.json',baseline)
    assert baseline['fault']['count']==0 and not baseline['fault']['armed'] and not baseline['fault']['consumed']
    assert baseline['dns'] and baseline['tcp'] and baseline['https_full_body_bytes']>0
    current=baseline;session=diag(current)['session_tag'];assert re.fullmatch('[0-9a-f]{64}',session)
    assert diag(current)['correlation_status']=='VALID'
    assert not diag(current)['lifecycle'].get('evidence_watch')
    stages={(event['stage'],event['state']) for event in diag(current)['lifecycle']['trace']}
    assert ('FAMILY_TLS','ESTABLISHED') in stages and ('GATEWAY_SESSION','ESTABLISHED') in stages
    current,flow=candidate(phone_call,session,lambda value:save('selection-failure.json',value))
    save('selection-state.json',current)
    key=dict(session=session,direction='client_to_gateway',sequence=flow['send_next'],attempt=1,generation='')
    rx=remote_call(dict(session=session,operation='prearm',key=key));save('receiver-prearm.json',rx)
    assert rx['state']=='ARMED';key=rx['key'];assert len(bytes.fromhex(key['generation']))==16
    tx=phone_call(dict(operation='correlation',request=dict(operation='prearm',key=key)));save('sender-prearm.json',tx)
    assert tx['state']=='ARMED' and tx['key']==key
    target=phone_call(dict(operation='correlation',request=dict(operation='targeted_arm',key=key,prearm=rx)))
    save('sender-targeted-arm.json',target)
    if target.get('result')!='ARMED':raise PreparationAborted(target.get('reason','TARGETED_CONTROL_REJECTED'))
    armed=target['fault'];assert armed['target']=='logical_data_attempt0' and armed['sequence']==key['sequence'] and target['key']==key
    assert armed['armed'] and not armed['consumed'] and armed['count']==0
    assert phone_call({'operation':'traffic'})['started']
    deadline=time.monotonic()+24;descriptor=None
    while time.monotonic()<deadline:
        tx=phone_call(dict(operation='correlation',request=dict(operation='status',key=key)))
        save('sender-correlation-'+str(time.time_ns())+'.json',tx)
        if tx.get('descriptor') and tx['state']=='COMPLETE':
            descriptor=tx['descriptor'];break
        assert tx['state']=='ARMED',tx['state'];time.sleep(.15)
    assert descriptor,'Selected attempt1 descriptor unavailable'
    assert descriptor['key']==key
    save('sender-descriptor.json',descriptor)
    rx=remote_call(dict(session=session,operation='bind',key=key,descriptor=descriptor));save('receiver-bind.json',rx)
    while time.monotonic()<deadline:
        current=phone_call({'operation':'status'});save('sender-pinned-'+str(time.time_ns())+'.json',current)
        rx=remote_call(dict(session=session,operation='status',key=key));save('receiver-pinned-'+str(time.time_ns())+'.json',rx)
        watch=diag(current)['lifecycle'].get('evidence_watch',{})
        if rx['state']=='COMPLETE' and watch.get('state')=='COMPLETE':break
        assert rx['state'] not in ('EXPIRED','CONFLICT','CLEANED');time.sleep(.15)
    assert rx['state']=='COMPLETE' and watch['state']=='COMPLETE'
    ack=rx['reliable']['ack'];assert ack['result']=='ok' and ack['sent_ns']>=ack['created_ns']>0 and 'token' not in ack
    assert rx['reliable']['consumed']['after']['receive_next']>key['sequence']
    assert rx['reliable']['accepted']['sequence']==key['sequence']
    assert rx['reliable']['accepted']['before']['buffered']>0
    assert rx['reliable']['consumed']['buffered_successor_ready'] and rx['reliable']['consumed']['after']['receive_mask']&1
    assert current['fault']['count']==1 and current['fault']['consumed'] and not current['fault']['armed'] and current['fault']['sequence']==key['sequence']
    assert watch['events']['ack_received']['ack_base']>key['sequence'] and watch['events']['base_advanced']['ack_base']>key['sequence']
    save('complete-pinned-proof.json',dict(receiver=rx,sender=watch,fault=current['fault'],descriptor=descriptor))
    proof=True
    rxclean=remote_call(dict(session=session,operation='cleanup',key=key));save('receiver-cleanup.json',rxclean);assert rxclean['state']=='CLEANED'
    txclean=phone_call(dict(operation='correlation',request=dict(operation='cleanup',key=key)));save('sender-cleanup.json',txclean);assert txclean['state']=='CLEANED'
    deadline=time.monotonic()+30
    while time.monotonic()<deadline:
        current=phone_call({'operation':'status'});save('continuity-'+str(time.time_ns())+'.json',current)
        assert 'traffic_error' not in current and current['healthy']
        assert diag(current)['session_tag']==session and not diag(current)['reliable_terminal']
        if current.get('traffic'):break
        time.sleep(.5)
    assert len(current['traffic']['requests'])==3
    save('experiment-result.json',dict(result='PASS',selected_sequence=key['sequence'],pinned_complete=True,traffic=current['traffic'],one_drop=True))
except PreparationAborted as error:
    save('experiment-result.json',dict(result='PREPARATION_ABORTED',reason=str(error),intentional_drops=0,pinned_complete=False))
except Exception as error:
    classification='EVIDENCE_INCOMPLETE'
    try:
        failure_status=phone_call({'operation':'status'});save('failure-status.json',failure_status)
        if not failure_status['healthy'] or diag(failure_status)['reliable_terminal']:classification='TRANSPORT_FAILURE'
    except Exception:classification='OPERATOR_OR_ENDPOINT_FAILURE'
    save('failure-classification.json',dict(classification=classification))
    save('experiment-result.json',dict(result='PARTIAL' if proof else 'FAIL',exception_type=type(error).__name__,bounded_reason=str(error)[:160] if isinstance(error,AssertionError) else 'operator/test error; inspect retained receipts',pinned_complete=proof))
finally:
    if phone:
        if key:
            try:save('final-receiver-cleanup.json',remote_call(dict(session=session,operation='cleanup',key=key)))
            except Exception:pass
            try:save('final-sender-cleanup.json',phone_call(dict(operation='correlation',request=dict(operation='cleanup',key=key))))
            except Exception:pass
        try:save('final-disarm.json',phone_call({'operation':'stop'}))
        except Exception:pass
        phone.close()
    if connection:connection.close()
    try:instrument.wait(timeout=90)
    except subprocess.TimeoutExpired:
        adb('shell','am','force-stop','com.familyconnect.app.friends');instrument.wait(timeout=15)
    instrument_log.close();remote.stdin.close();remote.wait(timeout=10)
    adb('forward','--remove','tcp:'+str(port))
    save('instrumentation-exit.json',dict(exit=instrument.returncode,finished=time.time()))
print((output/'experiment-result.json').read_text())
