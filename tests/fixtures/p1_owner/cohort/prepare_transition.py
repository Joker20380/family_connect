import json
import os
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[4]
WORK = ROOT / 'state-client-build/tester-p1-cohort-20261023'
BASE = ROOT / 'state-client-build/p1-lifecycle-101-20261021'


def main():
    os.umask(0o077)
    helpers = runpy.run_path(str(ROOT/'tests/fixtures/speed_candidate/prepare.py'))
    write, digest = helpers['write'], helpers['digest']
    build = json.loads((WORK/'gateway-build.json').read_text())
    assert digest(WORK/'gateway-group') == build['sha256']
    target = WORK/'transitions'
    assert not target.exists()
    for name in ('private','receipts'):
        (target/name).mkdir(mode=0o700,parents=True)
    pins = {}
    for name in ('operate.py','transition_remote.py','readiness.py'):
        original = BASE/'transitions'/name
        pins[name] = digest(original)
        source = original.read_text().replace(build['parent_sha256'],'CANDIDATE_HASH')
        source = source.replace('f631bd997ffc3a58a3216f8657062bef3edb1dcf38ec340c94dd26d3c625763e',build['parent_sha256'])
        source = source.replace('CANDIDATE_HASH',build['sha256'])
        source = source.replace('p1-lifecycle-101-20261021','tester-p1-cohort-20261023')
        if name == 'operate.py':
            source = source.replace('/gateway-speed','/gateway-group')
        write(target/name,source)
    write(target/'prepared.json',json.dumps(dict(candidate=build['sha256'],baseline=build['parent_sha256'],source_pins=pins,
                                               shared_restart_required=True,policy_mutations=0,network_operations=0),indent=2)+'\n')
    print('TRANSITION_PREPARED_NOT_DEPLOYED')


if __name__ == '__main__':
    main()
