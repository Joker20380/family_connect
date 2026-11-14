"""Runs in an isolated operator SSH process, never in a Django request."""
import hashlib
import importlib
from pathlib import Path
import sys
import time
import zipimport


def collect_technical_metadata(config):
    result = dict(schema=1, source='gateway-ru', observed_at=int(time.time()), status='unavailable', devices=[])
    try:
        archive = Path(config['archive']).resolve(strict=True)
        if hashlib.sha256(archive.read_bytes()).hexdigest() != config['archive_sha256']:
            return result
        name = 'control.friends.technical_metadata'
        if any(key == 'control' or key.startswith('control.') for key in sys.modules):
            return result
        sys.path.insert(0, str(archive))
        try:
            module = importlib.import_module(name)
            expected = str(archive / 'control/friends/technical_metadata.py')
            if (module.__file__ != expected or module.__spec__.origin != expected
                    or not isinstance(module.__spec__.loader, zipimport.zipimporter)
                    or Path(module.__spec__.loader.archive).resolve() != archive):
                return result
            result['devices'] = module.read_all(Path('/opt/apps/family_connect/friends-access/technical-metadata.sqlite'), result['observed_at'])
        finally:
            sys.path.pop(0)
        result['status'] = 'ok'
    except (OSError, ValueError, ImportError, KeyError):
        result.update(status='unavailable', devices=[])
    return result
