from dataclasses import replace
import json
import os
from pathlib import Path
import sys
import base64
import subprocess
import tarfile

import pytest

from control.friends import profile_store as store, restricted_maintenance as maintenance
from control.friends.restricted import iso
from test_restricted_maintenance import make_crl, setup, permit_for, private_file


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


def test_packaged_renewal_construct_uses_exact_api_and_canonical_route(canonical, tmp_path):
    package = Path(os.environ['FC_TEST_RENEWAL_PACKAGE'])
    extracted = tmp_path / 'packaged'
    extracted.mkdir(mode=0o700)
    (extracted / 'state').mkdir(mode=0o700)
    with tarfile.open(package, 'r:gz') as archive:
        archive.extractall(extracted, filter='data')
    manifest = json.loads((extracted / 'source-manifest.json').read_bytes())
    for path in (extracted / 'renewal').glob('*.py'):
        path.chmod(0o600)
    anchor = private_file(extracted / 'anchor', base64.b64encode(b'synthetic-trust-anchor'))
    configuration = dict(schema=1, role='NL', live=str(canonical.locator.directory_port.path.parent),
        state=str(extracted / 'state'), database=None, anchor=str(anchor),
        anchor_sha256=store.digest(b'synthetic-trust-anchor'), api_archive=str(extracted / 'api.pyz'),
        api_sha256=manifest['api_sha256'], service_units=['synthetic-gateway.service'],
        source_files=manifest['source_files'], source_sha256=manifest['source_sha256'],
        admission_mode='all_activated', profile_locator=str(canonical.fixed_locator),
        profile_locator_sha256=store.digest(canonical.fixed_locator.read_bytes()))
    config = private_file(extracted / 'node.json', store.encode(configuration))
    probe = '''import sys,json,hashlib
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import node
instance,identity=node.construct(Path(sys.argv[2]))
from control.friends import restricted,profile_store
assert restricted.__file__.startswith('/proc/self/fd/')
assert profile_store.__file__.startswith('/proc/self/fd/')
assert hashlib.sha256(Path(restricted.__file__.split('/control/')[0]).read_bytes()).hexdigest()==json.loads(Path(sys.argv[2]).read_bytes())['api_sha256']
assert instance.inspect()['files']['gateway.json']==sys.argv[3]
assert str(instance.profile_store.locator.profile)==sys.argv[4]
assert str(instance.directory_path())==sys.argv[5]
assert str(instance.profile_store.locator.lock)==sys.argv[6]
assert instance.barrier.units==('synthetic-gateway.service',)
assert identity==sys.argv[7]
'''
    result = subprocess.run([sys.executable, '-I', '-B', '-c', probe, str(extracted / 'renewal'), str(config),
        store.digest(canonical.before), str(canonical.locator.profile), str(canonical.locator.directory_port.path),
        str(canonical.locator.lock), manifest['source_sha256']], capture_output=True)
    assert result.returncode == 0, result.stderr.decode()
    assert canonical.locator.profile.read_bytes() == canonical.before
    assert canonical.profile.read_bytes() == canonical.before


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


@pytest.fixture
def canonical_maintenance(canonical):
    canonical.maintenance_config = maintenance.CanonicalConfiguration(canonical.store, b'm' * 32)
    canonical.maintenance_operation = maintenance.Operation(canonical.maintenance_config, canonical.permit,
                                                           clock=lambda: canonical.now)
    return canonical


@pytest.mark.parametrize('action', ['reconcile_current_floor', 'apply_exact_crl'])
def test_bounded_maintenance_uses_canonical_profile_and_exact_target(canonical_maintenance, action):
    fixture = canonical_maintenance
    before_directory = fixture.locator.directory_port.path.read_bytes()
    old_profile = fixture.profile.read_bytes()
    payload = fixture.payload if action == 'reconcile_current_floor' else make_crl(fixture, 27212)
    permit, request = permit_for(fixture, action=action, payload=payload)
    operation = maintenance.Operation(fixture.maintenance_config, permit, clock=lambda: fixture.now)
    response = operation.execute(request)
    assert response['result'] == 'PASS'
    target_number = 27211 if action == 'reconcile_current_floor' else 27212
    assert json.loads(fixture.store.read()) == dict(json.loads(fixture.before), minimum_crl=target_number,
                                                  revocations=payload.decode())
    assert store.metadata(fixture.locator.profile.stat()) == fixture.locator.profile_metadata
    assert fixture.profile.read_bytes() == old_profile
    assert fixture.locator.directory_port.path.read_bytes() == before_directory
    assert operation.execute(request)['result'] == 'IDEMPOTENT'
    assert operation.reconcile(request)['result'] == 'IDEMPOTENT'
    journal = json.loads((operation.root / 'journal.json').read_bytes())['journal']
    assert journal['attempt_count'] == 1 and journal['committed_write']


@pytest.mark.parametrize('phase', ['before_prepare', 'before_replace', 'after_replace'])
def test_bounded_maintenance_accepts_publisher_rotation(canonical_maintenance, monkeypatch, phase):
    fixture = canonical_maintenance
    original = os.replace
    if phase == 'before_prepare':
        rotate(fixture)
    def replacement(source, target, **kwargs):
        if target == fixture.locator.profile.name and phase == 'before_replace':
            rotate(fixture)
        original(source, target, **kwargs)
        if target == fixture.locator.profile.name and phase == 'after_replace':
            rotate(fixture)
    monkeypatch.setattr(os, 'replace', replacement)
    response = fixture.maintenance_operation.execute(fixture.request)
    assert response['result'] == 'PASS'
    assert response['directory_sha256'] != fixture.permit['expected_directory_sha256']
    assert fixture.maintenance_operation.execute(fixture.request)['result'] == 'IDEMPOTENT'


@pytest.mark.parametrize('failure', ['binding', 'publisher_contract', 'mode', 'time_rollback', 'same_generation'])
def test_bounded_maintenance_rolls_back_profile_only(canonical_maintenance, monkeypatch, failure):
    fixture = canonical_maintenance
    original = os.replace
    changed = []
    def replacement(source, target, **kwargs):
        original(source, target, **kwargs)
        if target != fixture.locator.profile.name or changed:
            return
        changed.append(True)
        port = fixture.locator.directory_port
        if failure == 'publisher_contract':
            Path(port.publisher_contract[0][0]).write_bytes(b'changed-contract')
        elif failure == 'mode':
            port.path.chmod(0o644)
        elif failure == 'binding':
            rotate(fixture, valid=False)
        else:
            value = json.loads(port.path.read_bytes())
            if failure == 'time_rollback':
                value.update(issued_at=iso(fixture.now - 2), expires_at=iso(fixture.now + 898))
            else:
                value['seeds'][0]['join_url'] = 'https://telemost.yandex.ru/j/synthetic-conflict'
            pending = port.path.with_name('publisher-fault')
            pending.write_bytes(store.encode(value))
            os.chown(pending, port.expected['uid'], port.expected['gid'])
            pending.chmod(port.expected['mode'])
            original(pending, port.path)
        changed.append((port.path.read_bytes(), store.metadata(port.path.stat())))
    monkeypatch.setattr(os, 'replace', replacement)
    with pytest.raises(maintenance.MaintenanceError, match='MAINTENANCE_ROLLED_BACK'):
        fixture.maintenance_operation.execute(fixture.request)
    assert fixture.store.read() == fixture.before
    assert store.metadata(fixture.locator.profile.stat()) == fixture.locator.profile_metadata
    port = fixture.locator.directory_port
    assert (port.path.read_bytes(), store.metadata(port.path.stat())) == changed[-1]
    journal = json.loads((fixture.maintenance_operation.root / 'journal.json').read_bytes())['journal']
    assert journal['state'] == 'ROLLED_BACK' and journal['attempt_count'] == 1
    with pytest.raises(maintenance.MaintenanceError):
        fixture.maintenance_operation.execute(fixture.request)
    assert fixture.store.read() == fixture.before


def test_bounded_maintenance_and_renewal_share_one_lock(canonical_maintenance):
    fixture = canonical_maintenance
    other = store.ProfileStore(fixture.locator, clock=lambda: fixture.now)
    with other.lock():
        with pytest.raises(maintenance.MaintenanceError, match='MAINTENANCE_PRECONDITION_CHANGED'):
            fixture.maintenance_operation.execute(fixture.request)
    assert not fixture.maintenance_operation.root.exists()
    transaction(fixture, 'credential_renewal', fixture.before)
    with pytest.raises(maintenance.MaintenanceError, match='MAINTENANCE_PRECONDITION_CHANGED'):
        fixture.maintenance_operation.execute(fixture.request)
    assert not fixture.maintenance_operation.root.exists()


@pytest.mark.parametrize('target,flags,allowed', [('parent', 0x81000, True), ('profile', 0x81000, False),
    ('profile', 0x80000, True), ('parent', 0x80010, False), ('profile', 0x80020, False), ('parent', 0x80080, False)])
def test_structural_index_flag_only_allowed_for_directories(canonical, monkeypatch, target, flags, allowed):
    path = canonical.locator.profile.parent if target == 'parent' else canonical.locator.profile
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    def ioctl(descriptor, request, buffer, mutate):
        buffer[:] = flags.to_bytes(len(buffer), sys.byteorder)
    monkeypatch.setattr(store.fcntl, 'ioctl', ioctl)
    try:
        if allowed:
            store.extended_metadata(descriptor)
        else:
            with pytest.raises(store.ProfileError, match='EXTENDED_METADATA_UNSUPPORTED'):
                store.extended_metadata(descriptor)
    finally:
        os.close(descriptor)


@pytest.mark.parametrize('case', ['valid', 'missing', 'unknown', 'duplicate', 'nonfinite', 'mode', 'owner',
                                 'locator_hash', 'locator_override', 'package_hash', 'operation', 'lock_missing'])
def test_canonical_maintenance_fixed_configuration(canonical_maintenance, monkeypatch, case):
    fixture = canonical_maintenance
    key = private_file(fixture.root / 'journal.key', fixture.maintenance_config.journal_key)
    package = private_file(fixture.root / 'bound.pyz', b'synthetic immutable package')
    package.chmod(0o400)
    value = dict(schema=2, profile_locator=str(fixture.fixed_locator),
                 profile_locator_sha256=store.digest(fixture.fixed_locator.read_bytes()), journal_key=str(key),
                 package_sha256=store.digest(package.read_bytes()), operation_id=fixture.permit['operation_id'])
    if case == 'missing':
        del value['profile_locator']
    elif case == 'unknown':
        value['profile'] = str(fixture.profile)
    elif case == 'locator_hash':
        value['profile_locator_sha256'] = '0' * 64
    elif case == 'package_hash':
        value['package_sha256'] = '0' * 64
    elif case == 'operation':
        value['operation_id'] = 'restricted_maintenance_' + 'b' * 32
    elif case == 'locator_override':
        monkeypatch.setenv('PROFILE_LOCATOR', str(fixture.profile))
    elif case == 'lock_missing':
        fixture.locator.lock.unlink()
    raw = store.encode(value)
    if case == 'duplicate':
        raw = b'{"schema":2,' + raw[1:]
    elif case == 'nonfinite':
        raw = raw.replace(b'"schema":2', b'"schema":NaN')
    config = private_file(fixture.root / 'canonical-fixed.json', raw)
    monkeypatch.setattr(maintenance, 'CONFIGURATION_PATH', config)
    if case == 'mode':
        config.chmod(0o644)
    elif case == 'owner':
        os.chown(config, 41001, 41002)
    if case in ('valid', 'locator_override'):
        loaded = maintenance.load_configuration(fixture.permit, package)
        assert loaded.contract() == fixture.maintenance_config.contract()
        assert loaded.profile == fixture.locator.profile and loaded.sync_lock == fixture.locator.lock
        assert maintenance.Operation(loaded, fixture.permit, clock=lambda: fixture.now).execute(fixture.request)['result'] == 'PASS'
    else:
        with pytest.raises(maintenance.MaintenanceError):
            maintenance.load_configuration(fixture.permit, package)


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


@pytest.fixture
def renewal(canonical, tmp_path):
    from test_activated_maintenance import Cluster
    root = tmp_path / 'renewal'
    root.mkdir(mode=0o700)
    cluster = Cluster(root)
    node = cluster.nodes['NL']
    canonical.locator.profile.write_bytes(node.read('gateway.json')[0])
    node.profile_store = store.ProfileStore(canonical.locator, clock=cluster.clock)
    publisher = canonical.locator.directory_port.path
    def publish(raw):
        pending = publisher.with_name('publisher-rotation')
        pending.write_bytes(raw)
        pending.chmod(0o600)
        os.chown(pending, 41001, 41002)
        os.replace(pending, publisher)
    original_resume = node.barrier.resume
    def resume(**arguments):
        original_resume(**arguments)
        publish((node.live / 'directory.json').read_bytes())
    node.barrier.resume = resume
    cluster.now += 12000
    value = json.loads((node.live / 'directory.json').read_bytes())
    value.update(issued_at=iso(cluster.now - 1), expires_at=iso(cluster.now + 3599))
    publish(store.encode(value))
    canonical.cluster = cluster
    canonical.node = node
    canonical.before = node.profile_store.read()
    return canonical


def test_accepted_renewal_source_uses_canonical_profile_and_journal(renewal):
    node = renewal.node
    old_path = node.live / 'gateway.json'
    old_raw = old_path.read_bytes()
    result = renewal.cluster.scheduled('canonical')
    assert result['result'] == 'COMMITTED', result
    profile = json.loads(node.profile_store.read())
    assert profile['minimum_crl'] == 2
    assert profile['revocations'] == renewal.cluster.snapshot()['crl']
    assert old_path.read_bytes() == old_raw
    assert node.read('gateway.json')[1] == renewal.locator.profile_metadata
    operation = 'test-renewal-operation-canonical'
    assert not (node.state / 'owner.json').exists()
    assert json.loads((node.state / 'completed.json').read_bytes())[operation]['result'] == 'CLEANED'
    assert json.loads((node.state / 'archive' / operation / 'files.json').read_bytes())['gateway.json']['mode'] == 0o640
    assert node.public_gateway()['minimum_crl'] == 2
    stable = node.profile_store.read()
    assert renewal.cluster.scheduled('canonical')['result'] == 'NOOP'
    assert node.profile_store.read() == stable


def test_renewal_promotion_holds_shared_maintenance_lock(renewal):
    observations = []
    competitor = store.ProfileStore(renewal.locator, clock=renewal.cluster.clock)
    def probe(stage):
        if stage == 'before-rename-gateway.json':
            with pytest.raises(store.ProfileError, match='PROFILE_TRANSACTION_BUSY'):
                with competitor.lock():
                    pytest.fail('Maintenance interleaved with renewal promotion')
            observations.append(stage)
    renewal.node.fault = probe
    result = renewal.cluster.scheduled('locked')
    assert result['result'] == 'COMMITTED', result
    assert observations == ['before-rename-gateway.json']
    with pytest.raises(store.ProfileError, match='PROFILE_CAS_FAILED'):
        competitor.transact('stale_maintenance_01', 'reconcile_current_floor',
            expected_sha256=store.digest(renewal.before), permit=lambda: None, persist=lambda *args: None)


def test_canonical_renewal_rollback_exact_bytes_and_metadata(renewal):
    before = renewal.node.profile_store.read()
    def fail(stage):
        if stage == 'after-rename-gateway.json':
            raise RuntimeError('synthetic post-rename failure')
    renewal.node.fault = fail
    result = renewal.cluster.scheduled('rollback')
    assert result['result'] == 'ABORTED', result
    assert renewal.node.profile_store.read() == before
    assert store.metadata(renewal.locator.profile.stat()) == renewal.locator.profile_metadata
    assert not (renewal.node.state / 'owner.json').exists()
    assert json.loads((renewal.node.state / 'completed.json').read_bytes())['test-renewal-operation-rollback']['result'] == 'CLEANED'


def test_canonical_renewal_promote_replay_preserves_exact_target(renewal):
    def interrupt(stage):
        if stage == 'NL_PROMOTED':
            raise KeyboardInterrupt()
    renewal.cluster.controller.fault = interrupt
    with pytest.raises(KeyboardInterrupt):
        renewal.cluster.scheduled('replay')
    target = renewal.node.profile_store.read()
    operation = 'test-renewal-operation-replay'
    first = renewal.node.readback(operation)
    assert renewal.node.promote(operation) == first
    assert renewal.node.profile_store.read() == target
    renewal.cluster.controller.fault = lambda stage: None
    assert renewal.cluster.scheduled('recover')['result'] == 'ABORTED'
    assert renewal.node.profile_store.read() == renewal.before
