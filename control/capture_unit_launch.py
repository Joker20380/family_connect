"""Operation-owned systemd start condition; not a substitute for cgroup termination."""
import ctypes
import hashlib
import os
from pathlib import Path
import re
import subprocess

from control.capture_native import fingerprint, identity, read, record, require


def call(*arguments):
    return subprocess.run(['/usr/bin/systemctl', *arguments], check=True, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10).stdout.decode()


def observed(unit):
    names = ('Id', 'LoadState', 'FragmentPath', 'DropInPaths', 'Conditions', 'ActiveState',
             'SubState', 'Job', 'MainPID', 'ControlPID', 'ControlGroup', 'KillMode',
             'Result', 'ExecMainStatus', 'NeedDaemonReload', 'InvocationID')
    args = ['show', unit]
    for name in names:
        args.extend(['-p', name])
    result = dict(line.split('=', 1) for line in call(*args).splitlines())
    require(result['Id'] == unit and result['LoadState'] == 'loaded', 'LAUNCH_UNIT_BINDING')
    return result


def conditions(unit):
    library = ctypes.CDLL('libsystemd.so.0')
    bus, reply, properties = ctypes.c_void_p(), ctypes.c_void_p(), ctypes.c_void_p()
    path = ctypes.c_char_p()
    destination = b'org.freedesktop.systemd1'
    def checked(result):
        require(result >= 0, 'LAUNCH_SYSTEM_BUS_' + str(-result))
        return result
    try:
        checked(library.sd_bus_open_system(ctypes.byref(bus)))
        checked(library.sd_bus_set_method_call_timeout(bus, ctypes.c_uint64(2000000)))
        checked(library.sd_bus_call_method(bus, destination, b'/org/freedesktop/systemd1',
            b'org.freedesktop.systemd1.Manager', b'LoadUnit', None, ctypes.byref(reply), b's', unit.encode()))
        checked(library.sd_bus_message_read(reply, b'o', ctypes.byref(path)))
        checked(library.sd_bus_get_property(bus, destination, path, b'org.freedesktop.systemd1.Unit',
            b'Conditions', None, ctypes.byref(properties), b'a(sbbsi)'))
        checked(library.sd_bus_message_enter_container(properties, ord('a'), b'(sbbsi)'))
        rows = []
        while checked(library.sd_bus_message_enter_container(properties, ord('r'), b'sbbsi')):
            name, parameter = ctypes.c_char_p(), ctypes.c_char_p()
            trigger, negate, state = ctypes.c_int(), ctypes.c_int(), ctypes.c_int()
            checked(library.sd_bus_message_read(properties, b'sbbsi', ctypes.byref(name),
                ctypes.byref(trigger), ctypes.byref(negate), ctypes.byref(parameter), ctypes.byref(state)))
            rows.append([name.value.decode(), bool(trigger.value), bool(negate.value),
                         parameter.value.decode(), state.value])
            checked(library.sd_bus_message_exit_container(properties))
        return rows
    finally:
        library.sd_bus_message_unref(properties)
        library.sd_bus_message_unref(reply)
        library.sd_bus_unref(bus)


class UnitLaunchHold:
    def __init__(self, unit, journal, operation):
        require(os.geteuid() == 0 and re.fullmatch(r'(?:family-connect|fc-ha02-lab)-[a-zA-Z0-9_-]+\.service', unit),
                'LAUNCH_UNIT_SCOPE')
        require(re.fullmatch('[a-f0-9]{32}', operation), 'LAUNCH_OPERATION')
        self.unit, self.operation = unit, operation
        self.journal = Path(journal)
        require(self.journal.is_absolute() and not any(path.is_symlink()
                for path in (self.journal, *self.journal.parents)), 'LAUNCH_JOURNAL_PATH')
        self.journal.mkdir(mode=0o700, exist_ok=False)
        self.marker = Path('/run') / ('fc-ha02-launch-' + operation + '-' + hashlib.sha256(unit.encode()).hexdigest()[:16])
        self.dropin = Path('/run/systemd/system') / (unit + '.d') / ('98-fc-ha02-' + operation + '.conf')
        self.raw = ('[Unit]\nConditionPathExists=!' + str(self.marker) + '\n').encode()
        self.before = observed(unit)
        require(self.before['KillMode'] == 'control-group' and self.before['NeedDaemonReload'] == 'no',
                'LAUNCH_UNIT_LIFECYCLE')
        self.fragment_sha = hashlib.sha256(Path(self.before['FragmentPath']).read_bytes()).hexdigest()
        self.plan = dict(unit=unit, operation=operation, marker=str(self.marker), dropin=str(self.dropin),
                         before=self.before, fragment_sha256=self.fragment_sha,
                         dropin_sha256=hashlib.sha256(self.raw).hexdigest(),
                         boot=Path('/proc/sys/kernel/random/boot_id').read_text())
        self.pin = fingerprint(self.plan)
        record(self.journal, 'plan.json', self.plan)
        self.attempted = self.active = False
        self.watch = None

    def __enter__(self):
        require(not self.attempted, 'LAUNCH_NO_REACQUIRE')
        self.attempted = True
        record(self.journal, 'install-intent.json', dict(plan=self.pin))
        descriptor = os.open(self.marker, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
        os.fchmod(descriptor, 0o644)
        os.close(descriptor)
        self.marker_identity = identity(self.marker)
        record(self.journal, 'marker.json', dict(identity=self.marker_identity))
        self.dropin.parent.mkdir(mode=0o755, exist_ok=True)
        require(not self.dropin.parent.is_symlink(), 'LAUNCH_DROPIN_DIRECTORY')
        descriptor = os.open(self.dropin, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(self.raw)
            stream.flush()
            os.fsync(stream.fileno())
        call('daemon-reload')
        library = ctypes.CDLL(None, use_errno=True)
        self.watch = library.inotify_init1(os.O_NONBLOCK | os.O_CLOEXEC)
        require(self.watch >= 0, 'LAUNCH_CONTINUITY_WATCH')
        for path in (self.marker, self.dropin, self.dropin.parent):
            require(library.inotify_add_watch(self.watch, os.fsencode(path),
                    0x2 | 0x4 | 0x40 | 0x80 | 0x100 | 0x200 | 0x400 | 0x800) >= 0,
                    'LAUNCH_CONTINUITY_WATCH')
        self.active = True
        self.check()
        record(self.journal, 'closed.json', dict(plan=self.pin))
        return self

    def check(self):
        try:
            require(self.active, 'LAUNCH_NOT_HELD')
            try:
                changed = os.read(self.watch, 65536)
            except BlockingIOError:
                changed = b''
            require(not changed, 'LAUNCH_CONTINUITY_LOST')
            require(not self.marker.is_symlink() and self.marker.is_file() and
                    identity(self.marker) == self.marker_identity and self.marker.stat().st_size == 0 and
                    self.dropin.read_bytes() == self.raw, 'LAUNCH_HOLD_CHANGED')
            current = observed(self.unit)
            require(current['FragmentPath'] == self.before['FragmentPath'] and current['NeedDaemonReload'] == 'no' and
                    hashlib.sha256(Path(current['FragmentPath']).read_bytes()).hexdigest() == self.fragment_sha and
                    str(self.dropin) in current['DropInPaths'].split() and
                    any(row[:4] == ['ConditionPathExists', False, True, str(self.marker)]
                        for row in conditions(self.unit)),
                    'LAUNCH_EFFECTIVE_CONDITION')
            return self.pin
        except BaseException:
            self.active = False
            raise

    def __exit__(self, error_type, error, traceback):
        self.active = False
        if self.watch is not None:
            os.close(self.watch)
            self.watch = None
        try:
            release_unit(self.journal, self.pin)
        except Exception as cleanup:
            if error is None:
                raise
            error.add_note('LAUNCH_RECOVERY_REQUIRED_' + type(cleanup).__name__)


def release_unit(journal, pin):
    root = Path(journal)
    plan = read(root, 'plan.json')
    require(fingerprint(plan) == pin and plan['boot'] == Path('/proc/sys/kernel/random/boot_id').read_text(),
            'LAUNCH_RELEASE_BINDING')
    if (root / 'released.json').exists():
        return read(root, 'released.json')
    marker, dropin = Path(plan['marker']), Path(plan['dropin'])
    require(plan['unit'].endswith('.service') and marker.parent == Path('/run') and
            dropin.parent == Path('/run/systemd/system') / (plan['unit'] + '.d'), 'LAUNCH_RELEASE_SCOPE')
    if not (root / 'release-intent.json').exists():
        require(marker.is_file() and dropin.is_file(), 'LAUNCH_RELEASE_PRESTATE')
        record(root, 'release-intent.json', dict(plan=pin))
    if dropin.exists():
        require(hashlib.sha256(dropin.read_bytes()).hexdigest() == plan['dropin_sha256'], 'LAUNCH_FOREIGN_DROPIN')
        dropin.unlink()
    call('daemon-reload')
    require(str(dropin) not in observed(plan['unit'])['DropInPaths'].split(), 'LAUNCH_RELEASE_UNCONFIRMED')
    if marker.exists():
        require(not marker.is_symlink() and marker.is_file() and
                identity(marker) == read(root, 'marker.json')['identity'] and marker.stat().st_size == 0,
                'LAUNCH_FOREIGN_MARKER')
        marker.unlink()
    result = dict(result='OWN_UNIT_START_CONDITION_REMOVED', unit=plan['unit'], writer_resume='NOT_PERFORMED')
    record(root, 'released.json', result)
    return result
