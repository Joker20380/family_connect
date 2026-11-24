import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import control_ha_writer_preflight as writers


def test_dispatchers_redact_commands_and_keys_without_claiming_policy():
    raw = (b'restrict,command="/opt/apps/family_connect/private-command secret-value" ssh-ed25519 private-key\n'
           b'ssh-ed25519 other-private-key\n# comment\n')
    result = writers.dispatch_summary(raw, 'authorized_keys')
    serialized = json.dumps(result)
    assert all(value not in serialized for value in ('private-command', 'secret-value', 'private-key'))
    assert result['without_explicit_forced_command'] == 1
    assert result['effective_sshd_policy'] == 'NOT_ATTESTED'
    assert result['all_writers_qualified'] is False


@pytest.mark.parametrize('raw', [b'x' * (writers.LIMIT + 1), b'\xff'])
def test_dispatch_bounds_and_encoding_fail_closed(raw):
    with pytest.raises((ValueError, UnicodeError)):
        writers.dispatch_summary(raw, 'cron')


def test_system_schedules_cover_all_directories_and_redact_names(tmp_path):
    directory = tmp_path / 'etc/cron.d'
    directory.mkdir(parents=True)
    (directory / 'private-name').write_text('* * * * * root /opt/apps/family_connect/run secret-token\n')
    (directory / 'unrelated').write_text('* * * * * root /unrelated/command\n')
    (directory / 'empty').write_bytes(b'')
    result = writers.system_schedules(tmp_path)
    raw = json.dumps(result)
    assert len(result) == 6
    assert result['/etc/crontab']['status'] == 'ABSENT'
    assert len(result['/etc/cron.d']['entries']) == 3
    assert all(value not in raw for value in ('private-name', 'secret-token', '/unrelated/command'))
    assert sum(len(entry['scoped_lines']) for entry in result['/etc/cron.d']['entries'].values()) == 1


@pytest.mark.parametrize('kind', ['file', 'directory'])
def test_schedule_symlinks_not_followed(tmp_path, kind):
    target = tmp_path / 'outside'
    target.mkdir()
    (target / 'cron').write_text('private')
    path = tmp_path / 'link'
    path.symlink_to(target / 'cron' if kind == 'file' else target)
    assert writers.schedule_file(path if kind == 'file' else path / 'cron') == {'status': 'REFUSED'}


def test_schedule_directory_bounds(tmp_path):
    directory = tmp_path / 'etc/cron.d'
    directory.mkdir(parents=True)
    for index in range(129):
        (directory / str(index)).touch()
    assert writers.system_schedules(tmp_path)['/etc/cron.d'] == {'status': 'REFUSED'}


def test_account_lookup_is_closed_and_cron_is_read_only(tmp_path, monkeypatch):
    called = []
    def lookup(name):
        if name != 'root':
            raise KeyError(name)
        return SimpleNamespace(pw_uid=0, pw_dir=str(tmp_path))
    def run(command, **kwargs):
        called.append(command)
        assert kwargs['timeout'] == 5 and kwargs['env']['LC_ALL'] == 'C'
        return SimpleNamespace(returncode=1, stderr=b'no crontab for root\n')
    monkeypatch.setattr(writers.pwd, 'getpwnam', lookup)
    monkeypatch.setattr(writers.subprocess, 'run', run)
    result = writers.account_dispatchers('RU')
    assert set(result) == set(writers.ACCOUNTS['RU'])
    assert result['root']['cron']['status'] == 'ABSENT'
    assert result['fc-friends']['status'] == 'ACCOUNT_ABSENT'
    assert called == [['crontab', '-l', '-u', 'root']]


def test_cron_error_not_absence(tmp_path, monkeypatch):
    monkeypatch.setattr(writers, 'ACCOUNTS', {'RU': ('root',)})
    monkeypatch.setattr(writers.pwd, 'getpwnam', lambda name: SimpleNamespace(pw_uid=0, pw_dir=str(tmp_path)))
    monkeypatch.setattr(writers.subprocess, 'run', lambda *args, **kwargs:
                        SimpleNamespace(returncode=1, stderr=b'permission denied'))
    assert writers.account_dispatchers('RU')['root']['cron']['status'] == 'REFUSED'


def test_kernel_locks_filter_inode_and_preserve_waiters():
    raw = (b'1: FLOCK ADVISORY WRITE 123 08:ab:456 0 EOF\n'
           b'1: -> FLOCK ADVISORY WRITE 124 08:ab:456 0 EOF\n'
           b'2: POSIX ADVISORY READ 999 08:ab:987 0 100\n')
    result = writers.lock_records(raw, {'application': (8, 171, 456), 'registration': (8, 171, 10)})
    assert [entry['pid'] for entry in result['application']] == [123, 124]
    assert [entry['waiting'] for entry in result['application']] == [False, True]
    assert result['registration'] == []
    assert '999' not in json.dumps(result)


@pytest.mark.parametrize('raw', [b'invalid', b'1: FLOCK ADVISORY WRITE 1 broken 0 EOF\n', b'x' * (2*1024*1024+1)])
def test_bad_kernel_lock_observation_refused(raw):
    with pytest.raises(ValueError):
        writers.lock_records(raw, {})


def test_unheld_node_locks_are_not_quiescence_and_are_never_created(tmp_path):
    directory = tmp_path / 'friends-awg'
    directory.mkdir()
    for relative in writers.LOCKS.values():
        (tmp_path / relative).touch()
    (tmp_path / 'locks').write_bytes(b'')
    before = {path: path.stat() for path in directory.iterdir()}
    result = writers.node_locks(tmp_path, tmp_path)
    assert result['quiescent'] is False and result['locks_acquired'] is False
    assert all(path.stat() == info for path, info in before.items())
    (directory / 'registration.lock').unlink()
    with pytest.raises(FileNotFoundError):
        writers.node_locks(tmp_path, tmp_path)
    assert not (directory / 'registration.lock').exists()


def process_stat(start):
    return b'12 (name with ) tricky) ' + b' '.join([b'S'] + [b'0'] * 18 + [str(start).encode()])


def test_process_stat_handles_spaces_and_parentheses():
    assert writers.process_identity(process_stat(1234)) == 1234
    with pytest.raises(ValueError):
        writers.process_identity(b'12 broken')


@pytest.fixture
def cgroup(tmp_path, monkeypatch):
    name = 'family-connect-example.service'
    groups = tmp_path / 'cgroup'
    directory = groups / 'system.slice' / name
    directory.mkdir(parents=True)
    (directory / 'cgroup.procs').write_bytes(b'12\n')
    proc = tmp_path / 'proc'
    process = proc / '12'
    process.mkdir(parents=True)
    (process / 'stat').write_bytes(process_stat(100))
    (process / 'cmdline').write_bytes(b'python\0private-token\0')
    monkeypatch.setattr(writers.census, 'systemctl', lambda *args:
                        f'Id={name}\nControlGroup=/system.slice/{name}\n')
    return name, proc, groups, directory


def test_unit_processes_are_pinned_and_redacted(cgroup):
    name, proc, groups, directory = cgroup
    result = writers.unit_processes(name, proc, groups)
    assert result['processes'][0]['start_ticks'] == 100
    assert 'private-token' not in json.dumps(result)
    assert result['in_flight'] == 'NOT_ATTESTED'
    nested = directory / 'child'
    nested.mkdir()
    (nested / 'cgroup.procs').write_bytes(b'99\n')
    assert writers.unit_processes(name, proc, groups)['processes'][1]['status'] == 'EXITED_DURING_OBSERVATION'


def test_unit_cgroup_symlink_refused(cgroup):
    name, proc, groups, directory = cgroup
    (directory / 'escape').symlink_to(proc)
    with pytest.raises(ValueError, match='CGROUP_SYMLINK'):
        writers.unit_processes(name, proc, groups)


def test_pid_reuse_refused(cgroup, monkeypatch):
    name, proc, groups, directory = cgroup
    starts = iter([100, 101])
    monkeypatch.setattr(writers, 'process_identity', lambda raw: next(starts))
    with pytest.raises(ValueError, match='PROCESS_REUSED'):
        writers.unit_processes(name, proc, groups)


@pytest.mark.parametrize('group', ['/system.slice/other.service', '/../family-connect-example.service', 'relative'])
def test_unrelated_cgroup_refused(cgroup, monkeypatch, group):
    name, proc, groups, directory = cgroup
    monkeypatch.setattr(writers.census, 'systemctl', lambda *args: f'Id={name}\nControlGroup={group}\n')
    with pytest.raises(ValueError, match='CGROUP_SCOPE'):
        writers.unit_processes(name, proc, groups)


def test_equal_observations_never_authorize_capture(monkeypatch):
    name = 'family-connect-example.service'
    monkeypatch.setattr(writers.census, 'unit_names', lambda: [name])
    monkeypatch.setattr(writers.census, 'observe_unit', lambda name: {'state': 'running'})
    monkeypatch.setattr(writers, 'unit_processes', lambda name: {'processes': []})
    monkeypatch.setattr(writers, 'account_dispatchers', lambda node: {})
    monkeypatch.setattr(writers, 'system_schedules', lambda: {})
    monkeypatch.setattr(writers, 'node_locks', lambda: {'locks': []})
    result = writers.collect('RU')
    assert result['unit_observations_equal'] is True
    assert result['capture_permitted'] is False and result['all_writers_qualified'] is False
    assert result['services_changed'] is False and result['locks_acquired'] is False
    assert len(result['unresolved']) == 5


def test_observation_error_is_not_empty_success():
    def fail():
        raise PermissionError('private-detail')
    assert writers.observed(fail) == {'status': 'REFUSED'}
