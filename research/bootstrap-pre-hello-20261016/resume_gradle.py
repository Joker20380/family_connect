import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import zipfile

parser = argparse.ArgumentParser()
parser.add_argument('--out', type=Path, required=True)
parser.add_argument('--tools', type=Path, required=True)
args = parser.parse_args()
receipt = json.loads((args.out/'receipt.json').read_text())
assert receipt['exit'] != 0 and 'Operation not permitted' in (args.out/'gradle.log').read_text()
(args.out/'sandbox-receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
(args.out/'gradle.log').rename(args.out/'sandbox-gradle.log')
env = dict(os.environ, JAVA_HOME=str(args.tools/'jdk'), ANDROID_HOME=str(args.tools/'android'),
           ANDROID_SDK_ROOT=str(args.tools/'android'), GRADLE_USER_HOME=str(args.tools/'gradle-home'))
env['PATH'] = str(args.tools/'jdk/bin')+os.pathsep+env['PATH']
with (args.out/'gradle.log').open('wb') as output:
    receipt['exit'] = subprocess.run(receipt['command'], cwd=args.out/'source/clients/android', env=env,
                                     stdout=output, stderr=subprocess.STDOUT, timeout=900).returncode
receipt['log_sha256'] = hashlib.sha256((args.out/'gradle.log').read_bytes()).hexdigest()
for apk in (args.out/'android/app/outputs/apk').glob('**/*.apk'):
    with zipfile.ZipFile(apk) as bundle:
        embedded = hashlib.sha256(bundle.read('lib/arm64-v8a/libfc_restricted.so')).hexdigest()
        assert embedded == receipt['native_sha256']
        receipt['apk'] = dict(name=apk.name, sha256=hashlib.sha256(apk.read_bytes()).hexdigest(), embedded_native_sha256=embedded, size=apk.stat().st_size)
(args.out/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
print(json.dumps({key: receipt[key] for key in ('exit', 'source_delta_sha256', 'native_sha256', 'apk') if key in receipt}), flush=True)
raise SystemExit(receipt['exit'])
