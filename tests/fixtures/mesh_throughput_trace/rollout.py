"""Reuse the hash-pinned ordinary19Oct rollout, changing only artifact/staging IDs."""

import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
WORK = ROOT / 'state-client-build/mesh-throughput-trace-20261019'
PREVIOUS = ROOT / 'state-client-build/beta88-throughput-20261019'
PINS = {'operate.py': 'c24f1ee919874d04ff262f77f6ddc1b69637f505238c9fdf44cc7c5fda45e4c8',
        'transition_remote.py': 'c7346a16ae425018eef11af4d47c9edf28c997746f53c05cda177861e803ea46',
        'readiness.py': '859fd99a9e5f95c0891adc29bc2f703461d470036beaaef18b087c138ba4499a'}
GATEWAY = 'f8e6ff0761468672258c3fdd2b69c8c0aefe4ae7ada1fb48e64641191ded71bf'
OLD = '04886384ce0bfa80568aea7e6d6fd2fec6ee0ed300a071ea806a8ef6a29a033b'


def main():
    os.umask(0o077)
    assert sys.argv[1:] and sys.argv[1] in ('stage', 'deploy', 'rollback', 'readiness')
    assert hashlib.sha256((WORK / 'gateway-trace-final').read_bytes()).hexdigest() == GATEWAY
    assert json.loads((WORK / 'receipts/gateway-final-build.json').read_text())['exit'] == 0
    assert json.loads((WORK / 'receipts/final-trace-race.json').read_text())['exit'] == 0
    sources = {}
    for name, expected in PINS.items():
        path = PREVIOUS / name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected
        sources[name] = path.read_text().replace(OLD, GATEWAY).replace(
            '.beta88-throughput-observation-20261019-stage', '.mesh-throughput-trace-20261019-stage')
    sources['operate.py'] = sources['operate.py'].replace('root.parent/"mesh-perf-3/diagnostic-broker-final"', 'root/"gateway-trace-final"')
    sources['transition_remote.py'] = sources['transition_remote.py'].replace(
        '".transport-write-batching-"+mode', '".mesh-throughput-trace-20261019-"+mode')
    sources['readiness.py'] = sources['readiness.py'].replace("'before', 'observation', 'candidate', 'accepted-return', 'final'", "'before', 'observation', 'observation-recheck', 'candidate', 'accepted-return', 'final'")
    (WORK / 'private').mkdir(mode=0o700, exist_ok=True)
    target = WORK / 'transition_remote.py'
    if target.exists():
        assert target.read_text() == sources['transition_remote.py']
    else:
        with target.open('x') as handle:
            handle.write(sources['transition_remote.py'])
    name = 'readiness.py' if sys.argv[1] == 'readiness' else 'operate.py'
    if name == 'readiness.py':
        assert sys.argv[2:] and sys.argv[2] in ('before', 'observation', 'observation-recheck', 'accepted-return')
        sys.argv = [str(WORK / name), *sys.argv[2:]]
    exec(compile(sources[name], str(WORK / name), 'exec'), dict(__name__='__main__', __file__=str(WORK / name)))


if __name__ == '__main__':
    main()
