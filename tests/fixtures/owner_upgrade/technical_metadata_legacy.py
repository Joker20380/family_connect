"""Bounded transient collector output; pipe directly to import_technical_metadata."""
import argparse
import hashlib
import hmac
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys

from collect_inventory import BASE, ssh_command
from control.friends.pseudonyms import seal

MAX_EXPORT_BYTES = 64 * 1024 * 1024


def collect(known_hosts=None, base=BASE, run=subprocess.run):
    local = base / '.local'
    config_path, key_path = local / 'technical-metadata-source.json', local / 'inventory-hmac.key'
    for path in (config_path, key_path):
        if any(parent.is_symlink() for parent in (path, *path.parents)) or path.stat().st_mode & 0o077:
            raise ValueError('Private metadata collector inputs required')
    config = json.loads(config_path.read_text())
    if (set(config) != {'python', 'archive', 'archive_sha256'} or
            not all(isinstance(value, str) for value in config.values()) or
            not all(Path(config[name]).is_absolute() for name in ('python', 'archive')) or
            not re.fullmatch('[0-9a-f]{64}', config['archive_sha256'])):
        raise ValueError('Pinned metadata source required')
    key = key_path.read_bytes()
    if len(key) != 32:
        raise ValueError('Existing full device HMAC key required')
    command = ssh_command('gateway-ru', known_hosts)
    command[-1] = shlex.quote(config['python']) + ' -I -B -'
    script = (base / 'apps/console/technical_metadata_collector.py').read_text()
    script += '\nimport json\nprint(json.dumps(collect_technical_metadata(' + repr(config) + '), ensure_ascii=False, allow_nan=False))\n'
    response = run(command, input=script.encode(), capture_output=True, check=True, timeout=45)
    if len(response.stdout) > MAX_EXPORT_BYTES:
        raise ValueError('Metadata bound exceeded')
    data = json.loads(response.stdout)
    if data.get('source') != 'gateway-ru' or type(data.get('devices')) is not list or len(data['devices']) > 5000:
        raise ValueError('Invalid source')
    for row in data['devices']:
        device = row.pop('device')
        if not isinstance(device, str) or not re.fullmatch('[0-9a-f]{32}', device):
            raise ValueError('Invalid device binding')
        row['pseudonym'] = hmac.new(key, device.encode(), hashlib.sha256).hexdigest()
    raw = json.dumps(seal(data, 'technical_metadata', key), ensure_ascii=False, allow_nan=False).encode()
    if len(raw) > MAX_EXPORT_BYTES:
        raise ValueError('Metadata projection bound exceeded')
    return raw


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--known-hosts', type=Path)
    args = parser.parse_args()
    try:
        raw = collect(args.known_hosts)
    except (OSError, ValueError, KeyError, subprocess.SubprocessError):
        parser.exit(1, 'Technical metadata source unavailable; payload not logged\n')
    sys.stdout.buffer.write(raw)


if __name__ == '__main__':
    main()
