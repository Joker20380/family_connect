import errno
import multiprocessing
import os
from pathlib import Path
import signal
import subprocess
import time
import uuid

import pytest

from control.capture_native import ReadOnlyTrees, read, readonly, reconcile, reject_old_handles, unique_mount
from control.capture_domain import ClosedCgroup, LaunchLock
from control.capture_native import identity


@pytest.fixture(autouse=True)
def private_namespace():
    assert os.geteuid() == 0
    assert os.environ.get('FC_NATIVE_PRIVATE_NAMESPACE') == '1'
    assert os.readlink('/proc/self/ns/mnt') != os.readlink('/proc/1/ns/mnt')


@pytest.fixture
def native(tmp_path):
    assert os.geteuid() == 0, 'Run in an isolated root mount namespace, not an unprivileged skip'
    assert os.environ.get('FC_NATIVE_PRIVATE_NAMESPACE') == '1'
    root = tmp_path / 'tree'
    root.mkdir(mode=0o700)
    (root / 'aliases.json').write_bytes(b'unchanged')
    seal = ReadOnlyTrees([root], tmp_path / 'journal', 'isolated-native')
    yield root, seal
    seal.release()


def test_late_open_and_parent_rename_refused(native):
    root, seal = native
    outside = root.parent / 'temporary'
    outside.write_bytes(b'late')
    seal.acquire()
    lease = seal.check()
    for operation in (lambda: (root / 'new').write_bytes(b'late'),
                      lambda: outside.replace(root / 'aliases.json'),
                      lambda: (root / 'aliases.json').unlink()):
        with pytest.raises(OSError) as error:
            operation()
        assert error.value.errno in (errno.EROFS, errno.EXDEV)
        assert seal.check() == lease
    assert (root / 'aliases.json').read_bytes() == b'unchanged'
    assert outside.exists()


def old_handle(path, connection, mapping):
    import mmap
    descriptor = os.open(path, os.O_RDWR)
    if mapping:
        buffer = mmap.mmap(descriptor, 0, flags=mmap.MAP_SHARED, prot=mmap.PROT_READ | mmap.PROT_WRITE)
        assert buffer[0] == ord('u')
        os.close(descriptor)
    connection.send('OPEN')
    connection.recv()


@pytest.mark.parametrize('mapping', [False, True])
@pytest.mark.parametrize('alias', [False, True])
def test_old_fd_and_prefaulted_mapping_are_not_fenced_by_bind(native, mapping, alias):
    root, seal = native
    view = root
    if alias:
        view = root.parent / 'other-namespace-view'
        view.mkdir()
        subprocess.run(['mount', '--bind', str(root), str(view)], check=True)
    parent, child = multiprocessing.Pipe()
    process = multiprocessing.Process(target=old_handle, args=(view / 'aliases.json', child, mapping))
    process.start()
    assert parent.poll(3) and parent.recv() == 'OPEN'
    try:
        seal.acquire()
        with pytest.raises(ValueError, match='NATIVE_UNMANAGED'):
            reject_old_handles([root])
        process.terminate()
        process.join(3)
        assert not process.is_alive()
        assert reject_old_handles([root])['launch_coverage'] == 'REQUIRED_SEPARATELY'
    finally:
        if process.is_alive():
            process.kill()
            process.join(3)
        if alias:
            subprocess.run(['umount', str(view)], check=True)


def test_mount_loss_and_reacquisition_never_reuses_lease(native):
    root, seal = native
    seal.acquire()
    original = unique_mount(root)
    subprocess.run(['umount', str(root)], check=True)
    subprocess.run(['mount', '--bind', str(root), str(root)], check=True)
    subprocess.run(['mount', '-o', 'remount,bind,ro', str(root)], check=True)
    assert unique_mount(root) != original
    try:
        with pytest.raises(ValueError, match='NATIVE_MOUNT_LOST'):
            seal.check()
        with pytest.raises(ValueError, match='NATIVE_NOT_HELD'):
            seal.check()
        assert read(seal.journal, 'failed.json')['reason'] == 'NATIVE_MOUNT_LOST'
        with pytest.raises(ValueError, match='NATIVE_RECONCILE_FOREIGN_MOUNT'):
            seal.release()
    finally:
        subprocess.run(['umount', str(root)], check=True)
        from control.capture_native import record
        record(seal.journal, 'release-0-intent.json', read(seal.journal, 'bind-0-observed.json'))


def test_remount_rw_ro_same_mount_is_not_continuous_lease(native):
    root, seal = native
    seal.acquire()
    original = unique_mount(root)
    subprocess.run(['mount', '-o', 'remount,bind,rw', str(root)], check=True)
    subprocess.run(['mount', '-o', 'remount,bind,ro', str(root)], check=True)
    assert unique_mount(root) == original
    with pytest.raises(ValueError, match='NATIVE_MOUNT_NAMESPACE_CHANGED'):
        seal.check()
    with pytest.raises(ValueError, match='NATIVE_NOT_HELD'):
        seal.check()


def test_lost_release_response_is_reconciled_without_second_unmount(native, monkeypatch):
    root, seal = native
    seal.acquire()
    from control import capture_native
    original = capture_native.command

    def lost(arguments):
        original(arguments)
        raise TimeoutError('response lost after unmount')

    monkeypatch.setattr(capture_native, 'command', lost)
    with pytest.raises(TimeoutError):
        seal.release()
    assert not readonly(root)
    monkeypatch.setattr(capture_native, 'command', lambda arguments: pytest.fail('repeated effect'))
    first = reconcile(seal.journal, seal.plan_hash)
    assert reconcile(seal.journal, seal.plan_hash) == first
    assert first['writer_resume'] == 'NOT_PERFORMED'


def died(root, journal, connection):
    seal = ReadOnlyTrees([root], journal, 'dead-participant')
    seal.acquire()
    connection.send(seal.plan_hash)
    signal.pause()


def test_participant_death_leaves_external_mount_until_explicit_reconciliation(tmp_path):
    root = tmp_path / 'tree'
    root.mkdir()
    journal = tmp_path / 'journal'
    parent, child = multiprocessing.Pipe()
    process = multiprocessing.Process(target=died, args=(root, journal, child))
    process.start()
    assert parent.poll(5)
    pin = parent.recv()
    process.kill()
    process.join(3)
    assert readonly(root)
    assert not (journal / 'released.json').exists()
    assert reconcile(journal, pin)['result'] == 'OWN_NATIVE_MOUNTS_RELEASED'
    assert not readonly(root)
    with pytest.raises(FileExistsError):
        ReadOnlyTrees([root], journal, 'dead-participant')


def test_live_controller_prevents_new_process_reconciliation(native):
    root, seal = native
    seal.acquire()
    with pytest.raises(BlockingIOError):
        reconcile(seal.journal, seal.plan_hash)
    assert readonly(root)


def test_changed_plan_is_not_cleanup_authority(native):
    root, seal = native
    seal.acquire()
    with pytest.raises(ValueError, match='NATIVE_PLAN_CHANGED'):
        seal.active = False
        os.close(seal.controller)
        seal.controller = None
        reconcile(seal.journal, '0' * 64)
    assert readonly(root)


def test_nested_mount_is_not_silently_writable(tmp_path):
    root = tmp_path / 'tree'
    root.mkdir()
    nested = root / 'nested'
    nested.mkdir()
    subprocess.run(['mount', '--bind', str(nested), str(nested)], check=True)
    try:
        with pytest.raises(ValueError, match='NATIVE_NESTED_MOUNT'):
            ReadOnlyTrees([root], tmp_path / 'journal', 'nested-refusal')
    finally:
        subprocess.run(['umount', str(nested)], check=True)


@pytest.fixture
def domain(tmp_path):
    directory = Path('/sys/fs/cgroup') / ('fc-ha02-native-lab-' + uuid.uuid4().hex)
    directory.mkdir()
    launch = tmp_path / 'launch.lock'
    launch.touch(mode=0o600)
    with LaunchLock(launch, identity(launch)) as lock:
        yield directory, lock
    (directory / 'cgroup.kill').write_text('1')
    (directory / 'cgroup.freeze').write_text('0')
    deadline = time.monotonic() + 3
    while 'populated 1' in (directory / 'cgroup.events').read_text():
        assert time.monotonic() < deadline
        time.sleep(.01)
    directory.rmdir()


def detached_writer(directory, path, connection):
    import mmap
    (directory / 'cgroup.procs').write_text(str(os.getpid()))
    descriptor = os.open(path, os.O_RDWR)
    buffer = mmap.mmap(descriptor, 0, flags=mmap.MAP_SHARED, prot=mmap.PROT_READ | mmap.PROT_WRITE)
    assert buffer[0] == ord('u')
    child = os.fork()
    if child:
        os._exit(0)
    os.setsid()
    connection.send('DETACHED_AND_PREFAULTED')
    signal.pause()


def test_whole_domain_exit_precedes_native_seal(native, domain):
    root, seal = native
    directory, launch = domain
    parent, child = multiprocessing.Pipe()
    process = multiprocessing.Process(target=detached_writer, args=(directory, root / 'aliases.json', child))
    process.start()
    assert parent.poll(3) and parent.recv() == 'DETACHED_AND_PREFAULTED'
    process.join(3)
    assert process.exitcode == 0
    assert 'populated 1' in (directory / 'cgroup.events').read_text()
    with ClosedCgroup(directory, launch, root.parent / 'domain-journal') as boundary:
        seal.acquire()
        assert reject_old_handles([root])['result'] == 'NO_OBSERVED_OLD_HANDLES'
        assert boundary.receipt['result'] == 'KERNEL_DOMAIN_EMPTY_AND_LATE_LAUNCH_FROZEN'
        assert boundary.check() == boundary.lease
        seal.release()


def late_writer(directory, path):
    (directory / 'cgroup.procs').write_text(str(os.getpid()))
    path.write_bytes(b'should not run')


def uncooperative_writer(directory, connection):
    (directory / 'cgroup.procs').write_text(str(os.getpid()))
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    connection.send('STARTED')
    signal.pause()


def test_graceful_exit_timeout_never_accepts_or_hides_surviving_writer(domain, tmp_path):
    directory, launch = domain
    parent, child = multiprocessing.Pipe()
    process = multiprocessing.Process(target=uncooperative_writer, args=(directory, child))
    process.start()
    assert parent.poll(3) and parent.recv() == 'STARTED'
    boundary = ClosedCgroup(directory, launch, tmp_path / 'timeout-journal', seconds=.1)
    try:
        with pytest.raises(ValueError, match='DOMAIN_CLEAN_EXIT_TIMEOUT'):
            boundary.__enter__()
        assert process.is_alive() and not boundary.active
        assert read(boundary.journal, 'failed.json')['reason'] == 'DOMAIN_CLEAN_EXIT_TIMEOUT'
        assert not (boundary.journal / 'held.json').exists()
    finally:
        process.kill()
        process.join(3)


def test_domain_release_response_loss_is_read_back_not_repeated(domain, tmp_path, monkeypatch):
    from control import capture_domain
    directory, launch = domain
    boundary = ClosedCgroup(directory, launch, tmp_path / 'release-journal')
    boundary.__enter__()
    original = capture_domain.record
    def lost(root, name, value):
        if name == 'released.json':
            raise OSError('isolated lost response after thaw')
        return original(root, name, value)
    monkeypatch.setattr(capture_domain, 'record', lost)
    with pytest.raises(OSError, match='lost response'):
        boundary.__exit__(None, None, None)
    assert (directory / 'cgroup.freeze').read_text().strip() == '0'
    monkeypatch.setattr(capture_domain, 'record', original)
    result = capture_domain.reconcile_domain(boundary.journal, boundary.plan_hash, launch)
    assert result['result'] == 'OWN_EMPTY_DOMAIN_THAWED'
    assert capture_domain.reconcile_domain(boundary.journal, boundary.plan_hash, launch) == result


def test_late_attach_is_frozen_and_invalidates_domain(domain, tmp_path):
    directory, launch = domain
    boundary = ClosedCgroup(directory, launch, tmp_path / 'domain-journal')
    boundary.__enter__()
    target = tmp_path / 'late-effect'
    process = multiprocessing.Process(target=late_writer, args=(directory, target))
    process.start()
    deadline = time.monotonic() + 3
    while 'populated 1' not in (directory / 'cgroup.events').read_text():
        assert time.monotonic() < deadline
        time.sleep(.01)
    assert not target.exists()
    with pytest.raises(ValueError, match='DOMAIN_LATE_WORK_OR_FREEZE_LOST'):
        boundary.check()
    with pytest.raises(ValueError, match='DOMAIN_NOT_HELD'):
        boundary.check()
    (directory / 'cgroup.kill').write_text('1')
    process.join(3)
    assert not process.is_alive() and not target.exists()
    os.close(boundary.directory_fd)
    os.close(boundary.watch)


def test_launch_lock_rejects_new_manual_admission(domain):
    directory, launch = domain
    import fcntl
    descriptor = os.open(launch.path, os.O_RDONLY)
    try:
        with pytest.raises(BlockingIOError):
            fcntl.flock(descriptor, fcntl.LOCK_SH | fcntl.LOCK_NB)
    finally:
        os.close(descriptor)


def test_freeze_loss_then_reacquisition_is_terminal(domain, tmp_path):
    directory, launch = domain
    boundary = ClosedCgroup(directory, launch, tmp_path / 'domain-journal')
    boundary.__enter__()
    (directory / 'cgroup.freeze').write_text('0')
    (directory / 'cgroup.freeze').write_text('1')
    try:
        with pytest.raises(ValueError, match='DOMAIN_FREEZE_CHANGED'):
            boundary.check()
        with pytest.raises(ValueError, match='DOMAIN_NOT_HELD'):
            boundary.check()
    finally:
        from control.capture_domain import reconcile_domain
        reconcile_domain(boundary.journal, boundary.plan_hash, launch)
        os.close(boundary.directory_fd)
        os.close(boundary.watch)


def test_effective_unit_condition_blocks_late_start_and_only_own_release(tmp_path):
    from control.capture_unit_launch import UnitLaunchHold, call, release_unit
    operation = uuid.uuid4().hex
    unit = 'fc-ha02-lab-' + operation + '.service'
    path = Path('/run/systemd/system') / unit
    effect = tmp_path / 'unit-effect'
    path.write_text('[Unit]\nDescription=Isolated HA native launch qualification\n'
                    '[Service]\nType=oneshot\nKillMode=control-group\nExecStart=/usr/bin/touch ' + str(effect) + '\n')
    call('daemon-reload')
    hold = UnitLaunchHold(unit, tmp_path / 'unit-journal', operation)
    try:
        with hold:
            call('start', unit)
            assert not effect.exists()
            assert hold.check() == hold.pin
            assert 'ConditionResult=no' in call('show', unit, '-p', 'ConditionResult')
        call('start', unit)
        assert effect.exists()
        assert release_unit(hold.journal, hold.pin)['writer_resume'] == 'NOT_PERFORMED'
    finally:
        call('stop', unit)
        if hold.dropin.exists():
            hold.dropin.unlink()
        if hold.marker.exists():
            hold.marker.unlink()
        path.unlink()
        hold.dropin.parent.rmdir()
        call('daemon-reload')


def test_launch_condition_rewrite_cannot_be_hidden_by_restoring_same_bytes(tmp_path):
    from control.capture_unit_launch import UnitLaunchHold, call
    unit = 'fc-ha02-lab-' + uuid.uuid4().hex + '.service'
    path = Path('/run/systemd/system') / unit
    path.write_text('[Service]\nType=oneshot\nExecStart=/bin/true\nKillMode=control-group\n')
    call('daemon-reload')
    hold = UnitLaunchHold(unit, tmp_path / 'journal', uuid.uuid4().hex)
    try:
        with hold:
            hold.dropin.write_bytes(hold.raw)
            with pytest.raises(ValueError, match='LAUNCH_CONTINUITY_LOST'):
                hold.check()
            with pytest.raises(ValueError, match='LAUNCH_NOT_HELD'):
                hold.check()
    finally:
        path.unlink()
        hold.dropin.parent.rmdir()
        call('daemon-reload')


def hung_mount(root, journal, connection):
    from control.capture_process import hard_deadline
    with hard_deadline(.3):
        seal = ReadOnlyTrees([root], journal, 'hung-snapshot')
        seal.acquire()
        connection.send(seal.plan_hash)
        time.sleep(10)


def test_hung_snapshot_deadline_does_not_claim_external_cleanup(tmp_path):
    root = tmp_path / 'tree'
    root.mkdir()
    journal = tmp_path / 'journal'
    parent, child = multiprocessing.Pipe()
    process = multiprocessing.Process(target=hung_mount, args=(root, journal, child))
    process.start()
    assert parent.poll(3)
    pin = parent.recv()
    process.join(2)
    assert process.exitcode == -signal.SIGKILL
    assert readonly(root) and not (journal / 'released.json').exists()
    assert reconcile(journal, pin)['result'] == 'OWN_NATIVE_MOUNTS_RELEASED'
    assert not readonly(root)
