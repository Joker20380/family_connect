from contextlib import contextmanager
import importlib.util
from pathlib import Path
import select
import signal
import subprocess
import sys
from types import SimpleNamespace

import pytest

from control.capture_gate import GateError, initialize
from control.friends.transport_gateway import Gateway, SERVICES


@pytest.fixture
def gateway(tmp_path, monkeypatch):
    source = Path(__file__).parents[1] / 'deploy/friends/awg-gateway.py'
    spec = importlib.util.spec_from_file_location('awg_cleanup_gateway', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    return module


class Engine:
    def __init__(self, failures=()):
        self.calls = []
        self.failures = set(failures)
        self.done = False

    def poll(self):
        return 0 if self.done else None

    def terminate(self):
        self.calls.append('terminate')
        if 'terminate' in self.failures:
            raise OSError('synthetic terminate failure')

    def kill(self):
        self.calls.append('kill')
        if 'kill' in self.failures:
            raise OSError('synthetic kill failure')

    def wait(self, timeout=None):
        self.calls.append(('wait', timeout))
        if timeout is None:
            raise KeyboardInterrupt
        if timeout in self.failures:
            raise subprocess.TimeoutExpired(['synthetic-engine'], timeout)
        self.done = True
        return 0


@pytest.fixture
def running(gateway, monkeypatch):
    state = SimpleNamespace(engine=Engine(), calls=[], failing=None)
    monkeypatch.setattr(gateway, 'settings', lambda: dict(network='10.83.0.0/16',
        address='10.83.0.1/16', external='synthetic0'))
    monkeypatch.setattr(gateway, 'paid_engine', lambda: None)
    monkeypatch.setattr(gateway, 'Path', lambda value: SimpleNamespace(read_text=lambda: '1')
        if value == '/proc/sys/net/ipv4/ip_forward' else Path(value))
    monkeypatch.setattr(gateway.subprocess, 'Popen', lambda *args, **kwargs: state.engine)
    monkeypatch.setattr(gateway.signal, 'signal', lambda *args: None)

    def command(arguments, check=True):
        state.calls.append(tuple(arguments))
        if not check and tuple(arguments) == state.failing:
            raise subprocess.TimeoutExpired(arguments, 8)
        return 1 if '-C' in arguments else 0

    monkeypatch.setattr(gateway, 'command', command)
    return state


@pytest.mark.parametrize('failure', [
    ('iptables', '-D', 'FORWARD', '-i', 'fcopen31', '-j', 'FCFRIENDS31'),
    ('iptables', '-D', 'FORWARD', '-o', 'fcopen31', '-m', 'conntrack', '--ctstate', 'ESTABLISHED,RELATED', '-j', 'ACCEPT'),
    ('iptables', '-t', 'nat', '-D', 'POSTROUTING', '-s', '10.83.0.0/16', '-o', 'synthetic0', '-j', 'MASQUERADE'),
    ('iptables', '-F', 'FCFRIENDS31'), ('iptables', '-X', 'FCFRIENDS31'),
])
def test_cleanup_failure_does_not_skip_engine_or_interface(gateway, running, failure):
    running.failing = failure
    with pytest.raises(subprocess.TimeoutExpired):
        gateway.run()
    assert running.engine.done
    assert running.calls[-1] == ('ip', 'link', 'del', 'fcopen31')
    assert ('iptables', '-X', 'FCFRIENDS31') in running.calls
    assert sum('-D' in arguments for arguments in running.calls) == 3


def test_normal_run_cleanup_preserves_reverse_rule_order(gateway, running):
    gateway.run()
    removed = [arguments for arguments in running.calls if '-D' in arguments]
    assert [arguments[1] for arguments in removed] == ['-t', '-D', '-D']
    assert 'POSTROUTING' in removed[0] and 'conntrack' in removed[1] and '-i' in removed[2]
    assert running.engine.calls == [('wait', None), 'terminate', ('wait', 10)]
    assert running.calls[-1] == ('ip', 'link', 'del', 'fcopen31')


def test_handler_setup_failure_still_cleans_owned_engine(gateway, running, monkeypatch):
    def fail(*args):
        raise RuntimeError('synthetic signal setup')

    monkeypatch.setattr(gateway.signal, 'signal', fail)
    with pytest.raises(RuntimeError, match='synthetic signal setup'):
        gateway.run()
    assert running.engine.done
    assert running.calls[-1] == ('ip', 'link', 'del', 'fcopen31')


@pytest.mark.parametrize('failures', [(10,), ('terminate',), (10, 'kill'), (10, 2)])
def test_failed_graceful_stop_always_attempts_kill_and_bounded_reap(gateway, failures):
    process = Engine(failures)
    with pytest.raises((OSError, subprocess.TimeoutExpired)):
        gateway.stop_engine(process)
    assert 'kill' in process.calls and process.calls[-1] == ('wait', 2)
    assert process.done is (2 not in failures)


def test_exited_engine_is_reaped_without_signals(gateway):
    process = Engine()
    process.done = True
    gateway.stop_engine(process)
    assert process.calls == [('wait', 10)]


def test_engine_cleanup_failure_still_deletes_interface(gateway, running):
    running.engine.failures.add(10)
    with pytest.raises(subprocess.TimeoutExpired):
        gateway.run()
    assert running.engine.done and 'kill' in running.engine.calls
    assert running.calls[-1] == ('ip', 'link', 'del', 'fcopen31')


@contextmanager
def native_engine(ignore_term=False):
    body = ('import signal,time; '
        + ('signal.signal(signal.SIGTERM, signal.SIG_IGN); ' if ignore_term else '')
        + 'print("ready",flush=True); time.sleep(30)')
    process = subprocess.Popen([sys.executable, '-I', '-B', '-u', '-c', body],
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        assert select.select([process.stdout], [], [], 3)[0]
        assert process.stdout.readline() == b'ready\n'
        yield process
    finally:
        if process.poll() is None:
            process.kill()
        process.wait(timeout=2)
        process.stdout.close()
        process.stderr.close()


def test_native_engine_reaped_before_final_cleanup_and_gate_release(gateway, tmp_path, monkeypatch):
    gate = initialize(tmp_path / 'capture')
    events = []
    with native_engine() as process:
        def command(arguments, check=True):
            assert list((gate.directory / 'pending').iterdir())
            if arguments[:3] == ['ip', 'link', 'del']:
                assert process.poll() is not None
            events.append(arguments)

        monkeypatch.setattr(gateway, 'command', command)
        with gate.operation():
            gateway.cleanup(process, [])
        assert process.returncode == -signal.SIGTERM
    assert events[-1] == ['ip', 'link', 'del', gateway.IFACE]
    assert not list((gate.directory / 'pending').iterdir())
    with gate.drain(.1):
        pass


def test_native_timeout_is_reaped_but_pending_survives_retry(gateway, tmp_path):
    gate = initialize(tmp_path / 'capture')
    with native_engine(ignore_term=True) as process:
        with pytest.raises(subprocess.TimeoutExpired):
            with gate.operation():
                gateway.stop_engine(process, grace_seconds=.05, kill_seconds=1)
        assert process.returncode == -signal.SIGKILL
    markers = list((gate.directory / 'pending').iterdir())
    assert len(markers) == 1
    with native_engine() as retry:
        with gate.operation():
            gateway.stop_engine(retry)
    assert list((gate.directory / 'pending').iterdir()) == markers
    with pytest.raises(GateError, match='UNSETTLED_OPERATION'):
        with gate.drain(.1):
            pytest.fail('uncertainty must not become a capture permit')


def test_native_network_error_and_stalled_engine_attempt_all_cleanup(gateway, tmp_path, monkeypatch):
    gate = initialize(tmp_path / 'capture')
    events = []
    original = gateway.stop_engine
    monkeypatch.setattr(gateway, 'stop_engine', lambda process:
        original(process, grace_seconds=.05, kill_seconds=1))
    with native_engine(ignore_term=True) as process:
        def command(arguments, check=True):
            assert list((gate.directory / 'pending').iterdir())
            events.append(arguments)
            if arguments == ['iptables', '-F', 'FCFRIENDS31']:
                raise subprocess.TimeoutExpired(arguments, 8)
            if arguments[:3] == ['ip', 'link', 'del']:
                assert process.returncode == -signal.SIGKILL

        monkeypatch.setattr(gateway, 'command', command)
        with pytest.raises(subprocess.TimeoutExpired):
            with gate.operation():
                gateway.cleanup(process, [])
        assert process.returncode == -signal.SIGKILL
    assert events == [['iptables', '-F', 'FCFRIENDS31'], ['iptables', '-X', 'FCFRIENDS31'],
        ['ip', 'link', 'del', gateway.IFACE]]
    with pytest.raises(GateError, match='UNSETTLED_OPERATION'):
        with gate.drain(.1):
            pytest.fail('failed cleanup must not permit capture')


def test_emergency_stop_stays_asynchronous_not_a_completion_receipt():
    engine = Gateway.__new__(Gateway)
    calls = []
    engine.run = lambda arguments: calls.append(arguments)
    assert engine.stop_all() is None
    assert calls == [['systemctl', '--no-block', 'stop', *SERVICES]]
