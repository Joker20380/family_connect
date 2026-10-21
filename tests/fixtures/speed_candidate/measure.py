"""Bounded owner phase, reusing the existing Android HTTP/1.1 TUN request meter.

Requires independently collected current endpoint receipts; never changes profiles.
"""

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
from prepare import ROOT, WORK, APK_SHA, GATEWAY_SHA, digest


def main():
    os.umask(0o077)
    phase, receipt_path = sys.argv[1:]
    sequence = {'original96':'P0','P0a':'P0','P1a':'P1','P2a':'P2','P2b':'P2','P1b':'P1','P0b':'P0'}
    assert phase in sequence
    profile = sequence[phase]
    gate = json.loads(Path(receipt_path).read_text())
    assert gate['phase'] == phase and gate['owner_verified'] and gate['gateway_verified']
    assert 0 <= time.time()-gate['observed_epoch'] < 90, 'FRESH_ENDPOINT_RECEIPTS_REQUIRED'
    legacy = phase == 'original96'
    if legacy:
        assert gate['limits_basis'] == 'EXACT_96_734_FIXED_DEFAULTS_NOT_LIVE_OPEN_EXPORT'
        assert gate['readback']['phone']['apk_sha256'] == APK_SHA
        assert gate['readback']['gateway']['sha256'] == GATEWAY_SHA
        assert gate['readback']['gateway']['operator'] == dict(**{'rtp-pacing':'OFF','mux-profile':'LEGACY64','mux-counters':'OFF','speed-profile':None})
    for endpoint in (() if legacy else ('android_diagnostic','gateway_diagnostic')):
        record = gate[endpoint]
        assert record['speed_profile'] == profile
        assert record['session_tag'] == gate['session_tag']
        expected = dict(local_send=8,local_receive=16,peer_receive=16,effective_send=8,local_write_completion=False) if profile=='P0' else dict(local_send=32,local_receive=32,peer_receive=32,effective_send=32,local_write_completion=profile=='P2')
        assert record['reliable_limits'] == expected
        assert record['mux_profile'] == ('LEGACY64' if profile=='P0' else 'CREDIT128')
        assert record['mux_window'] == (65536 if profile=='P0' else 131072)
    original=ROOT/'tests/fixtures/mesh_throughput_trace/measure.py'
    assert digest(original)=='17e76fb9f3d8c46b5e7e4b5c55fa0f8098b59aef63e0e66c94cbce81b2c2a5ef'
    tree=ast.parse(original.read_text())
    helpers=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in ('adb','topology')]
    request=next(node for node in ast.walk(tree) if isinstance(node,ast.FunctionDef) and node.name=='request')
    namespace=dict(globals());exec(compile(ast.Module(body=helpers,type_ignores=[]),str(original),'exec'),namespace)
    adb,topology=namespace['adb'],namespace['topology']
    initial=topology();assert initial==gate['topology']
    if not legacy:
        reference=json.loads((WORK/'phase-original96/scope.json').read_text())['topology']
        assert all(initial[key]==reference[key] for key in ('underlay','transports')), 'UNDERLYING_NETWORK_CHANGED_NO_PAIRED_COMPARISON'
    apk=adb('pm path com.familyconnect.app.friends').stdout.strip().removeprefix('package:')
    expected_apk = APK_SHA if legacy else json.loads((WORK/'delivery/signing-receipt.json').read_text())['signed']['sha256']
    assert adb('sha256sum '+shlex.quote(apk)).stdout.split()[0]==expected_apk==gate['phone_apk_sha256']
    build=dict(sha256=GATEWAY_SHA) if legacy else json.loads((WORK/'gateway-build.json').read_text())
    assert gate['gateway_sha256']==build['sha256']
    out=WORK/('phase-'+phase);out.mkdir(mode=0o700)
    (out/'scope.json').write_text(json.dumps(gate,indent=2))
    remote='''
import hashlib,json,subprocess
from pathlib import Path
state=dict(line.split('=',1) for line in subprocess.check_output(['systemctl','show','family-connect-restricted-bootstrap.service','-p','MainPID,InvocationID,ActiveState'],text=True).splitlines())
assert state['ActiveState']=='active'
assert hashlib.sha256((Path('/proc')/state['MainPID']/'exe').read_bytes()).hexdigest()==EXPECTED
print(json.dumps(state))
'''.replace('EXPECTED',repr(build['sha256']))
    gateway=json.loads(subprocess.check_output(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','root@186.246.45.246','python3 -B -'],input=remote,text=True,timeout=25))
    assert gateway['MainPID']==gate['gateway_pid'] and gateway['InvocationID']==gate['gateway_invocation']
    reserved=WORK/('traffic-'+phase+'-reservation.json');assert not reserved.exists()
    amount=(8<<20)+12*1024
    assert sum(json.loads(path.read_text())['intended_bytes'] for path in WORK.glob('traffic-*-reservation.json'))+amount<=64<<20
    reserved.write_text(json.dumps(dict(intended_bytes=amount,no_retries=True,phase=phase,profile=profile)))
    collector_source=ROOT/'tests/fixtures/queue_retry/measure.py'
    assert digest(collector_source)=='b3558a77d7772e2035ef5c7bd66fdc3a5eebb8b7b79173b6903c16ca9c36e8f5'
    expression=next(node for node in ast.walk(ast.parse(collector_source.read_text())) if isinstance(node,ast.Assign) and any(isinstance(name,ast.Name) and name.id=='collector' for name in node.targets))
    namespace.update(gateway=gateway,start=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC'))
    exec(compile(ast.Module(body=[expression],type_ignores=[]),str(collector_source),'exec'),namespace)
    capture=(out/'capture-private.jsonl').open('x');errors=(out/'capture.stderr').open('x')
    collector=subprocess.Popen(['ssh','-o','BatchMode=yes','root@186.246.45.246','python3 -B -c '+shlex.quote(namespace['collector'])],stdin=subprocess.PIPE,stdout=capture,stderr=errors)
    remote_root='/data/local/tmp/fc-speed-'+phase+'-20261021'
    stop=threading.Event();requests=[];cells=[]
    namespace.update(out=out,remote_root=remote_root,stop=stop,lock=threading.Lock(),requests=requests,
        fields=('http_code','http_version','ssl_verify_result','remote_ip','local_port','num_connects','size_download','time_namelookup','time_connect','time_appconnect','time_starttransfer','time_total'))
    exec(compile(ast.Module(body=[request],type_ignores=[]),str(original),'exec'),namespace)
    def check():
        assert topology()==initial and not stop.is_set()
        assert 'network{'+gate['vpn_network']+'}' in adb('dumpsys connectivity').stdout, 'TUN_SESSION_CHANGED_STOP'
    def small(prefix):
        for index in range(6):
            check();namespace['request'](prefix+'-'+str(index),1024);time.sleep(.1)
    failure = None
    try:
        adb('umask 077; mkdir '+remote_root).check_returncode()
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
            (out/'cells.json').write_text(json.dumps(cells,indent=2));check()
    except BaseException as error:
        failure=type(error).__name__+': '+str(error)
        raise
    finally:
        collector.stdin.close()
        try:collector.wait(timeout=15)
        except subprocess.TimeoutExpired:collector.kill();collector.wait()
        capture.close();errors.close();adb('rmdir '+remote_root)
        (out/'summary.json').write_text(json.dumps(dict(profile=profile,cells=cells,attempts=len(requests),passed=sum(row['valid'] for row in requests),phase_exception=failure,late_errors_require_final_export=True,clean_acceptance=False),indent=2))


if __name__=='__main__':main()
