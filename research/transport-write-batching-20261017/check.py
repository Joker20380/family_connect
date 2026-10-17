import ast
import json
import os
from pathlib import Path
import signal
import sys
import time

root=Path(__file__).resolve().parent
state=root.parent
tools=state/'field65-export16/diag-source-freeze-1/resume-tools'
output=root/sys.argv[1]
output.mkdir(mode=0o700)
sensor=next(zone/'temp' for zone in Path('/sys/class/thermal').glob('thermal_zone*') if (zone/'type').read_text().strip()=='x86_pkg_temp')
environment=os.environ|dict(GOMAXPROCS='1',GOTOOLCHAIN='local',GOWORK='off',GOPROXY='off',GOSUMDB='off',GOFLAGS='-mod=readonly',GOCACHE=str(tools/'go-cache'),GOPATH=str(tools/'gopath'),GOMODCACHE=str(tools/'gopath/pkg/mod'))
for key in ('FC_FAMILY_TEST_FIXTURES','YANDEX_TELEMOST_OAUTH_TOKEN','FC_TELEMOST_ROOM'):environment.pop(key,None)
receipts=[]
batch_start=time.monotonic()
import hashlib
import subprocess
retained=state/'reliable-full-stack-1/run.py'
definitions=[node for node in ast.parse(retained.read_text()).body if isinstance(node,ast.FunctionDef) and node.name in ('temperature','interrupt','run')]
exec(compile(ast.Module(body=definitions,type_ignores=[]),str(retained),'exec'))
signal.signal(signal.SIGTERM,interrupt)
signal.signal(signal.SIGINT,interrupt)
source=state/'browser-admission-fix-1/source' if sys.argv[2]=='baseline' else root/'source'
overlay=output/'overlay.json'
overlay.write_text(json.dumps({'Replace':{str(source/'carrier/familysession/batch_envelope_test.go'):str(root/'fixtures/batch_envelope_test.go')}}))
go=str(tools/'go/bin/go')
run('envelope',[go,'test','-p=1','-overlay='+str(overlay),'./familysession','-run','^TestQueuedMessageEnvelope$','-count=3','-timeout=65s','-v'],source/'carrier')
if sys.argv[2]!='baseline':
 for mode in ('normal','race'):
  run('regression-'+mode,[go,'test','-p=1',*(['-race'] if mode=='race' else []),'./familysession','./tcpforward','-run','^Test(Batch|Mux|Admission|Canonical|ExpiredLease|TLSRecordReplay|Queued)','-count=1','-timeout=100s','-failfast','-v'],source/'carrier')
