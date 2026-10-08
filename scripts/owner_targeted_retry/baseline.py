import datetime
import json
from pathlib import Path
import subprocess
import sys
import time

from contract import digest, validate, verify_pair


output = Path(__file__).resolve().parent
action = sys.argv[1]
assert action in ('baseline', 'control')
manifest = verify_pair(output / 'accepted-pair.json')
receipt = json.loads((output / 'fresh-preflight.json').read_text())
assert receipt['result'] == 'PASS'
assert 0 <= time.time() - datetime.datetime.fromisoformat(receipt['utc']).timestamp() < 900
assert datetime.datetime.fromisoformat(receipt['leaf_expiry']).timestamp() - time.time() > 1800
validate(receipt['observed'], manifest)
assert digest(output / 'baseline-helper-beta70.apk') == json.loads((output / 'helper-signature.json').read_text())['sha256']
target = {'baseline': 'OwnerPairBaselineTest#restrictedBaseline', 'control': 'OwnerControlSessionTest#statusOnlySession'}[action]
command = ['adb', '-s', '31ce63ba', 'shell', 'am', 'instrument', '-w', '-r', '-e',
           'class', 'com.familyconnect.app.' + target, '-e', 'owner_serial', '31ce63ba',
           '-e', 'expected_version', '70', 'com.familyconnect.app.friends.test/androidx.test.runner.AndroidJUnitRunner']
with (output / (action + '-attempt.json')).open('x') as stream:
    json.dump(dict(started=time.time(), command=command), stream)
response = subprocess.run(command, capture_output=True, text=True, timeout=480)
with (output / (action + '.log')).open('x') as stream:
    stream.write(response.stdout + '\n' + response.stderr)
entries = [json.loads(line.split('=', 1)[1]) for line in response.stdout.splitlines()
           if line.startswith('INSTRUMENTATION_STATUS: owner_evidence=')]
passed = response.returncode == 0 and 'OK (1 test)' in response.stdout and 'FAILURES!!!' not in response.stdout
with (output / (action + '.json')).open('x') as stream:
    json.dump(dict(result='PASS' if passed else 'FAIL', evidence=entries, exit=response.returncode), stream, indent=2)
assert passed, 'STOP: first live failure retained; no retry'
