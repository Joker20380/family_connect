import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--tools', type=Path, required=True)
parser.add_argument('--out', type=Path, required=True)
parser.add_argument('--before', action='store_true')
args = parser.parse_args()
args.out.mkdir(parents=True, exist_ok=False)
(args.out / 'tmp').mkdir()
env = dict(os.environ, TMPDIR=str(args.out / 'tmp'), GOTOOLCHAIN='local', GOPROXY='off', GOSUMDB='off', GOCACHE=str(args.out.parent / 'cache'), GOPATH=str(args.tools / 'gopath'), GOMAXPROCS='4')
for key in ('FC_FAMILY_TEST_FIXTURES', 'YANDEX_TELEMOST_OAUTH_TOKEN', 'FC_TELEMOST_ROOM', 'GOFLAGS'):
    env.pop(key, None)
runs = []
for name, count in (('normal', 1), ('race', 3)):
    command = [str(args.tools / 'go/bin/go'), 'test', '-v', '-count=' + str(count), '-timeout=180s']
    if name == 'race':
        command.append('-race')
    command += ['-run=^TestReceiveStall', './telemost'] if args.before else ['./reliablestream', './telemost', './familysession', './tcpforward', './sessiontrace', './restrictedowner', './startupdiag']
    log = args.out / (name + '.log')
    with log.open('wb') as output:
        try:
            code = subprocess.run(command, cwd=args.source, env=env, stdout=output, stderr=subprocess.STDOUT, timeout=360).returncode
        except subprocess.TimeoutExpired:
            code = 'TIMEOUT'
    runs.append(dict(mode=name, count=count, exit=code, log=log.name, sha256=hashlib.sha256(log.read_bytes()).hexdigest(), command=command))
    (args.out / 'runs.json').write_text(json.dumps(runs, indent=2) + '\n')
    print(name, code, flush=True)
raise SystemExit(0 if all(run['exit'] == 0 for run in runs) else 1)
