"""Reproducible isolated bootstrap worker using the pinned official RNS sources."""
import argparse
import base64
import hashlib
import importlib.metadata
import io
import json
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CHANNEL_SHA256 = '70593713d1d915904d10cf0cac0eb21ca41b11b4dedcdb7973d0da236579ada0'
VERSIONS = {'rns': ('1.5.1', 'RNS'), 'pyserial': ('3.5', 'serial')}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def distribution_files(name, version, package):
    distribution = importlib.metadata.distribution(name)
    if distribution.version != version:
        raise ValueError('Unexpected dependency version: ' + name)
    entries = {}
    for entry in distribution.files or ():
        parts = entry.parts
        if not parts or parts[0] not in (package, name + '-' + version + '.dist-info'):
            continue
        if '__pycache__' in parts or entry.name == 'RECORD':
            continue
        if '..' in parts or entry.is_absolute() or entry.hash is None or entry.hash.mode != 'sha256':
            raise ValueError('Unverified dependency member: ' + str(entry))
        path = Path(distribution.locate_file(entry))
        raw = path.read_bytes()
        checksum = base64.urlsafe_b64encode(hashlib.sha256(raw).digest()).decode().rstrip('=')
        if path.is_symlink() or len(raw) != entry.size or checksum != entry.hash.value:
            raise ValueError('Dependency RECORD mismatch: ' + str(entry))
        entries[str(entry)] = raw
    if package + '/__init__.py' not in entries:
        raise ValueError('Missing dependency package: ' + name)
    return entries


def archive(entries):
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as bundle:
        for name, raw in sorted(entries.items()):
            member = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            member.create_system = 3
            member.external_attr = 0o100644 << 16
            member.compress_type = zipfile.ZIP_DEFLATED
            bundle.writestr(member, raw)
    return output.getvalue()


def assemble(destination):
    if destination.exists():
        raise ValueError('Use a fresh RNS build directory')
    channel = (ROOT / 'clients/rns/fc_rns_transport.py').read_bytes()
    if digest(channel) != CHANNEL_SHA256:
        raise ValueError('Accepted106 channel differs from pinned source')
    entries = {'__main__.py': (ROOT / 'clients/rns/launcher.py').read_bytes(),
               'fc_rns_worker.py': (ROOT / 'clients/rns/worker.py').read_bytes(), 'fc_rns_transport.py': channel}
    for name, (version, package) in VERSIONS.items():
        entries.update(distribution_files(name, version, package))
    notices = {path.name: path.read_bytes() for path in sorted((ROOT / 'clients/rns/licenses').glob('*.txt'))}
    if set(notices) != {'Reticulum.txt', 'PySerial.txt'}:
        raise ValueError('Missing pinned dependency notices')
    entries.update({'licenses/' + name: raw for name, raw in notices.items()})
    inventory = {name: digest(raw) for name, raw in sorted(entries.items())}
    source_digest = digest(json.dumps(inventory, sort_keys=True, separators=(',', ':')).encode())
    raw = archive(entries)
    destination.mkdir(parents=True)
    executable = destination / 'fc-rns.pyz'
    executable.write_bytes(raw)
    executable.chmod(0o644)
    version = json.loads(subprocess.run(['/usr/bin/python3', '-I', '-S', str(executable), '--version'],
                                       check=True, capture_output=True, timeout=10).stdout)
    if version != dict(rns_protocol=1, rns='1.5.1', pyserial='3.5', crypto_provider='internal'):
        raise ValueError('Isolated RNS metadata mismatch')
    (destination / 'licenses').mkdir()
    for name, content in notices.items():
        (destination / 'licenses' / name).write_bytes(content)
    manifest = dict(schema=1, source_digest=source_digest, sources=inventory, runtime=version,
                    files={'fc-rns.pyz': dict(sha256=digest(raw), size=len(raw))},
                    channel_sha256=CHANNEL_SHA256, windows_embedded_python='NOT_PACKAGED')
    (destination / 'build.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(dict(source_digest=source_digest, files=manifest['files'], runtime=version)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    assemble(parser.parse_args().out.resolve())


if __name__ == '__main__':
    main()
