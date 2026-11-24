"""Lifecycle veto for a drained gate; observations do not fence uncooperative writers."""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

from .capture_gate import require

UNITS = {'family-connect-friends-awg.service', 'family-connect-friends-tcp.service',
         'family-connect-paid-watch.service'}
FIELDS = {
    'Unit': {'Id': 's', 'LoadState': 's', 'ActiveState': 's', 'SubState': 's', 'Job': '(uo)',
             'NeedDaemonReload': 'b', 'InvocationID': 'ay', 'StateChangeTimestampMonotonic': 't'},
    'Service': {'MainPID': 'u', 'ControlPID': 'u', 'ControlGroup': 's', 'Result': 's',
                'ReloadResult': 's', 'NRestarts': 'u', 'ExecMainStartTimestampMonotonic': 't'},
}


def validate(binding):
    require(type(binding) is dict and set(binding) == {'scope', 'units'} and
            binding['scope'] in ('system', 'user'), 'SYSTEMD_BINDING')
    require(type(binding['units']) is dict and 0 < len(binding['units']) <= 3, 'SYSTEMD_UNITS')
    for name, digest in binding['units'].items():
        require(type(name) is str and (name in UNITS if binding['scope'] == 'system' else
                re.fullmatch(r'fc-ha-lifecycle-[0-9a-f]{16}\.service', name)), 'SYSTEMD_UNIT_SCOPE')
        require(type(digest) is str and re.fullmatch('[0-9a-f]{64}', digest), 'SYSTEMD_SHA')
    return binding


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def command(scope, arguments, deadline):
    remaining = deadline - time.monotonic()
    require(remaining > 0, 'SYSTEMD_DEADLINE')
    environment = {'PATH': '/usr/bin:/bin', 'LANG': 'C'}
    if scope == 'user':
        environment['XDG_RUNTIME_DIR'] = '/run/user/' + str(os.getuid())
    result = subprocess.run(['/usr/bin/busctl', '--' + scope, '--json=short', '--timeout=1',
                             *arguments], capture_output=True, cwd='/', env=environment, timeout=remaining)
    require(result.returncode == 0 and not result.stderr and len(result.stdout) <= 65536, 'SYSTEMD_QUERY')
    return result.stdout


def properties(scope, name, deadline):
    lookup = json.loads(command(scope, ['call', 'org.freedesktop.systemd1', '/org/freedesktop/systemd1',
        'org.freedesktop.systemd1.Manager', 'GetUnit', 's', name], deadline))
    require(type(lookup) is dict and lookup.get('type') == 'o' and type(lookup.get('data')) is list and
            len(lookup['data']) == 1, 'SYSTEMD_LOOKUP')
    location = lookup['data'][0]
    require(type(location) is str and re.fullmatch(r'/org/freedesktop/systemd1/unit/[A-Za-z0-9_]+', location),
            'SYSTEMD_OBJECT')
    result = {}
    for interface, fields in FIELDS.items():
        rows = command(scope, ['get-property', 'org.freedesktop.systemd1', location,
            'org.freedesktop.systemd1.' + interface, *fields], deadline).splitlines()
        require(len(rows) == len(fields), 'SYSTEMD_PROPERTIES')
        for (field, signature), raw in zip(fields.items(), rows, strict=True):
            row = json.loads(raw)
            require(type(row) is dict and set(row) == {'type', 'data'} and row['type'] == signature,
                    'SYSTEMD_PROPERTY_TYPE')
            expected = str if signature == 's' else bool if signature == 'b' else int if signature in ('u', 't') else list
            require(type(row['data']) is expected, 'SYSTEMD_PROPERTY_VALUE')
            result[field] = row['data']
    require(result['Id'] == name and result['LoadState'] == 'loaded', 'SYSTEMD_UNIT')
    require(result['ActiveState'] == 'active' and result['SubState'] == 'running' and
            result['Job'] == [0, '/'] and type(result['Job'][0]) is int and
            result['ControlPID'] == 0 and result['MainPID'] > 1 and
            result['Result'] == result['ReloadResult'] == 'success' and not result['NeedDaemonReload'],
            'SYSTEMD_UNSETTLED')
    require(len(result['InvocationID']) == 16 and any(result['InvocationID']) and
            all(type(value) is int and 0 <= value <= 255 for value in result['InvocationID']) and
            result['StateChangeTimestampMonotonic'] > 0 and result['ExecMainStartTimestampMonotonic'] > 0 and
            result['NRestarts'] >= 0, 'SYSTEMD_EPOCH')
    return result


def bounded(path, limit=8192):
    with path.open('rb') as stream:
        raw = stream.read(limit + 1)
    require(len(raw) <= limit, 'SYSTEMD_FILE_BOUNDS')
    return raw


def process(pid, proc):
    require(type(pid) is int and pid > 1, 'SYSTEMD_PID')
    directory = proc / str(pid)
    before = bounded(directory / 'stat')
    fields = before.rsplit(b')', 1)[-1].split()
    require(before.split(b' ', 1)[0] == str(pid).encode() and len(fields) >= 20 and
            fields[0] not in (b'Z', b'X', b'x') and fields[19].isdigit(), 'SYSTEMD_PROCESS')
    executable = (directory / 'exe').stat()
    command_sha = hashlib.sha256(bounded(directory / 'cmdline', 65536)).hexdigest()
    after = bounded(directory / 'stat').rsplit(b')', 1)[-1].split()
    require(len(after) >= 20 and after[19] == fields[19] and after[0] not in (b'Z', b'X', b'x') and
            executable == (directory / 'exe').stat(), 'SYSTEMD_PROCESS_CHANGED')
    return [pid, int(fields[19]), executable.st_dev, executable.st_ino, command_sha]


def processes(group, name, *, root=Path('/sys/fs/cgroup'), proc=Path('/proc')):
    require(type(group) is str and group.startswith('/') and not group.startswith('//') and
            group == os.path.normpath(group) and '..' not in Path(group).parts and
            Path(group).name == name, 'SYSTEMD_CGROUP')
    directory = root / group.lstrip('/')
    require(all(not item.is_symlink() for item in (directory, *directory.parents)), 'SYSTEMD_CGROUP_SYMLINK')
    paths, result, members = [directory], {}, set()
    while paths:
        current = paths.pop()
        require(len(result) < 64, 'SYSTEMD_CGROUP_BOUNDS')
        before = current.stat()
        entries = list(current.iterdir())
        require(len(entries) <= 256 and all(not entry.is_symlink() for entry in entries), 'SYSTEMD_CGROUP_ENTRIES')
        children = sorted(entry.name for entry in entries if entry.is_dir())
        paths.extend(current / child for child in children)
        events = bounded(current / 'cgroup.events').splitlines()
        require(b'frozen 0' in events, 'SYSTEMD_CGROUP_FROZEN')
        raw = bounded(current / 'cgroup.procs')
        pids = raw.split()
        require(len(members) + len(pids) <= 128 and all(item.isdigit() for item in pids), 'SYSTEMD_PROCESS_BOUNDS')
        identities = [process(int(item), proc) for item in pids]
        require(all(item[0] not in members for item in identities) and
                len({item[0] for item in identities}) == len(identities), 'SYSTEMD_PROCESS_DUPLICATE')
        members.update(item[0] for item in identities)
        after = current.stat()
        require(raw == bounded(current / 'cgroup.procs') and
                children == sorted(entry.name for entry in current.iterdir() if entry.is_dir()) and
                (before.st_dev, before.st_ino) == (after.st_dev, after.st_ino), 'SYSTEMD_CGROUP_CHANGED')
        result[str(current.relative_to(directory))] = [before.st_dev, before.st_ino, sorted(identities)]
    return result, members


def observe(scope, name, deadline):
    before = properties(scope, name, deadline)
    groups, members = processes(before['ControlGroup'], name)
    require(before['MainPID'] in members, 'SYSTEMD_MAIN_OUTSIDE_CGROUP')
    require(before == properties(scope, name, deadline), 'SYSTEMD_LIFECYCLE_CHANGED')
    require(time.monotonic() < deadline, 'SYSTEMD_DEADLINE')
    return digest(dict(properties=before, groups=groups,
                       boot=bounded(Path('/proc/sys/kernel/random/boot_id')).decode('ascii').strip()))


class SystemdState:
    def __init__(self, binding):
        self.binding = json.loads(json.dumps(validate(binding)))
        self.held = False

    def verify(self):
        require(self.held, 'SYSTEMD_NOT_HELD')
        deadline = time.monotonic() + .75
        for name, expected in self.binding['units'].items():
            require(observe(self.binding['scope'], name, deadline) == expected, 'SYSTEMD_BINDING_CHANGED')

    @contextmanager
    def hold(self):
        require(not self.held, 'SYSTEMD_ALREADY_HELD')
        self.held = True
        try:
            self.verify()
            yield self
        finally:
            self.held = False
