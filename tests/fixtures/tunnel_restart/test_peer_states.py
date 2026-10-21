"""Reproduce unchanged PC semantics in a separate test copy, never deployed."""

import json
import os
import shutil
import subprocess

from preserve import ROOT, WORK, digest


def main():
    os.umask(0o077)
    source = WORK / 'gateway-source/carrier'
    manifest = json.loads((WORK / 'gateway-build.json').read_text())
    assert all(digest(source / name) == value for name, value in manifest['files'].items())
    target = WORK / 'peer-state-regression-source'
    shutil.copytree(source, target)
    shutil.copyfile(ROOT / 'tests/fixtures/tunnel_restart/peer_state_test.go', target / 'telemost/restart_audit_test.go')
    tools = ROOT / 'state-client-build/field65-export16/diag-source-freeze-1/resume-tools'
    environment = {key: value for key, value in os.environ.items() if not key.startswith(('GO', 'CGO', 'FC_', 'YANDEX_'))}
    environment.update(GOTOOLCHAIN='local', GOWORK='off', GOPROXY='off', GOSUMDB='off', GOMAXPROCS='2',
                       GOPATH=str(tools / 'gopath'), GOCACHE=str(WORK / 'go-cache'))
    with (WORK / 'tests/peer-state-race.jsonl').open('xb') as log:
        result = subprocess.run([tools / 'go/bin/go', 'test', '-race', '-json', '-count=1', '-run', '^TestRestartAudit', './telemost'],
                                cwd=target, env=environment, stdout=log, stderr=subprocess.STDOUT, timeout=120)
    assert result.returncode == 0
    print('UNCHANGED_PEER_STATE_REPRODUCER_PASS_6_CASES')


if __name__ == '__main__':
    main()
