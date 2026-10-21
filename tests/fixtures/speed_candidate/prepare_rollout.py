"""Materialize existing guarded rollout, without stage/restart/network operations."""

import json
from prepare import ROOT, WORK, GATEWAY_SHA, digest, write

PINS = {
    'operate.py': 'c24f1ee919874d04ff262f77f6ddc1b69637f505238c9fdf44cc7c5fda45e4c8',
    'transition_remote.py': 'c7346a16ae425018eef11af4d47c9edf28c997746f53c05cda177861e803ea46',
    'readiness.py': '859fd99a9e5f95c0891adc29bc2f703461d470036beaaef18b087c138ba4499a',
}


def main():
    build = json.loads((WORK / 'gateway-build.json').read_text())
    candidate = build['sha256']
    assert digest(WORK / 'gateway-speed') == candidate
    target = WORK / 'transitions'
    for folder in ('private','receipts'):
        (target / folder).mkdir(mode=0o700,parents=True,exist_ok=True)
    replacements = {
        '4b722d2d7f2159b96953e27777494bf596768f860ee8da7e634fb1100b08fab7': GATEWAY_SHA,
        '04886384ce0bfa80568aea7e6d6fd2fec6ee0ed300a071ea806a8ef6a29a033b': candidate,
        '0eb38db8e1ec95ce67a358de2aaf910d4aa666fe9a80ee349d26a601aef734e6': candidate,
        '.beta88-throughput-observation-20261019-stage': '.speed-candidate-20261021-stage',
        '".transport-write-batching-"+mode': '".speed-candidate-20261021-"+mode',
        'root.parent/"mesh-perf-3/diagnostic-broker-final"': 'Path(' + repr(str(WORK/'gateway-speed')) + ')',
        "root.parent / 'field65-export16/gateway-seed-supervisor-op-readiness-1/receipts'": 'Path(' + repr(str(ROOT/'state-client-build/field65-export16/gateway-seed-supervisor-op-readiness-1/receipts')) + ')',
    }
    for name,pin in PINS.items():
        original = ROOT/'state-client-build/beta88-throughput-20261019'/name
        assert digest(original) == pin
        text = original.read_text()
        for old,new in replacements.items():text=text.replace(old,new)
        if name=='readiness.py':
            text=text.replace("'observation', 'candidate', 'accepted-return'", "'observation', 'candidate', 'candidate-ready', 'accepted-return'")
        if name=='operate.py':
            text=text.replace('mode=sys.argv[1]', '''mode=sys.argv[1]
if mode in ("deploy","rollback"):
    assert sys.argv[2:]==["--shared-restart-approved"], "Coordinate shared gateway restart first"
    sys.argv=sys.argv[:2]''')
        write(target/name,text)
    (target/'prepared.json').write_text(json.dumps(dict(candidate=candidate,baseline=GATEWAY_SHA,original_pins=PINS,network_operations=0,staged=False,restart_requires_explicit_coordination=True),indent=2))
    print('PREPARED_ONLY_NO_SSH_NO_STAGE_NO_RESTART')


if __name__=='__main__':main()
