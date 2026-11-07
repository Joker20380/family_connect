"""Build a closed cold-provisioning entry; never deploy or create provider rooms."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def build(output, go):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    subprocess.run([str(go), 'build', '-trimpath', '-o', str(output/'cold-provision-entry'),
                    './cmd/cold-provision-entry'], cwd=ROOT/'carrier', check=True)
    paths = json.loads((ROOT/'deploy/friends/restricted/http-runtime-files.json').read_text())
    paths += ['control/friends/bootstrap_locator.py', 'scripts/cold_provision_locator.py']
    sources = {name: (ROOT/name).read_bytes() for name in paths}
    sources['__main__.py'] = b'from scripts.cold_provision_locator import main\nmain()\n'
    for name in ('control/__init__.py', 'scripts/__init__.py', 'clients/__init__.py', 'clients/desktop/__init__.py'):
        sources.setdefault(name, b'')
    with zipfile.ZipFile(output/'cold-provision-locator.pyz', 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, raw in sorted(sources.items()):
            archive.writestr(zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0)), raw)
    for source, name in [('control/requirements.lock','control.lock'), ('device_identity/requirements.lock','identity.lock'),
                         ('deploy/friends/restricted/cold-provision-entry@.service','cold-provision-entry@.service'),
                         ('deploy/friends/restricted/cold-provision-deployment.json','deployment.json'),
                         ('deploy/friends/restricted/COLD_FIELD_DELIVERY.md','HANDOFF.md'),
                         ('scripts/prepare_cold_field_apk.py','prepare_cold_field_apk.py')]:
        shutil.copyfile(ROOT/source, output/name)
    entry_sources = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                     for path in sorted((ROOT/'carrier').rglob('*'))
                     if path.is_file() and (path.suffix in ('.go', '.mod', '.sum'))}
    clean = not subprocess.check_output(['git', 'status', '--porcelain', '--', 'carrier',
                                        'scripts/cold_provision_locator.py', 'scripts/package_cold_provision.py',
                                        'scripts/prepare_cold_field_apk.py', 'deploy/friends/restricted/COLD_FIELD_DELIVERY.md',
                                        'deploy/friends/restricted/cold-provision-entry@.service',
                                        'deploy/friends/restricted/cold-provision-deployment.json'], cwd=ROOT).strip()
    manifest = {'source': subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip(),
                'target': subprocess.check_output([str(go), 'env', 'GOOS', 'GOARCH', 'CGO_ENABLED'], cwd=ROOT/'carrier', text=True).splitlines(),
                'source_clean': clean, 'carrier_source_files': entry_sources,
                'source_files': {name: hashlib.sha256(raw).hexdigest() for name,raw in sources.items()},
                'artifacts': {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in output.iterdir()},
                'authority': 'existing restricted issuer; no keys, DB, test fixtures or OAuth in package',
                'rpc': ['/friends/restricted-readiness/challenge', '/friends/restricted-readiness'],
                'maximum_entry_lifetime_seconds': 420}
    (output/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--go', type=Path, required=True)
    args = parser.parse_args()
    build(args.output, args.go)
