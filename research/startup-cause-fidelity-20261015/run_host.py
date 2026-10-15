import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--review', type=Path, required=True)
parser.add_argument('--tools', type=Path, required=True)
parser.add_argument('--out', type=Path, required=True)
parser.add_argument('--before', action='store_true')
args = parser.parse_args()
root = Path(__file__).resolve().parent
args.out.mkdir(parents=True, exist_ok=False)
stage = args.out/'carrier'
shutil.copytree(args.source/'carrier', stage)
for name in ('admission_repro_test.go','tls_fixture_test.go'):
    shutil.copy2(args.review/'research/bootstrap-hello-admission-20261015'/name,stage/'bootstrap'/name)
shutil.copy2(root/'tests/fidelity_test.go',stage/'bootstrap/fidelity_test.go')
shutil.copy2(args.review/'research/chat-vpn-handoff-20261015/tests/handoff_test.go',stage/'bootstrap/handoff_test.go')
env = dict(os.environ,GOTOOLCHAIN='local',GOPROXY='off',GOSUMDB='off',GOCACHE=str(args.out/'cache'),GOPATH=str(args.tools/'gopath'))
for name in ('FC_FAMILY_TEST_FIXTURES','YANDEX_TELEMOST_OAUTH_TOKEN','FC_TELEMOST_ROOM','GOFLAGS'):
    env.pop(name,None)
runs=[]
for mode,count in ([('before',1)] if args.before else [('normal',1),('race',3)]):
    command=[str(args.tools/'go/bin/go'),'test','-tags=seedacceptance','-v',f'-count={count}','-timeout=180s']
    if mode=='race': command.append('-race')
    command += (['-run=^TestFidelityReceive$','./bootstrap'] if args.before else ['-run=TestFidelity|TestHandoff|TestReproAdmission|TestPrimary|TestControlled|TestIndependent|TestCause|TestFriendsStartup|TestDirectory|TestPreserve|TestChat|TestVPN|TestCancellation|TestOpening|TestSimultaneous|TestCompatibility','./startupdiag','./restrictedowner','./bootstrap'])
    log=args.out/f'{mode}.log'
    with log.open('wb') as output:
        code=subprocess.run(command,cwd=stage,env=env,stdout=output,stderr=subprocess.STDOUT,timeout=240).returncode
    runs.append({'mode':mode,'count':count,'exit':code,'command':command,'log':log.name,'sha256':hashlib.sha256(log.read_bytes()).hexdigest()})
    print(mode,code,flush=True)
(args.out/'runs.json').write_text(json.dumps(runs,indent=2)+'\n')
raise SystemExit(1 if any(run['exit'] != 0 for run in runs) else 0)
