import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

parser = argparse.ArgumentParser()
parser.add_argument('--go', required=True, type=Path)
parser.add_argument('--gopath', required=True, type=Path)
parser.add_argument('--work', required=True, type=Path)
args = parser.parse_args()
root = Path(__file__).resolve().parent
repo = root.parents[1]
args.work.mkdir(parents=True, exist_ok=False)
stage = args.work / 'carrier'
shutil.copytree(repo / 'research/supervisor-20261015/baseline/carrier', stage)
shutil.copytree(root / 'changed/carrier/restrictedowner', stage / 'restrictedowner')
for name in ('admission_repro_test.go', 'tls_fixture_test.go'):
    shutil.copy2(repo / 'research/bootstrap-hello-admission-20261015' / name, stage / 'bootstrap' / name)
shutil.copy2(root / 'tests/handoff_test.go', stage / 'bootstrap/handoff_test.go')
env = dict(os.environ, GOTOOLCHAIN='local', GOPROXY='off', GOSUMDB='off', GOCACHE=str(args.work/'go-cache'), GOPATH=str(args.gopath))
for key in ('FC_FAMILY_TEST_FIXTURES', 'YANDEX_TELEMOST_OAUTH_TOKEN', 'FC_TELEMOST_ROOM', 'GOFLAGS'):
    env.pop(key, None)
manifest = {'scope': 'LOCAL_SOURCE_TESTS_NOT_ANDROID_EXECUTION', 'repetitions': {'normal': 1, 'race': 3}, 'runs': [], 'go': subprocess.check_output([args.go, 'version'], text=True).strip()}
def run(command, log):
    started = time.monotonic()
    with (args.work/log).open('wb') as output:
        try:
            code = subprocess.run(command, cwd=stage, env=env, stdout=output, stderr=subprocess.STDOUT, timeout=300).returncode
        except subprocess.TimeoutExpired:
            code = 'TIMEOUT'
    row = {'command': list(map(str, command)), 'log': log, 'exit': code, 'elapsed_s': round(time.monotonic()-started, 3), 'sha256': hashlib.sha256((args.work/log).read_bytes()).hexdigest()}
    manifest['runs'].append(row)
    (args.work/'results.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps({'log': log, 'exit': code}), flush=True)
    if code != 0:
        raise SystemExit('Unexpected failure retained; no automatic retry')

for mode, count in (('normal', 1), ('race', 3)):
    for package, pattern in (('restrictedowner', '^Test'), ('bootstrap', '^Test(HandoffRealBroker|ReproAdmission)$'), ('wholedevice', '^Test(ProductionDeliveryRejectsBindingTrustExpiryBounds|CachedBootstrapCryptoDeadlinesAndRevocation|ProductionDeliveryToExistingFamilyMaterial)$'), ('familysession', '^Test(AdmissionFailures|ExpiredLeaseAndBounds)$')):
        binary = args.work / f'{package}-{mode}.test'
        build = [str(args.go), 'test', '-c', '-tags=seedacceptance', '-o', str(binary)]
        if mode == 'race':
            build.append('-race')
        run(build + ['./'+package], f'{package}-{mode}-build.log')
        manifest.setdefault('binaries', {})[binary.name] = hashlib.sha256(binary.read_bytes()).hexdigest()
        run([binary, '-test.v', '-test.run='+pattern, '-test.count='+str(count), '-test.timeout=90s'], f'{package}-{mode}.log')
manifest['result'] = 'PASS'
(args.work/'results.json').write_text(json.dumps(manifest, indent=2)+'\n')
