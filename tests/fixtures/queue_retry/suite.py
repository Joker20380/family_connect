"""Affected offline race regressions, preserving each failed run."""

import json
import os
import subprocess
import sys

from prepare import ROOT, WORK


def main():
    source=sys.argv[1];label=sys.argv[2]
    assert source in ('candidate-source','observation-source','candidate-observed-source')
    tools=ROOT/'state-client-build/field65-export16/diag-source-freeze-1/resume-tools'
    environment={key:value for key,value in os.environ.items() if not key.startswith(('GO','CGO','FC_','YANDEX_'))}
    environment.update(GOTOOLCHAIN='local',GOWORK='off',GOPROXY='off',GOSUMDB='off',GOMAXPROCS='2',GOPATH=str(tools/'gopath'),GOCACHE=str(WORK/'go-cache'))
    environment['FC_EXPECT_SEED_OBSERVABILITY']='1'
    packages=['./reliablestream','./telemost','./familysession','./tcpforward','./roombroker','./bootstrap','./cmd/bootstrap-broker']
    if source!='observation-source':packages.insert(0,'./localwrite')
    if len(sys.argv)>3:
        assert sys.argv[3] in ('seed-only','local-only')
        packages=['./cmd/bootstrap-broker'] if sys.argv[3]=='seed-only' else ['./localwrite','./reliablestream']
    tags=[] if source=='candidate-source' else ['-tags=fc_perf_diagnostic']
    with (WORK/'tests'/(label+'.jsonl')).open('xb') as log:
        result=subprocess.run([tools/'go/bin/go','test','-race','-json','-count=1','-timeout','180s',*tags,*packages],cwd=WORK/source/'carrier',env=environment,stdout=log,stderr=subprocess.STDOUT,timeout=420)
    print(json.dumps(dict(source=source,exit=result.returncode)))
    raise SystemExit(result.returncode)


if __name__=='__main__':main()
