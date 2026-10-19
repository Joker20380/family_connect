"""Prepare only an unsigned same-key authority request using the existing node workflow."""

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tarfile


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser()
    parser.add_argument('--capsule', type=Path, required=True)
    parser.add_argument('--capsule-sha256', required=True)
    parser.add_argument('--operation', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--expected-authority-sha256', required=True)
    args = parser.parse_args()
    assert os.geteuid() == 0 and re.fullmatch('[a-z0-9-]{16,96}', args.operation)
    assert sha(args.capsule.read_bytes()) == args.capsule_sha256
    root = Path('/opt/apps/family_connect/friends-restricted')
    config = json.loads((root / 'renewal/node.json').read_bytes())
    assert config['role'] == 'RU' and config.get('admission_mode', 'legacy') == 'legacy'
    assert config['source_sha256'] == '5109a7c92ddd1937fe75ed7199866855a8cc20279bc226c35475d4cc81330145'
    assert all(sha((root / 'renewal' / name).read_bytes()) == value for name, value in config['source_files'].items())
    assert not (Path(config['state']) / 'owner.json').exists()
    assert not (Path(config['state']) / 'authority-request.json').exists()
    live = Path(config['live'])
    predecessor_raw = (live / 'issuer.json').read_bytes()
    assert sha(predecessor_raw) == args.expected_authority_sha256
    with tarfile.open(args.capsule, 'r:gz') as archive:
        members = archive.getmembers()
        assert all(member.isfile() and 0 <= member.size < 5_000_000 for member in members)
        assert len({member.name for member in members}) == len(members)
        content = {member.name: archive.extractfile(member).read() for member in members}
    manifest = json.loads(content['manifest.json'])
    assert manifest['admission_mode'] == 'all_activated' and manifest['authority_days'] == 90
    assert set(content) == {'manifest.json', 'bridge-access-v2.pyz'} | {
        'management/' + name for name in manifest['source_files']}
    assert all(re.fullmatch('[a-z_]+[.]py', name) and sha(content['management/' + name]) == expected
               for name, expected in manifest['source_files'].items())
    assert sha(content['bridge-access-v2.pyz']) == manifest['api_sha256']
    args.output.mkdir(mode=0o700, exist_ok=False)
    modules = args.output / 'modules'
    modules.mkdir(mode=0o700)
    for name in manifest['source_files']:
        (modules / name).write_bytes(content['management/' + name])
    api = args.output / 'api.pyz'
    api.write_bytes(content['bridge-access-v2.pyz'])
    sys.path[:0] = [str(modules), str(api)]
    from credential_renewal import Validator, atomic, canonical, digest, read_private, spki
    from production_node import ProductionNode
    from control.friends.restricted import delegation
    assert digest(canonical(manifest['source_files'])) == manifest['source_sha256']
    anchor_raw = read_private(Path(config['anchor']))
    anchor = base64.b64decode(anchor_raw.strip(), validate=True)
    assert sha(anchor) == config['anchor_sha256']
    state = args.output / 'request-state'
    state.mkdir(mode=0o700)
    node = ProductionNode('RU', live, state, Validator(anchor, delegation, all_activated=True))
    request = node.authority_request(args.operation)
    import time
    from cryptography import x509
    old, old_ca = delegation(request['previous_authority'], anchor, int(time.time()))
    new = request['successor_payload']
    new_ca = x509.load_pem_x509_certificate(new['authority'].encode())
    new_ca.verify_directly_issued_by(new_ca)
    assert new['sequence'] == old['sequence'] + 1
    assert all(new[name] == old[name] for name in ('family', 'gateway', 'minimum_revision'))
    assert spki(new_ca.public_key()) == spki(old_ca.public_key()) and new_ca.subject == old_ca.subject
    assert tuple(new_ca.extensions) == tuple(old_ca.extensions)
    assert new['expires_at'] - new['issued_at'] == 90 * 86400
    assert new_ca.not_valid_after_utc.timestamp() == new['expires_at']
    assert predecessor_raw == (live / 'issuer.json').read_bytes()
    assert not (Path(config['state']) / 'owner.json').exists()
    atomic(args.output / 'request.json', canonical(request))
    atomic(args.output / 'successor-ca.pem', new['authority'].encode())
    atomic(args.output / 'anchor.pub', anchor_raw)
    result = dict(result='UNSIGNED_REQUEST_PREPARED', operation_id=args.operation,
        request_sha256=digest(canonical(request)), successor_ca_sha256=digest(new['authority'].encode()),
        predecessor_file_sha256=sha(predecessor_raw), sequence_from=old['sequence'], sequence_to=new['sequence'],
        same_issuer_key=True, scope_unchanged=True, expires_at=new['expires_at'],
        request_expires_at=request['request_expires_at'], predecessor_expires_at=old['expires_at'],
        source_sha256=manifest['source_sha256'], active_materials_changed=False, root_signature=False)
    atomic(args.output / 'receipt.json', canonical(result))
    print(canonical(result).decode())


if __name__ == '__main__':
    main()
