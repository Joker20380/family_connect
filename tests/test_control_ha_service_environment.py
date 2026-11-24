import json
import os
from types import SimpleNamespace

import pytest

from scripts import control_ha_service_environment as probe


@pytest.mark.parametrize('raw,expected', [
    (b'', {}),
    (b'# comment\n; comment\n ONE=first\nONE=second\nEMPTY=\n', {'ONE': 'second', 'EMPTY': ''}),
    (b'A=  two words  \nB=" spaced value "\nC=\'single # literal\'\n',
     {'A': 'two words', 'B': ' spaced value ', 'C': 'single # literal'}),
    (b'PATH=$HOME/relative\nPERCENT=%i\nHASH=literal#value\n',
     {'PATH': '$HOME/relative', 'PERCENT': '%i', 'HASH': 'literal#value'}),
])
def test_explicit_literal_file_subset(raw, expected):
    assert probe.environment_file(raw) == expected


@pytest.mark.parametrize('raw', [b'export TOKEN=value', b'BAD-NAME=value', b'=value', b' A =value',
    b'A="unterminated', b'A=\'unterminated', b'A=one\\ two', b'A="one\\n"', b'A="first\nsecond"',
    b'A=prefix"quoted"', b'A=one\r\n', b'A=\x00', b'A=\xff', b'A=x\n' * 20000])
def test_unsupported_file_syntax_refuses_instead_of_guessing(raw):
    with pytest.raises((ValueError, UnicodeError)):
        probe.environment_file(raw)


@pytest.mark.parametrize('raw', [b'A=value', b'A=x\x00A=y\x00', b'A=x\x00\x00', b'=x\x00',
    b'A=\xff\x00', b'A=' + b'x' * 262144 + b'\x00'])
def test_process_environment_shape_refuses(raw):
    with pytest.raises((ValueError, UnicodeError)):
        probe.process_environment(raw)


def test_systemd_precedence_unset_and_no_value_disclosure():
    result = probe.compare(['TOKEN=loaded-secret', 'KEEP=base', 'DROP=bad', 'REMOVED=bad'],
        [b'TOKEN=file-secret\nKEEP=first\n', b'KEEP=last\n'], ['DROP=bad', 'REMOVED', 'MANAGER_ONLY'],
        b'TOKEN=file-secret\x00KEEP=last\x00UNRELATED=private\x00')
    assert result['classification'] == 'SELECTED_ENVIRONMENT_MATCH'
    assert result['unqualified_process_names'] == 1
    assert result['compared_names'] == ['DROP', 'KEEP', 'MANAGER_ONLY', 'REMOVED', 'TOKEN']
    serialized = json.dumps(result)
    assert all(value not in serialized for value in ('loaded-secret', 'file-secret', 'last', 'private', 'UNRELATED'))


def test_mismatch_missing_and_failed_unset_are_not_matches():
    result = probe.compare(['TOKEN=expected', 'MISSING=value', 'DROP=value'], [], ['DROP'],
        b'TOKEN=actual\x00DROP=value\x00')
    assert result['classification'] == 'SELECTED_ENVIRONMENT_DIFFER'
    assert result['missing_names'] == ['MISSING']
    assert result['mismatched_names'] == ['TOKEN']
    assert result['unexpectedly_present_names'] == ['DROP']
    assert probe.compare(['A=kept'], [], ['A=other'], b'A=kept\x00')['classification'].endswith('_MATCH')


@pytest.mark.parametrize('environment,files,unset', [([], [], []), (['INVALID'], [], []),
    (['A=x'], [b''] * 9, []), (['A=x'], [], ['BAD-NAME']), (['A=x'], [], ['UNKNOWN=value'])])
def test_unknown_or_unbounded_inputs_refuse(environment, files, unset):
    with pytest.raises(ValueError, match='SERVICE_ENVIRONMENT_REFUSED'):
        probe.compare(environment, files, unset, b'A=x\x00')


@pytest.mark.parametrize('unsafe', ['symlink', 'hardlink', 'writable', 'oversized', 'parent_symlink'])
def test_file_pins_reject_unsafe_files(tmp_path, unsafe):
    target = tmp_path / 'environment'
    target.write_text('A=synthetic-private')
    target.chmod(0o600)
    if unsafe == 'symlink':
        alias = tmp_path / 'alias'
        alias.symlink_to(target)
        target = alias
    elif unsafe == 'hardlink':
        (tmp_path / 'alias').hardlink_to(target)
    elif unsafe == 'writable':
        target.chmod(0o666)
    elif unsafe == 'oversized':
        target.write_bytes(b'x' * 65537)
    else:
        alias = tmp_path / 'alias'
        alias.symlink_to(tmp_path, target_is_directory=True)
        target = alias / target.name
    with pytest.raises(ValueError, match='SERVICE_ENVIRONMENT_REFUSED'):
        probe.read_file(target, owner=os.geteuid())


def test_pins_contain_no_environment_values(tmp_path):
    target = tmp_path / 'environment'
    target.write_text('TOKEN=synthetic-private')
    target.chmod(0o600)
    raw, pin = probe.read_file(target, owner=os.geteuid())
    assert raw == b'TOKEN=synthetic-private' and len(pin['sha256']) == 64
    assert 'synthetic-private' not in json.dumps(pin)


@pytest.mark.parametrize('spelling', ['relative.env', '/tmp/../file', '/tmp/./file', '/tmp//file',
    '//tmp/file', '/tmp/file/', '/tmp/%i.env', '/tmp/*.env', '/tmp/?.env', '/tmp/[a].env', '/tmp/\nfile'])
def test_literal_paths_refuse_unexpanded_or_ambiguous_inputs(spelling):
    with pytest.raises(ValueError, match='SERVICE_ENVIRONMENT_REFUSED'):
        probe.literal_path(spelling)


@pytest.fixture
def observation(monkeypatch):
    state = SimpleNamespace(properties={
        'ActiveState': 'active', 'SubState': 'running', 'ControlPID': 0, 'MainPID': 123,
        'InvocationID': [1] * 16, 'NeedDaemonReload': False,
        'EnvironmentFiles': [['/scoped/provider.env', False]], 'Environment': ['MODE=loaded'],
        'UnsetEnvironment': [], 'ExecStopPost': [
            ['/usr/bin/python3', ['/usr/bin/python3', '-B', '/scoped/stop.py', 'fixed'], False, 0, 0, 0, 0, 0, 0, 0]],
    }, calls=0, file_calls=0, process_calls=0, drift=None, mode='file-secret')
    monkeypatch.setattr(probe.os, 'geteuid', lambda: 0)

    def properties():
        state.calls += 1
        current = dict(state.properties)
        if state.calls == 2 and state.drift == 'unit':
            current['InvocationID'] = [2] * 16
        return current

    def read_file(spelling):
        state.file_calls += 1
        raw = b'import os\n' if spelling.endswith('.py') else b'MODE=file-secret\n'
        digest = probe.digest(raw)
        if state.file_calls > 2 and state.drift == 'file':
            digest = '0' * 64
        return raw, dict(metadata=[1], sha256=digest)

    def process_snapshot(pid):
        assert pid == 123
        state.process_calls += 1
        ticks = '2' if state.process_calls == 2 and state.drift == 'process' else '1'
        return ticks, ('MODE=' + state.mode).encode() + b'\x00'

    monkeypatch.setattr(probe, 'properties', properties)
    monkeypatch.setattr(probe, 'read_file', read_file)
    monkeypatch.setattr(probe, 'process_snapshot', process_snapshot)
    return state


def test_observation_binds_process_and_hook_without_executing_or_disclosing(observation):
    result = probe.observe()
    assert result['classification'] == 'SELECTED_ENVIRONMENT_MATCH'
    assert result['stop_post'][0]['imports'] == ['os']
    assert result['stop_post'][0]['executed'] is False
    assert all(result[key] is False for key in ('services_changed', 'helper_executed',
        'full_runtime_qualified', 'capture_permitted', 'independent_approval', 'values_disclosed'))
    assert 'file-secret' not in json.dumps(result)
    assert observation.calls == observation.process_calls == 2 and observation.file_calls == 4


@pytest.mark.parametrize('flags', [[], ['-I', '-B'], ['-E', '-s', '-B'], ['-u']])
def test_python_hook_flags_preserved_without_execution(observation, flags):
    observation.properties['ExecStopPost'][0][1] = ['/usr/bin/python3', *flags, '/scoped/stop.py', '/private/output']
    assert probe.observe()['stop_post'][0]['executed'] is False


@pytest.mark.parametrize('argument', ['-c', '-m', '-X', '--', '-S'])
def test_unqualified_python_dispatch_refuses(observation, argument):
    observation.properties['ExecStopPost'][0][1][1] = argument
    with pytest.raises(ValueError, match='SERVICE_ENVIRONMENT_REFUSED'):
        probe.observe()


def test_missing_optional_file_is_checked_again_without_exposing_values(observation, monkeypatch, tmp_path):
    missing = tmp_path / 'absent.env'
    observation.properties['EnvironmentFiles'] = [[str(missing), True]]
    observation.properties['Environment'] = ['MODE=file-secret']
    observation.properties['ExecStopPost'] = []

    def read_missing(spelling):
        assert spelling == str(missing)
        raise FileNotFoundError

    monkeypatch.setattr(probe, 'read_file', read_missing)
    result = probe.observe()
    assert result['absent_optional_files'] == [str(missing)]
    assert result['classification'] == 'SELECTED_ENVIRONMENT_MATCH'
    assert 'file-secret' not in json.dumps(result)
    missing.symlink_to(tmp_path / 'still-absent')
    with pytest.raises(ValueError, match='SERVICE_ENVIRONMENT_REFUSED'):
        probe.observe()


def test_optional_glob_is_not_treated_as_an_absent_literal(observation):
    observation.properties['EnvironmentFiles'] = [['/scoped/*.env', True]]
    with pytest.raises(ValueError, match='SERVICE_ENVIRONMENT_REFUSED'):
        probe.observe()


@pytest.mark.parametrize('drift', ['unit', 'process', 'file'])
def test_drift_during_readback_refuses(observation, drift):
    observation.drift = drift
    with pytest.raises(ValueError, match='SERVICE_ENVIRONMENT_REFUSED'):
        probe.observe()


def test_different_process_environment_is_reported_not_approved(observation):
    observation.mode = 'unexpected-private'
    result = probe.observe()
    assert result['classification'] == 'SELECTED_ENVIRONMENT_DIFFER'
    assert result['mismatched_names'] == ['MODE']
    assert 'unexpected-private' not in json.dumps(result)


@pytest.mark.parametrize('change', ['inactive', 'control', 'shell_hook', 'relative_hook', 'invalid_pid'])
def test_unsupported_or_busy_runtime_refuses(observation, change):
    if change == 'inactive':
        observation.properties['ActiveState'] = 'inactive'
    elif change == 'control':
        observation.properties['ControlPID'] = 321
    elif change == 'shell_hook':
        observation.properties['ExecStopPost'][0][1][0] = '/bin/sh'
    elif change == 'relative_hook':
        observation.properties['ExecStopPost'][0][1][2] = 'relative.py'
    else:
        observation.properties['InvocationID'] = [True] * 16
    with pytest.raises(ValueError, match='SERVICE_ENVIRONMENT_REFUSED'):
        probe.observe()


def test_main_sanitizes_exception(capsys, monkeypatch):
    def fail():
        raise ValueError('synthetic-private-value')

    monkeypatch.setattr(probe, 'observe', fail)
    assert probe.main() == 2
    result = capsys.readouterr()
    assert 'synthetic-private-value' not in result.out + result.err
    assert json.loads(result.out)['capture_permitted'] is False
