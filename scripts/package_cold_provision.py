"""Build a closed cold-provisioning entry; never deploy or create provider rooms."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def source_identity():
    if subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=normal'], cwd=ROOT).strip():
        raise ValueError('clean committed source required')
    return subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()


def build(output, go):
    revision = source_identity()
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
                         ('scripts/prepare_cold_field_apk.py','prepare_cold_field_apk.py'),
                         ('scripts/cold_field_preflight.py','cold_field_preflight.py'),
                         ('scripts/cold-field-qualified.json','cold-field-qualified.json')]:
        shutil.copyfile(ROOT/source, output/name)
    entry_sources = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                     for path in sorted((ROOT/'carrier').rglob('*'))
                     if path.is_file() and (path.suffix in ('.go', '.mod', '.sum'))}
    if source_identity() != revision:
        raise ValueError('source moved during packaging')
    manifest = {'source': revision,
                'builder_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                'target': subprocess.check_output([str(go), 'env', 'GOOS', 'GOARCH', 'CGO_ENABLED'], cwd=ROOT/'carrier', text=True).splitlines(),
                'source_clean': True, 'carrier_source_files': entry_sources,
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
