"""A finite cgroup-v2 writer domain, behind its already closed launch admission."""
import fcntl
import ctypes
import os
from pathlib import Path
import signal
import stat
import time

from control.capture_native import fingerprint, require, record, read


class LaunchLock:
    def __init__(self, path, expected):
        self.path, self.expected = Path(path), expected
        self.descriptor = None

    def __enter__(self):
        require(self.descriptor is None and not self.path.is_symlink(), 'DOMAIN_LAUNCH_REENTRY')
        descriptor = os.open(self.path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            info = os.fstat(descriptor)
            require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size == 0 and
                    [info.st_dev, info.st_ino, info.st_uid, stat.S_IMODE(info.st_mode)] == self.expected,
                    'DOMAIN_LAUNCH_BINDING')
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.descriptor = descriptor
            return self
        except BaseException:
            os.close(descriptor)
            raise

    def check(self):
        require(self.descriptor is not None, 'DOMAIN_LAUNCH_LOST')
        info = self.path.stat()
        require([info.st_dev, info.st_ino, info.st_uid, stat.S_IMODE(info.st_mode)] == self.expected and
                ' FLOCK ' in Path(f'/proc/self/fdinfo/{self.descriptor}').read_text() and
                ' WRITE ' in Path(f'/proc/self/fdinfo/{self.descriptor}').read_text(), 'DOMAIN_LAUNCH_LOST')
        return fingerprint(self.expected)

    def __exit__(self, error_type, error, traceback):
        if self.descriptor is not None:
            os.close(self.descriptor)
            self.descriptor = None


class ClosedCgroup:
    def __init__(self, directory, launch, journal, *, seconds=5):
        self.directory = Path(directory)
        require(self.directory.is_absolute() and self.directory.parent != Path('/') and
                Path('/sys/fs/cgroup') in self.directory.parents and
                not any(path.is_symlink() for path in (self.directory, *self.directory.parents)),
                'DOMAIN_CGROUP_PATH')
        require(isinstance(launch, LaunchLock) and 0 < seconds <= 20, 'DOMAIN_LAUNCH_REQUIRED')
        self.launch, self.seconds = launch, seconds
        self.directory_fd = os.open(self.directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        info = os.fstat(self.directory_fd)
        self.pin = [info.st_dev, info.st_ino]
        self.journal = Path(journal)
        require(self.journal.is_absolute() and not any(path.is_symlink()
                for path in (self.journal, *self.journal.parents)), 'DOMAIN_JOURNAL_PATH')
        self.journal.mkdir(mode=0o700, exist_ok=False)
        self.plan = dict(directory=str(self.directory), pin=self.pin, launch=str(launch.path),
                         launch_pin=launch.expected, boot=Path('/proc/sys/kernel/random/boot_id').read_text())
        self.plan_hash = fingerprint(self.plan)
        record(self.journal, 'plan.json', self.plan)
        self.watch = None
        self.attempted = self.active = False

    def events(self):
        return dict(line.split() for line in (self.directory / 'cgroup.events').read_text().splitlines())

    def same(self):
        info = self.directory.stat()
        require([info.st_dev, info.st_ino] == self.pin and os.fstat(self.directory_fd).st_nlink > 0,
                'DOMAIN_CGROUP_REPLACED')
        self.launch.check()

    def __enter__(self):
        try:
            return self._acquire()
        except BaseException as error:
            self.active = False
            self.failure(error)
            if self.directory_fd is not None:
                os.close(self.directory_fd)
                self.directory_fd = None
            if self.watch is not None:
                os.close(self.watch)
                self.watch = None
            raise

    def _acquire(self):
        require(not self.attempted, 'DOMAIN_NO_REACQUIRE')
        self.attempted = True
        self.same()
        require(self.events().get('frozen') == '0', 'DOMAIN_PREEXISTING_FREEZE')
        signaled = set()
        deadline = time.monotonic() + self.seconds
        while self.events()['populated'] != '0':
            self.same()
            require(time.monotonic() < deadline, 'DOMAIN_CLEAN_EXIT_TIMEOUT')
            paths = [self.directory / 'cgroup.procs', *self.directory.glob('*/**/cgroup.procs')]
            require(len(paths) <= 64, 'DOMAIN_GROUP_BOUNDS')
            for path in paths:
                try:
                    pids = path.read_text().split()
                except FileNotFoundError:
                    continue
                require(len(pids) <= 128, 'DOMAIN_PROCESS_BOUNDS')
                for value in pids:
                    pid = int(value)
                    require(pid != os.getpid(), 'DOMAIN_CONTROLLER_INSIDE')
                    try:
                        descriptor = os.pidfd_open(pid)
                    except ProcessLookupError:
                        continue
                    try:
                        membership = Path(f'/proc/{pid}/cgroup').read_text().strip()
                        expected = '0::/' + str(path.parent.relative_to('/sys/fs/cgroup'))
                        require(membership == expected, 'DOMAIN_PROCESS_ESCAPED')
                        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
                        signaled.add(pid)
                    except (ProcessLookupError, FileNotFoundError):
                        pass
                    finally:
                        os.close(descriptor)
            time.sleep(.01)
        self.same()
        record(self.journal, 'empty.json', dict(pin=self.pin, signal='SIGTERM', signaled_count=len(signaled)))
        library = ctypes.CDLL(None, use_errno=True)
        self.watch = library.inotify_init1(os.O_NONBLOCK | os.O_CLOEXEC)
        require(self.watch >= 0 and library.inotify_add_watch(self.watch,
                os.fsencode(self.directory / 'cgroup.freeze'), 0x2 | 0x400 | 0x800) >= 0,
                'DOMAIN_CONTINUITY_WATCH')
        record(self.journal, 'freeze-intent.json', dict(pin=self.pin))
        (self.directory / 'cgroup.freeze').write_text('1')
        while self.events().get('frozen') != '1':
            require(time.monotonic() < deadline, 'DOMAIN_FREEZE_TIMEOUT')
            time.sleep(.01)
        try:
            os.read(self.watch, 65536)
        except BlockingIOError:
            pass
        self.active = True
        self.lease = fingerprint(dict(pin=self.pin, launch=self.launch.check()))
        self.check()
        self.receipt = dict(result='KERNEL_DOMAIN_EMPTY_AND_LATE_LAUNCH_FROZEN', lease=self.lease,
                            graceful_signal='SIGTERM', signaled_count=len(signaled), history_settled=False)
        record(self.journal, 'held.json', self.receipt)
        return self

    def check(self):
        try:
            require(self.active, 'DOMAIN_NOT_HELD')
            self.same()
            try:
                changed = os.read(self.watch, 65536)
            except BlockingIOError:
                changed = b''
            require(not changed, 'DOMAIN_FREEZE_CHANGED')
            require(self.events() == {'populated': '0', 'frozen': '1'}, 'DOMAIN_LATE_WORK_OR_FREEZE_LOST')
            return self.lease
        except BaseException as error:
            self.active = False
            self.failure(error)
            raise

    def failure(self, error):
        if not (self.journal / 'failed.json').exists():
            try:
                record(self.journal, 'failed.json', dict(reason=str(error), cleanup='RECONCILIATION_REQUIRED'))
            except Exception as cleanup:
                error.add_note('DOMAIN_FAILURE_RECORD_' + type(cleanup).__name__)

    def __exit__(self, error_type, error, traceback):
        try:
            self.check()
            reconcile_domain(self.journal, self.plan_hash, self.launch)
            self.active = False
        except Exception as cleanup:
            if error is None:
                raise
            error.add_note('DOMAIN_RECONCILIATION_REQUIRED_' + type(cleanup).__name__)
        finally:
            os.close(self.directory_fd)
            self.directory_fd = None
            if self.watch is not None:
                os.close(self.watch)
                self.watch = None


def reconcile_domain(journal, plan_hash, launch):
    root = Path(journal)
    plan = read(root, 'plan.json')
    require(fingerprint(plan) == plan_hash, 'DOMAIN_RECONCILE_PLAN')
    if (root / 'released.json').exists():
        return read(root, 'released.json')
    require(isinstance(launch, LaunchLock) and launch.check() == fingerprint(plan['launch_pin']) and
            str(launch.path) == plan['launch'] and plan['boot'] ==
            Path('/proc/sys/kernel/random/boot_id').read_text(), 'DOMAIN_RECONCILE_AUTHORITY')
    directory = Path(plan['directory'])
    info = directory.stat()
    require([info.st_dev, info.st_ino] == plan['pin'], 'DOMAIN_RECONCILE_REPLACED')
    events = dict(line.split() for line in (directory / 'cgroup.events').read_text().splitlines())
    require(events.get('populated') == '0', 'DOMAIN_RECONCILE_WRITERS_REMAIN')
    intent = root / 'release-intent.json'
    if not intent.exists():
        require(events.get('frozen') == '1' and (root / 'freeze-intent.json').exists(), 'DOMAIN_RECONCILE_STATE')
        record(root, intent.name, dict(pin=plan['pin']))
    if events.get('frozen') == '1':
        (directory / 'cgroup.freeze').write_text('0')
    require((directory / 'cgroup.freeze').read_text().strip() == '0', 'DOMAIN_RELEASE_UNCONFIRMED')
    result = dict(result='OWN_EMPTY_DOMAIN_THAWED', writer_resume='NOT_PERFORMED', capture_permitted=False)
    record(root, 'released.json', result)
    return result
