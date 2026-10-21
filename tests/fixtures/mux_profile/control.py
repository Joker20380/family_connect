"""One phone-side64KiB control with counters off; no session-attribution claim."""

import ast
import concurrent.futures
import datetime
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import threading
import time
from prepare import ROOT, WORK, digest

os.umask(0o077)
original=ROOT/'tests/fixtures/mesh_throughput_trace/measure.py'
assert digest(original)=='17e76fb9f3d8c46b5e7e4b5c55fa0f8098b59aef63e0e66c94cbce81b2c2a5ef'
tree=ast.parse(original.read_text())
functions=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in ('adb','topology')]
request=next(node for node in ast.walk(tree) if isinstance(node,ast.FunctionDef) and node.name=='request')
namespace=dict(globals());exec(compile(ast.Module(body=functions+[request],type_ignores=[]),str(original),'exec'),namespace)
out=WORK/'off-control';out.mkdir(mode=0o700,exist_ok=False)
root='/data/local/tmp/fc-mux-profile-off-control'
namespace['adb']('umask 077; mkdir '+root).check_returncode()
namespace.update(out=out,remote_root=root,stop=threading.Event(),lock=threading.Lock(),requests=[],fields=('http_code','http_version','ssl_verify_result','remote_ip','local_port','num_connects','size_download','time_namelookup','time_connect','time_appconnect','time_starttransfer','time_total'))
before=namespace['topology']()
assert sum(json.loads(path.read_text())['intended_bytes'] for path in WORK.glob('traffic-*-reservation.json'))+65536<=64*1024*1024
(WORK/'traffic-offcontrol-reservation.json').write_text(json.dumps(dict(intended_bytes=65536,no_retries=True)))
try:
    result=namespace['request']('off-control',65536)
    after=namespace['topology']()
    (out/'summary.json').write_text(json.dumps(dict(valid=result['valid'],bytes=int(result['metrics']['BODY_BYTES']),seconds=float(result['metrics']['time_total']),before=before,after=after,counters_off=True,session_attribution=False),indent=2))
finally:namespace['adb']('rmdir '+root)
