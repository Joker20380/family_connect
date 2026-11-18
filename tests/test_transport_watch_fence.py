import contextlib
import io
import json
import multiprocessing
from pathlib import Path

import pytest

from control.friends import transport_gateway as module
from test_transport_enforcement import engine, envelope, registry
from test_transport_observation_mode import candidate, collector
from test_transport_failure_serialization import entrypoint_for


def test_watch_error_excludes_registration_after_async_stop_request(
        candidate, registry, collector, monkeypatch):
    gateway, current, live, initial = candidate
    gateway.accept(envelope(registry))
    gateway.apply()
    context = multiprocessing.get_context('fork')
    stop_requested = context.Event()
    results = context.Queue()

    def watch_process():
        original_init = module.Gateway.__init__
        def initialize(self, runtime, **kwargs):
            original_init(self, runtime, clock=gateway.clock, monotonic=gateway.monotonic, **kwargs)
        def broken_readback(self):
            raise ValueError('ENGINE_READBACK_MISMATCH')
        module.Gateway.__init__ = initialize
        module.Gateway.apply_serialized = broken_readback
        module.Gateway.stop_all = lambda self: stop_requested.set()
        try:
            module.watch(gateway.gateway, run=gateway.run)
        except BaseException as error:
            results.put(dict(role='watch', error=str(error)))

    def register_process():
        registration = module.Gateway(gateway.gateway, clock=gateway.clock,
            monotonic=gateway.monotonic, run=gateway.run)
        registration.stop_all = lambda: None
        entrypoint = entrypoint_for(monkeypatch, registration, registry, initial, 'reconcile')
        output = io.StringIO()
        error = None
        live['calls'].clear()
        with contextlib.redirect_stdout(output):
            try:
                entrypoint.register()
            except BaseException as failure:
                error = str(failure)
        results.put(dict(role='register', ack=bool(output.getvalue()), error=error,
            queries=len([command for command in live['calls'] if command[0] != 'systemctl'])))

    watcher = context.Process(target=watch_process)
    watcher.start()
    try:
        assert stop_requested.wait(5)
        watcher.join(5)
        assert not watcher.is_alive()
        registration = context.Process(target=register_process)
        registration.start()
        registration.join(10)
        if registration.is_alive():
            registration.kill()
            registration.join()
            raise AssertionError('registration exceeded its bounded operation')
        observed = {item['role']: item for item in [results.get(timeout=2), results.get(timeout=2)]}
        print(json.dumps(observed, sort_keys=True))
        assert observed['watch']['error'] == 'ENGINE_READBACK_MISMATCH'
        assert observed['register'] == dict(role='register', ack=False,
            error='TRANSPORT_RECOVERY_REQUIRED', queries=0)
        assert collector()['status'] == 'unavailable'
        assert module.read(gateway.root/'transport-failure.json')['reason'] == 'ENGINE_READBACK_MISMATCH'
    finally:
        if watcher.is_alive():
            watcher.kill()
        watcher.join()
        results.close()


@pytest.mark.parametrize('state', ['active', 'activating', 'deactivating', 'inactive', 'failed'])
def test_explicit_recovery_requires_actual_stopped_units(candidate, registry, state):
    gateway, current, live, initial = candidate
    gateway.accept(envelope(registry))
    authority = gateway.path.read_bytes()
    gateway.fence_path.mkdir()
    gateway.run = lambda command: ('LoadState=loaded\nActiveState='+state+'\nMainPID=0\nControlPID=0\nJob=\n').encode()
    if state in ('inactive', 'failed'):
        gateway.recover()
        assert not gateway.fence_path.exists()
    else:
        with pytest.raises(ValueError, match='TRANSPORT_RECOVERY_REQUIRES_STOPPED_UNITS'):
            gateway.recover()
        assert gateway.fence_path.exists()
    assert gateway.path.read_bytes() == authority


@pytest.mark.parametrize('field,value', [('MainPID', '1'), ('ControlPID', '1'), ('Job', '34'), ('LoadState', 'not-found')])
def test_pending_stop_or_live_pid_never_clears_fence(candidate, registry, field, value):
    gateway, current, live, initial = candidate
    gateway.accept(envelope(registry))
    gateway.fence_path.mkdir()
    properties = dict(LoadState='loaded', ActiveState='inactive', MainPID='0', ControlPID='0', Job='')
    properties[field] = value
    gateway.run = lambda command: '\n'.join(key+'='+value for key, value in properties.items()).encode()
    with pytest.raises(ValueError, match='TRANSPORT_RECOVERY_REQUIRES_STOPPED_UNITS'):
        gateway.recover()
    assert gateway.fence_path.exists()


def test_recovery_final_deadline_rearms_fence_before_unlock(candidate, registry, monkeypatch):
    gateway, current, live, initial = candidate
    gateway.accept(envelope(registry))
    gateway.fence_path.mkdir()
    gateway.run = lambda command: b'LoadState=loaded\nActiveState=inactive\nMainPID=0\nControlPID=0\nJob=\n'
    original_rmdir = Path.rmdir
    def remove(path):
        original_rmdir(path)
        if path == gateway.fence_path:
            module.CURRENT_OPERATION.get().deadline -= 9
    monkeypatch.setattr(Path, 'rmdir', remove)
    with pytest.raises(TimeoutError, match='TRANSPORT_OPERATION_DEADLINE'):
        gateway.recover()
    assert gateway.fence_path.exists()
