from dataclasses import replace
import json
import os
from pathlib import Path

import pytest

from control.friends import profile_store as store
from control.friends.restricted import iso
from test_restricted_maintenance import make_crl, setup


@pytest.fixture
def canonical(setup, tmp_path):
    assert os.geteuid() == 0, 'Use the isolated root test container'
    for parent in (tmp_path, *tmp_path.parents):
        if parent == Path('/'):
            break
        parent.chmod(0o755)
    root = tmp_path / 'canonical'
    root.mkdir(mode=0o750)
    os.chown(root, 0, 41003)
    profile = root / 'profile.json'
    profile.write_bytes(setup.profile.read_bytes())
    os.chown(profile, 0, 41003)
    profile.chmod(0o640)
    private = tmp_path / 'control'
    private.mkdir(mode=0o700)
    lock = private / 'profile.lock'
    lock.touch(mode=0o600)
    operations = private / 'operations'
    operations.mkdir(mode=0o700)
    publisher = tmp_path / 'publisher'
    publisher.mkdir(mode=0o1770)
    os.chown(publisher, 0, 41002)
    publisher.chmod(0o1770)
    directory = publisher / 'directory.json'
    directory.write_bytes(setup.directory.read_bytes())
    os.chown(directory, 41001, 41002)
    directory.chmod(0o600)
    executable = private / 'publisher-contract'
    executable.write_bytes(b'synthetic-publisher-contract')
    executable.chmod(0o600)
    parent_info = publisher.stat()
    port = store.DirectoryPort(directory, dict(uid=41001, gid=41002, mode=0o600),
        dict(path=str(publisher), **store.metadata(parent_info), device=parent_info.st_dev, inode=parent_info.st_ino),
        ((str(executable), store.digest(executable.read_bytes()), store.metadata(executable.stat())),))
    locator = store.Locator(profile, lock, operations, 41003, port)
    locator.validate()
    setup.locator = locator
    setup.store = store.ProfileStore(locator, clock=lambda: setup.now)
    setup.before = profile.read_bytes()
    setup.receipts = []
    setup.permit_checks = []
    setup.fixed_locator = root / 'locator.json'
    setup.fixed_locator.write_bytes(store.encode(dict(schema=1, lock_version=1, profile=str(profile), lock=str(lock),
        operations=str(operations), reader_gid=41003, directory=dict(path=str(directory), metadata=port.expected,
        publisher_parent=port.publisher_parent, publisher_contract=port.publisher_contract))))
    os.chown(setup.fixed_locator, 0, 41003)
    setup.fixed_locator.chmod(0o640)
    return setup


def transaction(fixture, action='reconcile_current_floor', payload=None, persist=None, permit=None):
    return fixture.store.transact('synthetic_operation_01', action, expected_sha256=store.digest(fixture.before),
        payload=payload, permit=permit or (lambda: fixture.permit_checks.append(True)),
        persist=persist or (lambda record, before, target: fixture.receipts.append(record)))


def rotate(fixture, *, valid=True):
    port = fixture.locator.directory_port
    value = json.loads(port.path.read_bytes())
    value.update(issued_at=iso(fixture.now), expires_at=iso(fixture.now + 900))
    if not valid:
        value['family'] = 'c' * 32
    pending = port.path.with_name('publisher-next')
    pending.write_bytes(store.encode(value))
    os.chown(pending, port.expected['uid'], port.expected['gid'])
    pending.chmod(port.expected['mode'])
    os.replace(pending, port.path)


@pytest.mark.parametrize('consumer', ['gateway', 'snapshot', 'renewal', 'maintenance', 'exact_crl'])
def test_fixed_locator_resolves_one_profile_and_independent_directory(canonical, consumer, monkeypatch):
    monkeypatch.setenv('SSH_ORIGINAL_COMMAND', '--profile attacker')
    monkeypatch.setenv('FC_PROFILE', '/invalid/ignored')
    actual = store.Locator.load(canonical.fixed_locator)
    assert actual.profile == canonical.locator.profile
    assert actual.lock == canonical.locator.lock
    assert actual.directory_port.path == canonical.locator.directory_port.path
    assert actual.profile.parent != actual.directory_port.path.parent
    assert not actual.profile.is_relative_to(actual.directory_port.path.parent)


@pytest.mark.parametrize('field,value', [('schema', True), ('lock_version', 2), ('reader_gid', True),
                                       ('extra', 'forbidden'), ('profile', '../invalid')])
def test_locator_rejects_schema_and_path_overrides(canonical, field, value):
    config = json.loads(canonical.fixed_locator.read_bytes())
    config[field] = value
    canonical.fixed_locator.write_bytes(store.encode(config))
    with pytest.raises((store.ProfileError, OSError)):
        store.Locator.load(canonical.fixed_locator)


def test_locator_rejects_shared_publisher_boundary(canonical):
    with pytest.raises(store.ProfileError, match='LOCATOR_PATH_CONFLICT'):
        replace(canonical.locator, profile=canonical.locator.directory_port.path.parent / 'profile.json').validate()


def test_shared_lock_is_existing_root_owned_and_not_recreated(canonical):
    canonical.locator.lock.unlink()
    with pytest.raises(FileNotFoundError):
        transaction(canonical)
    assert not canonical.locator.lock.exists()


@pytest.mark.parametrize('target', ['profile', 'lock'])
@pytest.mark.parametrize('mutation', ['symlink', 'hardlink', 'mode', 'owner'])
def test_protected_material_metadata_fail_closed(canonical, target, mutation):
    path = getattr(canonical.locator, target)
    if mutation == 'symlink':
        raw = path.read_bytes()
        other = path.with_name('elsewhere')
        other.write_bytes(raw)
        path.unlink()
        path.symlink_to(other)
    elif mutation == 'hardlink':
        os.link(path, path.with_name('alias'))
    elif mutation == 'mode':
        path.chmod(0o666)
    else:
        os.chown(path, 41001, 41002)
    with pytest.raises((store.ProfileError, OSError)):
        transaction(canonical)
    assert not canonical.receipts


@pytest.mark.parametrize('label,reader', [('gateway', 41001), ('snapshot', 41004), ('publisher', 41005)])
def test_reader_access_without_write_privilege(canonical, label, reader):
    process = os.fork()
    if process == 0:
        try:
            os.setgroups([41003] if label != 'publisher' else [41002])
            os.setgid(reader)
            os.setuid(reader)
            try:
                resolved = store.Locator.load(canonical.fixed_locator)
                assert resolved.profile == canonical.locator.profile
                canonical.locator.profile.read_bytes()
                assert label != 'publisher'
            except PermissionError:
                assert label == 'publisher'
            for path in (canonical.locator.profile, canonical.locator.lock):
                try:
                    descriptor = os.open(path, os.O_WRONLY)
                except PermissionError:
                    pass
                else:
                    os.close(descriptor)
                    os._exit(2)
            os._exit(0)
        except BaseException:
            os._exit(3)
    assert os.waitpid(process, 0)[1] == 0


def test_floor_changes_only_floor_and_preserves_metadata(canonical):
    directory_raw = canonical.locator.directory_port.path.read_bytes()
    inode = canonical.locator.profile.stat().st_ino
    result = transaction(canonical)
    before, after = json.loads(canonical.before), json.loads(canonical.store.read())
    assert after == dict(before, minimum_crl=27211)
    assert canonical.locator.directory_port.path.read_bytes() == directory_raw
    assert canonical.locator.profile.stat().st_ino != inode
    assert store.metadata(canonical.locator.profile.stat()) == dict(uid=0, gid=41003, mode=0o640)
    assert result['state'] == 'COMMITTED'
    assert [receipt['state'] for receipt in canonical.receipts] == ['PREPARED', 'REPLACING', 'COMMITTED']
    assert len(canonical.permit_checks) >= 3
    assert not list(canonical.locator.profile.parent.glob('.profile.json.*'))


@pytest.mark.parametrize('number', [27211, 27212])
def test_renewal_equal_or_higher_crl_normalizes_floor(canonical, number):
    incoming = json.loads(canonical.before)
    incoming.update(revocations=make_crl(canonical, number).decode(), minimum_crl=27000)
    transaction(canonical, 'credential_renewal', store.encode(incoming))
    assert json.loads(canonical.store.read()) == dict(incoming, minimum_crl=number)


def test_renewal_lower_crl_rejected(canonical):
    incoming = dict(json.loads(canonical.before), revocations=make_crl(canonical, 27210).decode())
    with pytest.raises(store.ProfileError, match='CRL_ROLLBACK_REJECTED'):
        transaction(canonical, 'credential_renewal', store.encode(incoming))
    assert canonical.store.read() == canonical.before and not canonical.receipts


def test_renewal_floor_ahead_rejected(canonical):
    incoming = dict(json.loads(canonical.before), minimum_crl=27212)
    with pytest.raises(store.ProfileError, match='CRL_FLOOR_AHEAD'):
        transaction(canonical, 'credential_renewal', store.encode(incoming))


@pytest.mark.parametrize('field', ['family', 'gateway'])
def test_renewal_binding_mismatch_rejected(canonical, field):
    incoming = dict(json.loads(canonical.before), **{field: 'c' * 32})
    with pytest.raises(store.ProfileError, match='PROFILE_BINDING_CHANGED'):
        transaction(canonical, 'credential_renewal', store.encode(incoming))


def test_exact_crl_changes_only_crl_and_floor(canonical):
    payload = make_crl(canonical, 27212)
    transaction(canonical, 'apply_exact_crl', payload)
    assert json.loads(canonical.store.read()) == dict(json.loads(canonical.before), revocations=payload.decode(), minimum_crl=27212)


@pytest.mark.parametrize('number', [27210, 27211])
def test_exact_crl_requires_strict_increase(canonical, number):
    with pytest.raises(store.ProfileError, match='CRL_ROLLBACK_REJECTED'):
        transaction(canonical, 'apply_exact_crl', make_crl(canonical, number))


def test_exact_crl_bad_signature_rejected(canonical):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    with pytest.raises(store.ProfileError, match='CRL_INVALID'):
        transaction(canonical, 'apply_exact_crl', make_crl(canonical, 27212, signing=Ed25519PrivateKey.generate()))


def test_renewal_and_maintenance_contend_on_same_lock(canonical):
    other = store.ProfileStore(canonical.locator, clock=lambda: canonical.now)
    with canonical.store.lock():
        with pytest.raises(store.ProfileError, match='PROFILE_TRANSACTION_BUSY'):
            with other.lock():
                pytest.fail('Second writer entered the lock')
    transaction(canonical)
    with pytest.raises(store.ProfileError, match='PROFILE_CAS_FAILED'):
        transaction(canonical, 'credential_renewal', canonical.before)


def test_directory_legitimate_atomic_rotation_does_not_rollback(canonical, monkeypatch):
    original = os.replace
    def replace_and_rotate(source, target, **kwargs):
        original(source, target, **kwargs)
        if target == canonical.locator.profile.name:
            rotate(canonical)
    monkeypatch.setattr(os, 'replace', replace_and_rotate)
    result = transaction(canonical)
    assert result['directory_before']['sha256'] != result['directory_after']['sha256']
    assert result['state'] == 'COMMITTED'
    assert json.loads(canonical.store.read())['minimum_crl'] == 27211


def test_invalid_directory_after_write_restores_exact_profile_not_directory(canonical, monkeypatch):
    original = os.replace
    changes = []
    def replace_and_invalidate(source, target, **kwargs):
        original(source, target, **kwargs)
        if target == canonical.locator.profile.name and not changes:
            changes.append(True)
            rotate(canonical, valid=False)
    monkeypatch.setattr(os, 'replace', replace_and_invalidate)
    with pytest.raises(store.ProfileError, match='DIRECTORY_INVALID'):
        transaction(canonical)
    assert canonical.store.read() == canonical.before
    assert store.metadata(canonical.locator.profile.stat()) == canonical.locator.profile_metadata
    assert json.loads(canonical.locator.directory_port.path.read_bytes())['family'] == 'c' * 32
    assert canonical.receipts[-1]['state'] == 'ROLLED_BACK'


def test_changed_publisher_contract_blocks_before_profile_write(canonical):
    executable = Path(canonical.locator.directory_port.publisher_contract[0][0])
    executable.write_bytes(b'changed')
    with pytest.raises(store.ProfileError, match='PUBLISHER_CONTRACT_CHANGED'):
        transaction(canonical)
    assert canonical.store.read() == canonical.before


def test_directory_world_writable_parent_is_never_allowed(canonical):
    canonical.locator.directory_port.path.parent.chmod(0o1777)
    with pytest.raises(store.ProfileError, match='UNSAFE_PARENT'):
        transaction(canonical)


def test_permit_is_rechecked_immediately_before_replace(canonical):
    checks = []
    def permit():
        checks.append(True)
        store.require(len(checks) < 3, 'PERMIT_EXPIRED')
    with pytest.raises(store.ProfileError, match='PERMIT_EXPIRED'):
        transaction(canonical, permit=permit)
    assert canonical.store.read() == canonical.before
    assert canonical.receipts[-1]['state'] == 'NOT_APPLIED'


def test_replace_requires_lock(canonical):
    with pytest.raises(store.ProfileError, match='PROFILE_LOCK_REQUIRED'):
        canonical.store.replace(canonical.before, expected=canonical.before, permit=lambda: None)


@pytest.mark.parametrize('raw', [b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":1e999}', b'{"a":1.5}'])
def test_strict_json_rejects_ambiguous_or_noninteger_numbers(raw):
    with pytest.raises(store.ProfileError, match='INVALID_JSON'):
        store.parse(raw)
