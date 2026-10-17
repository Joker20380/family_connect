import ast
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
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
retained=state/'reliable-full-stack-1/run.py'
definitions=[node for node in ast.parse(retained.read_text()).body if isinstance(node,ast.FunctionDef) and node.name in ('temperature','interrupt','run')]
exec(compile(ast.Module(body=definitions,type_ignores=[]),str(retained),'exec'))
signal.signal(signal.SIGTERM,interrupt)
signal.signal(signal.SIGINT,interrupt)
source=state/'browser-admission-fix-1/source' if sys.argv[2]=='baseline' else root/('gateway-source' if sys.argv[2]=='gateway' else 'source')
go=str(tools/'go/bin/go')
if sys.argv[3]=='loss':
 for mode in ('normal','race'):
  run('actual-mux-loss-'+mode,[go,'test','-p=1',*(['-race'] if mode=='race' else []),'./tcpforward','-run','^TestBatchAuthenticatedLossyMux$','-count=2','-timeout=60s','-v'],source/'carrier')
elif sys.argv[3]=='heavy-long':
 original=(source/'carrier/tcpforward/mux_test.go').read_text()
 assert original.count('15*time.Second')==1 and original.count('15 * time.Second')==1
 extended=output/'mux_test.go'
 extended.write_text(original.replace('15*time.Second','60*time.Second').replace('15 * time.Second','60 * time.Second'))
 overlay=output/'overlay.json'
 overlay.write_text(json.dumps({'Replace':{str(source/'carrier/tcpforward/mux_test.go'):str(extended)}}))
 run('inherited-race-32-bounded-overlay',[go,'test','-p=1','-race','-overlay='+str(overlay),'./tcpforward','-run','^TestMuxConcurrentExactSegmentation$/^32$','-count=1','-timeout=80s','-v'],source/'carrier')
elif sys.argv[3]=='heavy':
 run('inherited-race-32',[go,'test','-p=1','-race','./tcpforward','-run','^TestMuxConcurrentExactSegmentation$/^32$','-count=1','-timeout=40s','-v'],source/'carrier')
else:
 overlay=output/'overlay.json'
 overlay.write_text(json.dumps({'Replace':{str(source/'carrier/tcpforward/mux_latency_test.go'):str(root/'fixtures/mux_latency_test.go')}}))
 run('tcp-envelope',[go,'test','-p=1','-overlay='+str(overlay),'./tcpforward','-run','^Test(MuxLatencyEnvelope|BrowserSlotsReleaseEnvelope)$','-count=3','-timeout=100s','-v'],source/'carrier')
 if sys.argv[2]!='baseline':
  for mode in ('normal','race'):
   run('changed-scope-'+mode,[go,'test','-p=1',*(['-race'] if mode=='race' else []),'-overlay='+str(overlay),'./familysession','./tcpforward','-run','^Test(Batch|BrowserSlots|MuxLatency|Admission|Authenticated|AuthenticationRequired|EndSiteTLS|Canonical|ExpiredLease|TLSRecordReplay)','-count=1','-timeout=100s','-v'],source/'carrier')
