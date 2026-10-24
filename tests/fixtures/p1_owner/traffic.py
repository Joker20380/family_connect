"""Reuse the pinned Android HTTP meter with a new, nonrefundable owner ledger."""
import argparse
import ast
import concurrent.futures
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import threading
import time

ROOT=Path(__file__).resolve().parents[3]
WORK=ROOT/'state-client-build/p1-owner-acceptance-20261021'
sys.path.insert(0,str(ROOT))
from scripts.owner_android_support import snapshot,save


def main():
    os.umask(0o077);parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('label');parser.add_argument('--mode',choices=['probe','phase','active'],required=True)
    parser.add_argument('--gate',required=True,type=Path)
    args=parser.parse_args();assert re.fullmatch('[A-Za-z0-9-]+',args.label)
    gate=json.loads(args.gate.read_text());assert time.time()-gate['observed_epoch']<90
    assert gate['profile'] in ('P0','P1') and gate['both_limits_verified']
    expected_apk=json.loads((WORK/'delivery/signing-receipt.json').read_text())['signed']['sha256']
    assert gate['apk_sha256']==expected_apk
    source=ROOT/'tests/fixtures/mesh_throughput_trace/measure.py'
    assert hashlib.sha256(source.read_bytes()).hexdigest()=='17e76fb9f3d8c46b5e7e4b5c55fa0f8098b59aef63e0e66c94cbce81b2c2a5ef'
    tree=ast.parse(source.read_text());helpers=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in ('adb','topology')]
    request=next(node for node in ast.walk(tree) if isinstance(node,ast.FunctionDef) and node.name=='request')
    namespace=dict(globals());exec(compile(ast.Module(body=helpers,type_ignores=[]),str(source),'exec'),namespace)
    adb,topology=namespace['adb'],namespace['topology'];initial=topology();assert initial==gate['topology']
    amount={'probe':1024,'phase':(8<<20)+12*1024,'active':(4<<20)+31*1024}[args.mode]
    ledger=WORK/'traffic-ledger';ledger.mkdir(mode=0o700,exist_ok=True)
    used=sum(json.loads(path.read_text())['requested_bound'] for path in ledger.glob('*.json'))
    assert used+amount<=64<<20
    save(ledger/(args.label+'.json'),dict(requested_bound=amount,no_refund=True,mode=args.mode,profile=gate['profile'],reserved_epoch=time.time()))
    out=WORK/('traffic-'+args.label);out.mkdir(mode=0o700)
    save(out/'gate.json',gate)
    collector_source=ROOT/'tests/fixtures/queue_retry/measure.py'
    assert hashlib.sha256(collector_source.read_bytes()).hexdigest()=='b3558a77d7772e2035ef5c7bd66fdc3a5eebb8b7b79173b6903c16ca9c36e8f5'
    expression=next(node for node in ast.walk(ast.parse(collector_source.read_text())) if isinstance(node,ast.Assign) and any(isinstance(name,ast.Name) and name.id=='collector' for name in node.targets))
    namespace.update(gateway=dict(MainPID=gate['gateway_pid'],InvocationID=gate['gateway_invocation']),start=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC'))
    exec(compile(ast.Module(body=[expression],type_ignores=[]),str(collector_source),'exec'),namespace)
    collector_code=namespace['collector'].replace("'--since',"+repr(namespace['start']),"'-n','0'").replace('time.monotonic()+600','time.monotonic()+1200')
    capture=(out/'capture-private.jsonl').open('x');capture_error=(out/'capture.stderr').open('x')
    collector=subprocess.Popen(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','root@186.246.45.246','python3 -B -c '+shlex.quote(collector_code)],stdin=subprocess.PIPE,stdout=capture,stderr=capture_error)
    remote_root='/data/local/tmp/fc-p1-owner-'+args.label
    stop=threading.Event();requests=[];cells=[]
    namespace.update(out=out,remote_root=remote_root,stop=stop,lock=threading.Lock(),requests=requests,fields=('http_code','http_version','ssl_verify_result','remote_ip','local_port','num_connects','size_download','time_namelookup','time_connect','time_appconnect','time_starttransfer','time_total'))
    exec(compile(ast.Module(body=[request],type_ignores=[]),str(source),'exec'),namespace)
    started=time.monotonic();observations=0
    monitor_stop=threading.Event()
    def monitor():
        for index in range(600):
            if monitor_stop.is_set():break
            try:
                value=snapshot('31ce63ba')
                save(out/('monitor-'+str(index)+'.json'),dict(epoch=time.time(),snapshot=value))
                if value['state']!='CONNECTED' or value['restricted_session'].get('session_tag')!=gate['session_tag']:stop.set()
            except Exception as error:
                save(out/('monitor-error-'+str(index)+'.json'),dict(error=type(error).__name__,epoch=time.time()));stop.set();return
            monitor_stop.wait(2)
    watcher=threading.Thread(target=monitor);watcher.start()
    def check():
        nonlocal observations
        assert topology()==initial and not stop.is_set(),'ROUTE_OR_HTTP_FAILURE'
        assert collector.poll() is None,'COLLECTOR_EXITED'
        phone=snapshot('31ce63ba');save(out/('snapshot-'+str(observations)+'.json'),phone);observations+=1
        assert phone['state']=='CONNECTED' and phone['vpn_capture_open'] and phone['restricted_readiness']=='READY'
        current=phone['restricted_session']
        assert current['session_tag']==gate['session_tag'] and current['terminal_reason']=='NONE','SESSION_CHANGED_OR_FAILED'
        assert current['reliable_limits']==gate['limits'] and current['mux_window']==gate['mux_window']
    def small(prefix):
        for index in range(6):check();namespace['request'](prefix+'-'+str(index),1024);time.sleep(.1)
    failure=None
    try:
        adb('umask 077; mkdir '+remote_root).check_returncode();check()
        if args.mode=='probe':namespace['request']('probe',1024)
        elif args.mode=='phase':
            small('idle')
            for flows in (1,2):
                check()
                with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
                    jobs=[pool.submit(namespace['request'],'bulk-'+str(flows)+'-'+str(index),(4<<20)//flows) for index in range(flows)]
                    probe=pool.submit(small,'loaded') if flows==1 else None
                    batch=[job.result() for job in jobs]
                    if probe is not None:probe.result()
                wall=max(float(row['metrics']['END']) for row in batch)-min(float(row['metrics']['BEGIN']) for row in batch)
                received=sum(int(row['metrics'].get('BODY_BYTES',0)) for row in batch)
                cells.append(dict(flows=flows,seconds=wall,bytes=received,mbit_s=received*8/wall/1e6,completed=sum(row['valid'] for row in batch)))
                check()
        else:
            assert gate['profile']=='P1'
            for index in range(31):
                time.sleep(max(0,started+index*30-time.monotonic()));check()
                namespace['request']('periodic-'+str(index),1024)
                if index in (0,10,20,30):namespace['request']('periodic-bulk-'+str(index),1<<20)
                check()
        check()
    except BaseException as error:
        failure=type(error).__name__+': '+str(error);raise
    finally:
        monitor_stop.set();watcher.join(timeout=15)
        collector.stdin.close()
        try:collector.wait(timeout=15)
        except subprocess.TimeoutExpired:collector.kill();collector.wait()
        capture.close();capture_error.close()
        adb('rmdir '+remote_root)
        save(out/'summary.json',dict(mode=args.mode,profile=gate['profile'],duration_seconds=time.monotonic()-started,cells=cells,attempts=len(requests),completed=sum(row['valid'] for row in requests),requested_bound=amount,actual_requested=sum(row['intended_bytes'] for row in requests),failure=failure,closure_acceptance='PENDING_BOTH_END_TERMINALS'))


if __name__=='__main__':main()
