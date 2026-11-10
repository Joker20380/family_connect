"""Offline allowlisted packaging; no SSH, installation, rebuild or production reads."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import shutil
import tarfile
import zipfile


SOURCE = '377cfe8a7a53ce0edc9d6691992ef97c1af5209c'
BUNDLE = 'ru-command-budget-377cfe8a.tar.gz'
BUNDLE_SHA = 'bd4a48d3624618e974e3a7a28f4ebbfcd06fcf17c525c59a079658729e6ebef2'
INVENTORY_SHA = '3880cc50219846334923244613accce774c5790e42cf3c7db953503c9f433217'
QUALIFICATION_SHA = '56c3bdb2a9f45ebcd857eebc083d1a5c8602158e951e7403948483058c321a07'
IMAGE = 'sha256:af9c993c2fcd60804ef576e2190dee88699830624ec74317a91eb6d9855284e9'
KIT_FILES = ('paid-transport.pyz', 'family-connect-paid-watch.service', 'awg-gateway.py',
    'paid-dependency.conf', 'paid-tcp-preflight.conf', 'paid-operator.pyz', 'paid-reconcile.pyz',
    'prepare_paid_transport.py')
SOURCE_FILES = ('scripts/test_paid_transport_systemd.py', 'scripts/test_fleet_canary.py',
    'scripts/ru_replacement_qualification.py', 'scripts/prepare_ru_replacement.py',
    'scripts/run_ru_replacement.py', 'pilot/fleet_canary.py', 'pilot/transport_systemd_fixture.py',
    'pilot/transport_enforcement_fixture.py', 'pilot/transport-production-awg.service',
    'pilot/transport-production-tcp.service', 'deploy/friends/install-awg.py',
    'deploy/friends/install-tcp.py', 'docs/operators/ru-transport-replacement.ru.md')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def checked(path, expected):
    if path.is_symlink() or not path.is_file():
        raise ValueError('REGULAR_INPUT_REQUIRED: '+path.name)
    raw = path.read_bytes()
    if digest(raw) != expected:
        raise ValueError('INPUT_HASH_MISMATCH: '+path.name)
    return raw


def validate_bundle(raw, inventory):
    expected = dict(inventory['files'], **{'inventory.json': INVENTORY_SHA})
    contents = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:gz') as archive:
        members = archive.getmembers()
        if len(members) != len(expected) or {member.name for member in members} != set(expected):
            raise ValueError('UNEXPECTED_BUNDLE_MEMBERS')
        for member in members:
            if not member.isfile() or member.size > 4*1024*1024:
                raise ValueError('UNSAFE_BUNDLE_MEMBER')
            content = archive.extractfile(member).read()
            if digest(content) != expected[member.name]:
                raise ValueError('NESTED_HASH_MISMATCH')
            if member.name == 'paid-transport.pyz':
                with zipfile.ZipFile(io.BytesIO(content)) as node:
                    if len(node.namelist()) != len(set(node.namelist())):
                        raise ValueError('DUPLICATE_NODE_MEMBERS')
                    modules = {name: digest(node.read(name)) for name in node.namelist()}
                    if modules != inventory['after_modules']:
                        raise ValueError('NODE_MODULE_MISMATCH')
            contents[member.name] = content
    return contents


def prepare(accepted, destination):
    inventory_raw = checked(accepted/'full-inventory.json', INVENTORY_SHA)
    inventory = json.loads(inventory_raw)
    raw = checked(accepted/BUNDLE, BUNDLE_SHA)
    if inventory['source_sha'] != SOURCE:
        raise ValueError('SOURCE_MISMATCH')
    contents = validate_bundle(raw, inventory)
    qualified = json.loads(checked(accepted/'systemd-qualified.private.json', QUALIFICATION_SHA))
    if qualified['result'] != 'PASS':
        raise ValueError('UNQUALIFIED_INPUT')
    verified = {}
    for name in KIT_FILES:
        content = contents[name] if name in contents else checked(accepted/'systemd-kit-check'/name, qualified['kit'][name])
        if digest(content) != qualified['kit'][name]:
            raise ValueError('QUALIFIED_PAIR_MISMATCH')
        verified[name] = content
    destination.mkdir(mode=0o700)
    (destination/'kit').mkdir()
    for name, content in verified.items():
        (destination/'kit'/name).write_bytes(content)
    (destination/BUNDLE).write_bytes(raw)
    (destination/'accepted-inventory.json').write_bytes(inventory_raw)
    root = Path(__file__).resolve().parents[1]
    for name in SOURCE_FILES:
        path = destination/'source'/name
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root/name, path)
    (destination/'input-provenance.json').write_text(json.dumps(dict(source=SOURCE,
        bundle_sha256=BUNDLE_SHA, inventory_sha256=INVENTORY_SHA, fixture_base_image=IMAGE,
        historical_qualification_sha256=QUALIFICATION_SHA,
        new_host_qualification='NOT_RUN', production_changes=0), indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--accepted', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    args = parser.parse_args()
    prepare(args.accepted.resolve(), args.destination)
