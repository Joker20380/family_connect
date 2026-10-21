"""Build only the three-file seed containment delta on the pinned gateway."""

import hashlib
import json
import os
from pathlib import Path
import subprocess

from preserve import ROOT, WORK, digest


def main():
    os.umask(0o077)
    source = WORK / 'gateway-source/carrier'
    parent = json.loads((ROOT / 'state-client-build/transport-write-batching-1/gateway-source.json').read_text())
    changed = {'cmd/bootstrap-broker/main.go', 'cmd/bootstrap-broker/seed_recovery.go', 'cmd/bootstrap-broker/seed_recovery_test.go'}
    files = {str(path.relative_to(source)): digest(path) for path in source.rglob('*') if path.is_file()}
    assert set(files) - set(parent['files']) == changed - {'cmd/bootstrap-broker/main.go'}
    assert all(files[name] == value for name, value in parent['files'].items() if name not in changed)
    for name in ('gateway-race.jsonl', 'gateway-race-rerun.jsonl'):
        records = []
        for line in (WORK / 'tests' / name).read_text().splitlines():
            try: records.append(json.loads(line))
            except ValueError: pass
        failures = [row.get('Test') for row in records if row['Action'] == 'fail']
        assert failures == (['TestSharedTimestampContract', None] if name == 'gateway-race.jsonl' else [])
    tools = ROOT / 'state-client-build/field65-export16/diag-source-freeze-1/resume-tools'
    environment = {key: value for key, value in os.environ.items() if not key.startswith(('GO', 'CGO', 'FC_', 'YANDEX_'))}
    environment.update(GOTOOLCHAIN='local', GOWORK='off', GOPROXY='off', GOSUMDB='off', GOMAXPROCS='2',
                       GOPATH=str(tools / 'gopath'), GOCACHE=str(WORK / 'go-cache'),
                       GOOS='linux', GOARCH='amd64', GOAMD64='v1', CGO_ENABLED='1')
    binary = WORK / 'gateway-seed-recovery'
    assert not binary.exists()
    command = [tools / 'go/bin/go', 'build', '-p=1', '-trimpath', '-buildvcs=false', '-o', binary, './cmd/bootstrap-broker']
    with (WORK / 'tests/gateway-build.log').open('xb') as log:
        result = subprocess.run(list(map(str, command)), cwd=source, env=environment, stdout=log, stderr=subprocess.STDOUT, timeout=600)
    assert result.returncode == 0
    receipt = dict(exit=0, sha256=digest(binary), source_inventory=hashlib.sha256(json.dumps(files, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
                   parent_inventory=parent['source_inventory'], changed=sorted(changed), files=files, build_tags=[],
                   toolchain_sha256=digest(tools / 'go/bin/go'))
    (WORK / 'gateway-build.json').write_text(json.dumps(receipt, indent=2))
    print(json.dumps({key: receipt[key] for key in ('exit', 'sha256', 'source_inventory', 'changed')}))


if __name__ == '__main__':
    main()
