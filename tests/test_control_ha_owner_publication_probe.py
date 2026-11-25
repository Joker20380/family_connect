import copy
import json
from pathlib import Path
import time

import pytest

from scripts import control_ha_owner_publication_probe as probe


def receipt():
    now = time.time_ns()
    return dict(purpose='family-connect/owner-publication-pg-boundary/v1', timeout_ms=2000,
                locked_at_ns=now, observed_at_ns=now, released_at_ns=now, finished_at_ns=now,
                external_settlement_proven=False, capture_permitted=False, rollback_acknowledged=True,
                message_counts=dict(draft=1, queued=0, unknown=0, refused=0, published=1))


@pytest.mark.parametrize('field,value', [('external_settlement_proven', True), ('capture_permitted', True),
    ('rollback_acknowledged', False), ('timeout_ms', 6000), ('purpose', 'another-proof'), ('released_at_ns', 0),
    ('locked_at_ns', 2 ** 80), ('finished_at_ns', 2 ** 80)])
def test_receipt_cannot_claim_more_than_the_observed_boundary(field, value):
    value_before = time.time_ns()
    observed = receipt()
    observed[field] = value
    with pytest.raises(ValueError):
        probe.validate_receipt(observed, value_before, time.time_ns())


@pytest.mark.parametrize('counts', [dict(unknown=1), dict(draft=True), dict(queued=-1), dict(other=0)])
def test_uncertain_or_malformed_counts_refuse(counts):
    started = time.time_ns()
    observed = receipt()
    observed['message_counts'].update(counts)
    with pytest.raises(ValueError, match='PUBLICATION_RECEIPT_UNCERTAIN'):
        probe.validate_receipt(observed, started, time.time_ns())


@pytest.fixture
def composed(tmp_path, monkeypatch):
    events = []
    items = {role: dict(Id=role + '-synthetic', Image=image, RestartCount=0,
                       State=dict(Running=True, Paused=False, Restarting=False, Pid=100, StartedAt='synthetic',
                                  Health=dict(Status='healthy')),
                       NetworkSettings=dict(Ports={'8000/tcp': [{'HostIp': '127.0.0.1', 'HostPort': '8765'}]}))
             for role, image in probe.IMAGES.items()}
    class API:
        def inspect(self, reference):
            return copy.deepcopy(next(item for role, item in items.items()
                                      if reference in ('fc-control-plane-0-' + role + '-1', item['Id'])))
    class Held:
        def __init__(self, *args, **kwargs):
            assert kwargs == dict(seconds=12)
            self.statuses = []
        def __enter__(self):
            events.append('dispatcher-held')
            return self
        def check(self):
            events.append('dispatcher-checked')
        def __exit__(self, *_):
            self.statuses = [0, 0]
            events.append('dispatcher-released')
    class Closed:
        def __init__(self, *args):
            pass
        def __enter__(self):
            events.append('ingress-closed')
            return self
        def check(self):
            events.append('ingress-checked')
        def __exit__(self, *_):
            events.append('ingress-released')
    def execute(api, target, raw, root):
        assert target == items['console']['Id'] and root == tmp_path and b'class PublicationFence:' in raw
        events.append('database-probe')
        return json.dumps(receipt()).encode()
    monkeypatch.setattr(probe, 'Docker', API)
    monkeypatch.setattr(probe, 'configuration', lambda value: value)
    monkeypatch.setattr(probe, 'equivalent', lambda current, original: probe.require(current == original, 'CONFIG_CHANGED'))
    monkeypatch.setattr(probe, 'workload', lambda item, role: probe.require(role == 'console', 'ROLE'))
    monkeypatch.setattr(probe.dispatcher, 'publisher_binding', lambda: (items['system_publisher'], dict(pid=100)))
    monkeypatch.setattr(probe.dispatcher, 'Hold', Held)
    monkeypatch.setattr(probe.ingress, 'Lease', Closed)
    monkeypatch.setattr(probe.ingress, 'Transport', lambda *args: None)
    monkeypatch.setattr(probe.ingress, 'health_status', lambda: 200)
    monkeypatch.setattr(probe, 'scheduler_idle', lambda binding: [])
    monkeypatch.setattr(probe, 'execute_source', execute)
    return tmp_path, events, items


def test_composed_probe_is_scoped_and_never_authorizes_capture(composed):
    root, events, _ = composed
    result = probe.probe(root, 'synthetic-tool')
    assert result['guards_released'] and result['runtime_and_configuration_unchanged']
    assert not result['capture_permitted'] and not result['external_settlement_proven']
    assert not result['support_settlement_proven'] and not result['manual_admission_closed']
    assert events.index('dispatcher-held') < events.index('ingress-closed') < events.index('database-probe')
    assert events[-2:] == ['ingress-released', 'dispatcher-released']
    assert (root / 'receipt.json').stat().st_mode & 0o777 == 0o600


def test_busy_publisher_refuses_before_console_closure(composed, monkeypatch):
    root, events, _ = composed
    def busy(binding):
        raise ValueError('UNSETTLED_PUBLISHER_CHILD')
    monkeypatch.setattr(probe, 'scheduler_idle', busy)
    with pytest.raises(ValueError, match='UNSETTLED_PUBLISHER_CHILD'):
        probe.probe(root, 'synthetic-tool')
    assert events == ['dispatcher-held', 'dispatcher-released']
    abort = json.loads((root / 'abort.json').read_text())
    assert abort['stage'] == 'publisher_idle' and abort['reason'] == 'UNSETTLED_PUBLISHER_CHILD'
    assert not abort['capture_permitted']


@pytest.mark.parametrize('failure', ['lost-exec-response', 'invalid-json', 'unknown-publication', 'changed-runtime'])
def test_composed_abort_releases_only_owned_guards_and_keeps_evidence(composed, monkeypatch, failure):
    root, events, items = composed
    original = probe.execute_source
    def fail(*args, **kwargs):
        value = original(*args, **kwargs)
        if failure == 'lost-exec-response':
            raise TimeoutError('synthetic timeout')
        if failure == 'invalid-json':
            return b'{}'
        if failure == 'changed-runtime':
            items['console']['State']['Pid'] += 1
            return value
        observed = json.loads(value)
        observed['message_counts']['unknown'] = 1
        return json.dumps(observed).encode()
    monkeypatch.setattr(probe, 'execute_source', fail)
    with pytest.raises((ValueError, KeyError, TimeoutError)):
        probe.probe(root, 'synthetic-tool')
    assert events[-2:] == ['ingress-released', 'dispatcher-released']
    assert (root / 'before.json').exists() and (root / 'source.json').exists()
    assert not (root / 'receipt.json').exists()


@pytest.mark.parametrize('command', [b'python\0manage.py\0publish_system_messages\0', b'sleep\x005\x00', b''])
def test_existing_publisher_child_is_not_killed_or_mistaken_for_sleep(monkeypatch, command):
    binding = dict(pid=100, uid=[1000] * 4, cgroup_sha256='synthetic')
    original = Path.read_text
    def text(path, *args, **kwargs):
        if str(path) == '/proc/100/task/100/children':
            return '101'
        if str(path) == '/proc/101/task/101/children':
            return ''
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'read_text', text)
    monkeypatch.setattr(Path, 'read_bytes', lambda path: command)
    monkeypatch.setattr(probe.dispatcher, 'process', lambda pid: (dict(binding, pid=pid, parent=100), 'S'))
    with pytest.raises(ValueError, match='UNSETTLED_PUBLISHER_CHILD'):
        probe.scheduler_idle(binding)


def frame(stream, raw):
    return bytes([stream, 0, 0, 0]) + len(raw).to_bytes(4, 'big') + raw


def test_docker_streams_are_not_mixed():
    assert probe.decode_stream(frame(1, b'{') + frame(2, b'error') + frame(1, b'}')) == (b'{}', b'error')


@pytest.mark.parametrize('raw', [b'x', frame(0, b'bad'), b'\x01bad\x00\x00\x00\x00',
                               frame(1, b'incomplete')[:-1], b'x' * 65537])
def test_unbounded_or_invalid_docker_output_refuses(raw):
    with pytest.raises(ValueError):
        probe.decode_stream(raw)


@pytest.mark.parametrize('failure', [None, 'wrong-user', 'timeout', 'still-running', 'stderr', 'exit-code'])
def test_exec_identity_is_recorded_before_start_and_unknown_results_retained(tmp_path, monkeypatch, failure):
    events = []
    identifier, target = 'a' * 64, 'b' * 64
    raw = b'print("synthetic")'
    item = dict(ContainerID=target, Running=False, ExitCode=0,
                ProcessConfig=dict(entrypoint='python', arguments=['-I', '-B', '-c', raw.decode()], user='console',
                                   privileged=False, tty=False))
    class API:
        def request(self, method, endpoint, body=None):
            if method == 'POST':
                assert endpoint == '/containers/' + target + '/exec'
                assert body['User'] == 'console' and body['Privileged'] is False
                assert (tmp_path / 'exec-intent.json').exists()
                return dict(Id=identifier)
            assert endpoint == '/exec/' + identifier + '/json'
            return item
    class Connection:
        def request(self, method, endpoint, **kwargs):
            assert method == 'POST' and endpoint == '/v1.52/exec/' + identifier + '/start'
            assert (tmp_path / 'exec-created.json').exists() and (tmp_path / 'exec-start-intent.json').exists()
            events.append('start')
        def getresponse(self):
            if failure == 'timeout':
                raise TimeoutError('unknown start outcome')
            return self
        status = 200
        def read(self, limit):
            assert limit == 65537
            if failure == 'still-running':
                item['Running'] = True
            if failure == 'exit-code':
                item['ExitCode'] = 1
            return frame(1, b'{}') + (frame(2, b'error') if failure == 'stderr' else b'')
        def close(self):
            events.append('close')
    monkeypatch.setattr(probe, 'DockerRead', Connection)
    if failure == 'wrong-user':
        item['ProcessConfig']['user'] = 'root'
    if failure:
        with pytest.raises((ValueError, TimeoutError)):
            probe.execute_source(API(), target, raw, tmp_path)
    else:
        assert probe.execute_source(API(), target, raw, tmp_path) == b'{}'
    assert (tmp_path / 'exec-created.json').exists()
    if failure == 'wrong-user':
        assert not events
    else:
        assert events == ['start', 'close']
    assert (tmp_path / 'exec-result.json').exists() == (failure not in ('wrong-user', 'timeout'))
