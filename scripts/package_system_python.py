"""Collect the existing locked runtime distributions using verified wheel RECORDs."""
import base64
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]


def collect():
    entries, versions = {}, {}
    for lock in ('provisioning/requirements.lock', 'messenger/requirements.lock'):
        for line in (ROOT / lock).read_text().splitlines():
            match = re.match(r'^([A-Za-z0-9_-]+)==([^ ]+)', line)
            if not match:
                continue
            name, version = match.groups()
            distribution = importlib.metadata.distribution(name)
            if distribution.version != version:
                raise ValueError('Runtime lock mismatch: ' + name)
            versions[name] = version
            count = 0
            for member in distribution.files or ():
                if (member.is_absolute() or '..' in member.parts or '__pycache__' in member.parts or
                        member.suffix in ('.pyc', '.pyo') or member.name == 'RECORD'):
                    continue
                if not member.hash or member.hash.mode != 'sha256':
                    raise ValueError('Unhashed runtime member: ' + str(member))
                path = Path(distribution.locate_file(member))
                raw = path.read_bytes()
                digest = base64.urlsafe_b64encode(hashlib.sha256(raw).digest()).decode().rstrip('=')
                if path.is_symlink() or digest != member.hash.value or len(raw) != member.size:
                    raise ValueError('Runtime RECORD mismatch: ' + str(member))
                key = 'vendor/' + str(member)
                if key in entries and entries[key] != raw:
                    raise ValueError('Runtime member collision')
                entries[key] = raw
                count += 1
            if not count:
                raise ValueError('Empty runtime distribution: ' + name)
    record = dict(schema=1, python=list(sys.version_info[:2]), distributions=versions,
                  files={name: hashlib.sha256(raw).hexdigest() for name, raw in sorted(entries.items())})
    entries['python-runtime.json'] = (json.dumps(record, sort_keys=True, indent=2) + '\n').encode()
    return entries
