"""Validate the negotiated profile and affected integration without live traffic."""

import json
import subprocess
import sys

from prepare import WORK, TOOLS, environment


def main():
    mode=sys.argv[1];assert mode in ('suite','delta','observed')
    options=['-tags=fc_perf_diagnostic'] if mode=='observed' else ([] if mode=='suite' else ['-run','TestMuxALPN|TestMuxProfile|TestMux128|TestMuxOperator|TestCredit128|TestMuxRevoked'])
    path=WORK/(mode+'-'+str(len(list(WORK.glob(mode+'-*.jsonl')))+1)+'.jsonl')
    env=environment();env['FC_EXPECT_SEED_OBSERVABILITY']='1'
    with path.open('x') as output:
        result=subprocess.run([TOOLS/'go/bin/go','test','-p=1','-race','-json','-count=1','-timeout=240s',*options,
                               './familysession','./tcpforward','./roombroker','./reliablestream','./sessiondiag','./sessiontrace','./telemost','./cmd/bootstrap-broker'],
                              cwd=WORK/('gateway-source/carrier' if mode=='observed' else 'carrier'),env=env,stdout=output,stderr=subprocess.STDOUT)
    print(json.dumps(dict(exit=result.returncode,path=str(path))))
    raise SystemExit(result.returncode)


if __name__=='__main__':main()
