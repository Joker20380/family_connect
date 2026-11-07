"""Pinned node-only forward recovery; never replace HTTP/operator/reconciler."""
import argparse
import json
from pathlib import Path
import subprocess
import zipfile

if __package__:
    from .package_paid_transport import archive, sha, ROOT
else:
    from package_paid_transport import archive, sha, ROOT

PREVIOUS_NODE = '7fa86e75162fc6c7f6c4ea8968ee3792027f05fc470a743c0b1b6cbb7af3eb2e'
PREVIOUS_GATEWAY = 'd7e57b79a5a4766c3dced902c4684f808b59ab99f4df37b47f6970eb5e92eb2a'
PREVIOUS_SOURCE = '2077c271d43d3bbe09f76e70934947bcc3fb51c6'


def build(node, gateway, output, source=ROOT):
    if sha(node.read_bytes()) != PREVIOUS_NODE or sha(gateway.read_bytes()) != PREVIOUS_GATEWAY:
        raise ValueError('EXACT_INSTALLED_V2_REQUIRED')
    with zipfile.ZipFile(node) as package:
        before = {name: package.read(name) for name in package.namelist()}
        if len(before) != len(package.namelist()):
            raise ValueError('DUPLICATE_ARCHIVE_MEMBER')
    policy = 'control/friends/transport_policy.py'
    if before[policy] != (source/policy).read_bytes():
        raise ValueError('POLICY_CHANGE_FORBIDDEN')
    after = dict(before)
    after['control/friends/transport_gateway.py'] = (source/'control/friends/transport_gateway.py').read_bytes()
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    archive(output/'paid-transport.pyz', after)
    (output/'awg-gateway.py').write_bytes((source/'deploy/friends/awg-gateway.py').read_bytes())
    for name in ('family-connect-paid-watch.service', 'paid-dependency.conf', 'paid-tcp-preflight.conf'):
        (output/name).write_bytes((source/'deploy/friends/paid-transport'/name).read_bytes())
    inventory = dict(schema=1, kind='node-forward-recovery', profile='paid-transports-v2',
        source_sha=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip(),
        source_dirty=bool(subprocess.check_output(['git','-C',str(source),'status','--porcelain'])),
        previous_node=PREVIOUS_NODE, previous_gateway=PREVIOUS_GATEWAY,
        files={path.name:sha(path.read_bytes()) for path in output.iterdir()},
        archives={'paid-transport.pyz':{name:sha(raw) for name,raw in after.items()}},
        before={name:sha(raw) for name,raw in before.items()})
    (output/'inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
    return inventory


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--node', type=Path, required=True)
    parser.add_argument('--gateway', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.node, args.gateway, args.output)))
