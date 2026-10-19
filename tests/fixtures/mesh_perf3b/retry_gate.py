import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


ROOT=Path(__file__).resolve().parents[3]
STATE=ROOT/'state-client-build/mesh-perf-3b'
OUT=STATE/'retry02'
os.umask(0o077)


def main():
    sys.path.insert(0,str(STATE/'api'))
    from control.friends.restricted import directory, timestamp_ns
    from control.friends.owner_handoff import ordered
    paths=[OUT/'ready-gate-v2-nl-production_directory_private.json',OUT/'canary-directory.json']
    values=[json.loads(path.read_bytes()) for path in paths]
    production,canary=values
    assert (STATE/'api/control/friends/owner_handoff.py').read_bytes()
    for path in paths:
        directory(path.read_bytes(),production['family'],production['seeds'][0]['gateway'],now=int(time.time()))
    assert not ordered(production,canary) and ordered(canary,production)
    assert canary['seeds']!=production['seeds']
    tools=ROOT/'state-client-build/field65-export16/diag-source-freeze-1/resume-tools'
    jars=[]
    for name in ('com.google.code.gson/gson/2.13.2','junit/junit/4.13.2','org.hamcrest/hamcrest-core/1.3'):
        jar,=(tools/'gradle-home/caches/modules-2/files-2.1'/name).glob('*/*.jar')
        jars.append(str(jar))
    classes=OUT/'gate-classes';classes.mkdir()
    classpath=os.pathsep.join([str(classes),str(STATE/'java-floors-final-classes'),*jars])
    commands=[[str(tools/'jdk/bin/javac'),'-classpath',classpath,'-d',str(classes),str(Path(__file__).with_name('ActualDirectoryGate.java'))],
              [str(tools/'jdk/bin/java'),'-classpath',classpath,'com.familyconnect.app.ActualDirectoryGate',str(STATE/'fixtures-v2/roundtrip.json'),str(paths[0]),str(paths[1])]]
    with (OUT/'actual-directory-gate.log').open('x') as handle:
        for command in commands:
            subprocess.run(command,stdout=handle,stderr=subprocess.STDOUT,timeout=30,check=True)
    expiry=timestamp_ns(canary['expires_at'])/1e9
    result=dict(result='RETURN_GATE_REJECTED',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        actual_directories_python_schema_family_gateway_time='PASS',actual_directory_java_floor_rejection='PASS',
        java_native_callback='STUB: only exact cache ordering is exercised; no device import',
        production_sha256=hashlib.sha256(paths[0].read_bytes()).hexdigest(),canary_sha256=hashlib.sha256(paths[1].read_bytes()).hexdigest(),
        production_issued_at=production['issued_at'],canary_issued_at=canary['issued_at'],canary_expires_at=canary['expires_at'],
        latest_arm_utc=datetime.datetime.fromtimestamp(int(expiry)-600-1800,datetime.timezone.utc).isoformat(),
        gates=dict(minimum_time_to_operation_deadline_seconds=1800,directory_margin_after_operation_deadline_seconds=600),
        owner_imports_performed=0,real_newer_return_available=False,
        log_sha256=hashlib.sha256((OUT/'actual-directory-gate.log').read_bytes()).hexdigest())
    with (OUT/'actual-directory-gate.json').open('x') as handle:json.dump(result,handle,indent=2)
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
