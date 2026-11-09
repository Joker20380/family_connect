"""RU-only diagnostic candidate over the exact installed PR9 archive; no deployment."""
import argparse
import json
from pathlib import Path
import subprocess
import zipfile

if __package__:
    from .package_paid_transport import ROOT, archive, sha
else:
    from package_paid_transport import ROOT, archive, sha

BASE_SOURCE = 'b811547fcfd15d112c66d5db77a708daaee1b0a7'
BASE_NODE = 'f747759cfcf5b2881a18f984c81c95647db90cd30e93eea78e60066826c73131'
BASE_GATEWAY = '9023d2c3f7c3a5127d67c509a16eb2d974810ff54d5b76cc225cd9b93e0b4234'
MODULE = 'control/friends/transport_gateway.py'


def build(node, gateway, output, source=ROOT):
    if sha(node.read_bytes()) != BASE_NODE or sha(gateway.read_bytes()) != BASE_GATEWAY:
        raise ValueError('EXACT_RU_PR9_INPUTS_REQUIRED')
    with zipfile.ZipFile(node) as package:
        before = {name: package.read(name) for name in package.namelist()}
        if len(before) != len(package.namelist()):
            raise ValueError('DUPLICATE_ARCHIVE_MEMBER')
    policy = 'control/friends/transport_policy.py'
    if before[policy] != (source/policy).read_bytes():
        raise ValueError('POLICY_CHANGE_FORBIDDEN')
    if gateway.read_bytes() != (source/'deploy/friends/awg-gateway.py').read_bytes():
        raise ValueError('GATEWAY_CHANGE_FORBIDDEN')
    after = dict(before)
    after[MODULE] = (source/MODULE).read_bytes()
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    archive(output/'paid-transport.pyz', after)
    receipt = dict(schema=1, kind='ru-diagnostic-only', production_installed=False,
        source_sha=subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip(),
        source_dirty=bool(subprocess.check_output(['git', '-C', str(source), 'status', '--porcelain'])),
        base_source=BASE_SOURCE, base_node=BASE_NODE, unchanged_gateway=BASE_GATEWAY,
        files={'paid-transport.pyz': sha((output/'paid-transport.pyz').read_bytes())},
        before_modules={name: sha(raw) for name, raw in before.items()},
        after_modules={name: sha(raw) for name, raw in after.items()})
    (output/'inventory.json').write_text(json.dumps(receipt, sort_keys=True, indent=2)+'\n')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--node', type=Path, required=True)
    parser.add_argument('--gateway', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.node, args.gateway, args.output)))
