"""Pinned receiver-deadline experiment; no deployment side effects."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from late_arrival import ROOT, SAVED, TOOLS, FIXTURE, digest

WORK = Path(os.environ.get('RTP_DEADLINE_OUT', ROOT / 'state-client-build/rtp-deadline-20261020'))


def prepare():
    source = SAVED / 'normal92/android-source'
    inventory = json.loads((SAVED / 'normal92/android-build/source-inventory.json').read_text())
    assert all(digest(source / name) == expected for name, expected in inventory.items())
    assert digest(SAVED / 'gateway-baseline-b9') == 'b9ae880731517753e456637e52dcc421b9f7d7b881b400c856989ae93193e9ba'
    WORK.mkdir(mode=0o700, exist_ok=False)
    shutil.copytree(source / 'carrier', WORK / 'carrier')
    (WORK / 'baseline.json').write_text(json.dumps(inventory, indent=2))
    patch = FIXTURE / 'finite-deadline.patch'
    if patch.exists():
        subprocess.run(['git', 'apply', str(patch)], cwd=WORK / 'carrier', check=True)


def run(integration=False, repeat=False):
    for name in ('late_arrival_test.go', 'deadline_test.go', 'late-arrival-input.json'):
        shutil.copyfile(FIXTURE / name, WORK / 'carrier/telemost' / name)
    shutil.copyfile(ROOT / 'tests/fixtures/tunnel_restart/peer_state_test.go', WORK / 'carrier/telemost/restart_audit_test.go')
    environment = {key: value for key, value in os.environ.items() if not key.startswith(('GO', 'CGO', 'FC_', 'YANDEX_'))}
    environment.update(GOTOOLCHAIN='local', GOWORK='off', GOPROXY='off', GOSUMDB='off', GOMAXPROCS='2',
                       GOPATH=str(TOOLS / 'gopath'), GOCACHE=str(SAVED / 'go-cache'), REPLAY_OUTPUT=str(WORK))
    label = 'integration' if integration else 'stress' if repeat else 'delta'
    index = len(list(WORK.glob(label+'-*.jsonl'))) + 1
    arguments = ['-skip', '^TestLate', './telemost', './familysession', './restrictedowner'] if integration else ['-run', '^TestDeadline', './telemost']
    with (WORK / f'{label}-{index}.jsonl').open('xb') as output:
        result = subprocess.run([TOOLS / 'go/bin/go', 'test', '-race', '-json', '-count='+('20' if repeat else '1'), '-timeout', '120s',
                                 *arguments], cwd=WORK / 'carrier', env=environment,
                                stdout=output, stderr=subprocess.STDOUT, timeout=180)
    print(json.dumps(dict(exit=result.returncode, log=f'{label}-{index}.jsonl')))
    raise SystemExit(result.returncode)


if __name__ == '__main__':
    os.umask(0o077)
    {'prepare': prepare, 'run': run, 'integration': lambda: run(True), 'stress': lambda: run(repeat=True)}[sys.argv[1]]()
