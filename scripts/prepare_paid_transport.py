"""Prepare a stopped gateway from a fresh canonical snapshot; never start engines."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys


def prepare(root, envelope, expected_archive, node):
    if os.geteuid() != 0:
        raise ValueError('ROOT_REQUIRED')
    archive = root/'paid-transport.pyz'
    if (archive.is_symlink() or archive.stat().st_uid != 0 or archive.stat().st_mode & 0o022
            or hashlib.sha256(archive.read_bytes()).hexdigest() != expected_archive):
        raise ValueError('VERIFIED_ARCHIVE_REQUIRED')
    for service in ('family-connect-friends-awg.service', 'family-connect-friends-tcp.service'):
        state = subprocess.check_output(['systemctl', 'show', '-p', 'ActiveState', '--value', service], timeout=5).decode().strip()
        if state != 'inactive':
            raise ValueError('STOPPED_ENGINES_REQUIRED')
    sys.path.insert(0, str(archive))
    from control.friends import transport_gateway, transport_policy
    for module in (transport_gateway, transport_policy):
        if not module.__file__.startswith(str(archive)+'/'):
            raise ValueError('ARCHIVE_MODULE_REQUIRED')
    transport_policy.validate(envelope, node, __import__('time').time())
    config, state = root/'transport-enforcement.json', root/'transport-state.json'
    if any(path.exists() or path.is_symlink() for path in (config, state)):
        raise ValueError('EXISTING_FENCE_MUST_BE_PRESERVED')
    spec = importlib.util.spec_from_file_location('paid_prepared_gateway', root/'awg-gateway.py')
    gateway = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = gateway
    spec.loader.exec_module(gateway)
    gateway.ROOT = root
    with gateway.database() as database:
        peers = {row[0] for row in database.execute('SELECT public FROM peers')}
    if not peers <= {row['public_key'] for row in envelope['decisions']}:
        raise ValueError('UNMAPPED_PEERS_REQUIRE_REVIEW')
    transport_gateway.write(config, dict(schema=1, profile=transport_policy.PROFILE, node=node, enabled=True))
    transport_gateway.write(state, dict(schema=1, node=node, records={}, observed_at=envelope['observed_at']))
    engine = transport_gateway.Gateway(gateway)
    engine.accept(envelope)
    engine.apply(starting=True)
    return dict(node=node, result='prepared-engines-stopped', archive_sha256=expected_archive)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--archive-sha256', required=True)
    parser.add_argument('--node', required=True)
    args = parser.parse_args()
    raw = sys.stdin.buffer.read(8000001)
    if len(raw) > 8000000:
        raise ValueError('SNAPSHOT_TOO_LARGE')
    print(json.dumps(prepare(args.root, json.loads(raw), args.archive_sha256, args.node)))


if __name__ == '__main__':
    main()
