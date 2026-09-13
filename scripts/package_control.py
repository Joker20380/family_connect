"""Build an opt-in, source-only Linux GUI/control preview; never a signed update."""
import argparse
import hashlib
import gzip
import io
import json
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parents[1]
DESKTOP = ('app.py', 'backend.py', 'profile_config.py', 'updates.py', 'update.pub', 'install-linux.sh')
CORE = ('__init__.py', 'ack.py', 'application.py', 'auth.py', 'cache.py',
        'configuration.py', 'control_route.py', 'envelope.py', 'models.py', 'relay.py', 'reticulum.py',
        'runtime.py', 'transaction.py')
FILES = ('scripts/install_control_route.py', 'clients/linux/control-route-helper.py', 'VERSION', 'device_identity/__init__.py', 'device_identity/device.py',
         'provisioning/requirements.lock', 'scripts/run_control_preview.py') + tuple(
    'clients/desktop/' + name for name in DESKTOP) + tuple('provisioning/' + name for name in CORE)


def package(root, output):
    payload = {}
    for name in FILES:
        source = root / name
        if source.is_symlink() or not source.is_file():
            raise ValueError('missing or unsafe public source: ' + name)
        payload[name] = source.read_bytes()
    digest = hashlib.sha256(json.dumps({name: hashlib.sha256(data).hexdigest()
        for name, data in sorted(payload.items())}, sort_keys=True).encode()).hexdigest()
    payload['manifest.json'] = (json.dumps(dict(schema_version=1, preview=True,
        bundle_id=digest, files={name: hashlib.sha256(data).hexdigest()
        for name, data in sorted(payload.items())}), indent=2) + '\n').encode()
    output.mkdir(parents=True, exist_ok=True)
    target = output / ('FamilyConnect-Control-Linux-preview-' + digest[:16] + '.tar.gz')
    with target.open('xb') as stream, gzip.GzipFile(fileobj=stream, mode='wb', filename='', mtime=0) as compressed, tarfile.open(fileobj=compressed, mode='w') as archive:
        for name, data in sorted(payload.items()):
            entry = tarfile.TarInfo('FamilyConnect-Control-preview/' + name)
            entry.size, entry.mode, entry.mtime = len(data), 0o600, 0
            archive.addfile(entry, io.BytesIO(data))
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'artifacts/control')
    args = parser.parse_args()
    print(package(ROOT, args.output))


if __name__ == '__main__':
    main()
