import contextlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

import pytest

from control.friends import transport_gateway as module


def test_progress_reader_accepts_legacy_and_new_field_order(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]/'scripts'))
    from test_paid_transport_systemd import progress_maxima
    progress = dict(result='complete', total=0.5, stages=dict(engine_query=0.3))
    records = [dict(transport_progress=progress), dict(transport_progress_gap=2.2),
        dict(diagnostic_messages_dropped=2, transport_progress=progress),
        dict(diagnostic_messages_dropped=2, transport_progress_gap=2.3)]
    journal = '\n'.join(['systemd status', '{"partial', '[]', ''] +
        [json.dumps(record, sort_keys=True) for record in records]).encode()
    assert progress_maxima(journal) == dict(total=0.5, progress_gap=2.3,
        stages=dict(engine_query=0.3), diagnostic_messages_dropped=2)
    with pytest.raises(AssertionError, match='MISSING_COMPLETED_PROGRESS_OR_GAP'):
        progress_maxima(b'no completed measurements\n')
    with pytest.raises(AssertionError):
        progress_maxima(journal+b'\n{"transport_progress_gap": 12.5}\n')


WATCH_OUTPUT_SCENARIO = '''import contextlib,os,sys,time
from pathlib import Path
if len(sys.argv)>2:sys.path.insert(0,sys.argv[2])
from control.friends import transport_gateway as module
Original=module.Gateway
class CompletedEngine(Original):
    def __init__(self,gateway,run):
        self.root=Path(sys.argv[1]);self.node='gateway-ru';self.clock=time.time
        self.run=lambda arguments:b'';self.completed=False
    @contextlib.contextmanager
    def operation(self):
        yield
    def apply(self,starting=False):
        if starting:return
        if self.completed:raise ValueError('ENGINE_READBACK_MISMATCH')
        with Original.operation(self):
            self.completed=True
            os.write(1,b'BODY_COMPLETE\\n')
    def stop_all(self):
        os.write(1,b'PROTECTIVE_STOP\\n')
module.Gateway=CompletedEngine
module.time.sleep=lambda seconds:None
try:module.watch(None)
except ValueError:os.write(1,b'FAILURE_RETURNED\\n')
'''


def test_watch_notifications_and_failure_record_with_unread_stderr(tmp_path):
    channel = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    address = str(tmp_path/'notify')
    channel.bind(address)
    channel.setblocking(False)
    try:
        with blocked_sink('socket') as descriptor:
            process = subprocess.Popen([sys.executable,'-c',WATCH_OUTPUT_SCENARIO,str(tmp_path)],
                stdout=subprocess.PIPE,stderr=descriptor,env={**os.environ,'NOTIFY_SOCKET':address})
            try:
                output, _ = process.communicate(timeout=2)
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait(timeout=2)
        assert process.returncode==0
        assert output.splitlines()==[b'BODY_COMPLETE',b'PROTECTIVE_STOP',b'FAILURE_RETURNED']
        assert channel.recv(1024)==b'READY=1'
        assert channel.recv(1024)==b'WATCHDOG=1'
        with pytest.raises(BlockingIOError):channel.recv(1024)
        failure=json.loads((tmp_path/'transport-failure.json').read_text())
        assert failure['reason']=='ENGINE_READBACK_MISMATCH'
        assert failure['diagnostic_messages_dropped']>=1
        assert json.loads((tmp_path/'transport-attempt.json').read_text())['result']=='error'
    finally:
        channel.close()


@contextlib.contextmanager
def blocked_sink(kind):
    if kind == 'socket':
        writer, reader = socket.socketpair()
        writer.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 4096)
        descriptor = writer.fileno()
    else:
        read_descriptor, descriptor = os.pipe()
    try:
        os.set_blocking(descriptor, False)
        while True:
            try:
                os.write(descriptor, b'x' * 4096)
            except BlockingIOError:
                break
        os.set_blocking(descriptor, True)
        yield descriptor
    finally:
        if kind == 'socket':
            writer.close()
            reader.close()
        else:
            os.close(descriptor)
            os.close(read_descriptor)


@pytest.mark.parametrize('kind', ['pipe', 'socket'])
def test_unread_diagnostics_do_not_block_completed_operation_or_failure_record(tmp_path, kind):
    source = '''import os,sys
from pathlib import Path
from control.friends import transport_gateway as module
engine=module.Gateway.__new__(module.Gateway)
with engine.operation():
    os.write(1,b'BODY_COMPLETE\\n')
os.write(1,b'AFTER_OPERATION\\n')
module.report_failure(ValueError('ENGINE_READBACK_MISMATCH'),'watch',Path(sys.argv[1]))
os.write(1,b'BEFORE_PROTECTIVE_STOP\\n')
'''
    with blocked_sink(kind) as descriptor:
        process = subprocess.Popen([sys.executable, '-c', source, str(tmp_path)],
            stdout=subprocess.PIPE, stderr=descriptor)
        try:
            output, _ = process.communicate(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            output, _ = process.communicate(timeout=2)
            pytest.fail('Completed operation blocked in diagnostic output: ' + output.decode())
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=2)
        assert os.get_blocking(descriptor)
    assert process.returncode == 0
    assert output.splitlines() == [b'BODY_COMPLETE', b'AFTER_OPERATION', b'BEFORE_PROTECTIVE_STOP']
    failure = json.loads((tmp_path/'transport-failure.json').read_text())
    assert failure['reason'] == 'ENGINE_READBACK_MISMATCH'
    assert failure['diagnostic_messages_dropped'] >= 1


def test_output_loss_is_explicit_on_next_success(monkeypatch):
    reader, writer = socket.socketpair()
    try:
        monkeypatch.setattr(module.sys, 'stderr', writer.makefile('w'))
        monkeypatch.setattr(module, 'DIAGNOSTIC_MESSAGES_DROPPED', 3)
        assert module.emit(dict(transport_progress_gap=2.0))
        result = json.loads(reader.recv(16384))
        assert result['diagnostic_messages_dropped'] == 3
        assert result['transport_progress_gap'] == 2.0
    finally:
        reader.close()
        writer.close()


def test_regular_file_diagnostic_sink_is_not_a_blocking_io_path(tmp_path, monkeypatch):
    with (tmp_path/'diagnostic.log').open('w') as output:
        monkeypatch.setattr(module.sys, 'stderr', output)
        before = module.DIAGNOSTIC_MESSAGES_DROPPED
        assert not module.emit(dict(transport_progress_gap=2.0))
        assert module.DIAGNOSTIC_MESSAGES_DROPPED == before + 1
    assert (tmp_path/'diagnostic.log').read_bytes() == b''


def test_watcher_requires_controlled_recovery_not_unbounded_restart():
    unit = (Path(__file__).resolve().parents[1]/'deploy/friends/paid-transport/family-connect-paid-watch.service').read_text()
    assert 'Restart=no\n' in unit
    assert 'WatchdogSec=12\n' in unit
    assert 'TimeoutStartSec=45\n' in unit


def test_watchdog_is_not_sent_for_an_uncompleted_apply(monkeypatch):
    notifications, failures = [], []
    class FailingEngine:
        def __init__(self, gateway, run):
            self.run = run

        @contextlib.contextmanager
        def operation(self):
            yield

        def apply(self, starting=False):
            if not starting:
                raise TimeoutError('TRANSPORT_OPERATION_DEADLINE')

        def fail_closed(self, error, mode):
            failures.append((type(error), mode))

    monkeypatch.setattr(module, 'Gateway', FailingEngine)
    monkeypatch.setattr(module, 'notify', notifications.append)
    with pytest.raises(TimeoutError):
        module.watch(None, run=lambda arguments: b'')
    assert notifications == ['READY=1']
    assert failures == [(TimeoutError, 'watch')]
