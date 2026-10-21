"""Build paired observation only, retaining current b9 bootstrap1011 exactly."""

import hashlib
import json
import os
import subprocess

from preserve import ROOT, WORK, PARENT, digest


def main():
    os.umask(0o077)
    source=WORK/'gateway-source/carrier'
    tested=WORK/'validation/carrier'
    files={str(path.relative_to(source)):digest(path) for path in source.rglob('*') if path.is_file()}
    assert all(digest(tested/name)==expected for name,expected in files.items())
    for mode in ('default','observation'):
        rows=[json.loads(line) for line in (WORK/'validation/results'/(mode+'.jsonl')).read_text().splitlines() if line.startswith('{')]
        assert not any(row['Action']=='fail' for row in rows)
        assert sum(row['Action']=='pass' and not row.get('Test') for row in rows)==7
    for name in ('main.go','seed_recovery.go','seed_recovery_test.go'):
        relative='cmd/bootstrap-broker/'+name
        assert digest(source/relative)==digest(PARENT/'gateway-source/carrier'/relative)
    tools=ROOT/'state-client-build/field65-export16/diag-source-freeze-1/resume-tools'
    environment={key:value for key,value in os.environ.items() if not key.startswith(('GO','CGO','FC_','YANDEX_'))}
    environment.update(GOTOOLCHAIN='local',GOWORK='off',GOPROXY='off',GOSUMDB='off',GOMAXPROCS='2',GOPATH=str(tools/'gopath'),
                       GOCACHE=str(WORK/'go-cache'),GOOS='linux',GOARCH='amd64',GOAMD64='v1',CGO_ENABLED='1')
    binary=WORK/'gateway-observation';assert not binary.exists()
    with (WORK/'gateway-build.log').open('xb') as log:
        result=subprocess.run([tools/'go/bin/go','build','-p=1','-trimpath','-buildvcs=false','-tags=fc_perf_diagnostic',
                               '-o',binary,'./cmd/bootstrap-broker'],cwd=source,env=environment,stdout=log,stderr=subprocess.STDOUT,timeout=300)
    assert result.returncode==0
    receipt=dict(sha256=digest(binary),inventory=hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
                 files=files,bootstrap1011_preserved=True,observation_only=True,deployed=False)
    (WORK/'gateway-build.json').write_text(json.dumps(receipt,indent=2))
    print(json.dumps({key:receipt[key] for key in ('sha256','inventory','bootstrap1011_preserved','deployed')}))


if __name__=='__main__':main()
