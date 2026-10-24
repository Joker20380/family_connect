"""Build a disposable local authenticated worker; never a release artifact."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[3]


def build(go, output, xray_source):
    sys.path.insert(0, str(ROOT))
    from scripts.build_desktop_mesh import XRAY_REVISION, PATCH_SHA256, digest
    output.mkdir(parents=True, exist_ok=False)
    patch = ROOT / 'clients/mesh/xray-packet-boundary.patch'
    assert digest(patch) == PATCH_SHA256
    archive = output / 'xray.tar'
    subprocess.run(['git', '-C', str(xray_source), 'archive', '--format=tar', '-o', str(archive), XRAY_REVISION], check=True)
    xray = output / 'xray'
    xray.mkdir()
    with tarfile.open(archive) as bundle:
        bundle.extractall(xray, filter='data')
    subprocess.run(['git', 'apply', str(patch)], cwd=xray, check=True,
                   env=dict(os.environ, GIT_CEILING_DIRECTORIES=str(output)))
    source = ROOT / 'carrier/wholedevice/session.go'
    text = source.read_text().replace('import (', 'import (\n "os"\n "net/netip"', 1)
    signature = 'func openDirectory(ctx context.Context, raw []byte, directory bootstrap.Directory, network *underlay.Network, event func(string)) (*Session, error) {'
    assert text.count(signature) == 1
    text = text.replace(signature, signature + '\n return l021Open(ctx, raw)\n}\n\n' + signature.replace('openDirectory(', 'unusedProductionDirectory('))
    replacement = output / 'session.go'
    replacement.write_text(text + '\n' + Path(__file__).with_name('session.go.txt').read_text())
    overlay = output / 'overlay.json'
    owner = ROOT / 'carrier/restrictedchat/owner.go'
    owner_text = owner.read_text()
    for operation in ('owner.active++', 'owner.active--'):
        assert owner_text.count(operation) == 1
        owner_text = owner_text.replace(operation, operation + '\n wholedevice.L021Event(fmt.Sprintf("leases:%d", owner.active))')
    owner_replacement = output / 'owner.go'
    owner_replacement.write_text(owner_text)
    overlay.write_text(json.dumps({'Replace': {str(source): str(replacement), str(owner): str(owner_replacement)}}))
    module = output / 'fixture.mod'
    module.write_text((ROOT / 'clients/mesh/go.mod').read_text().replace('../../carrier', str(ROOT / 'carrier')))
    with module.open('a') as destination:
        destination.write('\nreplace github.com/xtls/xray-core => ' + str(xray) + '\n')
    module.with_suffix('.sum').write_bytes((ROOT / 'clients/mesh/go.sum').read_bytes())
    environment = dict(os.environ, CGO_ENABLED='1', GOTOOLCHAIN='local', GOWORK='off')
    subprocess.run([go, 'build', '-race', '-buildvcs=false', '-overlay=' + str(overlay), '-modfile=' + str(module),
                    '-ldflags=-checklinkname=0', '-o', str(output / 'fc-mesh-fixture'), './cmd/fc-mesh'],
                   cwd=ROOT / 'clients/mesh', env=environment, check=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--go', required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--xray', type=Path, required=True)
    arguments = parser.parse_args()
    build(arguments.go, arguments.out.resolve(), arguments.xray.resolve())
