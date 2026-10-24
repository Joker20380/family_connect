"""Finite106 Wi-Fi control using the retained meter and the existing32MiB budget."""
import ast
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import sys
import threading
import time

import accept as previous

ROOT=previous.ROOT
WORK=ROOT/'state-client-build/owner-wifi-resume-20261023'
APK='242855c43e889e708234ce2f687fa02d37bccb1eee408904f09216b6abd8f020'


def main():
    os.umask(0o077)
    label=sys.argv[1]
    assert re.fullmatch('[a-zA-Z0-9-]+',label)
    mode=sys.argv[3] if len(sys.argv)>3 else 'control'
    assert mode in ('control','probe')
    out=WORK/label;out.mkdir(exist_ok=False)
    stop=threading.Event();finished=threading.Event();requests=[]
    remote_root='/data/local/tmp/fc-wifi106-'+label
    source=ROOT/'tests/fixtures/mesh_throughput_trace/measure.py'
    syntax=ast.parse(source.read_text())
    initial={}

    def adb(command,timeout=25):
        if '/system/bin/curl' in command:
            assert not stop.is_set()
            command=command.replace('/system/bin/curl','/system/bin/curl --interface '+shlex.quote(initial['interface']),1)
            body=re.search(r'--output (\S+)\.body',command)
            assert body and body[1].startswith(remote_root+'/')
            pid_path=body[1]+'.pid'
            command=command.replace('; result=$?;', ' & meter_pid=$!; echo "$meter_pid" > '+pid_path+'; wait "$meter_pid"; result=$?; rm -f '+pid_path+';',1)
        return previous.adb(command,timeout)

    namespace=dict(adb=adb,re=re)
    topology_node=next(node for node in syntax.body if isinstance(node,ast.FunctionDef) and node.name=='topology')
    exec(compile(ast.Module(body=[topology_node],type_ignores=[]),str(source),'exec'),namespace)

    def observe(name,tag=None):
        phone=previous.snapshot(previous.SERIAL)
        previous.save(out/(name+'.json'),dict(utc=previous.utc(),snapshot=phone))
        assert phone['network_class']=='WIFI','NETWORK_PHASE_CHANGED'
        current=previous.healthy(phone,tag,106)
        topology=namespace['topology']()
        raw=adb('dumpsys connectivity').stdout
        underlay=[line for line in raw.splitlines() if line.strip().startswith('NetworkAgentInfo{network{'+topology['underlay']+'}')]
        assert len(underlay)==1 and 'ni{WIFI' in underlay[0] and 'Transports: WIFI ' in underlay[0], 'UNDERLAY_NOT_WIFI'
        assert not initial or topology==initial,'TOPOLOGY_CHANGED'
        return current,topology

    tag,initial=observe('phone-before')
    package_path=adb('pm path com.familyconnect.app.friends').stdout.strip().removeprefix('package:')
    assert package_path.startswith('/data/app/') and '\n' not in package_path
    assert adb('sha256sum '+shlex.quote(package_path)).stdout.split()[0]==APK
    evidence=Path(sys.argv[2]).resolve()
    assert evidence.is_relative_to((ROOT/'state-client-build').resolve())
    manifest=json.loads((evidence/'acquisition-manifest.json').read_text())
    for record in manifest['records']:
        assert record['returncode']==0
        assert hashlib.sha256((evidence/record['file']).read_bytes()).hexdigest()==record['sha256']
    remote=json.loads((evidence/'runtime.json').read_text())
    assert 0<=time.time()-remote['epoch']<600,'FRESH_GATEWAY_READBACK_REQUIRED'
    records,errors=previous.runpy.run_path(str(ROOT/'tests/fixtures/queue_retry/journal.py'))['reassemble']((evidence/'journal.jsonl').read_text().splitlines())
    remote['parser_errors']=errors;remote['records']=[]
    for row in records:
        try:message=json.loads(row.get('MESSAGE',''))
        except ValueError:continue
        remote['records'].append(dict(at=row['__REALTIME_TIMESTAMP'],invocation=row.get('_SYSTEMD_INVOCATION_ID'),**message))
    previous.save(out/'gateway-provenance.json',dict(path=str(evidence),manifest_sha256=hashlib.sha256((evidence/'acquisition-manifest.json').read_bytes()).hexdigest()))
    previous.save(out/'gateway-analysis.json',remote)
    assert remote['binary_sha256']==previous.GATEWAY and remote['state']['ActiveState']=='active' and not remote['parser_errors']
    matching=[row for row in remote['records'] if row.get('diagnostic',{}).get('session_tag')==tag and row['invocation']==remote['state']['InvocationID']]
    profiles=[row['diagnostic'] for row in matching if row.get('event')=='session_profile']
    assert len(profiles)==1 and not any(row.get('event')=='session_terminal' for row in matching)
    profile=profiles[0]
    assert profile['speed_profile']=='P1' and profile['reliable_limits']==previous.LIMITS
    assert profile['mux_profile']=='CREDIT128' and profile['mux_window']==131072
    gate=dict(utc=previous.utc(),tag=tag,topology=initial,profile=profile,gateway=previous.GATEWAY,
        invocation=remote['state']['InvocationID'],apk=APK,wifi_upstream_independence='UNKNOWN',
        tariff_state='OWNER_REPORTED_MOBILE_THROTTLING_20261022',meter_sha256=hashlib.sha256(source.read_bytes()).hexdigest())
    previous.save(out/'gate.json',gate)
    print('BOTH_END_WIFI_TUN_P1_GATE_PASS',flush=True)
    old=ROOT/'state-client-build/owner-wifi-resume-20261022/traffic-ledger.json'
    ledger=json.loads(old.read_text());reservations=WORK/'traffic-reservations';reservations.mkdir(exist_ok=True)
    amount=1024 if mode=='probe' else (8<<20)+16*1024
    reserved=ledger['reserved_bytes']+sum(json.loads(path.read_text())['reserved_bytes'] for path in reservations.glob('*.json'))
    assert ledger['limit_bytes']==32<<20 and reserved+amount<=ledger['limit_bytes']
    previous.save(reservations/(label+'.json'),dict(utc=previous.utc(),reserved_bytes=amount,previous_reserved=reserved,
        parent_ledger_sha256=hashlib.sha256(old.read_bytes()).hexdigest(),refundable=False,includes_failed_attempts=True))
    namespace.update(out=out,remote_root=remote_root,stop=stop,lock=threading.Lock(),requests=requests,time=time,shlex=shlex,json=json,
        fields=('http_code','http_version','ssl_verify_result','remote_ip','local_port','num_connects','size_download',
                'time_namelookup','time_connect','time_appconnect','time_starttransfer','time_total'))
    request_node=next(node for node in ast.walk(syntax) if isinstance(node,ast.FunctionDef) and node.name=='request')
    exec(compile(ast.Module(body=[request_node],type_ignores=[]),str(source),'exec'),namespace)

    def abort_meter():
        command='for file in '+remote_root+'/*.pid; do test -f "$file" || continue; read meter_pid < "$file"; '
        command+='case "$meter_pid" in ""|*[!0-9]*) continue;; esac; '
        command+='tr "\\000" " " < /proc/"$meter_pid"/cmdline 2>/dev/null | grep -F '+shlex.quote(remote_root+'/')+' >/dev/null && kill -TERM "$meter_pid"; done'
        previous.adb(command)

    def monitor():
        for index in range(180):
            if finished.wait(2):return
            try:observe('monitor-%03d'%index,tag)
            except Exception as failure:
                previous.save(out/'monitor-failure.json',dict(utc=previous.utc(),error=str(failure)))
                stop.set();abort_meter();return
        stop.set();abort_meter()

    def request(name,size):
        assert not stop.is_set()
        observe('before-'+name,tag)
        result=namespace['request'](name,size)
        assert result['valid'],'INCOMPLETE_BODY_SEE_METER_AND_TRANSPORT_SEPARATELY'
        return result

    adb('umask 077; mkdir '+remote_root).check_returncode()
    watcher=threading.Thread(target=monitor);watcher.start()
    cells=[];failure=None
    try:
        if mode=='probe':
            request('small-reconnect',1024)
            observe('phone-after',tag)
            return
        for index in range(4):request('small-before-'+str(index),1024)
        for flows in (1,2):
            with concurrent.futures.ThreadPoolExecutor(max_workers=flows+1) as pool:
                bulk=[pool.submit(request,'bulk-%d-%d'%(flows,index),(4<<20)//flows) for index in range(flows)]
                time.sleep(1)
                for index in range(2):request('small-during-%d-%d'%(flows,index),1024)
                batch=[future.result() for future in bulk]
            wall=max(float(row['metrics']['END']) for row in batch)-min(float(row['metrics']['BEGIN']) for row in batch)
            cells.append(dict(flows=flows,seconds=wall,bytes=sum(row['intended_bytes'] for row in batch),mbit_s=(4<<20)*8/wall/1e6))
        for index in range(4):request('small-after-'+str(index),1024)
        for index in range(4):
            assert not finished.wait(10)
            request('idle-small-'+str(index),1024)
        observe('phone-after',tag)
    except BaseException as error:
        failure=type(error).__name__+': '+str(error)
        raise
    finally:
        finished.set();watcher.join(timeout=15)
        previous.adb('rmdir '+remote_root)
        previous.save(out/'summary.json',dict(utc=previous.utc(),mode=mode,cells=cells,attempts=len(requests),
            completed=sum(row['valid'] for row in requests),reserved_bytes=amount,
            actual_requested=sum(row['intended_bytes'] for row in requests),failure=failure,
            monitor_stopped=not watcher.is_alive(),network_change_recorded=(out/'monitor-failure.json').exists()))
        print('FINITE_WIFI_CONTROL_FINISHED',failure,flush=True)


if __name__=='__main__':main()
