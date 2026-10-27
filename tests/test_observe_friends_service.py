import copy
import json
import subprocess
from types import SimpleNamespace

import pytest

from scripts import observe_friends_service as observer

EXPECTED = ['/runtime/python', '-I', '/artifacts/accepted.pyz', '--port', '18086']
UNIT_PATH = observer.MANAGER_PATH + '/unit/friends'


def variant(kind, value):
    return {'type': kind, 'data': value}


def properties():
    unit = {name: variant(kind, value) for name, kind, value in (
        ('Id', 's', observer.UNIT), ('ActiveState', 's', 'active'), ('SubState', 's', 'running'),
        ('FragmentPath', 's', '/etc/systemd/system/' + observer.UNIT),
        ('DropInPaths', 'as', ['/etc/systemd/system/' + observer.UNIT + '.d/zzz.conf']),
        ('NeedDaemonReload', 'b', False), ('Job', '(uo)', [0, '/']))}
    service = {name: variant(kind, value) for name, kind, value in (
        ('MainPID', 'u', 123), ('Result', 's', 'success'), ('NRestarts', 'u', 0),
        ('ExecMainStartTimestamp', 't', 1793124336363230),
        ('ExecMainStartTimestampMonotonic', 't', 4859529630329),
        ('User', 's', ''), ('Group', 's', ''), ('WorkingDirectory', 's', ''),
        ('Environment', 'as', ['TOKEN=private-test-value', 'PYTHONDONTWRITEBYTECODE=1']),
        ('ExecStart', 'a(sasbttttuii)', [[EXPECTED[0], EXPECTED.copy(), False, 0, 0, 0, 0, 123, 0, 0]]))}
    return unit, service


class FixtureBus:
    def __init__(self):
        self.unit, self.service = properties()
        self.job_rows = []
        self.calls = []
        self.change = None

    def call(self, path, interface, method, signature, *arguments):
        self.calls.append(method)
        if self.change:
            self.change(self, method)
        if method == 'GetUnit':
            return UNIT_PATH
        if method == 'ListJobs':
            return copy.deepcopy(self.job_rows)
        return copy.deepcopy(self.unit if arguments[-1].endswith('.Unit') else self.service)


def process_fixture(pid):
    return {'pid': pid, 'start_ticks': 80, 'argv_sha256': observer.digest(EXPECTED)}


def observe(bus):
    return observer.observe(EXPECTED, bus=bus, read_process=process_fixture)


def test_empty_jobs_and_complete_stable_readback_are_sanitized():
    bus = FixtureBus()
    receipt = observe(bus)
    assert receipt['jobs']['count'] == 0
    assert receipt['service']['effective_execstart_matches']
    assert receipt['service']['running_argv_matches']
    assert receipt['service']['environment_names'] == ['PYTHONDONTWRITEBYTECODE', 'TOKEN']
    assert 'private-test-value' not in json.dumps(receipt)
    assert EXPECTED[2] not in json.dumps(receipt)
    assert receipt['restarts'] == 0
    assert bus.calls == ['GetUnit', 'ListJobs', 'GetAll', 'GetAll', 'GetAll', 'GetAll', 'ListJobs']


@pytest.mark.parametrize('target', [False, True])
def test_nonempty_jobs_have_same_typed_contract(target):
    bus = FixtureBus()
    bus.job_rows = [[1, observer.UNIT if target else 'other.service', 'start', 'running',
        '/org/freedesktop/systemd1/job/1', UNIT_PATH]]
    receipt = observe(bus)
    assert receipt['jobs']['count'] == 1
    assert receipt['jobs']['target_count'] == int(target)
    assert 'other.service' not in json.dumps(receipt)


@pytest.mark.parametrize('rows', [None, {}, [1], [[True, 'a', 'b', 'c', '/', '/']],
    [[1, 'a', 'b', 'c', '/', '/'], [1, 'a', 'b', 'c', '/', '/']], [[1, 'a', 'b', 'c', 'bad', '/']]])
def test_malformed_jobs_fail_closed(rows):
    bus = FixtureBus()
    bus.job_rows = rows
    with pytest.raises(observer.ObservationError, match='ListJobs:'):
        observe(bus)


@pytest.mark.parametrize('raw,signature,code', [
    (b'', 'o', 'INVALID_JSON'), (b'JOB UNIT TYPE STATE\n', 'o', 'INVALID_JSON'),
    (b'{"type":"o","type":"s","data":["/"]}', 'o', 'INVALID_JSON'),
    (b'{"type":"o","data":[NaN]}', 'o', 'INVALID_JSON'),
    (b'\xff', 'o', 'INVALID_JSON'), (b'[]', 'o', 'INVALID_TYPED_RESPONSE'),
    (b'{"type":"s","data":["/"]}', 'o', 'INVALID_TYPED_RESPONSE'),
    (b'{"type":"o","data":[]}', 'o', 'INVALID_TYPED_RESPONSE'),
    (b'{"type":"o","data":["/"],"extra":1}', 'o', 'INVALID_TYPED_RESPONSE'),
    (b'x' * (observer.MAX_RESPONSE + 1), 'o', 'RESPONSE_SIZE')])
def test_invalid_transport_has_stage_and_no_raw_content(raw, signature, code):
    with pytest.raises(observer.ObservationError) as caught:
        observer.decode_response(raw, signature, 'GetUnit')
    assert (caught.value.stage, caught.value.code) == ('GetUnit', code)


@pytest.mark.parametrize('rows', [[], [[4, 'other.service', 'start', 'waiting', '/', '/']]])
def test_bus_decodes_typed_empty_and_nonempty_jobs(rows):
    def runner(command, **kwargs):
        assert command == ['/usr/bin/busctl', '--system', '--json=short', 'call', observer.DESTINATION,
            observer.MANAGER_PATH, observer.DESTINATION + '.Manager', 'ListJobs']
        assert kwargs['stderr'] == subprocess.DEVNULL and kwargs['timeout'] == 10
        return SimpleNamespace(returncode=0, stdout=json.dumps({'type': 'a(usssoo)', 'data': [rows]}).encode())
    assert observer.jobs(observer.Bus(runner))['count'] == len(rows)


@pytest.mark.parametrize('failure,code', [('timeout', 'BUS_TIMEOUT'), ('missing', 'BUS_UNAVAILABLE'),
    ('exit', 'BUS_CALL_FAILED')])
def test_transport_failures_suppress_private_stderr(failure, code):
    def runner(command, **kwargs):
        if failure == 'timeout':
            raise subprocess.TimeoutExpired(command, 10, stderr=b'private-test-value')
        if failure == 'missing':
            raise OSError('private-test-value')
        return SimpleNamespace(returncode=1, stdout=b'private-test-value')
    with pytest.raises(observer.ObservationError) as caught:
        observer.jobs(observer.Bus(runner))
    assert caught.value.code == code
    assert 'private-test-value' not in str(caught.value)


def test_transport_cannot_mutate_unit():
    with pytest.raises(observer.ObservationError, match='UNSUPPORTED_READ'):
        observer.Bus().call(observer.MANAGER_PATH, observer.DESTINATION + '.Manager',
            'RestartUnit', 'o', 'ss', observer.UNIT, 'replace')


@pytest.mark.parametrize('name,changed', [('MainPID', None), ('MainPID', variant('u', True)),
    ('NRestarts', variant('u', -1)), ('Result', variant('b', True)),
    ('Environment', variant('as', ['BAD'])), ('Environment', variant('as', ['X=1', 'X=2'])),
    ('ExecStart', variant('as', [])), ('ExecStart', variant('a(sasbttttuii)', [])),
    ('ExecStart', variant('a(sasbttttuii)', [[], []]))])
def test_missing_or_wrong_properties(name, changed):
    bus = FixtureBus()
    if changed is None:
        del bus.service[name]
    else:
        bus.service[name] = changed
    with pytest.raises(observer.ObservationError):
        observe(bus)


@pytest.mark.parametrize('change', ['archive', 'port', 'extra', 'path', 'ignore', 'bad_type'])
def test_exact_execstart_not_dropin_presence(change):
    bus = FixtureBus()
    row = bus.service['ExecStart']['data'][0]
    if change == 'archive': row[1][2] = '/other.pyz'
    if change == 'port': row[1][-1] = '8080'
    if change == 'extra': row[1].append('--secret=private-test-value')
    if change == 'path': row[0] = '/other/python'
    if change == 'ignore': row[2] = True
    if change == 'bad_type': row[-1] = True
    if change in ('path', 'ignore', 'bad_type'):
        with pytest.raises(observer.ObservationError): observe(bus)
    else:
        receipt = observe(bus)
        assert not receipt['service']['effective_execstart_matches']
        assert 'private-test-value' not in json.dumps(receipt)


@pytest.mark.parametrize('field', ['MainPID', 'NRestarts', 'Environment', 'ExecMainStartTimestampMonotonic'])
def test_race_between_service_snapshots(field):
    bus = FixtureBus()
    def change(fixture, method):
        if fixture.calls.count('GetAll') == 4:
            value = fixture.service[field]['data']
            fixture.service[field]['data'] = value + ['OTHER=value'] if type(value) is list else value + 1
    bus.change = change
    with pytest.raises(observer.ObservationError, match='SERVICE_CHANGED_DURING_READ'):
        observe(bus)


def test_race_between_job_snapshots():
    bus = FixtureBus()
    def change(fixture, method):
        if fixture.calls.count('ListJobs') == 2:
            fixture.job_rows = [[2, 'other.service', 'start', 'waiting', '/', '/']]
    bus.change = change
    with pytest.raises(observer.ObservationError, match='JOBS_CHANGED_DURING_READ'):
        observe(bus)


def test_pid_reuse_detected():
    reads = []
    def read_process(pid):
        reads.append(pid)
        return dict(process_fixture(pid), start_ticks=len(reads))
    with pytest.raises(observer.ObservationError, match='SERVICE_CHANGED_DURING_READ'):
        observer.observe(EXPECTED, bus=FixtureBus(), read_process=read_process)


def test_selected_candidate_may_be_observed_before_restart():
    old = EXPECTED.copy()
    old[2] = '/artifacts/old.pyz'
    receipt = observer.observe(EXPECTED, old, bus=FixtureBus(), read_process=lambda pid:
        dict(process_fixture(pid), argv_sha256=observer.digest(old)))
    assert receipt['service']['effective_execstart_matches'] and receipt['service']['running_argv_matches']


def test_proc_reader_handles_comm_parentheses_without_exposing_arguments(tmp_path):
    directory = tmp_path / '123'
    directory.mkdir()
    (directory / 'stat').write_text('123 (comm (with) spaces) S ' + '0 ' * 18 + '80 0 0')
    (directory / 'cmdline').write_bytes(b'/python\0--secret=private-test-value\0')
    result = observer.process(123, tmp_path)
    assert result['start_ticks'] == 80
    assert 'private-test-value' not in json.dumps(result)


@pytest.mark.parametrize('pid', [0, True, -1, 123])
def test_unavailable_process_fails_closed(pid, tmp_path):
    with pytest.raises(observer.ObservationError): observer.process(pid, tmp_path)


def test_cli_structured_error(monkeypatch, capsys):
    def fail(*args, **kwargs):
        raise observer.ObservationError('GetAll:Service', 'BUS_TIMEOUT')
    monkeypatch.setattr(observer, 'observe', fail)
    assert observer.main(['--python', '/python', '--archive', '/candidate.pyz']) == 1
    assert json.loads(capsys.readouterr().out) == {'schema': 1, 'result': 'OBSERVATION_BLOCKED',
        'stage': 'GetAll:Service', 'code': 'BUS_TIMEOUT', 'restarts': 0}
