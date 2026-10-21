"""Reuse the serialized ordinary transition with fresh receipts and exact hashes."""

import json
import os
import subprocess
import sys

from prepare import ROOT, WORK, GATEWAY, digest


PINS = {
    'operate.py': 'c24f1ee919874d04ff262f77f6ddc1b69637f505238c9fdf44cc7c5fda45e4c8',
    'transition_remote.py': 'c7346a16ae425018eef11af4d47c9edf28c997746f53c05cda177861e803ea46',
    'readiness.py': '859fd99a9e5f95c0891adc29bc2f703461d470036beaaef18b087c138ba4499a',
}


def main():
    os.umask(0o077)
    mode = sys.argv[1]
    assert mode in ('stage', 'deploy', 'rollback', 'readiness')
    resumed = sys.argv[2:] == ['resumed']
    if resumed:
        assert mode == 'deploy'
        abort = json.loads((WORK / 'transitions/receipts/ssh-abort-readback.json').read_text())
        assert abort['result'] == 'PREMUTATION_ABORT_CONFIRMED' and not abort['deploy_intent']
    artifact = json.loads((WORK / 'build-result.json').read_text())
    candidate = artifact['binary_sha256']
    binary = ROOT / artifact['binary']
    assert digest(binary) == candidate
    assert artifact['baseline_gateway'] == GATEWAY
    assert digest(ROOT / 'tests/fixtures/rtp_pacing/packet-pacing.patch') == artifact['patch_sha256']
    inventory = json.loads((WORK / 'source-inventory.json').read_text())
    assert all(digest(WORK / 'candidate' / name) == value for name, value in inventory.items())
    for name, value in artifact['test_logs'].items():
        assert digest(WORK / name) == value
    assert artifact['passed_candidate_cases_including_subtests'] == 613
    target = WORK / 'transitions'
    for name in ('private', 'receipts'):
        (target / name).mkdir(parents=True, exist_ok=True)
    previous = ROOT / 'state-client-build/beta88-throughput-20261019'
    replacements = {
        '4b722d2d7f2159b96953e27777494bf596768f860ee8da7e634fb1100b08fab7': GATEWAY,
        '04886384ce0bfa80568aea7e6d6fd2fec6ee0ed300a071ea806a8ef6a29a033b': candidate,
        '0eb38db8e1ec95ce67a358de2aaf910d4aa666fe9a80ee349d26a601aef734e6': candidate,
        '.beta88-throughput-observation-20261019-stage': '.rtp-pacing-20261020-stage',
        '".transport-write-batching-"+mode': '".rtp-pacing-20261020-"+mode',
        'root.parent/"mesh-perf-3/diagnostic-broker-final"': 'Path(' + repr(str(binary)) + ')',
        "root.parent / 'field65-export16/gateway-seed-supervisor-op-readiness-1/receipts'":
            'Path(' + repr(str(ROOT / 'state-client-build/field65-export16/gateway-seed-supervisor-op-readiness-1/receipts')) + ')',
    }
    sources = {}
    for name, pin in PINS.items():
        original = previous / name
        assert digest(original) == pin
        text = original.read_text()
        for old, new in replacements.items():
            text = text.replace(old, new)
        if name == 'operate.py' and resumed:
            old = 'jump=["-J","root@186.246.45.246"] if role=="RU" else []'
            assert old in text
            text = text.replace(old, 'jump=[]')
        sources[name] = text
    remote = target / 'transition_remote.py'
    if remote.exists():
        assert remote.read_text() == sources['transition_remote.py']
    else:
        patch = '*** Begin Patch\n*** Add File: ' + str(remote) + '\n'
        patch += ''.join('+' + line + '\n' for line in sources['transition_remote.py'].splitlines())
        subprocess.run(['apply_patch'], input=patch + '*** End Patch\n', text=True, check=True, stdout=subprocess.DEVNULL)
    name = 'readiness.py' if mode == 'readiness' else 'operate.py'
    sys.argv = [str(target / name), *(sys.argv[2:] if mode == 'readiness' else [mode] + (['resumed'] if resumed else []))]
    exec(compile(sources[name], str(target / name), 'exec'), dict(__name__='__main__', __file__=str(target / name)))


if __name__ == '__main__':
    main()
