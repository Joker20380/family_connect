import json
import subprocess
from types import SimpleNamespace

import pytest

from scripts import control_ha_reload_diagnosis as diagnosis


@pytest.fixture
def observed(tmp_path, monkeypatch):
    monkeypatch.setattr(diagnosis, 'manager_view', lambda: {'mount': [1, 2], 'root': [3, 4]})
    root = tmp_path / 'units'
    root.mkdir()
    manager = dict(Version=diagnosis.VERSION, UnitPath=[str(root), str(tmp_path / 'missing')])
    unit = dict(Id=diagnosis.UNIT, Names=[diagnosis.UNIT], LoadState='loaded', NeedDaemonReload=True,
                FragmentPath='', SourcePath='', DropInPaths=[])
    calls = []
    def run(arguments):
        calls.append(arguments)
        assert arguments[0] == 'get-property' and arguments[1] == 'org.freedesktop.systemd1'
        if arguments[3].endswith('.Manager'):
            fields, values = diagnosis.MANAGER_FIELDS, manager
        else:
            assert arguments[2] == '/org/freedesktop/systemd1/unit/_2d_2eslice'
            fields, values = diagnosis.UNIT_FIELDS, unit
        return b'\n'.join(json.dumps(dict(type=signature, data=values[name])).encode()
                          for name, signature in fields.items())
    monkeypatch.setattr(diagnosis, 'run', run)
    return root, manager, unit, calls


@pytest.mark.parametrize('outdated', [True, False])
def test_empty_builtin_sentinel_distinguishes_manager_flag_without_permit(observed, outdated):
    root, manager, unit, calls = observed
    unit['NeedDaemonReload'] = outdated
    result = diagnosis.observe()
    assert result['classification'] == ('MANAGER_WIDE_OUTDATED_WITNESS' if outdated else 'NO_MANAGER_WIDE_OUTDATED_WITNESS')
    assert result['need_daemon_reload'] is outdated and result['checked_absent_paths'] == 6
    assert result['started_at_ns'] <= result['finished_at_ns']
    assert all(result[name] is False for name in ('capture_permitted', 'reload_performed',
        'services_changed', 'full_unit_equivalence', 'originating_operation_identified'))
    assert list(root.iterdir()) == [] and len(calls) == 4


@pytest.mark.parametrize('change', [
    {'Id': 'other.slice'}, {'Names': ['-.slice', 'alias.slice']}, {'LoadState': 'not-found'},
    {'NeedDaemonReload': 'yes'}, {'NeedDaemonReload': 1}, {'FragmentPath': '/unit'},
    {'SourcePath': '/proc/self/mountinfo'}, {'DropInPaths': ['/drop-in']}, {'Names': [1]},
])
def test_ambiguous_sentinel_does_not_explain_reload(observed, change):
    observed[2].update(change)
    with pytest.raises(ValueError, match='RELOAD_DIAGNOSIS_REFUSED'):
        diagnosis.observe()


@pytest.mark.parametrize('change', [
    {'Version': '259'}, {'UnitPath': []}, {'UnitPath': ['/a', '/a']},
    {'UnitPath': ['relative']}, {'UnitPath': ['/']}, {'UnitPath': ['//units']},
    {'UnitPath': ['/units/../other']}, {'UnitPath': ['/a\x00b']}, {'UnitPath': [False]},
])
def test_unqualified_manager_or_lookup_paths_refuse(observed, change):
    observed[1].update(change)
    with pytest.raises(ValueError, match='RELOAD_DIAGNOSIS_REFUSED'):
        diagnosis.observe()


@pytest.mark.parametrize('relative', diagnosis.RELATIVES)
@pytest.mark.parametrize('kind', ['file', 'directory', 'dangling_symlink'])
def test_possible_unit_or_dropin_source_prevents_inference(observed, relative, kind):
    path = observed[0] / relative
    if kind == 'file':
        path.write_bytes(b'[Unit]\n')
    elif kind == 'directory':
        path.mkdir()
    else:
        path.symlink_to(observed[0] / 'absent-target')
    with pytest.raises(ValueError, match='RELOAD_DIAGNOSIS_REFUSED'):
        diagnosis.observe()
    assert path.exists() or path.is_symlink()


def test_changed_flag_during_observation_refuses(observed, monkeypatch):
    original = diagnosis.snapshot
    def snapshot():
        result = original()
        observed[2]['NeedDaemonReload'] = False
        return result
    monkeypatch.setattr(diagnosis, 'snapshot', snapshot)
    with pytest.raises(ValueError, match='RELOAD_DIAGNOSIS_REFUSED'):
        diagnosis.observe()


def test_permission_error_is_not_absence(observed, monkeypatch):
    def denied(*args):
        raise PermissionError('private-value')
    monkeypatch.setattr(diagnosis.Path, 'lstat', denied)
    with pytest.raises(PermissionError):
        diagnosis.observe()


@pytest.mark.parametrize('raw', [b'{}', b'{', b'{"type":"b","data":false}', b'{"type":"s","data":1}'])
def test_bad_bus_reply_refuses(monkeypatch, raw):
    monkeypatch.setattr(diagnosis, 'run', lambda *args: raw)
    with pytest.raises(ValueError):
        diagnosis.properties('/object', 'Unit', {'Id': 's'})


def test_command_is_bounded_read_only_and_drops_external_bus_environment(monkeypatch):
    monkeypatch.setenv('DBUS_SYSTEM_BUS_ADDRESS', 'private-value')
    def run(arguments, **options):
        assert arguments == ['/usr/bin/busctl', '--system', '--json=short', '--timeout=2', '--', 'get-property']
        assert options == dict(capture_output=True, timeout=3, cwd='/', env={'PATH': '/usr/bin:/bin', 'LANG': 'C'})
        return subprocess.CompletedProcess(arguments, 0, b'{}', b'')
    monkeypatch.setattr(subprocess, 'run', run)
    assert diagnosis.run(['get-property']) == b'{}'


@pytest.mark.parametrize('failure', ['timeout', 'exit', 'stderr', 'oversized'])
def test_query_failure_never_returns_evidence(monkeypatch, failure):
    def run(arguments, **options):
        if failure == 'timeout':
            raise subprocess.TimeoutExpired(arguments, 3)
        return subprocess.CompletedProcess(arguments, 1 if failure == 'exit' else 0,
            b'x' * 65537 if failure == 'oversized' else b'{}', b'private' if failure == 'stderr' else b'')
    monkeypatch.setattr(subprocess, 'run', run)
    with pytest.raises((ValueError, subprocess.TimeoutExpired)):
        diagnosis.run(['get-property'])


def test_cli_error_is_sanitized(monkeypatch, capsys):
    monkeypatch.setattr(diagnosis.os, 'geteuid', lambda: 0)
    def observe():
        raise OSError('private-value')
    monkeypatch.setattr(diagnosis, 'observe', observe)
    assert diagnosis.main() == 1
    output = capsys.readouterr().out
    assert 'private-value' not in output
    assert json.loads(output)['classification'] == 'RELOAD_DIAGNOSIS_REFUSED'


@pytest.mark.parametrize('different', ['/proc/1/ns/mnt', '/proc/1/root', None])
def test_manager_filesystem_view_must_match(monkeypatch, different):
    monkeypatch.setattr(diagnosis.os, 'stat', lambda path: SimpleNamespace(st_dev=1, st_ino=3 if path == different else 2))
    if different:
        with pytest.raises(ValueError, match='RELOAD_DIAGNOSIS_REFUSED'):
            diagnosis.manager_view()
    else:
        assert diagnosis.manager_view() == {'mount': [1, 2], 'root': [1, 2]}
