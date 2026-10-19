import json
import os
from pathlib import Path
import subprocess


os.umask(0o077)
CODE = r'''
import ast,hashlib,json,shlex,subprocess
from pathlib import Path
raw=subprocess.check_output(['systemctl','show','family-connect-credential-renewal.service','--property=ExecStart','--value'],text=True,timeout=10)
arguments=shlex.split(raw.split('argv[]=',1)[1].split(' ;',1)[0])
script,=[Path(arg) for arg in arguments if arg.endswith('runtime_controller.py')]
source=script.with_name('credential_renewal.py')
assignments={}
for node in ast.parse(source.read_bytes()).body:
    if isinstance(node,ast.Assign) and any(isinstance(target,ast.Name) and target.id in ('THRESHOLD','VALIDITY') for target in node.targets):
        assignments[ast.unparse(node.targets[0])]=ast.unparse(node.value)
units=subprocess.check_output(['systemctl','list-unit-files','--no-legend','family-connect-*'],text=True,timeout=10)
sync_units=[line.split()[0] for line in units.splitlines() if 'directory' in line and line.split()[0].endswith('.service')]
print(json.dumps(dict(renewal_source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),policy=assignments,directory_units=sync_units)))
'''
reply=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','root@185.251.89.19',"python3 - <<'PY'\n"+CODE+'\nPY'],capture_output=True,text=True,timeout=40)
out=Path(__file__).resolve().parents[3]/'state-client-build/mesh-perf-3b/retry02'
(out/'renewal-policy-v2.stderr').write_text(reply.stderr)
assert reply.returncode==0,'READ_ONLY_POLICY_FAILED'
value=json.loads(reply.stdout)
with (out/'renewal-policy-v2.json').open('x') as handle:json.dump(value,handle,indent=2)
print(json.dumps(value,indent=2))
