"""Build a pinned, local server-only variant; never install from this command."""

import hashlib
import json
import os
import subprocess
import sys

from prepare import ROOT, WORK, digest


def main():
    os.umask(0o077)
    variant=sys.argv[1];assert variant in ('observation','candidate-observed','candidate')
    label=sys.argv[2] if len(sys.argv)>2 else variant
    source=WORK/(variant+'-source')/'carrier'
    for name in ('main.go','seed_recovery.go','seed_recovery_test.go'):
        relative='cmd/bootstrap-broker/'+name
        assert digest(source/relative)==digest(WORK/'baseline-source/carrier'/relative)
    files={str(path.relative_to(source)):digest(path) for path in source.rglob('*') if path.is_file()}
    tools=ROOT/'state-client-build/field65-export16/diag-source-freeze-1/resume-tools'
    environment={key:value for key,value in os.environ.items() if not key.startswith(('GO','CGO','FC_','YANDEX_'))}
    environment.update(GOTOOLCHAIN='local',GOWORK='off',GOPROXY='off',GOSUMDB='off',GOMAXPROCS='2',GOPATH=str(tools/'gopath'),GOCACHE=str(WORK/'go-cache'),GOOS='linux',GOARCH='amd64',GOAMD64='v1',CGO_ENABLED='1')
    tags=[] if variant=='candidate' else ['-tags=fc_perf_diagnostic']
    binary=WORK/('gateway-'+label);assert not binary.exists()
    with (WORK/'tests'/(label+'-build.log')).open('xb') as log:
        result=subprocess.run([tools/'go/bin/go','build','-p=1','-trimpath','-buildvcs=false',*tags,'-o',binary,'./cmd/bootstrap-broker'],cwd=source,env=environment,stdout=log,stderr=subprocess.STDOUT,timeout=300)
    assert result.returncode==0
    receipt=dict(sha256=digest(binary),inventory=hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest(),files=files,tags=tags,bootstrap1011_preserved=True)
    with (WORK/(label+'-build.json')).open('x') as output:json.dump(receipt,output,indent=2)
    print(json.dumps({key:receipt[key] for key in ('sha256','inventory','bootstrap1011_preserved')}))


if __name__=='__main__':main()
