"""One guarded SACK-hole candidate, reusing the accepted ordinary switch procedure."""

import hashlib
import json
import os
from pathlib import Path
import sys

from rollout import GATEWAY, OLD, PINS, PREVIOUS, ROOT, WORK


def main():
    os.umask(0o077)
    mode = sys.argv[1]
    assert mode in ('stage', 'deploy', 'rollback', 'readiness')
    directory = WORK / 'candidate'
    manifest = json.loads((directory / 'artifact.json').read_text())
    expected = manifest['sha256']
    assert hashlib.sha256((directory / 'gateway-sack-holes').read_bytes()).hexdigest() == expected
    for label in ('holes-after', 'integration-after', 'gateway-build'):
        assert json.loads((directory / ('receipts/' + label + '.json')).read_text())['exit'] == 0
    replacements = {OLD: expected,
        '4b722d2d7f2159b96953e27777494bf596768f860ee8da7e634fb1100b08fab7': GATEWAY,
        '.beta88-throughput-observation-20261019-stage': '.mesh-throughput-sack-holes-20261019-stage',
        '".transport-write-batching-"+mode': '".mesh-throughput-sack-holes-20261019-"+mode',
        'root.parent/"mesh-perf-3/diagnostic-broker-final"': 'root/"gateway-sack-holes"',
        "root.parent / 'field65-export16/gateway-seed-supervisor-op-readiness-1/receipts'":
            "root.parents[1] / 'field65-export16/gateway-seed-supervisor-op-readiness-1/receipts'",
    }
    sources = {}
    for name, pin in PINS.items():
        path = PREVIOUS / name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == pin
        value = path.read_text()
        for old, new in replacements.items():
            value = value.replace(old, new)
        if name == 'readiness.py':
            value = value.replace('0eb38db8e1ec95ce67a358de2aaf910d4aa666fe9a80ee349d26a601aef734e6', expected)
        sources[name] = value
    target = directory / 'transition_remote.py'
    if target.exists():
        assert target.read_text() == sources['transition_remote.py']
    else:
        with target.open('x') as handle:
            handle.write(sources['transition_remote.py'])
    name = 'readiness.py' if mode == 'readiness' else 'operate.py'
    if mode == 'readiness':
        assert sys.argv[2:] and sys.argv[2] in ('before', 'candidate', 'final', 'accepted-return')
        sys.argv = [str(directory / name), *sys.argv[2:]]
    exec(compile(sources[name], str(directory / name), 'exec'), dict(__name__='__main__', __file__=str(directory / name)))


if __name__ == '__main__':
    main()
