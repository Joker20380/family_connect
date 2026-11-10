"""RU-only manual-recovery/bounded-output candidate over the installed PR15 bytes."""
import argparse
import json
from pathlib import Path
import subprocess
import zipfile

if __package__:
    from .package_paid_transport import ROOT, archive, sha
else:
    from package_paid_transport import ROOT, archive, sha

BASE_SOURCE = 'fa0ec71e402ddddad161d0f7dc8f5ed8e0e92eaf'
BASE_NODE = '125c796a30c3fba1772c47b96963517350087ad04aad675b6f33a31a5383276c'
BASE_GATEWAY = '9023d2c3f7c3a5127d67c509a16eb2d974810ff54d5b76cc225cd9b93e0b4234'
MODULE = 'control/friends/transport_gateway.py'
UNIT = 'family-connect-paid-watch.service'


def build(node, gateway, unit, output, source=ROOT):
    historical_unit = subprocess.check_output(['git', '-C', str(source), 'show',
        BASE_SOURCE+':deploy/friends/paid-transport/'+UNIT])
    if (sha(node.read_bytes()) != BASE_NODE or sha(gateway.read_bytes()) != BASE_GATEWAY
            or unit.read_bytes() != historical_unit):
        raise ValueError('EXACT_RU_PR15_INPUTS_REQUIRED')
    with zipfile.ZipFile(node) as package:
        before = {name: package.read(name) for name in package.namelist()}
        if len(before) != len(package.namelist()):
            raise ValueError('DUPLICATE_ARCHIVE_MEMBER')
    policy = 'control/friends/transport_policy.py'
    if before[policy] != (source/policy).read_bytes():
        raise ValueError('POLICY_CHANGE_FORBIDDEN')
    if gateway.read_bytes() != (source/'deploy/friends/awg-gateway.py').read_bytes():
        raise ValueError('GATEWAY_CHANGE_FORBIDDEN')
    candidate_unit = (source/'deploy/friends/paid-transport'/UNIT).read_bytes()
    if candidate_unit != historical_unit.replace(b'Restart=on-failure\nRestartSec=5\n', b'Restart=no\n'):
        raise ValueError('UNRELATED_UNIT_CHANGE')
    after = dict(before)
    after[MODULE] = (source/MODULE).read_bytes()
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    archive(output/'paid-transport.pyz', after)
    (output/UNIT).write_bytes(candidate_unit)
    receipt = dict(schema=1, kind='ru-manual-recovery-bounded-diagnostics', production_installed=False,
        source_sha=subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip(),
        source_dirty=bool(subprocess.check_output(['git', '-C', str(source), 'status', '--porcelain'])),
        base_source=BASE_SOURCE, base_node=BASE_NODE, unchanged_gateway=BASE_GATEWAY,
        base_unit_sha256=sha(historical_unit), recovery_contract='RECOVERY_REQUIRED; explicit controlled start',
        files={name:sha((output/name).read_bytes()) for name in ('paid-transport.pyz', UNIT)},
        before_modules={name:sha(raw) for name,raw in before.items()},
        after_modules={name:sha(raw) for name,raw in after.items()})
    (output/'inventory.json').write_text(json.dumps(receipt, sort_keys=True, indent=2)+'\n')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('node','gateway','unit','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.node,args.gateway,args.unit,args.output)))
