import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser()
for name in ('work', 'tools'):
    parser.add_argument('--'+name, type=Path, required=True)
args = parser.parse_args()
env = dict(os.environ, GOTOOLCHAIN='local', GOPROXY='off', GOSUMDB='off',
           GOCACHE=str(args.work/'cache'), GOPATH=str(args.tools/'gopath'))
for name in ('FC_FAMILY_TEST_FIXTURES', 'YANDEX_TELEMOST_OAUTH_TOKEN', 'FC_TELEMOST_ROOM', 'GOFLAGS'):
    env.pop(name, None)
env['CORRELATION_RECEIPT'] = str(args.work/'deadline-native.json')
runs = []
for mode, count in (('normal', 1), ('race', 3)):
    for variant, packages in (('client', ['./bootstrap', './startupdiag']), ('gateway', ['./cmd/bootstrap-broker'])):
        command = [str(args.tools/'go/bin/go'), 'test', '-tags=seedacceptance', '-v', '-count='+str(count), '-timeout=90s']
        if mode == 'race':
            command.append('-race')
        command += ['-run=^TestCorrelation', *packages]
        log = args.work/(variant+'-'+mode+'.log')
        with log.open('wb') as output:
            status = subprocess.run(command, cwd=args.work/variant, env=env, stdout=output, stderr=subprocess.STDOUT, timeout=300).returncode
        runs.append(dict(mode=mode, variant=variant, count=count, command=command, exit=status,
                         log=log.name, sha256=hashlib.sha256(log.read_bytes()).hexdigest()))
        (args.work/'runs.json').write_text(json.dumps(runs, indent=2)+'\n')
        print(variant, mode, status, flush=True)
        if status != 0:
            raise SystemExit('Failure retained; no retry-until-pass')
