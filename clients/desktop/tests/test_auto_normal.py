import copy
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import sys
from dataclasses import replace
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'clients/linux'))
import auto_normal
import auto_normal_worker as worker
from auto_guard import policy
from auto_policy import Context, Failure
from auto_configuration import verified
from test_auto_configuration import response, PRIVATE


@pytest.fixture
def state(tmp_path, monkeypatch):
    configuration = verified(response(), 1, 'nl', PRIVATE)
    configuration = replace(configuration, awg=configuration.awg.replace('192.0.2.1', '8.8.8.8'),
                            tcp=configuration.tcp.replace('192.0.2.1', '8.8.8.8'))
    directory = tmp_path / 'owner'
    directory.mkdir(mode=0o700)
    links, calls = [], []

    def read(path):
        return json.loads(path.read_bytes())

    def write(path, value):
        path.write_text(json.dumps(value))
        path.chmod(0o600)

    for module in (auto_normal, worker):
        monkeypatch.setattr(module, 'private_read', read)
    monkeypatch.setattr(auto_normal, 'private_write', write)
    guard = SimpleNamespace(directory=directory, uid=1000, generation='a'*32, lock=None,
        record=dict(schema=1, uid=1000, generation='a'*32, current=policy(), pending=None),
        _owned=lambda: None, snapshot=lambda: None, system=SimpleNamespace(links=lambda: copy.deepcopy(links)))

    def runner(operation, profile, context):
        context.check()
        calls.append((operation, profile))
        if operation == 'up':
            links[:] = [dict(ifname=guard.record['current']['selected']['interface'], ifindex=7,
                            flags=['UP'], linkinfo=dict(info_kind='tun'))]
        elif operation == 'down':
            links.clear()

    current = auto_normal.NormalCandidate(guard, runner)
    return current, guard, configuration, links, calls


@pytest.mark.parametrize('kind', ['awg', 'tcp'])
def test_single_attempt_drives_helper_contract_and_durable_nonsecret_intent(state, kind):
    current, guard, configuration, links, calls = state
    selected = current.prepare(configuration, kind, Context(20000))
    raw = current.path.read_text()
    assert 'PrivateKey' not in raw and 'tcp_id' not in raw and 'profile' not in raw
    assert not calls
    guard.record['current'] = policy('probe', selected)
    assert current.open(Context(20000)) == (7, False)
    assert [item[0] for item in calls] == ['install', 'up'] and current.profile is None
    guard.record['current'] = policy('ready', selected, 7)
    assert current.health(Context(10000))
    guard.record['current'] = policy(selected=selected)
    current.close(Context(20000))
    current.release(Context(20000))
    assert not links and not current.path.exists() and current.record is None
    assert [item[0] for item in calls] == ['install', 'up', 'health', 'down', 'forget']


def test_pending_cleanup_cannot_be_overwritten_or_released(state):
    current, guard, configuration, links, calls = state
    selected = current.prepare(configuration, 'tcp', Context(20000))
    before = current.path.read_bytes()
    with pytest.raises((Failure, ValueError)):
        current.prepare(configuration, 'awg', Context(20000))
    with pytest.raises((Failure, ValueError)):
        current.release(Context(20000))
    assert current.path.read_bytes() == before and not calls


@pytest.mark.parametrize('failure', ['cancel', 'deadline', 'wrong-plan', 'not-ready', 'wrong-kind'])
def test_failed_open_never_returns_connected_and_keeps_cleanup_intent(state, failure):
    current, guard, configuration, links, calls = state
    selected = current.prepare(configuration, 'awg', Context(20000))
    guard.record['current'] = policy('probe', selected)
    context = Context(20000)
    if failure == 'cancel':
        context.cancel.set()
    elif failure == 'deadline':
        context.deadline = 0
    elif failure == 'wrong-plan':
        guard.record['current'] = policy()
    else:
        original = current.runner
        def runner(operation, profile, context):
            original(operation, profile, context)
            if operation == 'up':
                links[0]['flags' if failure == 'not-ready' else 'linkinfo'] = [] if failure == 'not-ready' else dict(info_kind='bridge')
        current.runner = runner
    with pytest.raises((Failure, ValueError)):
        current.open(context)
    assert current.path.exists()
    guard.record['current'] = policy(selected=selected)
    current.close(Context(20000))
    assert not current.path.exists()


def test_failed_cleanup_retains_journal_and_crash_reconciler_uses_same_identity(state):
    current, guard, configuration, links, calls = state
    selected = current.prepare(configuration, 'tcp', Context(20000))
    original = current.runner
    def broken(operation, profile, context):
        if operation == 'down':
            raise Failure()
    current.runner = broken
    with pytest.raises(Failure):
        current.close(Context(20000))
    assert current.path.exists() and current.profile is None
    replacement = auto_normal.NormalCandidate(guard, original)
    replacement.close(Context(20000))
    assert not current.path.exists() and [item[0] for item in calls] == ['down', 'forget']


@pytest.fixture(params=['awg', 'tcp'])
def existing_helper(state, request, tmp_path, monkeypatch):
    current, guard, configuration, links, calls = state
    kind = request.param
    selected = current.prepare(configuration, kind, Context(20000))
    guard.record['current'] = policy('probe', selected)
    spec = importlib.util.spec_from_file_location('test_auto_existing_'+kind, ROOT / ('clients/linux/'+kind+'-helper.py'))
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    helper.ROOT = tmp_path / kind
    helper.ROOT.mkdir()
    helper.RUN = tmp_path / 'tcp-run'
    helper.RUN.mkdir(exist_ok=True)
    monkeypatch.setattr(worker, 'trusted', lambda *args: None)
    monkeypatch.setattr(helper, 'read', lambda path, private=False: path.read_text())
    def write(path, text, mode):
        path.write_text(text)
        path.chmod(mode)
    monkeypatch.setattr(helper, 'write', write)
    if kind == 'awg':
        monkeypatch.setattr(helper, 'supports_awg31', lambda: True)
    operations = []
    monkeypatch.setattr(helper, 'execute', lambda: operations.append(tuple(sys.argv)))
    monkeypatch.setattr(helper, 'probe_interface', lambda *args: operations.append(('health', *args)))
    if kind == 'awg':
        monkeypatch.setattr(helper, 'healthy', lambda *args: operations.append(('health', *args)))
    lease = SimpleNamespace(record=guard.record, normal=current.record, _owned=lambda: None)
    return current, guard, configuration, helper, lease, operations


def test_fixed_helper_keeps_original_parser_and_root_profile_layout(existing_helper):
    current, guard, configuration, helper, lease, operations = existing_helper
    selected = current.record['selected']
    request = dict(schema=1, operation='install', profile=current.profile)
    worker.execute(lease, request, helper)
    path = helper.ROOT / (selected['interface']+'.conf')
    assert path.stat().st_mode & 0o777 == 0o600
    worker.execute(lease, dict(schema=1, operation='up', profile=''), helper)
    assert operations[-1] == ('helper', 'up', selected['interface'])
    guard.record['current'] = policy('ready', selected, 7)
    worker.execute(lease, dict(schema=1, operation='health', profile=''), helper)
    guard.record['current'] = policy(selected=selected)
    worker.execute(lease, dict(schema=1, operation='down', profile=''), helper)
    assert operations[-1] == ('helper', 'down', selected['interface'])
    worker.execute(lease, dict(schema=1, operation='forget', profile=''), helper)
    assert not list(helper.ROOT.iterdir())


@pytest.mark.parametrize('corruption', ['owner', 'generation', 'endpoint', 'orphan-config'])
def test_worker_never_removes_foreign_profiles(existing_helper, corruption):
    current, guard, configuration, helper, lease, operations = existing_helper
    identifier = current.record['selected']['interface']
    metadata = worker.expected_metadata(lease)
    if corruption != 'orphan-config':
        key = {'owner': 'owner', 'generation': 'auto_generation', 'endpoint': 'endpoint'}[corruption]
        metadata[key] = 'foreign'
        (helper.ROOT / (identifier+'.json')).write_text(json.dumps(metadata))
    (helper.ROOT / (identifier+'.conf')).write_text('foreign private contents')
    guard.record['current'] = policy(selected=current.record['selected'])
    with pytest.raises((Failure, ValueError)):
        worker.execute(lease, dict(schema=1, operation='forget', profile=''), helper)
    assert (helper.ROOT / (identifier+'.conf')).read_text() == 'foreign private contents' and not operations


@pytest.mark.parametrize('bad', [dict(schema=1, operation='exec', profile=''), dict(schema=True, operation='up', profile=''),
    dict(schema=1, operation='up', profile='', command='/bin/sh'), dict(schema=1, operation='up', profile='secret'),
    dict(schema=1, operation='install', profile='PostUp = /bin/sh')])
def test_worker_rejects_commands_unknown_keys_and_unsafe_profiles(existing_helper, bad):
    current, guard, configuration, helper, lease, operations = existing_helper
    with pytest.raises((Failure, ValueError)):
        worker.execute(lease, bad, helper)
    assert not list(helper.ROOT.iterdir()) and not operations


def test_partial_install_claim_is_cleaned_only_when_no_interface_exists(existing_helper):
    current, guard, configuration, helper, lease, operations = existing_helper
    metadata = helper.ROOT / (current.record['selected']['interface']+'.json')
    metadata.write_text(json.dumps(worker.expected_metadata(lease)))
    guard.record['current'] = policy(selected=current.record['selected'])
    worker.execute(lease, dict(schema=1, operation='down', profile=''), helper)
    worker.execute(lease, dict(schema=1, operation='forget', profile=''), helper)
    assert not metadata.exists() and not operations


@pytest.mark.parametrize('claim', [True, False])
def test_interrupted_atomic_writes_remove_only_generation_owned_temporary_files(existing_helper, claim):
    current, guard, configuration, helper, lease, operations = existing_helper
    identifier = current.record['selected']['interface']
    metadata, path = helper.ROOT / (identifier+'.json'), helper.ROOT / (identifier+'.conf')
    if claim:
        metadata.write_text(json.dumps(worker.expected_metadata(lease)))
    owned = [worker.temporary_path(lease, target) for target in (path, metadata)]
    for target in owned:
        target.write_text('synthetic interrupted write')
    foreign = helper.ROOT / '.other-profile'
    foreign.write_text('untouched')
    guard.record['current'] = policy(selected=current.record['selected'])
    worker.execute(lease, dict(schema=1, operation='down', profile=''), helper)
    worker.execute(lease, dict(schema=1, operation='forget', profile=''), helper)
    assert not metadata.exists() and all(not target.exists() for target in owned)
    assert foreign.read_text() == 'untouched' and not operations


@pytest.mark.parametrize('lock_state', ['held', 'unheld', 'wrong-fd', 'independent-fd'])
def test_private_helper_requires_the_actual_inherited_lock_description(state, monkeypatch, lock_state):
    current, guard, configuration, links, calls = state
    current.prepare(configuration, 'tcp', Context(20000))
    (guard.directory / 'guard.json').write_text(json.dumps(guard.record))
    descriptor = os.open(guard.directory / 'lock', os.O_RDWR | os.O_CREAT, 0o600)
    other = None
    monkeypatch.setattr(worker, 'DIRECTORY', guard.directory)
    monkeypatch.setattr(worker.os, 'geteuid', lambda: 0)
    monkeypatch.setattr(worker, 'trusted', lambda path, directory=False: path.lstat())
    try:
        if lock_state != 'unheld':
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        passed = descriptor
        if lock_state in ('wrong-fd', 'independent-fd'):
            other = os.open(guard.directory / ('lock' if lock_state == 'independent-fd' else 'other'), os.O_RDWR | os.O_CREAT, 0o600)
            passed = other
        if lock_state == 'held':
            lease = worker.Lease(passed)
            assert lease.normal == current.record
        else:
            with pytest.raises((Failure, ValueError, BlockingIOError)):
                worker.Lease(passed)
    finally:
        os.close(descriptor)
        if other is not None:
            os.close(other)


def test_helper_deadline_drains_process_and_preserves_parent_lease(state, monkeypatch, tmp_path):
    current, guard, configuration, links, calls = state
    script = tmp_path / 'slow_helper.py'
    script.write_text('import time\ntime.sleep(60)\n')
    monkeypatch.setattr(auto_normal, 'WORKER', script)
    descriptor = os.open(guard.directory / 'lock', os.O_RDWR | os.O_CREAT, 0o600)
    guard.lock = descriptor
    processes = []
    original = auto_normal.subprocess.Popen
    def start(*args, **kwargs):
        process = original(*args, **kwargs)
        processes.append(process)
        return process
    monkeypatch.setattr(auto_normal.subprocess, 'Popen', start)
    try:
        with pytest.raises(Failure, match='NETWORK'):
            auto_normal.HelperRunner(guard)('up', '', Context(100))
        assert len(processes) == 1 and processes[0].poll() is not None
        assert processes[0].stdin.closed and os.fstat(descriptor).st_nlink == 1
    finally:
        os.close(descriptor)


@pytest.mark.parametrize('manual_kind', ['awg', 'tcp', 'mesh'])
@pytest.mark.parametrize('journal', ['guard.json', 'normal.json', 'awg'])
def test_existing_manual_starts_refuse_auto_ownership_without_a_root_lease(tmp_path, monkeypatch, manual_kind, journal):
    import backend
    original_open, original_stat = os.open, os.fstat
    original_exists = os.path.lexists
    descriptors = set()
    def opened(path, flags, *args, **kwargs):
        if path == '/run/family-connect-transport.lock':
            descriptor = original_open(tmp_path / 'transport.lock', flags, *args, **kwargs)
            descriptors.add(descriptor)
            return descriptor
        return original_open(path, flags, *args, **kwargs)
    def info(descriptor):
        value = original_stat(descriptor)
        if descriptor in descriptors:
            return SimpleNamespace(st_mode=value.st_mode, st_uid=0, st_nlink=1)
        return value
    monkeypatch.setattr(backend.os, 'open', opened)
    monkeypatch.setattr(backend.os, 'fstat', info)
    monkeypatch.setattr(backend.os, 'geteuid', lambda: 0)
    pending = '/run/family-connect-awg/active.json' if journal == 'awg' else '/run/family-connect-auto/'+journal
    monkeypatch.setattr(backend.os.path, 'lexists', lambda path: True if path == pending else original_exists(path))
    if journal == 'awg' and manual_kind == 'awg':
        with backend.privileged_transport_start(manual_kind):
            pass
        return
    with pytest.raises(backend.BackendError, match='Disconnect '+('AWG' if journal == 'awg' else 'Auto')):
        with backend.privileged_transport_start(manual_kind):
            pytest.fail('A manual transport must not overlap Auto')
