"""One-shot locator issuance in the existing restricted authority custody."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile

from control.friends.access import Access
from control.friends.bootstrap_locator import issue
from control.friends.restricted import bounded_file, from_env


def publish(database, material, certificate, state, node, sequence):
    database, material, certificate, state = map(Path, (database, material, certificate, state))
    if not all(path.is_absolute() for path in (database, material, certificate, state)) or not database.is_file():
        raise ValueError('existing absolute inputs required')
    with sqlite3.connect(database.as_uri()+'?mode=ro', uri=True) as connection:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {'devices', 'invites', 'restricted_grants', 'restricted_challenges', 'restricted_certificates'}.issubset(tables):
            raise ValueError('existing registry schema required')
    os.environ['FC_FRIENDS_RESTRICTED_DIR'] = str(material)
    service = from_env(Access(database), node)
    seed = bounded_file(state/'seed.json', 8192)
    encoded = issue(service, seed, bounded_file(certificate, 8192).decode('ascii'), sequence)
    output = state/'locator.json'
    with tempfile.NamedTemporaryFile(dir=state, prefix='.locator-', delete=False) as target:
        temporary = Path(target.name)
        try:
            target.write(encoded)
            target.flush()
            os.fchmod(target.fileno(), 0o644)
            os.fsync(target.fileno())
            os.link(temporary, output)
        finally:
            temporary.unlink()
    descriptor = os.open(state, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return {'locator_sha256': hashlib.sha256(encoded).hexdigest(), 'node': node}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('database', 'material', 'certificate', 'state'):
        parser.add_argument('--'+name, required=True)
    parser.add_argument('--node', choices=('nl-amsterdam-1', 'nl-amsterdam-2'), required=True)
    parser.add_argument('--sequence', type=int, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(publish(**vars(args))))
    except Exception:
        print('LOCATOR_ISSUANCE_REJECTED_PRIVATE_DETAILS_SUPPRESSED', file=sys.stderr)
        raise SystemExit(1)


if __name__ == '__main__':
    main()
