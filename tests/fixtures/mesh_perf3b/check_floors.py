import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

root = Path(__file__).resolve().parents[3]
out = root / 'state-client-build/mesh-perf-3b'
tools = root / 'state-client-build/field65-export16/diag-source-freeze-1/resume-tools'
source = root / 'state-client-build/transport-write-batching-1/source/clients/android/app/src'
os.umask(0o077)
label = sys.argv[1] if len(sys.argv) > 1 else 'java-floors'
classes = out / (label + '-classes')
classes.mkdir()
jars = []
for library in ['com.google.code.gson/gson/2.13.2', 'junit/junit/4.13.2', 'org.hamcrest/hamcrest-core/1.3']:
    jar, = (tools / 'gradle-home/caches/modules-2/files-2.1' / library).glob('*/*.jar')
    jars.append(str(jar))
classpath = os.pathsep.join(jars + [str(root/'state-client-build/transport-write-batching-1/source/tests/vectors')])
names = ['RestrictedCache', 'ControlJson', 'ReadinessImportResult', 'OwnerPrewarmReceipt']
files = [source/'main/java/com/familyconnect/app'/(name+'.java') for name in names]
files += [source/'test/java/com/familyconnect/app/RestrictedCacheTest.java', root/'tests/fixtures/mesh_perf3b/FloorRoundtrip.java']
commands = [
    [str(tools/'jdk/bin/javac'), '-d', str(classes), '-classpath', classpath, *map(str, files)],
    [str(tools/'jdk/bin/java'), '-classpath', str(classes)+os.pathsep+classpath, 'org.junit.runner.JUnitCore', 'com.familyconnect.app.RestrictedCacheTest'],
    [str(tools/'jdk/bin/java'), '-classpath', str(classes)+os.pathsep+classpath, 'com.familyconnect.app.FloorRoundtrip', str(out/'fixtures-v2/roundtrip.json')],
]
started = time.time()
log = out / 'receipts' / (label + '.log')
records = []
with log.open('xb') as handle:
    for command in commands:
        result = subprocess.run(command, stdout=handle, stderr=subprocess.STDOUT, timeout=60)
        records.append(dict(executable=Path(command[0]).name, exit=result.returncode))
        if result.returncode:
            break
record = dict(seconds=time.time()-started, runs=records,
              sources={str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in files},
              log_sha256=hashlib.sha256(log.read_bytes()).hexdigest(),
              native_validation='separate validator required; Java validator stub only tests persistent floors')
with (out/'receipts'/(label+'.json')).open('x') as handle:json.dump(record, handle, indent=2)
print(json.dumps(dict(runs=records, seconds=record['seconds'])))
