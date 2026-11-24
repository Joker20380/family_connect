import base64
import copy
import io
import json
import tarfile
from types import SimpleNamespace

import pytest

from scripts import control_ha_owner_source_binding as source
from tests.test_control_ha_owner_admission_preflight import container


def archive(raw=b'value = 1\n', name='manage.py', *, kind=tarfile.REGTYPE, extra=False, link=''):
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode='w') as package:
        info = tarfile.TarInfo(name)
        info.size, info.mode, info.type, info.linkname = len(raw), 0o644, kind, link
        package.addfile(info, io.BytesIO(raw))
        if extra:
            package.addfile(info, io.BytesIO(raw))
    header = base64.b64encode(json.dumps(dict(name=name, size=len(raw), mode=0o644, linkTarget=link)).encode()).decode()
    return output.getvalue(), header


class FakeReader:
    def __init__(self):
        self.containers, self.executions, self.calls = set(), set(), []
        self.items = {name: container(name, gate=None) for name in source.preflight.NAMES}
        self.raw = b'import os\npassword = "private-value"\n'
        for name, item in self.items.items():
            item['Image'] = source.IMAGES[name]
            item['Config']['WorkingDir'] = '/app/control_plane'
            item['ExecIDs'] = []
        self.observed = {}

    def inspect(self, name):
        self.calls.append(('inspect', name))
        return copy.deepcopy(next(item for key, item in self.items.items() if name in (key, item['Id'])))

    def source(self, container_id, name):
        self.calls.append(('source', container_id, name))
        return None if name in source.OPTIONAL else self.raw

    def execution(self, execution):
        self.calls.append(('execution', execution))
        return self.observed[execution]


@pytest.fixture
def reader():
    return FakeReader()


@pytest.fixture
def candidate():
    return {name: source.source_record(b'candidate = 1\n') for name in source.SOURCES}


def test_sources_are_observed_twice_without_authorization(reader, candidate):
    result = source.collect(reader, candidate)
    assert result['observations_equal'] and len(reader.calls) == 44
    assert len(result['containers']) == 2
    for item in result['containers']:
        assert len(item['sources']) == len(source.SOURCES)
        assert all(not record['candidate_match'] for record in item['sources'].values())
        assert not item['runtime']['binding']['gate_configured']
    for field in ('capture_permitted', 'all_writers_qualified', 'services_changed', 'commands_executed_in_containers'):
        assert result[field] is False
    for private in ('private-value', 'private-secret', 'command-value', '/private/entry', '/private/host-capture'):
        assert private not in json.dumps(result)
    assert 'MANUAL_DISPATCH_NOT_CLOSED' in result['unresolved']


def test_matching_source_never_proves_loaded_code_or_manual_coverage(reader, candidate):
    reader.source = lambda container_id, name: b'candidate = 1\n'
    result = source.collect(reader, candidate)
    assert all(record['candidate_match'] for item in result['containers'] for record in item['sources'].values())
    assert not result['capture_permitted']
    assert 'LOADED_BYTES_NOT_ATTESTED' in result['unresolved']


def test_running_manual_exec_is_bound_and_redacted(reader, candidate):
    execution = 'e' * 64
    item = reader.items[source.preflight.NAMES[0]]
    item['ExecIDs'] = [execution]
    reader.observed[execution] = dict(ID=execution, ContainerID=item['Id'], Running=True, Pid=456, ExitCode=0,
        ProcessConfig=dict(entrypoint='python', arguments=['manage.py', 'shell', '--password=private-exec'], user='private-user'))
    result = source.collect(reader, candidate)
    record = result['containers'][0]['execution_observations'][0]
    assert record['running'] and record['pid'] == 456
    assert record['command']['known_token_mentions'] == ['manage.py', 'python', 'shell']
    assert 'private-exec' not in json.dumps(result) and 'private-user' not in json.dumps(result)
    assert not record['command']['dispatch_coverage_proved']


@pytest.mark.parametrize('field,value', [('ID', 'f' * 64), ('ContainerID', 'b' * 64),
    ('Running', 1), ('Pid', -1), ('ExitCode', None)])
def test_wrong_exec_binding_refuses(field, value):
    execution = dict(ID='e' * 64, ContainerID='a' * 64, Running=False, Pid=0, ExitCode=0,
                     ProcessConfig=dict(entrypoint='python', arguments=[]))
    execution[field] = value
    with pytest.raises(ValueError):
        source.execution_record(execution, 'e' * 64, 'a' * 64)


@pytest.mark.parametrize('field', ['source', 'container', 'executions', 'working_directory'])
def test_observation_change_refuses(reader, candidate, field):
    original = reader.source
    reads = 0

    def changing(container_id, name):
        nonlocal reads
        reads += 1
        if reads == 2 * len(source.SOURCES) + 1:
            item = reader.items[source.preflight.NAMES[0]]
            if field == 'container':
                item['RestartCount'] += 1
            elif field == 'executions':
                item['ExecIDs'] = ['e' * 64]
            elif field == 'working_directory':
                item['Config']['WorkingDir'] = '/changed'
            else:
                return b'changed = 1\n'
        return original(container_id, name)

    reader.source = changing
    with pytest.raises(ValueError, match='INSTALLED_BINDING_CHANGED'):
        source.collect(reader, candidate)


@pytest.mark.parametrize('executions', [False, '', ['bad'], ['e' * 64] * 2, ['e' * 64] * 65])
def test_invalid_execution_inventory_refuses(reader, candidate, executions):
    reader.items[source.preflight.NAMES[0]]['ExecIDs'] = executions
    with pytest.raises(ValueError):
        source.collect(reader, candidate)
    assert not any(call[0] == 'source' for call in reader.calls)


def test_new_image_refuses_without_reading_its_files(reader, candidate):
    reader.items[source.preflight.NAMES[0]]['Image'] = 'sha256:' + '9' * 64
    with pytest.raises(ValueError, match='INSTALLED_IMAGE_CHANGED'):
        source.collect(reader, candidate)
    assert not any(call[0] == 'source' for call in reader.calls)


def test_nested_mount_resolution(reader):
    item = reader.items[source.preflight.NAMES[0]]
    item['Mounts'] = [dict(Type='bind', Source='/private-parent', Destination='/app', RW=True),
                      dict(Type='tmpfs', Destination='/app/control_plane', RW=False)]
    result = source.covering_mount(item, 'control_plane/manage.py')
    assert result['kind'] == 'tmpfs' and result['readonly']
    assert '/private-parent' not in json.dumps(result)


@pytest.mark.parametrize('raw,mentioned', [
    (b'from control.capture_gate import Gate\n', True),
    (b'from .capture import configured_gate\n', True),
    (b'from fc_control_plane.capture import operation\n', True),
    (b'x = "fc_control_plane.middleware.CaptureAdmission"\n', True),
    (b'# from control.capture_gate import Gate\n', False),
    (b'secret = "private-value"\n', False),
])
def test_source_syntax_is_only_a_redacted_mention(raw, mentioned):
    result = source.source_record(raw)
    assert result['capture_syntax_mentioned'] == mentioned
    assert 'private-value' not in json.dumps(result)


@pytest.mark.parametrize('raw', [b'', b'x' * (source.FILE_LIMIT + 1), b'\xff', b'not valid python ...'])
def test_invalid_source_refuses(raw):
    with pytest.raises(ValueError):
        source.source_record(raw)


def test_regular_archive_reads_without_extracting():
    raw, header = archive()
    assert source.archive_file(raw, header, 'control_plane/manage.py') == b'value = 1\n'


@pytest.mark.parametrize('kind', [tarfile.SYMTYPE, tarfile.LNKTYPE, tarfile.DIRTYPE, tarfile.FIFOTYPE])
def test_nonregular_archive_refused(kind):
    raw, header = archive(kind=kind, link='/private' if kind in (tarfile.SYMTYPE, tarfile.LNKTYPE) else '')
    with pytest.raises(ValueError):
        source.archive_file(raw, header, 'control_plane/manage.py')


@pytest.mark.parametrize('mutation', ['extra', 'path', 'size', 'mode', 'header', 'duplicate', 'oversize', 'gzip', 'truncated'])
def test_archive_shape_refuses(mutation):
    raw, header = archive(extra=mutation == 'extra')
    metadata = json.loads(base64.b64decode(header))
    if mutation == 'path':
        metadata['name'] = '../manage.py'
    elif mutation == 'size':
        metadata['size'] += 1
    elif mutation == 'mode':
        metadata['mode'] = 0o4755
    header = base64.b64encode(json.dumps(metadata).encode()).decode()
    if mutation == 'header':
        header = 'not-base64'
    elif mutation == 'duplicate':
        header = base64.b64encode(b'{"name":"manage.py","name":"manage.py"}').decode()
    elif mutation == 'oversize':
        raw = b'x' * (source.ARCHIVE_LIMIT + 1)
    elif mutation == 'gzip':
        import gzip
        raw = gzip.compress(raw)
    elif mutation == 'truncated':
        raw = raw[:600]
    with pytest.raises(ValueError):
        source.archive_file(raw, header, 'control_plane/manage.py')


def test_only_whitelisted_tokens_leave_command_parser():
    result = source.command_record(['sh', '-ec', 'python manage.py migrate --password private; exec gunicorn'])
    assert result['known_token_mentions'] == ['gunicorn', 'manage.py', 'migrate', 'python', 'sh']
    assert 'private' not in json.dumps(result) and not result['dispatch_coverage_proved']
    assert not source.command_record(['"unclosed'])['lexically_parsed']


@pytest.mark.parametrize('endpoint', ['/containers/other/json', '/containers/' + 'f' * 64 + '/json',
    '/exec/' + 'e' * 64 + '/json', '/containers/a/exec', '/containers/a/archive?path=%2Fetc%2Fshadow'])
def test_unselected_endpoints_refuse_before_network(endpoint, monkeypatch):
    monkeypatch.setattr(source.preflight, 'DockerRead', lambda: pytest.fail('network'))
    with pytest.raises(ValueError, match='READ_SCOPE'):
        source.Reader().request(endpoint)


def test_archive_http_is_get_only_and_bounded(monkeypatch):
    raw, header = archive()
    calls = []
    connection = SimpleNamespace(
        request=lambda *args: calls.append(args), close=lambda: calls.append(('close',)),
        getresponse=lambda: SimpleNamespace(status=200, read=lambda count: (calls.append(('read', count)) or raw),
            getheader=lambda name: header))
    monkeypatch.setattr(source.preflight, 'DockerRead', lambda: connection)
    reader = source.Reader()
    reader.containers.add('a' * 64)
    assert reader.source('a' * 64, 'control_plane/manage.py') == b'value = 1\n'
    assert calls[0] == ('GET', '/containers/' + 'a' * 64 + '/archive?path=%2Fapp%2Fcontrol_plane%2Fmanage.py')
    assert calls[1] == ('read', source.ARCHIVE_LIMIT + 1) and calls[-1] == ('close',)


@pytest.mark.parametrize('optional', [True, False])
def test_missing_only_optional_source_is_an_observation(monkeypatch, optional):
    monkeypatch.setattr(source.preflight, 'DockerRead', lambda: SimpleNamespace(
        request=lambda *args: None, close=lambda: None, getresponse=lambda: SimpleNamespace(status=404)))
    reader = source.Reader()
    reader.containers.add('a' * 64)
    if optional:
        assert reader.source('a' * 64, 'control/capture_gate.py') is None
    else:
        with pytest.raises(ValueError, match='DOCKER_READ_FAILED'):
            reader.source('a' * 64, 'control_plane/manage.py')


def test_candidate_is_closed_and_current():
    records = source.candidate()
    assert set(records) == set(source.SOURCES) and all(item['present'] for item in records.values())


def test_failure_output_is_redacted(monkeypatch, capsys):
    def fail():
        raise ValueError('private-exception')
    monkeypatch.setattr(source, 'collect', fail)
    assert source.main() == 1
    output = capsys.readouterr()
    assert output.out == '' and output.err == 'OWNER_SOURCE_BINDING_REFUSED\n'


def test_observed_source_is_never_executed(tmp_path):
    marker = tmp_path / 'executed'
    raw = f'open({str(marker)!r}, "w").close()\nraise RuntimeError("private")\n'.encode()
    assert source.source_record(raw)['present']
    assert not marker.exists()


@pytest.mark.parametrize('arguments', [['x'] * 129, [False], ['x' * 16385], 'python'])
def test_invalid_argv_is_not_treated_as_covered(arguments):
    with pytest.raises(ValueError, match='COMMAND_SHAPE'):
        source.command_record(arguments)


@pytest.mark.parametrize('status', [400, 403, 500])
def test_error_is_not_optional_absence(monkeypatch, status):
    monkeypatch.setattr(source.preflight, 'DockerRead', lambda: SimpleNamespace(
        request=lambda *args: None, close=lambda: None, getresponse=lambda: SimpleNamespace(status=status)))
    reader = source.Reader()
    reader.containers.add('a' * 64)
    with pytest.raises(ValueError, match='DOCKER_READ_FAILED'):
        reader.source('a' * 64, 'control/capture_gate.py')


@pytest.mark.parametrize('failure', ['oversize', 'duplicates'])
def test_json_response_bounds_and_duplicate_refusal(monkeypatch, failure):
    raw = b'x' * (source.preflight.LIMIT + 1) if failure == 'oversize' else b'{"Id":1,"Id":2}'
    closed = []
    monkeypatch.setattr(source.preflight, 'DockerRead', lambda: SimpleNamespace(
        request=lambda *args: None, close=lambda: closed.append(True),
        getresponse=lambda: SimpleNamespace(status=200, read=lambda count: raw)))
    with pytest.raises(ValueError):
        source.Reader().inspect(source.preflight.NAMES[0])
    assert closed == [True]


def test_archive_cannot_read_secret_path_even_in_selected_container(monkeypatch):
    monkeypatch.setattr(source.preflight, 'DockerRead', lambda: pytest.fail('network'))
    reader = source.Reader()
    reader.containers.add('a' * 64)
    with pytest.raises(ValueError, match='ARCHIVE_SCOPE'):
        reader.source('a' * 64, 'control_plane/.env')


def test_unrelated_exec_cannot_be_substituted(reader, candidate):
    execution = 'e' * 64
    reader.items[source.preflight.NAMES[0]]['ExecIDs'] = [execution]
    reader.observed[execution] = dict(ID=execution, ContainerID='f' * 64, Running=False, Pid=0, ExitCode=0)
    with pytest.raises(ValueError, match='EXEC_BINDING'):
        source.collect(reader, candidate)
