"""Install a bounded official DB-IP Lite MMDB pair atomically; keep one rollback set."""
import argparse
from datetime import datetime, timezone
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import time
import urllib.request
import uuid

MAX_COMPRESSED = 160 * 1024 * 1024
MAX_EXPANDED = 256 * 1024 * 1024
REQUIRED_FREE = 1536 * 1024 * 1024


class OfficialRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, url):
        if not url.startswith('https://download.db-ip.com/'):
            raise ValueError('Unexpected download origin')
        return super().redirect_request(request, response, code, message, headers, url)


def atomic_json(path, value):
    temporary = path.with_name(path.name + '.pending')
    with temporary.open('w') as output:
        json.dump(value, output, sort_keys=True, separators=(',', ':'))
        output.flush(); os.fsync(output.fileno())
    os.replace(temporary, path)
    descriptor = os.open(path.parent, os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def download(kind, version, destination, opener):
    url = f'https://download.db-ip.com/free/dbip-{kind}-lite-{version}.mmdb.gz'
    compressed = destination.with_suffix('.gz')
    request = urllib.request.Request(url, headers={'User-Agent': 'FamilyConnect-GeoIP-Updater/1.0 (+https://github.com/Joker20380/family_connect)'})
    with opener.open(request, timeout=30) as response, compressed.open('xb') as output:
        if not response.url.startswith('https://download.db-ip.com/'):
            raise ValueError('Unexpected download origin')
        size = 0
        deadline = time.monotonic() + 600
        while chunk := response.read(65536):
            size += len(chunk)
            if size > MAX_COMPRESSED or time.monotonic() > deadline:
                raise ValueError('Compressed database bound')
            output.write(chunk)
    with gzip.open(compressed, 'rb') as source, destination.open('xb') as output:
        size = 0
        while chunk := source.read(65536):
            size += len(chunk)
            if size > MAX_EXPANDED:
                raise ValueError('Expanded database bound')
            output.write(chunk)
        output.flush(); os.fsync(output.fileno())
    compressed.unlink()


def update(root, version, *, fetch=download):
    if not re.fullmatch(r'20\d{2}-(0[1-9]|1[0-2])', version):
        raise ValueError('Monthly release required')
    root = Path(root)
    if any(path.is_symlink() for path in (root, *root.parents)):
        raise ValueError('Unsafe database directory')
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (root / 'update.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        stage = None
        installed = False
        try:
            for abandoned in root.glob('.pending-*'):
                if abandoned.is_dir() and not abandoned.is_symlink():
                    shutil.rmtree(abandoned)
            if shutil.disk_usage(root).free < REQUIRED_FREE:
                raise ValueError('Insufficient staging and rollback space')
            import maxminddb
            stage = Path(tempfile.mkdtemp(prefix='.pending-', dir=root))
            descriptions = {}
            opener = urllib.request.build_opener(OfficialRedirect())
            for kind in ('city', 'asn'):
                path = stage / (kind + '.mmdb')
                fetch(kind, version, path, opener)
                if path.is_symlink() or not 0 < path.stat().st_size <= MAX_EXPANDED:
                    raise ValueError('Expanded database bound')
                with maxminddb.open_database(str(path)) as reader:
                    metadata = reader.metadata()
                    if (kind not in metadata.database_type.lower() or metadata.node_count <= 0 or
                            metadata.ip_version not in (4, 6) or
                            datetime.fromtimestamp(metadata.build_epoch, timezone.utc).strftime('%Y-%m') != version):
                        raise ValueError('Invalid MMDB structure or release month')
                with path.open('rb') as source:
                    descriptions[kind] = dict(sha256=hashlib.file_digest(source, 'sha256').hexdigest(),
                                              build_epoch=metadata.build_epoch, size=path.stat().st_size)
                path.chmod(0o400)
            prior = json.loads((root / 'current.json').read_text()) if (root / 'current.json').exists() else None
            if prior and not re.fullmatch('set-[0-9a-f]{32}', prior['directory']):
                raise ValueError('Unsafe prior manifest')
            if prior:
                atomic_json(root / 'previous.json', prior)
            directory = 'set-' + uuid.uuid4().hex
            os.rename(stage, root / directory); stage = None
            value = dict(schema=1, version=version, directory=directory, databases=descriptions)
            atomic_json(root / 'current.json', value)
            installed = True
            keep = {directory, prior['directory'] if prior else None}
            for path in root.glob('set-*'):
                if path.name not in keep and re.fullmatch('set-[0-9a-f]{32}', path.name) and not path.is_symlink():
                    shutil.rmtree(path)
            atomic_json(root / 'update-status.json', dict(status='ok', version=version, reason=None))
            return value
        except Exception:
            atomic_json(root / 'update-status.json', dict(status='failed', version=version,
                reason='new_set_installed_cleanup_failed' if installed else 'update_failed_previous_set_retained'))
            raise
        finally:
            if stage is not None:
                shutil.rmtree(stage)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--version', required=True)
    args = parser.parse_args()
    try:
        result = update(args.root, args.version)
    except Exception:
        parser.exit(1, 'GeoIP update failed; inspect current.json and update-status.json before retry\n')
    print(json.dumps(dict(status='ok', version=result['version'], databases=result['databases'],
                         integrity='locally computed SHA256, not a supplier signature')))


if __name__ == '__main__':
    main()
