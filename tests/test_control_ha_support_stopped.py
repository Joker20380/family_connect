import base64
import hashlib
import json
import os
from pathlib import Path
import signal
import socketserver
import subprocess
import sys
import threading

import pytest

from control.capture_gate import Gate, GateError
from scripts import control_ha_support_stopped as stopped
from scripts import control_ha_support_snapshot_reader as reader
from scripts import control_ha_support_resume as resume
from test_control_ha_support_handoff import paired, run, notice_snapshot, chat_runtime
from test_control_ha_support_replace import service
from test_control_ha_legacy_support import installed, read, wait_for
from test_control_ha_support_resume import stage_generation, Channel


def accepted(paired, tmp_path):
    manager, plan, root, data, mailbox = paired
    assert run(root, mailbox) == 'HANDOFF_OPEN_CAPTURE_DENIED'
    before = notice_snapshot(data, int(manager.state()['MainPID']), seed=True)
    with Gate(plan['gate']).operation() as operation:
        operation.uncertain()
    controller = stopped.StoppedSupport(root, tmp_path / 'stopped-component', mailbox)
    return controller, before


@pytest.mark.parametrize('service', [True], indirect=True)
def test_native_stopped_pending_capture_reader_repeat_and_linked_resume(paired, tmp_path, monkeypatch):
    manager, plan, root, data, mailbox = paired
    controller, before = accepted(paired, tmp_path)
    unrelated = tmp_path / 'unrelated'
    unrelated.mkdir(mode=0o700)
    (unrelated / 'retained.json').write_text('historical evidence')
    with pytest.raises(ValueError, match='STOPPED_OPERATION_CONTENTS'):
        stopped.StoppedSupport(root, unrelated, mailbox)
    assert (unrelated / 'retained.json').read_text() == 'historical evidence'
    partial = controller.root / '.receipt-12345678'
    partial.write_bytes(b'partial historical receipt')
    partial.chmod(0o600)
    stopped.StoppedSupport(root, controller.root, mailbox)
    original_authority = Path(plan['start_authority']).read_bytes()
    pending = {path.name: path.read_bytes() for path in (Path(plan['gate']) / 'pending').iterdir()}
    with pytest.raises(FileNotFoundError):
        controller.capture()
    assert controller.stop() == 'SUPPORT_STOPPED_HISTORY_UNSETTLED'
    assert controller.stop() == 'SUPPORT_STOPPED_HISTORY_UNSETTLED'
    with pytest.raises(GateError, match='UNSETTLED_OPERATION'):
        with Gate(plan['gate']).drain(.1):
            pytest.fail('ordinary drain must still reject history')
    receipt = controller.capture()
    assert controller.capture() == receipt
    assert stopped.StoppedSupport(root, controller.root, mailbox).capture() == receipt
    assert partial.read_bytes() == b'partial historical receipt'
    assert receipt['history_settled'] is receipt['fleet_capture'] is False
    assert receipt['started_at_ns'] < receipt['finished_at_ns']
    snapshot = read(Path(receipt['snapshot']))
    assert snapshot['captured_at_ns'] < receipt['finished_at_ns']
    assert receipt['reader']['pending'] > 0 and receipt['reader']['pending_before'] >= len(pending)
    prestop = read(controller.root / 'pending-before.json')['entries']
    assert {name: base64.b64decode(prestop['pending/' + name]['body']) for name in pending} == pending
    retained_pending = {path.name: path.read_bytes() for path in (Path(plan['gate']) / 'pending').iterdir()}
    assert reader.check(receipt['snapshot'], receipt['sha256'], root / 'plan.json') == receipt['reader']
    newer = tmp_path / 'forward'
    stage_generation(root, newer, data / 'forward', mailbox, mailbox.call('observe'), monkeypatch)
    assert resume.Resume(newer, Channel(mailbox)).run() == 'FORWARD_RESUME_OPEN_CAPTURE_DENIED'
    assert notice_snapshot(data, int(manager.state()['MainPID'])) == before
    assert Path(plan['start_authority']).read_bytes() == original_authority
    assert all((Path(plan['gate']) / 'pending' / name).read_bytes() == value for name, value in retained_pending.items())
    with pytest.raises((ValueError, OSError)):
        controller.capture()


@pytest.mark.parametrize('service', [True], indirect=True)
@pytest.mark.parametrize('boundary', ['reclose', 'intent', 'signal'])
def test_native_interrupted_stop_reconciles_same_operation(paired, tmp_path, monkeypatch, boundary):
    manager, plan, root, data, mailbox = paired
    controller, before = accepted(paired, tmp_path)
    original = mailbox.call if boundary == 'reclose' else controller.save if boundary == 'intent' else signal.pidfd_send_signal
    interrupted = False

    def lost(*args, **kwargs):
        nonlocal interrupted
        result = original(*args, **kwargs)
        selected = boundary == 'signal' or boundary == 'reclose' and args[0] == 'reclose' or boundary == 'intent' and args[0] == 'stop-intent'
        if selected and not interrupted:
            interrupted = True
            raise TimeoutError('synthetic controller loss after effect')
        return result

    target, name = (mailbox, 'call') if boundary == 'reclose' else (controller, 'save') if boundary == 'intent' else (signal, 'pidfd_send_signal')
    monkeypatch.setattr(target, name, lost)
    with pytest.raises(TimeoutError):
        controller.stop()
    monkeypatch.setattr(target, name, original)
    assert mailbox.call('observe')['observed']['fence']['new_link_admission'] == 'CLOSED'
    assert controller.stop() == 'SUPPORT_STOPPED_HISTORY_UNSETTLED'
    assert controller.capture()['reader']['pending'] > 0
    assert not (root / 'terminal-failure.json').exists()


@pytest.mark.parametrize('service', [True], indirect=True)
def test_native_partial_capture_reader_refusal_retains_data_and_releases_locks(paired, tmp_path, monkeypatch):
    manager, plan, root, data, mailbox = paired
    controller, before = accepted(paired, tmp_path)
    assert controller.stop() == 'SUPPORT_STOPPED_HISTORY_UNSETTLED'
    original = controller.readback
    monkeypatch.setattr(controller, 'readback', lambda *args: (_ for _ in ()).throw(ValueError('READER_UNAVAILABLE')))
    with pytest.raises(ValueError, match='READER_UNAVAILABLE'):
        controller.capture()
    assert not (controller.root / 'complete.json').exists()
    retained = {path.name: path.read_bytes() for path in controller.root.glob('snapshot-*.json')}
    assert len(retained) == 1
    monkeypatch.setattr(controller, 'readback', original)
    receipt = controller.capture()
    assert receipt['reader']['pending'] > 0
    assert all((controller.root / name).read_bytes() == raw for name, raw in retained.items())
    assert manager.state()['MainPID'] == '0'
    with pytest.raises(GateError, match='UNSETTLED_OPERATION'):
        with Gate(plan['gate']).drain(.1):
            pass


@pytest.mark.parametrize('service', [True], indirect=True)
def test_native_sigkill_capture_controller_preserves_partial_and_releases_owned_locks(paired, tmp_path):
    manager, plan, root, data, mailbox = paired
    controller, before = accepted(paired, tmp_path)
    assert controller.stop() == 'SUPPORT_STOPPED_HISTORY_UNSETTLED'
    with Gate(plan['gate']).operation():
        with pytest.raises(ValueError, match='STOPPED_GATE_BUSY'):
            controller.capture()

    class Handler(socketserver.StreamRequestHandler):
        def handle(self):
            request = json.loads(self.rfile.readline(65537))
            try:
                response = mailbox.call(request['action'], request['payload'])
            except ValueError as error:
                response = dict(error=str(error))
            self.wfile.write(json.dumps(response).encode() + b'\n')

    endpoint = tmp_path / 'control.sock'
    server = socketserver.UnixStreamServer(str(endpoint), Handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    ready = tmp_path / 'copy-ready'
    process = subprocess.Popen([sys.executable, str(Path(__file__).parent / 'fixtures/support_stopped_driver.py'),
                               str(root), str(controller.root), str(endpoint), str(ready)],
                              stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        wait_for(lambda: ready.exists() or process.poll() is not None)
        assert ready.exists(), process.communicate(timeout=1)[1].decode()
        process.kill()
        assert process.wait(5) == -signal.SIGKILL
        assert not (controller.root / 'complete.json').exists()
        retained = {path.name: path.read_bytes() for path in controller.root.glob('snapshot-*.json')}
        assert retained
        assert controller.capture()['reader']['pending'] > 0
        assert all((controller.root / name).read_bytes() == raw for name, raw in retained.items())
    finally:
        if process.poll() is None:
            process.kill()
        process.wait(5)
        server.shutdown()
        thread.join(5)
        server.server_close()


@pytest.mark.parametrize('service', [True], indirect=True)
def test_native_reader_rejects_missing_modified_history_or_forged_scope(paired, tmp_path):
    manager, plan, root, data, mailbox = paired
    controller, before = accepted(paired, tmp_path)
    assert controller.stop() == 'SUPPORT_STOPPED_HISTORY_UNSETTLED'
    receipt = controller.capture()
    for change in ('missing', 'bytes', 'settled', 'authority'):
        value = read(Path(receipt['snapshot']))
        marker = value['pending_history'][0]
        if change == 'missing':
            del value['entries'][marker]
        elif change == 'bytes':
            value['entries'][marker]['body'] = base64.b64encode(b'changed').decode()
            value['entries'][marker]['sha256'] = hashlib.sha256(b'changed').hexdigest()
        elif change == 'settled':
            value['history_settled'] = True
        else:
            value['boundary']['absence']['old_binding']['pid'] += 1
        raw = json.dumps(value).encode()
        tampered = controller.root / (change + '.json')
        tampered.write_bytes(raw)
        with pytest.raises(ValueError):
            reader.check(tampered, hashlib.sha256(raw).hexdigest(), root / 'plan.json')


def process_fixture(tmp_path, target, *, writable=False, mapping=False):
    root = tmp_path / 'proc'
    process = root / str(os.getpid() + 1000000)
    (process / 'fd').mkdir(parents=True)
    (process / 'fdinfo').mkdir()
    (process / 'fd/3').symlink_to(target)
    (process / 'fdinfo/3').write_text('flags:\t' + ('02' if writable else '00') + '\n')
    information = target.stat()
    maps = f'100-200 rw-s 0 {os.major(information.st_dev):x}:{os.minor(information.st_dev):x} {information.st_ino} private-name\n'
    (process / 'maps').write_text(maps if mapping else '')
    return root


@pytest.mark.parametrize('kind', ['descriptor', 'mapping', 'readonly'])
def test_unknown_direct_writer_descriptor_and_shared_mapping_refuse(tmp_path, kind):
    target = tmp_path / 'database'
    target.write_bytes(b'synthetic')
    proc = process_fixture(tmp_path, target, writable=kind == 'descriptor', mapping=kind == 'mapping')
    if kind == 'readonly':
        assert stopped.live_writer_fds([target], proc)['privileged_future_writers_fenced'] is False
    else:
        with pytest.raises(ValueError, match='UNMANAGED_WRITABLE_'):
            stopped.live_writer_fds([target], proc)


def test_collect_rejects_symlink_special_file_and_changed_source(tmp_path):
    target = tmp_path / 'tree'
    target.mkdir()
    (target / 'item').write_bytes(b'synthetic')
    observed, entries = stopped.collect({'store': target})
    (target / 'item').write_bytes(b'changed')
    with pytest.raises(Exception, match='OBSERVATION_CHANGED'):
        observed.verify()
    (target / 'link').symlink_to(target / 'item')
    with pytest.raises(Exception):
        stopped.collect({'store': target})
    (target / 'link').unlink()
    os.mkfifo(target / 'pipe')
    with pytest.raises(Exception):
        stopped.collect({'store': target})
