"""Equal-volume matrix reusing the existing phone request and bounded collector."""

import ast
import concurrent.futures
import datetime
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import threading
import time

from prepare import ROOT, WORK, APK, digest

sys.path.insert(0,str(ROOT/'tests/fixtures/queue_retry'))
from journal import reassemble


def counters(path):
    if not path.exists(): return []
    raw=[]
    for line in path.read_text().splitlines():
        try: row=json.loads(line)
        except json.JSONDecodeError: continue
        if row.get('kind')=='journal': raw.append(row['raw'])
    records,errors=reassemble(raw)
    output=[]
    for record in records:
        try: row=json.loads(record['MESSAGE'])
        except (json.JSONDecodeError,TypeError): continue
        if row.get('event')=='restricted_performance_v1': output.append(row)
    return output


def main():
    os.umask(0o077)
    target=WORK/'matrix';target.mkdir(mode=0o700,exist_ok=False)
    original=ROOT/'tests/fixtures/mesh_throughput_trace/measure.py'
    assert digest(original)=='17e76fb9f3d8c46b5e7e4b5c55fa0f8098b59aef63e0e66c94cbce81b2c2a5ef'
    tree=ast.parse(original.read_text())
    request=next(node for node in ast.walk(tree) if isinstance(node,ast.FunctionDef) and node.name=='request')
    helpers=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in ('adb','topology')]
    namespace=dict(globals());exec(compile(ast.Module(body=helpers,type_ignores=[]),str(original),'exec'),namespace)
    adb,topology=namespace['adb'],namespace['topology']
    initial=topology()
    apk=adb('pm path com.familyconnect.app.friends').stdout.strip().removeprefix('package:')
    assert adb('sha256sum '+shlex.quote(apk)).stdout.split()[0]==APK
    expected=json.loads((WORK/'observation-build.json').read_text())['sha256']
    remote="""
import hashlib,json,subprocess
from pathlib import Path
state=dict(line.split('=',1) for line in subprocess.check_output(['systemctl','show','family-connect-restricted-bootstrap.service','-p','MainPID,InvocationID,ActiveState,NRestarts'],text=True).splitlines())
assert state['ActiveState']=='active'
assert hashlib.sha256((Path('/proc')/state['MainPID']/'exe').read_bytes()).hexdigest()=='EXPECTED'
print(json.dumps(state))
""".replace('EXPECTED',expected)
    gateway=json.loads(subprocess.check_output(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=8','root@186.246.45.246','python3 -B -'],input=remote,text=True,timeout=25))
    (target/'preflight.json').write_text(json.dumps(dict(gateway=gateway,topology=initial,sha256=expected,utc=datetime.datetime.now(datetime.timezone.utc).isoformat())))
    collector_source=ROOT/'tests/fixtures/queue_retry/measure.py'
    collector_tree=ast.parse(collector_source.read_text())
    expression=next(node for node in ast.walk(collector_tree) if isinstance(node,ast.Assign) and any(isinstance(name,ast.Name) and name.id=='collector' for name in node.targets))
    namespace.update(gateway=gateway,start=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC'))
    exec(compile(ast.Module(body=[expression],type_ignores=[]),str(collector_source),'exec'),namespace)
    output=(target/'capture-private.jsonl').open('x');errors=(target/'capture.stderr').open('x')
    collector=subprocess.Popen(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=8','root@186.246.45.246','python3 -B -c '+shlex.quote(namespace['collector'])],stdin=subprocess.PIPE,stdout=output,stderr=errors)
    remote_root='/data/local/tmp/fc-mux-credit-matrix-20261020'
    adb('umask 077; mkdir '+remote_root).check_returncode()
    stop=threading.Event();requests=[]
    namespace.update(out=target,remote_root=remote_root,stop=stop,lock=threading.Lock(),requests=requests,
                     fields=('http_code','http_version','ssl_verify_result','remote_ip','local_port','num_connects','size_download','time_namelookup','time_connect','time_appconnect','time_starttransfer','time_total'))
    exec(compile(ast.Module(body=[request],type_ignores=[]),str(original),'exec'),namespace)
    cells=[]
    try:
        time.sleep(7)
        observed=counters(target/'capture-private.jsonl')
        assert observed and all(row['performance'].get('Window') and row['performance'].get('Mux') for row in observed),'COUNTERS_NOT_PRESENT_NO_BULK'
        assert len({row['session_tag'] for row in observed})==1,'AMBIGUOUS_SESSION_NO_BULK'
        session=observed[-1]['session_tag']
        (target/'counter-gate.json').write_text(json.dumps(dict(session_tag=session,snapshots=len(observed),full_packet_export=any(row['performance'].get('Media') for row in observed))))
        assert all(not row['performance'].get('Media') and 'Events' not in row['performance']['Window'] for row in observed)
        reserved=WORK/'traffic-matrix-reservation.json';assert not reserved.exists()
        reserved.write_text(json.dumps(dict(intended_bytes=24*1024*1024,limit_bytes=64*1024*1024,no_retries=True)))
        for number,flows in enumerate((1,2,4,4,2,1)):
            assert not stop.is_set() and topology()==initial
            assert {row['session_tag'] for row in counters(target/'capture-private.jsonl')}=={session},'SESSION_CHANGED_STOP'
            with concurrent.futures.ThreadPoolExecutor(max_workers=flows) as pool:
                batch=list(pool.map(lambda index:namespace['request'](f'cell-{number}-flow-{index}',4*1024*1024//flows),range(flows)))
            wall=max(float(row['metrics']['END']) for row in batch)-min(float(row['metrics']['BEGIN']) for row in batch)
            total=sum(int(row['metrics'].get('BODY_BYTES','0')) for row in batch)
            cell=dict(cell=number,flows=flows,bytes=total,wall_seconds=wall,aggregate_mbit_s=total*8/wall/1e6,completed=sum(row['valid'] for row in batch))
            cells.append(cell);(target/'cells.json').write_text(json.dumps(cells,indent=2));print(json.dumps(cell),flush=True)
            if stop.is_set():break
        time.sleep(5)
    finally:
        collector.stdin.close()
        try:collector.wait(timeout=15)
        except subprocess.TimeoutExpired:collector.kill();collector.wait()
        output.close();errors.close();adb('rmdir '+remote_root)
        (target/'summary.json').write_text(json.dumps(dict(cells=cells,requests=len(requests),completed=sum(row['valid'] for row in requests),bytes=sum(int(row['metrics'].get('BODY_BYTES','0')) for row in requests),final_topology=topology()),indent=2))


if __name__=='__main__':main()
