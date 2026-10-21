"""Exact ordinary rollout with existing material/floor/renewal guards, no canary."""

import json
import os
import sys

from preserve import ROOT, WORK, digest

PINS = {'operate.py': 'c24f1ee919874d04ff262f77f6ddc1b69637f505238c9fdf44cc7c5fda45e4c8',
        'transition_remote.py': 'c7346a16ae425018eef11af4d47c9edf28c997746f53c05cda177861e803ea46',
        'readiness.py': '859fd99a9e5f95c0891adc29bc2f703461d470036beaaef18b087c138ba4499a'}
CANDIDATE = 'b9ae880731517753e456637e52dcc421b9f7d7b881b400c856989ae93193e9ba'


def main():
    os.umask(0o077)
    assert sys.argv[1:] and sys.argv[1] in ('stage', 'deploy', 'rollback', 'readiness')
    assert digest(WORK / 'gateway-seed-recovery') == CANDIDATE
    assert json.loads((WORK / 'gateway-build.json').read_text())['sha256'] == CANDIDATE
    previous = ROOT / 'state-client-build/beta88-throughput-20261019'
    sources = {}
    for name, expected in PINS.items():
        assert digest(previous / name) == expected
        sources[name] = (previous / name).read_text().replace(
            '04886384ce0bfa80568aea7e6d6fd2fec6ee0ed300a071ea806a8ef6a29a033b', CANDIDATE).replace(
            '.beta88-throughput-observation-20261019-stage', '.tunnel-restart-20261019-stage')
    sources['operate.py'] = sources['operate.py'].replace('root.parent/"mesh-perf-3/diagnostic-broker-final"', 'root/"gateway-seed-recovery"')
    sources['transition_remote.py'] = sources['transition_remote.py'].replace('".transport-write-batching-"+mode', '".tunnel-restart-20261019-"+mode')
    sources['readiness.py'] = sources['readiness.py'].replace("'before', 'observation', 'candidate', 'accepted-return', 'final'", "'before', 'before-reconciled', 'observation', 'candidate', 'accepted-return', 'final'").replace("('before','accepted-return')", "('before','before-reconciled','accepted-return')")
    (WORK / 'private').mkdir(mode=0o700, exist_ok=True)
    (WORK / 'receipts').mkdir(mode=0o700, exist_ok=True)
    target = WORK / 'transition_remote.py'
    if target.exists():
        assert target.read_text() == sources['transition_remote.py']
    else:
        target.write_text(sources['transition_remote.py'])
    name = 'readiness.py' if sys.argv[1] == 'readiness' else 'operate.py'
    if name == 'readiness.py':
        assert sys.argv[2:] and sys.argv[2] in ('before', 'before-reconciled', 'observation', 'accepted-return', 'final')
        sys.argv = [str(WORK / name), *sys.argv[2:]]
    exec(compile(sources[name], str(WORK / name), 'exec'), dict(__name__='__main__', __file__=str(WORK / name)))


if __name__ == '__main__':
    main()
