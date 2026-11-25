import copy
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import pytest

from scripts import control_ha_dispatcher_hold as hold


@pytest.fixture
def scheduler(tmp_path):
    script = tmp_path / 'cycle.py'
    script.write_text('import os,time\nfrom pathlib import Path\n'
                      'Path("started").write_text(str(os.getpid()))\n'
                      'time.sleep(0.25)\n'
                      'with open("commits", "a") as stream: stream.write("committed\\n")\n')
    command = ['sh', '-ec', 'while :; do ' + sys.executable + ' cycle.py; sleep 0.1; done']
    child = subprocess.Popen(command, cwd=tmp_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             start_new_session=True)
    deadline = time.monotonic() + 3
    while not (tmp_path / 'started').exists():
        assert child.poll() is None and time.monotonic() < deadline
        time.sleep(0.01)
    binding, _ = hold.process(child.pid)
    try:
        yield child, binding, tmp_path
    finally:
        try:
            os.killpg(child.pid, signal.SIGCONT)
            os.killpg(child.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        child.wait(timeout=3)


def lines(root):
    path = root / 'commits'
    return len(path.read_text().splitlines()) if path.exists() else 0


def resumed(child, root, previous):
    deadline = time.monotonic() + 3
    while lines(root) <= previous:
        assert child.poll() is None and time.monotonic() < deadline
        time.sleep(0.01)


def test_inflight_child_finishes_without_new_dispatch(scheduler):
    child, binding, root = scheduler
    with hold.Hold(binding, seconds=2, lock_root=root / 'locks') as lease:
        time.sleep(0.4)
        completed = lines(root)
        assert completed == 1
        time.sleep(0.2)
        assert lines(root) == completed
        lease.check()
    assert lease.statuses == [0, 0]
    assert hold.process(child.pid)[0] == binding
    resumed(child, root, completed)


@pytest.mark.parametrize('failure', ['raise', 'guardian-killed', 'rescue-killed', 'guardian-frozen', 'deadline'])
def test_abort_and_independent_resume(scheduler, failure):
    child, binding, root = scheduler
    lease = hold.Hold(binding, seconds=0.7, lock_root=root / 'locks')
    with pytest.raises((RuntimeError, ValueError)):
        with lease:
            if failure == 'raise':
                raise RuntimeError('synthetic abort')
            if failure == 'guardian-killed':
                os.kill(lease.children[0][0], signal.SIGKILL)
            if failure == 'rescue-killed':
                os.kill(lease.children[1][0], signal.SIGKILL)
            if failure == 'guardian-frozen':
                os.kill(lease.children[0][0], signal.SIGSTOP)
            time.sleep(0.85)
            lease.check()
    assert hold.process(child.pid)[1] not in ('T', 't')
    resumed(child, root, lines(root))
    assert not lease.descriptors and not lease.children


def test_coordinator_sigkill_closes_lease(scheduler):
    child, binding, root = scheduler
    helper = '''import json,sys,time
from scripts.control_ha_dispatcher_hold import Hold
with Hold(json.loads(sys.argv[1]), seconds=2, lock_root=sys.argv[2]) as held:
    print(json.dumps([child for child, descriptor in held.children]), flush=True)
    time.sleep(10)
'''
    coordinator = subprocess.Popen([sys.executable, '-c', helper, json.dumps(binding), str(root / 'locks')],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        assert hold.ready(coordinator.stdout, 3)
        children = json.loads(coordinator.stdout.readline())
        descriptors = [os.pidfd_open(pid) for pid in children]
        coordinator.kill()
        coordinator.wait(timeout=3)
        assert coordinator.returncode == -signal.SIGKILL
        for descriptor in descriptors:
            assert hold.ready(descriptor, 3)
            os.close(descriptor)
        resumed(child, root, lines(root))
        assert hold.process(child.pid)[1] not in ('T', 't')
        with hold.Hold(binding, seconds=1, lock_root=root / 'locks') as retry:
            retry.check()
    finally:
        if coordinator.poll() is None:
            coordinator.kill()
            coordinator.wait(timeout=3)
        coordinator.stdout.close()
        coordinator.stderr.close()


@pytest.mark.parametrize('field,value', [('start', 1), ('parent', 1), ('uid', [-1] * 4), ('threads', 2),
                                       ('command_sha256', '0' * 64), ('pid_namespace', 'pid:[0]'),
                                       ('cgroup_sha256', '0' * 64)])
def test_changed_binding_refuses_before_signal(scheduler, field, value):
    child, binding, root = scheduler
    altered = copy.deepcopy(binding)
    altered[field] = value
    with pytest.raises(ValueError, match='TARGET_PREFLIGHT'):
        with hold.Hold(altered, lock_root=root / 'locks'):
            pytest.fail('changed process admitted')
    assert hold.process(child.pid)[1] not in ('T', 't')


def test_preexisting_stop_not_resumed(scheduler):
    child, binding, root = scheduler
    os.kill(child.pid, signal.SIGSTOP)
    deadline = time.monotonic() + 2
    while hold.process(child.pid)[1] != 'T':
        assert time.monotonic() < deadline
        time.sleep(0.01)
    with pytest.raises(ValueError, match='TARGET_PREFLIGHT'):
        with hold.Hold(binding, lock_root=root / 'locks'):
            pytest.fail('already stopped process admitted')
    assert hold.process(child.pid)[1] == 'T'


def test_concurrent_hold_refused_without_releasing_owner(scheduler):
    _, binding, root = scheduler
    with hold.Hold(binding, seconds=2, lock_root=root / 'locks') as first:
        with pytest.raises(BlockingIOError):
            with hold.Hold(binding, lock_root=root / 'locks'):
                pytest.fail('second hold admitted')
        first.check()


def test_surviving_coordinator_resumes_after_both_helpers_die(scheduler):
    child, binding, root = scheduler
    with hold.Hold(binding, seconds=2, lock_root=root / 'locks') as lease:
        for helper, _ in lease.children:
            os.kill(helper, signal.SIGSTOP)
        for helper, _ in lease.children:
            os.kill(helper, signal.SIGKILL)
    assert lease.statuses == [-signal.SIGKILL, -signal.SIGKILL]
    assert hold.process(child.pid)[1] not in ('T', 't')
    resumed(child, root, lines(root))


@pytest.mark.parametrize('seconds', [0, -1, 16, True, float('nan'), float('inf'), '1'])
def test_invalid_deadline(seconds):
    with pytest.raises(ValueError, match='LEASE_BOUNDS'):
        hold.Hold({}, seconds=seconds)


@pytest.mark.parametrize('kind', ['wide-directory', 'symlink-directory', 'wide-file', 'hardlink-file', 'symlink-file'])
def test_private_lock_refusals(scheduler, kind):
    child, binding, root = scheduler
    locks = root / 'locks'
    locks.mkdir(mode=0o700)
    lock = locks / (str(binding['pid']) + '-' + str(binding['start']) + '.lock')
    if kind == 'wide-directory':
        locks.chmod(0o755)
    elif kind == 'symlink-directory':
        link = root / 'linked'
        link.symlink_to(locks)
        locks = link
    elif kind == 'symlink-file':
        lock.symlink_to(root / 'no-target')
    else:
        lock.touch(mode=0o600)
        if kind == 'wide-file':
            lock.chmod(0o644)
        else:
            os.link(lock, root / 'extra-link')
    with pytest.raises((OSError, ValueError)):
        with hold.Hold(binding, lock_root=locks):
            pytest.fail('unsafe lock admitted')
    assert hold.process(child.pid)[1] not in ('T', 't')


def test_dead_process_refused(scheduler):
    child, binding, root = scheduler
    os.killpg(child.pid, signal.SIGTERM)
    child.wait(timeout=3)
    with pytest.raises(ProcessLookupError):
        with hold.Hold(binding, lock_root=root / 'locks'):
            pytest.fail('dead process admitted')


@pytest.mark.parametrize('failure', [1, 2])
def test_fork_failure_does_not_leave_target_stopped(scheduler, monkeypatch, failure):
    child, binding, root = scheduler
    original = hold.fork_job
    count = 0
    def failed(*arguments):
        nonlocal count
        count += 1
        if count == failure:
            raise OSError('synthetic fork failure')
        return original(*arguments)
    monkeypatch.setattr(hold, 'fork_job', failed)
    with pytest.raises(OSError):
        with hold.Hold(binding, seconds=0.3, lock_root=root / 'locks'):
            pytest.fail('incomplete rescue admitted')
    assert hold.process(child.pid)[1] not in ('T', 't')


@pytest.mark.parametrize('failure', [2, 3])
def test_pidfd_failure_reaps_owned_helpers(scheduler, monkeypatch, failure):
    child, binding, root = scheduler
    original = os.pidfd_open
    count = 0
    def failed(*arguments):
        nonlocal count
        count += 1
        if count == failure:
            raise OSError('synthetic descriptor exhaustion')
        return original(*arguments)
    monkeypatch.setattr(os, 'pidfd_open', failed)
    lease = hold.Hold(binding, seconds=0.3, lock_root=root / 'locks')
    with pytest.raises(OSError):
        with lease:
            pytest.fail('missing helper identity admitted')
    assert not lease.children and not lease.descriptors
    assert hold.process(child.pid)[1] not in ('T', 't')


@pytest.fixture
def publisher(monkeypatch):
    from scripts.control_ha_owner_replacement import Docker
    from tests.test_control_ha_owner_upgrade import installed
    item = installed('system_publisher')
    item['State']['Health'] = {'Status': 'healthy'}
    item['HostConfig']['Init'] = True
    binding = dict(pid=87654, start=123, parent=item['State']['Pid'], uid=[1000] * 4, threads=1,
                   command_sha256=hashlib.sha256(b'\0'.join(part.encode() for part in item['Config']['Cmd']) + b'\0').hexdigest())
    monkeypatch.setattr(Docker, 'inspect', lambda self, name: copy.deepcopy(item))
    monkeypatch.setattr(Path, 'read_text', lambda *args, **kwargs: '87654')
    monkeypatch.setattr(hold, 'process', lambda pid: (copy.deepcopy(binding), 'S'))
    return item, binding


def test_publisher_binding_is_scoped(publisher):
    item, binding = publisher
    assert hold.publisher_binding() == (item, binding)


@pytest.mark.parametrize('path,value', [
    (('Image',), 'sha256:' + '0' * 64), (('Name',), '/another-service'),
    (('Config', 'User'), 'root'), (('Config', 'Cmd'), ['sh', '-ec', 'other']),
    (('HostConfig', 'Init'), False), (('State', 'Running'), False),
    (('State', 'Health', 'Status'), 'unhealthy')])
def test_unreviewed_publisher_rejected(publisher, path, value):
    item, _ = publisher
    destination = item
    for name in path[:-1]:
        destination = destination[name]
    destination[path[-1]] = value
    with pytest.raises(ValueError):
        hold.publisher_binding()


@pytest.mark.parametrize('field,value', [('parent', -1), ('uid', [0] * 4), ('command_sha256', '0' * 64)])
def test_wrong_dispatcher_rejected(publisher, field, value):
    _, binding = publisher
    binding[field] = value
    with pytest.raises(ValueError, match='DISPATCHER_BINDING'):
        hold.publisher_binding()


@pytest.mark.parametrize('children', ['', '87654 87655'])
def test_ambiguous_dispatcher_rejected(publisher, monkeypatch, children):
    monkeypatch.setattr(Path, 'read_text', lambda *args, **kwargs: children)
    with pytest.raises(ValueError, match='DISPATCHER_CHILDREN'):
        hold.publisher_binding()
