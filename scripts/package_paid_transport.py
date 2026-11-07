"""Build a closed, disabled-by-default transport kit over an exact serving archive."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MODULES = ('control/friends/transport_policy.py', 'control/friends/transport_gateway.py')
BASELINE = '4bcbd7ed0dcc756965f5eb60aa340c8d5d638513a0af64ca93b50affce86b7fb'
GATEWAY = '8e536367a391661f003d0725afc13f69c45a9e43bb1763b61fd21ce0b998035a'
API_INSERT = b"    from control.friends.transport_policy import configuration_decision,node_for_host\n    node=node_for_host(ROOT,host)\n    if node is not None:record=configuration_decision(access,ROOT,node,record)\n"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def archive(path, contents):
    with zipfile.ZipFile(path, 'x', compression=zipfile.ZIP_DEFLATED) as output:
        for name, raw in sorted(contents.items()):
            entry = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = (0o40755 if name.endswith('/') else 0o100644) << 16
            output.writestr(entry, raw)


def build(baseline, gateway, output, source=ROOT):
    if sha(baseline.read_bytes()) != BASELINE or sha(gateway.read_bytes()) != GATEWAY:
        raise ValueError('OBSERVED_SERVING_INPUTS_REQUIRED')
    with zipfile.ZipFile(baseline) as package:
        if len(package.namelist()) != len(set(package.namelist())):
            raise ValueError('INVALID_SERVING_ARCHIVE')
        original = {name: package.read(name) for name in package.namelist()}
    replacement = (source/'deploy/friends/access-api.py').read_bytes()
    if replacement.count(API_INSERT) != 1 or replacement.replace(API_INSERT, b'') != original['friends_http.py']:
        raise ValueError('UNRELATED_HTTP_DELTA')
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    http = dict(original, **{'friends_http.py': replacement})
    for name in ('control/friends/transport_policy.py', 'control/friends/transport_reconcile.py'):
        http[name] = (source/name).read_bytes()
    archive(output/'friends-http.pyz', http)
    reconcile = dict(http, **{'__main__.py': b'from control.friends.transport_reconcile import main\nraise SystemExit(main())\n'})
    archive(output/'paid-reconcile.pyz', reconcile)
    native = {name: (source/name).read_bytes() for name in MODULES}
    native.update({'control/': b'', 'control/friends/': b'', 'control/friends/__init__.py': b''})
    archive(output/'paid-transport.pyz', native)
    (output/'awg-gateway.py').write_bytes((source/'deploy/friends/awg-gateway.py').read_bytes())
    (output/'prepare_paid_transport.py').write_bytes((source/'scripts/prepare_paid_transport.py').read_bytes())
    for path in (source/'deploy/friends/paid-transport').glob('*'):
        if path.is_file():
            (output/path.name).write_bytes(path.read_bytes())
    report = dict(schema=1, production_enabled=False, baseline_http_sha256=BASELINE, baseline_gateway_sha256=GATEWAY,
        http_before={name: sha(raw) for name, raw in original.items()}, http_after={name: sha(raw) for name, raw in http.items()},
        files={path.name: sha(path.read_bytes()) for path in output.iterdir()})
    (output/'inventory.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', required=True, type=Path)
    parser.add_argument('--gateway', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.baseline, args.gateway, args.output)))


if __name__ == '__main__':
    main()
