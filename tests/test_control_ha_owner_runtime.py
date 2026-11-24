import base64
from copy import deepcopy
import fcntl
import json
import os
from pathlib import Path
import signal
import sqlite3
import subprocess
import sys
import time

import pytest

from control.friends.access import Access
from control.friends import paid_beta, pseudonyms
from scripts import control_ha_owner_capture as capture
from scripts import control_ha_owner_runtime as runtime
from scripts.control_ha_installed_inventory import Refused


@pytest.fixture
def source(tmp_path):
    root = tmp_path / 'synthetic'
    root.mkdir(mode=0o700)
    access = Access(root / 'registry.sqlite3')
    access.initialize()
    with access.db() as database:
        paid_beta.migrate(database)
        database.execute('CREATE TABLE control_plane_fixture(singleton INTEGER PRIMARY KEY, version TEXT NOT NULL)')
        database.execute('INSERT INTO control_plane_fixture VALUES (1,?)', ('CONTROL-PLANE-1-SYNTHETIC-v2',))
        database.execute('CREATE TABLE control_plane_devices(device TEXT PRIMARY KEY REFERENCES devices(device), label TEXT NOT NULL)')
        for number in range(50):
            device = f'{number:032x}'
            database.execute('INSERT INTO devices VALUES (?,?,?,?,0)', (device, str(number), str(number), str(number)))
            database.execute('INSERT INTO control_plane_devices VALUES (?,?)', (device, 'Fixture ' + str(number)))
    (root / 'seed.lock').touch(mode=0o644)
    key = b'k' * 32
    aliases = dict(schema='fc-pseudonym-aliases-v1', generation=2,
                   key_check=pseudonyms.key_check(key, 2), entities=dict(device=[], panel_event=[]))
    alias_path = tmp_path / 'aliases.json'
    alias_path.write_bytes(capture.encoded(aliases))
    return root, alias_path


@pytest.fixture
def bundle(source):
    started = time.time_ns()
    snapshot = capture.capture(*source)
    files = {name: b'opaque compose retained, never executed' for name in runtime.FILES - snapshot['files'].keys()}
    password, secret = 'p' * 40, 's' * 64
    environments = {
        'console': dict(CONTROL_PLANE_MODE='synthetic', DJANGO_SECRET_KEY=secret, POSTGRES_PASSWORD=password),
        'postgres': dict(POSTGRES_PASSWORD=password),
        'system_publisher': dict(CONTROL_PLANE_MODE='synthetic', DJANGO_SECRET_KEY=secret,
                                 POSTGRES_PASSWORD=password, FC_SYSTEM_PUBLISHER_ORIGIN='https://example.test'),
    }
    files['containers.json'] = capture.encoded({role: dict(name=f'/fc-control-plane-0-{role}-1', id='a' * 64,
        image=image, started='2026-01-01T00:00:00Z', environment=[name + '=' + value for name, value in environments[role].items()],
        command=['not', 'executed'], entrypoint=None, mounts=[], labels={}) for role, image in runtime.IMAGES.items()})
    files['env-original'] = files['env-runtime'] = (
        f'CONTROL_PLANE_MODE=synthetic\nDJANGO_SECRET_KEY={secret}\nPOSTGRES_PASSWORD={password}\n').encode()
    files['inventory-hmac.key'] = b'k' * 32
    files['collector-aliases.json'] = source[1].read_bytes()
    files['publisher.token'] = b'a' * 64 + b'\n'
    for name in ('subscriptions-source.json', 'technical-metadata-source.json'):
        files[name] = capture.encoded(dict(python='/usr/bin/python3', archive='/opt/apps/family_connect/http.pyz', archive_sha256='a' * 64))
    files['transport-source.json'] = b'{"archives":{}}'
    files['origins.json'] = capture.encoded({name: '/fixture/' + name for name in runtime.FILES - {'origins.json'}})
    return runtime.build(snapshot, files, started, time.time_ns())


def test_private_roundtrip_and_closed_synthetic_schema(bundle, source, tmp_path):
    before = (source[0] / 'registry.sqlite3').read_bytes()
    summary = runtime.validate(bundle)
    assert summary['tables']['devices']['count'] == 50
    assert len(summary['tables']) == 9 and summary['files'] == 20
    key = os.urandom(32)
    capsule, pin = runtime.seal(bundle, key)
    assert b'p' * 40 not in capsule and b's' * 64 not in capsule
    value = runtime.unseal(capsule, key, pin)
    assert runtime.restore(value, tmp_path / 'restored') == summary
    assert (source[0] / 'registry.sqlite3').read_bytes() == before
    assert all(path.stat().st_mode & 0o777 == 0o600 for path in (tmp_path / 'restored').iterdir())
    assert signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0)


@pytest.mark.parametrize('lock', ('seed', 'database'))
def test_capture_never_waits_and_releases_locks(source, lock):
    if lock == 'seed':
        with (source[0] / 'seed.lock').open('rb') as stream:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            with pytest.raises(BlockingIOError):
                capture.capture(*source)
    else:
        database = sqlite3.connect(source[0] / 'registry.sqlite3', isolation_level=None)
        database.execute('BEGIN IMMEDIATE')
        try:
            with pytest.raises(sqlite3.OperationalError, match='locked'):
                capture.capture(*source)
        finally:
            database.rollback(); database.close()
    assert signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0)
    assert capture.capture(*source)['pg_pair_fence'] is False


@pytest.mark.parametrize('change', ('sidecar', 'schema', 'link', 'missing_lock', 'public_store'))
def test_unsafe_source_refused(source, change):
    root, aliases = source
    if change == 'sidecar':
        (root / 'registry.sqlite3-journal').touch()
    elif change == 'schema':
        with sqlite3.connect(root / 'registry.sqlite3') as database:
            database.execute('CREATE TABLE unknown(secret)')
    elif change == 'link':
        os.link(root / 'registry.sqlite3', root / 'alias')
    elif change == 'missing_lock':
        (root / 'seed.lock').unlink()
    else:
        (root / 'registry.sqlite3').chmod(0o644)
    with pytest.raises((ValueError, OSError)):
        capture.capture(*source)
    assert signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0)


@pytest.mark.parametrize('change', ('extra', 'missing', 'path', 'schema', 'fixture', 'foreign_key', 'key',
    'aliases', 'image', 'password', 'env', 'token', 'config', 'origins', 'duplicates', 'fence', 'deadline', 'interval'))
def test_invalid_or_expanded_authority_refused(bundle, change):
    value = deepcopy(bundle)
    files = runtime.unpack(value)
    if change in ('extra', 'path'):
        files['observations.json' if change == 'extra' else '../escape'] = b'{}'
    elif change == 'missing':
        del files['synthetic.sqlite']
    elif change in ('schema', 'fixture', 'foreign_key'):
        database = sqlite3.connect(':memory:')
        database.deserialize(files['synthetic.sqlite'])
        if change == 'schema': database.execute('CREATE TABLE observations(private)')
        elif change == 'fixture': database.execute("UPDATE control_plane_fixture SET version='old'")
        else: database.execute('DELETE FROM devices')
        database.commit(); files['synthetic.sqlite'] = database.serialize(); database.close()
    elif change == 'key': files['inventory-hmac.key'] = b'x' * 32
    elif change == 'aliases': files['panel-aliases.json'] = b'{}'
    elif change in ('image', 'password'):
        containers = json.loads(files['containers.json'])
        if change == 'image': containers['console']['image'] = 'sha256:' + 'b' * 64
        else: containers['console']['environment'].append('POSTGRES_PASSWORD=wrong')
        files['containers.json'] = capture.encoded(containers)
    elif change == 'env': files['env-runtime'] += b'UNEXPECTED=1\n'
    elif change == 'token': files['publisher.token'] = b'not-a-token'
    elif change == 'config': files['technical-metadata-source.json'] = b'{"observations":[]}'
    elif change == 'origins': files['origins.json'] = b'{}'
    elif change == 'duplicates': files['transport-source.json'] = b'{"archives":{},"archives":{}}'
    elif change == 'fence': value['pg_pair_fence'] = True
    elif change == 'deadline': value['barrier_seconds'] = float('nan')
    else: value['started_at_ns'] = value['captured_at_ns'] + 1
    value['files'] = {name: base64.b64encode(raw).decode() for name, raw in files.items()}
    with pytest.raises((ValueError, Refused)):
        runtime.validate(value)


def test_checkpoint_and_key_and_existing_destination_refusal(bundle, tmp_path):
    key = os.urandom(32)
    capsule, pin = runtime.seal(bundle, key)
    newer, newer_pin = runtime.seal(bundle, key)
    for blob, secret, checkpoint in ((capsule, key, newer_pin), (capsule, os.urandom(32), pin),
            (capsule, key, dict(pin, document_sha256='0' * 64)), (capsule + b'x', key, pin)):
        with pytest.raises(ValueError): runtime.unseal(blob, secret, checkpoint)
    runtime.restore(bundle, tmp_path / 'existing')
    with pytest.raises(FileExistsError): runtime.restore(bundle, tmp_path / 'existing')
    assert runtime.unseal(newer, key, newer_pin) == bundle


def test_kernel_deadline_releases_source_locks(source):
    code = '''
import sys,time
from pathlib import Path
from scripts import control_ha_owner_capture as capture
original=capture.Reader.raw
def delayed(self,*args,**kwargs):
    time.sleep(5)
    return original(self,*args,**kwargs)
capture.Reader.raw=delayed
capture.capture(*(Path(value) for value in sys.argv[1:]))
'''
    process = subprocess.run([sys.executable, '-c', code, *map(str, source)], capture_output=True, timeout=3)
    assert process.returncode == -signal.SIGALRM
    assert capture.capture(*source)['activation'] is False


def test_native_command_has_no_original_mount_or_network(tmp_path):
    from scripts.control_ha_owner_qualify import command
    arguments = command(tmp_path, 'fc-ha-owner-test')
    assert arguments[arguments.index('--network') + 1] == 'none'
    assert arguments[arguments.index('--entrypoint') + 1:] == ['python', runtime.IMAGES['console'], '-B', '-']
    assert arguments[arguments.index('--cap-drop') + 1] == 'ALL'
    assert '--read-only' in arguments and '--privileged' not in arguments
    assert arguments.count('--mount') == 1
    assert arguments[arguments.index('--mount') + 1] == f'type=bind,source={tmp_path},destination=/app/control_plane/.local,readonly'
    assert not any('fc-control-plane-0_' in argument or 'docker.sock' in argument for argument in arguments)
    with pytest.raises(ValueError): command(tmp_path, 'fc-control-plane-0-console-1')


def test_collector_container_drift_refuses_before_file_access(monkeypatch):
    from scripts import control_ha_owner_collect as collect
    rows = [dict(Name=f'/fc-control-plane-0-{role}-1', Image=image, Id='a' * 64,
        State=dict(Running=True, StartedAt='unchanged'), Config=dict(Env=[], Cmd=[], Entrypoint=None, Labels={}),
        Mounts=[dict(Destination='/second'), dict(Destination='/first')]) for role, image in runtime.IMAGES.items()]
    reversed_rows = deepcopy(rows)
    for row in reversed_rows: row['Mounts'].reverse()
    assert collect.selected(rows) == collect.selected(reversed_rows)
    monkeypatch.setattr(collect, 'inspect', lambda: rows)
    changed = deepcopy(rows)
    changed[0]['State']['StartedAt'] = 'changed'
    with pytest.raises(ValueError, match='CHANGED_SINCE_PREFLIGHT'): collect.collect(changed)
    changed[0]['Image'] = 'sha256:' + 'b' * 64
    with pytest.raises(ValueError, match='CONTAINER_IMAGE'): collect.selected(changed)


def test_collector_stream_only_executes_selected_inmemory_probe(monkeypatch):
    from types import SimpleNamespace
    from scripts import control_ha_owner_collect as collect
    calls = []
    def run(arguments, **options):
        calls.append((arguments, options))
        return SimpleNamespace(returncode=0, stdout=b'{"probe":true}')
    monkeypatch.setattr(collect.subprocess, 'run', run)
    assert collect.streamed('a' * 64, 'print(json.dumps({"probe":True}))') == {'probe': True}
    arguments, options = calls[0]
    assert arguments == ['docker', 'exec', '-i', 'a' * 64, 'python', '-I', '-B', '-']
    assert options['timeout'] == 10
    assert b'setrlimit' in options['input'] and b'write_bytes' not in options['input']
