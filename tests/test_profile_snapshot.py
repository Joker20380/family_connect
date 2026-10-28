import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from control.friends import profile_snapshot as reader, profile_store as store
from test_profile_store import canonical, rotate
from test_restricted_maintenance import private_file, setup


@pytest.fixture
def snapshot_configuration(canonical, monkeypatch):
    fixture = canonical
    executable = fixture.locator.profile.parent / 'renewal-helper'
    private_file(executable, b'#!/bin/sh\nexit 0\n')
    os.chown(executable, 0, fixture.locator.reader_gid)
    executable.chmod(0o750)
    config = fixture.locator.profile.parent / 'snapshot-fixed.json'
    value = dict(schema=1, profile_locator=str(fixture.fixed_locator),
                 profile_locator_sha256=store.digest(fixture.fixed_locator.read_bytes()),
                 renewal_helper=str(executable), renewal_helper_sha256=store.digest(executable.read_bytes()),
                 renewal_helper_metadata=store.metadata(executable.stat()))
    private_file(config, store.encode(value))
    os.chown(config, 0, fixture.locator.reader_gid)
    config.chmod(0o640)
    monkeypatch.setattr(reader, 'CONFIGURATION_PATH', config)
    fixture.snapshot_config = config
    fixture.snapshot_value = value
    return fixture


def test_snapshot_response_exactly_matches_accepted_archive(snapshot_configuration):
    fixture = snapshot_configuration
    archive = os.environ.get('FC_TEST_SNAPSHOT_ARCHIVE')
    assert archive, 'Exact retained generic archive required'
    assert hashlib.sha256(Path(archive).read_bytes()).hexdigest() == '0120dad028ead353b8b83a600538f3e578b2b46ddf871bf16e97529f9449f450'
    probe = ('import sys;sys.path.insert(0,sys.argv[1]);from pathlib import Path;'
             'from control.friends.restricted_sync import gateway;'
             'sys.stdout.buffer.write(gateway(Path(sys.argv[2]),Path(sys.argv[3]),sys.stdin.buffer.read(),int(sys.argv[4])))')
    request = store.encode(reader.SNAPSHOT_REQUEST)
    expected = subprocess.run([sys.executable, '-I', '-B', '-c', probe, archive, str(fixture.profile),
                               str(fixture.directory), str(fixture.now)], input=request, capture_output=True, check=True)
    before = fixture.store.read(), fixture.locator.directory_port.path.read_bytes()
    code, response = reader.dispatch(reader.Configuration.load(), request, now=fixture.now,
                                     run=lambda *args, **kwargs: pytest.fail('Snapshot attempted subprocess'))
    assert code == 0 and response == expected.stdout and not expected.stderr
    assert b'synthetic-key-marker' not in response and b'private_key' not in response
    assert (fixture.store.read(), fixture.locator.directory_port.path.read_bytes()) == before


@pytest.mark.parametrize('payload', [b'{}', b'{"schema":true,"operation":"READ_ONLY_SECURITY_SNAPSHOT"}',
    b'{"schema":1,"schema":1,"operation":"READ_ONLY_SECURITY_SNAPSHOT"}',
    b'{"revocations":"payload"}', b'{"schema":1,"operation":"reconcile_current_floor"}',
    b'{"schema":1,"operation":"READ_ONLY_SECURITY_SNAPSHOT","profile":"override"}', b'x' * 1048577])
def test_snapshot_rejects_write_and_override_requests(snapshot_configuration, payload):
    fixture = snapshot_configuration
    before = fixture.store.read()
    with pytest.raises(store.ProfileError):
        reader.dispatch(reader.Configuration.load(), payload, now=fixture.now,
                        run=lambda *args, **kwargs: pytest.fail('Unexpected RPC'))
    assert fixture.store.read() == before


def test_snapshot_does_not_acquire_or_create_writer_lock(snapshot_configuration):
    fixture = snapshot_configuration
    fixture.locator.lock.unlink()
    fixture.locator.operations.rmdir()
    _, response = reader.dispatch(reader.Configuration.load(), store.encode(reader.SNAPSHOT_REQUEST), now=fixture.now)
    assert json.loads(response)['profile']['minimum_crl'] == 27088
    assert not fixture.locator.lock.exists() and not fixture.locator.operations.exists()


def test_snapshot_accepts_publisher_rotation_without_profile_write(snapshot_configuration):
    fixture = snapshot_configuration
    rotate(fixture)
    _, response = reader.dispatch(reader.Configuration.load(), store.encode(reader.SNAPSHOT_REQUEST), now=fixture.now)
    assert base64.b64decode(json.loads(response)['directory']) == fixture.locator.directory_port.path.read_bytes()
    assert fixture.store.read() == fixture.before


def test_snapshot_rejects_profile_change_during_read(snapshot_configuration, monkeypatch):
    fixture = snapshot_configuration
    original = store.DirectoryPort.snapshot
    def raced(port, profile, now, **kwargs):
        result = original(port, profile, now, **kwargs)
        fixture.locator.profile.write_bytes(store.floor_target(fixture.before, now))
        return result
    monkeypatch.setattr(store.DirectoryPort, 'snapshot', raced)
    with pytest.raises(store.ProfileError, match='PROFILE_CHANGED_DURING_READ'):
        reader.dispatch(reader.Configuration.load(), store.encode(reader.SNAPSHOT_REQUEST), now=fixture.now)


@pytest.mark.parametrize('case', ['locator_hash', 'helper_hash', 'helper_mode', 'unknown', 'mode', 'owner'])
def test_snapshot_fixed_configuration_fails_closed(snapshot_configuration, case):
    fixture = snapshot_configuration
    value = fixture.snapshot_value.copy()
    if case == 'locator_hash':
        value['profile_locator_sha256'] = '0' * 64
    elif case == 'helper_hash':
        value['renewal_helper_sha256'] = '0' * 64
    elif case == 'helper_mode':
        Path(value['renewal_helper']).chmod(0o770)
    elif case == 'unknown':
        value['profile'] = str(fixture.profile)
    fixture.snapshot_config.write_bytes(store.encode(value))
    if case == 'mode':
        fixture.snapshot_config.chmod(0o644)
    elif case == 'owner':
        os.chown(fixture.snapshot_config, 41001, 41002)
    with pytest.raises(store.ProfileError):
        reader.Configuration.load()


def test_snapshot_rpc_preserves_existing_bounded_envelope(snapshot_configuration, monkeypatch):
    fixture = snapshot_configuration
    seen = []
    payload = dict(schema=1, role='NL', action='inspect', operation_id='synthetic-renewal-operation',
                   expected_source_sha256='a' * 64, payload=None)
    def run(arguments, **kwargs):
        seen.append((arguments, kwargs))
        kwargs['stdout'].write(b'{"ok":true}')
        return SimpleNamespace(returncode=0)
    monkeypatch.setenv('PROFILE_LOCATOR', str(fixture.profile))
    monkeypatch.setenv('PYTHONPATH', '/synthetic-untrusted')
    config = reader.Configuration.load()
    code, response = reader.dispatch(config, store.encode(dict(schema=1, operation='CREDENTIAL_RENEWAL_RPC', request=payload)), run=run)
    assert code == 0 and response == b'{"ok":true}'
    arguments, kwargs = seen[0]
    assert arguments == ['/usr/bin/sudo', '-n', '--', str(config.helper)]
    assert kwargs['input'] == store.encode(payload) and kwargs['timeout'] == 120
    assert kwargs['env'] == {'PATH': '/usr/bin:/bin', 'LANG': 'C'}
    assert fixture.store.read() == fixture.before


@pytest.mark.parametrize('command', ['', 'sh', 'restricted-sync --profile override'])
def test_snapshot_main_preserves_exact_ssh_command(snapshot_configuration, monkeypatch, command):
    monkeypatch.setenv('SSH_ORIGINAL_COMMAND', command)
    assert reader.main([]) == 2


def test_snapshot_reader_group_cannot_write_profile_or_lock(snapshot_configuration):
    fixture = snapshot_configuration
    port = fixture.locator.directory_port
    readable = port.path.parent / 'publisher-contract'
    readable.write_bytes(b'synthetic publisher')
    readable.chmod(0o755)
    value = json.loads(fixture.fixed_locator.read_bytes())
    value['directory']['publisher_contract'] = [[str(readable), store.digest(readable.read_bytes()), store.metadata(readable.stat())]]
    fixture.fixed_locator.write_bytes(store.encode(value))
    config = fixture.snapshot_value.copy()
    config['profile_locator_sha256'] = store.digest(fixture.fixed_locator.read_bytes())
    fixture.snapshot_config.write_bytes(store.encode(config))
    child = os.fork()
    if child == 0:
        try:
            os.setgroups([41002, fixture.locator.reader_gid])
            os.setgid(41002)
            os.setuid(41001)
            code, response = reader.dispatch(reader.Configuration.load(), store.encode(reader.SNAPSHOT_REQUEST), now=fixture.now)
            assert code == 0 and json.loads(response)['profile']['family'] == 'a' * 32
            for path in (fixture.locator.profile, fixture.locator.lock):
                try:
                    descriptor = os.open(path, os.O_WRONLY | os.O_NOFOLLOW)
                except PermissionError:
                    continue
                os.close(descriptor)
                raise AssertionError('reader can write protected material')
        except BaseException:
            os._exit(1)
        os._exit(0)
    assert os.waitpid(child, 0)[1] == 0
