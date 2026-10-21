"""Run bounded synthetic carrier tests on a copy of exact current sources."""

import json
import os
import shutil
import subprocess
import sys

from prepare import ROOT, WORK, digest


def main():
    os.umask(0o077)
    variant=sys.argv[1]
    assert variant in ('baseline','candidate')
    label=variant+(('-'+sys.argv[2]) if len(sys.argv)>2 else '')
    source=WORK/(variant+'-source')
    destination=WORK/(label+'-test-source')
    shutil.copytree(source,destination)
    shutil.copyfile(ROOT/'tests/fixtures/queue_retry/queue_retry_test.go',destination/'carrier/telemost/queue_retry_test.go')
    packages=['./telemost']
    if variant=='candidate':
        shutil.copyfile(ROOT/'tests/fixtures/queue_retry/local_deadline_test.go',destination/'carrier/reliablestream/local_deadline_test.go')
        packages.append('./reliablestream')
    tools=ROOT/'state-client-build/field65-export16/diag-source-freeze-1/resume-tools'
    environment={key:value for key,value in os.environ.items() if not key.startswith(('GO','CGO','FC_','YANDEX_'))}
    environment.update(GOTOOLCHAIN='local',GOWORK='off',GOPROXY='off',GOSUMDB='off',GOMAXPROCS='2',
                       GOPATH=str(tools/'gopath'),GOCACHE=str(WORK/'go-cache'))
    environment['FC_QUEUE_COMPLETION_EXPECTED']='1' if variant=='candidate' else '0'
    with (WORK/'tests'/(label+'-queue.jsonl')).open('xb') as log:
        result=subprocess.run([tools/'go/bin/go','test','-race','-json','-count=1','-timeout','30s','-run','^Test(QueueRetry|LocalCompletion)',*packages],
                              cwd=destination/'carrier',env=environment,stdout=log,stderr=subprocess.STDOUT,timeout=180)
    print(json.dumps(dict(variant=variant,exit=result.returncode)))
    raise SystemExit(result.returncode)


if __name__=='__main__':main()
