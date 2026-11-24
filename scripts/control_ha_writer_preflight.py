"""Read-only writer boundary evidence; never a quiescence or capture authorization."""
import argparse
import json
import os
from pathlib import Path
import pwd
import re
import resource
import signal
import stat
import subprocess
import sys
import time

from scripts import control_ha_installed_census as census

ACCOUNTS = {
    'RU': ('root', 'fc-friends', 'fc-load'),
    'NL1': ('root', 'family-restricted', 'fc-friends', 'fc-load', 'fc-mailbox', 'fc-relay'),
    'NL2': ('root', 'fc-rehearsal', 'fc-friends', 'fc-load', 'family-restricted'),
}
CRON_DIRECTORIES = ('/etc/cron.d', '/etc/cron.hourly', '/etc/cron.daily',
                    '/etc/cron.weekly', '/etc/cron.monthly')
LOCKS = {'application': 'friends-awg/application.lock', 'registration': 'friends-awg/registration.lock'}
LIMIT = 128 * 1024


def bounded(path, maximum=LIMIT):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as stream:
        before = os.fstat(stream.fileno())
        census.require(stat.S_ISREG(before.st_mode), 'NOT_REGULAR')
        raw = stream.read(maximum + 1)
        after = os.fstat(stream.fileno())
    census.require(len(raw) <= maximum, 'READ_BOUNDS')
    census.require((before.st_ino, before.st_mtime_ns, before.st_ctime_ns, before.st_size) ==
                   (after.st_ino, after.st_mtime_ns, after.st_ctime_ns, after.st_size), 'READ_CHANGED')
    return raw


def dispatch_summary(raw, kind):
    result = census.scoped_dispatch_lines(raw, kind)
    if kind == 'authorized_keys':
        lines = [line.strip() for line in raw.decode().splitlines()
                 if line.strip() and not line.lstrip().startswith('#')]
        result['without_explicit_forced_command'] = sum(
            re.search(r'(?:^|,)command="((?:[^"\\]|\\.)*)"', line) is None for line in lines)
        result['effective_sshd_policy'] = 'NOT_ATTESTED'
    return result


def schedule_file(path, kind='cron'):
    try:
        census.require(all(not parent.is_symlink() for parent in (path, *path.parents)), 'SYMLINK')
        return dict(status='OBSERVED', **dispatch_summary(bounded(path), kind))
    except FileNotFoundError:
        return dict(status='ABSENT')
    except (OSError, ValueError, UnicodeError):
        return dict(status='REFUSED')


def system_schedules(root=Path('/')):
    result = {'/etc/crontab': schedule_file(root / 'etc/crontab')}
    for directory in CRON_DIRECTORIES:
        path = root / directory.lstrip('/')
        try:
            census.require(all(not parent.is_symlink() for parent in (path, *path.parents)), 'SYMLINK')
            entries = list(path.iterdir())
            census.require(len(entries) <= 128, 'CRON_DIRECTORY_BOUNDS')
            result[directory] = dict(status='OBSERVED', entries={
                census.digest(entry.name.encode()): schedule_file(entry) for entry in sorted(entries)})
        except FileNotFoundError:
            result[directory] = dict(status='ABSENT')
        except (OSError, ValueError):
            result[directory] = dict(status='REFUSED')
    return result


def account_dispatchers(node):
    result = {}
    for account in ACCOUNTS[node]:
        try:
            entry = pwd.getpwnam(account)
        except KeyError:
            result[account] = dict(status='ACCOUNT_ABSENT')
            continue
        command = subprocess.run(['crontab', '-l', '-u', account], capture_output=True,
            timeout=5, env={'PATH': os.defpath, 'LC_ALL': 'C'})
        if command.returncode == 0:
            cron = dict(status='OBSERVED', **dispatch_summary(command.stdout, 'cron'))
        elif command.returncode == 1 and command.stderr.strip() == f'no crontab for {account}'.encode():
            cron = dict(status='ABSENT')
        else:
            cron = dict(status='REFUSED')
        result[account] = dict(uid=entry.pw_uid, cron=cron,
            default_authorized_keys=schedule_file(Path(entry.pw_dir) / '.ssh/authorized_keys', 'authorized_keys'))
    return result


def process_identity(raw):
    tail = raw.rsplit(b') ', 1)
    census.require(len(tail) == 2, 'PROCESS_STAT')
    fields = tail[1].split()
    census.require(len(fields) >= 20 and fields[19].isdigit(), 'PROCESS_STAT')
    return int(fields[19])


def unit_processes(name, proc=Path('/proc'), groups=Path('/sys/fs/cgroup')):
    census.require(census.UNIT.fullmatch(name), 'UNIT_SCOPE')
    raw = census.systemctl('show', name, '--property=Id,ControlGroup')
    values = dict(line.split('=', 1) for line in raw.splitlines() if '=' in line)
    census.require(values.get('Id') == name, 'UNIT_ID')
    group = values.get('ControlGroup', '')
    if not group:
        return dict(status='NO_CURRENT_CGROUP', processes=[], in_flight='NOT_ATTESTED')
    relative = Path(group.lstrip('/'))
    census.require(group.startswith('/') and '..' not in relative.parts and name in relative.parts,
                   'CGROUP_SCOPE')
    directory = groups / relative
    census.require(all(not parent.is_symlink() for parent in (directory, *directory.parents)), 'CGROUP_SYMLINK')
    paths = [directory]
    records = []
    observed = set()
    while paths:
        current = paths.pop()
        census.require(len(observed) < 128 and current not in observed, 'CGROUP_BOUNDS')
        observed.add(current)
        entries = list(current.iterdir())
        census.require(len(entries) <= 256, 'CGROUP_BOUNDS')
        for entry in entries:
            census.require(not entry.is_symlink(), 'CGROUP_SYMLINK')
            if entry.is_dir():
                paths.append(entry)
        members = bounded(current / 'cgroup.procs', 8192).split()
        census.require(len(members) <= 128 and all(member.isdigit() for member in members), 'PROCESS_BOUNDS')
        for member in members:
            census.require(len(records) < 128, 'PROCESS_BOUNDS')
            process = proc / member.decode()
            try:
                before = process_identity(bounded(process / 'stat', 8192))
                command = bounded(process / 'cmdline')
                after = process_identity(bounded(process / 'stat', 8192))
                census.require(before == after, 'PROCESS_REUSED')
                records.append(dict(pid=int(member), start_ticks=before,
                    command_sha256=census.digest(command), status='OBSERVED'))
            except FileNotFoundError:
                records.append(dict(pid=int(member), status='EXITED_DURING_OBSERVATION'))
    return dict(status='OBSERVED', processes=records, in_flight='NOT_ATTESTED',
                coverage='UNIT_CGROUP_ONLY_NOT_EXTERNAL_SSH_OR_DOCKER_EXEC')


def lock_records(raw, targets):
    census.require(len(raw) <= 2 * 1024 * 1024, 'LOCK_BOUNDS')
    found = {name: [] for name in targets}
    for line in raw.decode('ascii').splitlines():
        fields = line.split()
        waiting = len(fields) > 1 and fields[1] == '->'
        if waiting:
            fields.pop(1)
        census.require(len(fields) >= 8, 'LOCK_FORMAT')
        device = fields[5].split(':')
        census.require(len(device) == 3, 'LOCK_FORMAT')
        identity = (int(device[0], 16), int(device[1], 16), int(device[2]))
        for name, expected in targets.items():
            if identity == expected:
                found[name].append(dict(kind=fields[1], mode=fields[3], pid=int(fields[4]), waiting=waiting))
    return found


def node_locks(root=census.PRODUCT, proc=Path('/proc')):
    targets = {}
    identities = {}
    for name, relative in LOCKS.items():
        path = root / relative
        census.require(all(not parent.is_symlink() for parent in (path, *path.parents)), 'LOCK_SYMLINK')
        info = path.stat()
        census.require(stat.S_ISREG(info.st_mode) and info.st_size == 0 and info.st_nlink == 1, 'LOCK_SHAPE')
        identities[name] = (info.st_dev, info.st_ino)
        targets[name] = (os.major(info.st_dev), os.minor(info.st_dev), info.st_ino)
    result = lock_records(bounded(proc / 'locks', 2 * 1024 * 1024), targets)
    for name, relative in LOCKS.items():
        info = (root / relative).lstat()
        census.require(stat.S_ISREG(info.st_mode) and (info.st_dev, info.st_ino) == identities[name], 'LOCK_REPLACED')
    return dict(status='OBSERVED', locks=result, locks_acquired=False, quiescent=False)


def observed(observer, *arguments):
    try:
        return observer(*arguments)
    except (OSError, ValueError, UnicodeError, subprocess.SubprocessError):
        return dict(status='REFUSED')


def collect(node):
    census.require(node in ACCOUNTS, 'NODE')
    started = time.time_ns()
    names = census.unit_names()
    before = {name: observed(census.observe_unit, name) for name in names}
    processes = {name: observed(unit_processes, name) for name in names if name.endswith('.service')}
    accounts = observed(account_dispatchers, node)
    schedules = observed(system_schedules)
    locks = observed(node_locks)
    after_names = census.unit_names()
    after = {name: observed(census.observe_unit, name) for name in after_names}
    return dict(schema=1, node=node, started_at_ns=started, finished_at_ns=time.time_ns(),
        units_before=before, units_after=after, unit_observations_equal=before == after,
        processes=processes, accounts=accounts, system_schedules=schedules, node_locks=locks,
        coverage='EXPLICIT_ACCOUNTS_LITERAL_SCHEDULES_UNIT_CGROUPS_ONLY',
        unresolved=['HTTP_REQUEST_DRAIN', 'EXTERNAL_SSH_AND_DOCKER_EXEC', 'MANUAL_ADMIN_AND_DEPLOYMENTS',
                    'OWNER_PG_SYNTHETIC_DISPATCHERS', 'CROSS_HOST_CAPTURE_BOUNDARY'],
        capture_permitted=False, all_writers_qualified=False, services_changed=False,
        signals_sent=False, locks_acquired=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--node', choices=tuple(ACCOUNTS), required=True)
    arguments = parser.parse_args()
    census.require(not sys.stdout.isatty() and os.geteuid() == 0, 'PRIVATE_ROOT_CONSUMER_REQUIRED')
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    census.require(signal.getsignal(signal.SIGALRM) == signal.SIG_DFL and
                   signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0), 'ALARM_NOT_EXCLUSIVE')
    signal.alarm(120)
    try:
        print(json.dumps(collect(arguments.node), sort_keys=True))
    finally:
        signal.alarm(0)


if __name__ == '__main__':
    main()
