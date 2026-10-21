"""Final source gates plus explicit baseline reproduction of legacy assertions."""

import json
import os
import subprocess
import time
from prepare import ROOT, WORK, TOOLS, environment, digest


def main():
    os.umask(0o077)
    fixture = WORK / ('final-fixtures-' + str(time.time_ns()))
    python = ROOT/'state-client-build/field65-export16/telemost-admission-ownership-1/build/venv/bin/python'
    subprocess.run([python,'-m','pilot.telemost_family_fixture','--out',fixture],cwd=ROOT,check=True,timeout=30)
    results=[]
    cases=[('baseline-bootstrap',WORK/'compatibility/old-client',['-run','^TestProductIdentityOverBootstrapCarrier$'],['./bootstrap'],False),
           ('android-final',WORK/'android-source/carrier',['-skip','^TestProductIdentityOverBootstrapCarrier$|^TestLease'],['./localwrite','./reliablestream','./familysession','./tcpforward','./telemost','./wholedevice','./restrictedowner','./sessiondiag','./sessiontrace','./bootstrap','./roombroker','./cmd/bootstrap-broker'],False),
           ('gateway-final',WORK/'gateway-source',['-skip','^TestProductIdentityOverBootstrapCarrier$|^TestLease'],['./localwrite','./reliablestream','./familysession','./tcpforward','./telemost','./wholedevice','./sessiondiag','./sessiontrace','./bootstrap','./roombroker','./cmd/bootstrap-broker'],True)]
    for name,source,options,packages,tags in cases:
        env=environment();env.update(FC_FAMILY_TEST_FIXTURES=str(fixture),FC_EXPECT_SEED_OBSERVABILITY='1',FC_QUEUE_COMPLETION_EXPECTED='0')
        log=WORK/(name+'-'+str(time.time_ns())+'.jsonl')
        with log.open('x') as output:
            result=subprocess.run([TOOLS/'go/bin/go','test','-p=1','-race','-json','-count=1','-timeout=180s',*(['-tags=fc_perf_diagnostic'] if tags else []),*options,*packages],cwd=source,env=env,stdout=output,stderr=subprocess.STDOUT,timeout=600)
        rows=[json.loads(line) for line in log.read_text().splitlines() if line.startswith('{')]
        failed=[row.get('Test',row['Package']) for row in rows if row.get('Action')=='fail']
        results.append(dict(name=name,exit=result.returncode,log=log.name,sha256=digest(log),failed=failed,pass_count=sum(row.get('Action')=='pass' and bool(row.get('Test')) for row in rows),skip_count=sum(row.get('Action')=='skip' for row in rows)))
        (WORK/'final-checks.json').write_text(json.dumps(results,indent=2));print(json.dumps(results[-1]),flush=True)
    if any(record['exit'] for record in results[1:]):raise SystemExit(1)


if __name__=='__main__':main()
