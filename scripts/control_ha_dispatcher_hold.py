"""Bounded publisher scheduler hold, not a service stop or work-settlement permit."""
import argparse
import fcntl
import hashlib
import json
import math
import mmap
import os
from pathlib import Path
import select
import signal
import stat
import threading
import time


def require(condition, message):
    if not condition:
        raise ValueError(message)


def process(pid):
    require(type(pid) is int and pid > 1, 'PROCESS_ID')
    root = Path('/proc') / str(pid)
    before = (root / 'stat').read_text().rsplit(')', 1)[1].split()
    status = dict(line.split(':', 1) for line in (root / 'status').read_text().splitlines())
    result = dict(pid=pid, start=int(before[19]), parent=int(before[1]),
                  uid=[int(value) for value in status['Uid'].split()],
                  command_sha256=hashlib.sha256((root / 'cmdline').read_bytes()).hexdigest(),
                  cgroup_sha256=hashlib.sha256((root / 'cgroup').read_bytes()).hexdigest(),
                  pid_namespace=os.readlink(root / 'ns/pid'), threads=int(status['Threads']))
    after = (root / 'stat').read_text().rsplit(')', 1)[1].split()
    require(before[19] == after[19] and before[1] == after[1], 'PROCESS_CHANGED')
    return result, after[0]


def ready(descriptor, timeout=0):
    return bool(select.select([descriptor], [], [], max(0, timeout))[0])


def child_fds(keep):
    descriptors = [int(name) for name in os.listdir('/proc/self/fd')]
    for descriptor in descriptors:
        if descriptor not in keep:
            try:
                os.close(descriptor)
            except OSError:
                pass
    os.setsid()
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, signal.SIG_DFL)


def send(descriptor, number):
    try:
        signal.pidfd_send_signal(descriptor, number)
    except ProcessLookupError:
        pass


def guard(target, binding, control, events, lifeline, deadline, attempted):
    try:
        require(ready(lifeline, deadline - time.monotonic()) and os.read(lifeline, 1) == b'R', 'RESCUE_NOT_READY')
        require(ready(control, deadline - time.monotonic()) and os.read(control, 1) == b'A', 'NOT_ARMED')
        observed, state = process(binding['pid'])
        require(observed == binding and state in ('R', 'S', 'D') and not ready(target), 'TARGET_CHANGED')
        require(not ready(lifeline) and time.monotonic() < deadline, 'RESCUE_LOST')
        attempted[0] = 1
        send(target, signal.SIGSTOP)
        while True:
            require(time.monotonic() < deadline and not ready(target) and not ready(control) and
                    not ready(lifeline), 'HOLD_ABORTED')
            observed, state = process(binding['pid'])
            require(observed == binding, 'TARGET_CHANGED')
            if state == 'T':
                break
            time.sleep(0.005)
        os.write(events, b'H')
        select.select([control, lifeline, target], [], [], max(0, deadline - time.monotonic()))
    finally:
        if attempted[0]:
            send(target, signal.SIGCONT)


def rescue(target, guardian, lifeline, deadline, attempted):
    os.write(lifeline, b'R')
    if not ready(guardian, deadline - time.monotonic()):
        send(guardian, signal.SIGKILL)
        require(ready(guardian, 3), 'GUARDIAN_EXIT_UNCONFIRMED')
    if attempted[0]:
        send(target, signal.SIGCONT)


def fork_job(function, keep):
    child = os.fork()
    if child == 0:
        try:
            child_fds(keep)
            function()
        except BaseException:
            os._exit(1)
        os._exit(0)
    return child


class Hold:
    def __init__(self, binding, *, seconds=5, lock_root=None):
        require(type(seconds) in (int, float) and math.isfinite(seconds) and 0.2 <= seconds <= 15,
                'LEASE_BOUNDS')
        require(threading.active_count() == 1, 'SINGLE_THREADED_LAUNCHER_REQUIRED')
        self.binding, self.seconds = binding, seconds
        self.root = Path(lock_root) if lock_root else Path('/run/user') / str(os.geteuid()) / 'fc-ha-dispatcher'
        self.descriptors, self.children = [], []
        self.control = None
        self.attempted = mmap.mmap(-1, 1)
        self.started = False
        self.statuses = []

    def descriptor(self, descriptor):
        self.descriptors.append(descriptor)
        return descriptor

    def pipe(self):
        return tuple(self.descriptor(descriptor) for descriptor in os.pipe2(os.O_CLOEXEC))

    def close(self, descriptor):
        os.close(descriptor)
        self.descriptors.remove(descriptor)

    def track(self, child):
        self.children.append((child, None))
        descriptor = self.descriptor(os.pidfd_open(child))
        self.children[-1] = (child, descriptor)
        return descriptor

    def __enter__(self):
        try:
            self.root.mkdir(mode=0o700, exist_ok=True)
            require(self.root.is_absolute() and not any(path.is_symlink() for path in (self.root, *self.root.parents)),
                    'LOCK_DIRECTORY_PATH')
            info = self.root.stat()
            require(info.st_uid == os.geteuid() and stat.S_IMODE(info.st_mode) == 0o700, 'LOCK_DIRECTORY_MODE')
            name = str(self.binding['pid']) + '-' + str(self.binding['start']) + '.lock'
            lock = self.descriptor(os.open(self.root / name, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600))
            info = os.fstat(lock)
            require(stat.S_ISREG(info.st_mode) and info.st_uid == os.geteuid() and info.st_nlink == 1 and
                    stat.S_IMODE(info.st_mode) == 0o600, 'LOCK_FILE')
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            target = self.descriptor(os.pidfd_open(self.binding['pid']))
            self.target = target
            observed, state = process(self.binding['pid'])
            require(observed == self.binding and state in ('R', 'S', 'D') and not ready(target) and
                    self.binding['uid'] == [os.geteuid()] * 4 and self.binding['threads'] == 1, 'TARGET_PREFLIGHT')
            require(self.binding['pid'] != os.getpid(), 'SELF_TARGET')
            control, self.control = self.pipe()
            events, notification = self.pipe()
            lifeline, alive = self.pipe()
            self.deadline = time.monotonic() + self.seconds
            guardian_pid = fork_job(lambda: guard(target, self.binding, control, notification, lifeline,
                                                  self.deadline, self.attempted),
                                    {lock, target, control, notification, lifeline})
            guardian = self.track(guardian_pid)
            rescue_pid = fork_job(lambda: rescue(target, guardian, alive, self.deadline, self.attempted),
                                  {lock, target, guardian, alive})
            self.track(rescue_pid)
            for descriptor in (control, notification, lifeline, alive):
                self.close(descriptor)
            os.write(self.control, b'A')
            require(ready(events, self.seconds) and os.read(events, 1) == b'H', 'HOLD_NOT_CONFIRMED')
            self.close(events)
            self.started = True
            self.check()
            return self
        except BaseException:
            self.release()
            self.attempted.close()
            raise

    def check(self):
        observed, state = process(self.binding['pid'])
        require(self.started and observed == self.binding and state == 'T' and time.monotonic() < self.deadline and
                len(self.children) == 2 and not any(ready(descriptor) for _, descriptor in self.children),
                'HOLD_NO_LONGER_ACTIVE')

    def release(self):
        if self.control in self.descriptors:
            self.close(self.control)
        deadline = max(time.monotonic(), getattr(self, 'deadline', 0)) + 4
        try:
            for child, descriptor in self.children[:]:
                if descriptor is None:
                    while True:
                        found, status = os.waitpid(child, os.WNOHANG)
                        if found:
                            break
                        require(time.monotonic() < deadline, 'HELPER_EXIT_UNCONFIRMED')
                        time.sleep(0.01)
                else:
                    require(ready(descriptor, deadline - time.monotonic()), 'HELPER_EXIT_UNCONFIRMED')
                    _, status = os.waitpid(child, 0)
                self.statuses.append(os.waitstatus_to_exitcode(status))
                self.children.remove((child, descriptor))
            if self.attempted[0] and hasattr(self, 'target'):
                send(self.target, signal.SIGCONT)
        finally:
            for descriptor in self.descriptors[:]:
                self.close(descriptor)
        self.started = False

    def __exit__(self, *_):
        self.release()
        self.attempted.close()


def publisher_binding():
    from scripts.control_ha_owner_replacement import Docker
    from scripts.control_ha_owner_upgrade import workload
    item = Docker().inspect('fc-control-plane-0-system_publisher-1')
    require(type(item) is dict, 'PUBLISHER_MISSING')
    workload(item, 'system_publisher')
    require(item['State']['Health']['Status'] == 'healthy' and item['HostConfig']['Init'] is True, 'PUBLISHER_STATE')
    parent = item['State']['Pid']
    children = Path(f'/proc/{parent}/task/{parent}/children').read_text().split()
    require(len(children) == 1, 'DISPATCHER_CHILDREN')
    binding, state = process(int(children[0]))
    command = b'\0'.join(value.encode() for value in item['Config']['Cmd']) + b'\0'
    require(state in ('R', 'S', 'D') and binding['parent'] == parent and binding['uid'] == [1000] * 4 and
            binding['command_sha256'] == hashlib.sha256(command).hexdigest(), 'DISPATCHER_BINDING')
    return item, binding


def main():
    from scripts.control_ha_owner_replacement import configuration, equivalent, record
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--journal', type=Path, required=True)
    parser.add_argument('--hold-seconds', type=float, default=1)
    args = parser.parse_args()
    require(math.isfinite(args.hold_seconds) and 0.1 <= args.hold_seconds <= 2, 'PROBE_BOUNDS')
    require(args.journal.is_dir() and not any(args.journal.iterdir()) and
            not any(path.is_symlink() for path in (args.journal, *args.journal.parents)) and
            args.journal.stat().st_uid == os.geteuid() and stat.S_IMODE(args.journal.stat().st_mode) == 0o700,
            'PRIVATE_EMPTY_JOURNAL')
    item, binding = publisher_binding()
    record(args.journal, 'before', dict(container_id=item['Id'], image=item['Image'], binding=binding,
                                      observed_at_ns=time.time_ns(),
                                      started=item['State']['StartedAt'], restarts=item['RestartCount']))
    with Hold(binding, seconds=5) as held:
        held_at_ns = time.time_ns()
        time.sleep(args.hold_seconds)
        held.check()
    after, observed = publisher_binding()
    require(after['Id'] == item['Id'] and after['State']['StartedAt'] == item['State']['StartedAt'] and
            after['RestartCount'] == item['RestartCount'] and observed == binding and held.statuses == [0, 0],
            'RESUME_READBACK')
    equivalent(after, configuration(item))
    receipt = dict(scheduler_resumed=True, hold_seconds=args.hold_seconds, helper_exit_codes=held.statuses,
                   held_at_ns=held_at_ns, resumed_at_ns=time.time_ns(),
                   service_stopped=False, work_settlement_proven=False, capture_permitted=False)
    record(args.journal, 'receipt', receipt)
    print(json.dumps(receipt, sort_keys=True))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError):
        raise SystemExit('Dispatcher hold refused or unconfirmed; retain the journal and inspect runtime state.') from None
