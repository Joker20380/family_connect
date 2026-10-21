"""Run the saved receiver sequence on an isolated exact-native source copy."""

import json
import os
import shutil
import subprocess

from preserve import ROOT, WORK, PARENT


def main():
    os.umask(0o077)
    target = WORK / 'reproduction/carrier'
    shutil.copytree(PARENT / 'android-source/carrier', target)
    shutil.copyfile(ROOT / 'tests/fixtures/mesh_receive_path/saved_head_test.go', target / 'telemost/saved_head_test.go')
    tools = ROOT / 'state-client-build/field65-export16/diag-source-freeze-1/resume-tools'
    environment = {key:value for key,value in os.environ.items() if not key.startswith(('GO', 'CGO', 'FC_', 'YANDEX_'))}
    environment.update(GOTOOLCHAIN='local', GOWORK='off', GOPROXY='off', GOSUMDB='off', GOMAXPROCS='2',
                       GOPATH=str(tools / 'gopath'), GOCACHE=str(WORK / 'go-cache'))
    with (WORK / 'saved-receiver-reproduction.jsonl').open('xb') as output:
        result = subprocess.run([tools / 'go/bin/go', 'test', '-race', '-json', '-count=1', '-timeout', '30s',
                                 '-run', '^TestSaved', './telemost'], cwd=target, env=environment,
                                stdout=output, stderr=subprocess.STDOUT, timeout=240)
    print(json.dumps(dict(exit=result.returncode, production_modified=False)))
    raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()
