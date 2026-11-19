import contextlib
import io
import json
import multiprocessing
from pathlib import Path
import time

import pytest

from control.friends import transport_gateway as module
from test_transport_enforcement import engine, envelope, registry
from test_transport_failure_serialization import entrypoint_for
from test_transport_observation_mode import candidate, collector


MONOTONIC = time.monotonic


@pytest.mark.parametrize('fault', ['deadline', 'open-error'])
def test_prelock_failure_cannot_be_cleared_by_later_owner(candidate, registry, collector, monkeypatch, fault):
    gateway, current, live, initial = candidate
    gateway.accept(envelope(registry))
    gateway.apply()
    context = multiprocessing.get_context('fork')
    opened, release_open, owned, release_owner, finished, exit_owner = [context.Event() for _ in range(6)]
    results, events = context.Queue(), context.Queue()

    def participant(role):
        module.time.monotonic = MONOTONIC
        worker = module.Gateway(gateway.gateway, clock=gateway.clock, monotonic=gateway.monotonic, run=gateway.run)
        entrypoint = entrypoint_for(monkeypatch, worker, registry, initial, 'reconcile')
        original_open, original_accept = Path.open, worker.accept
        def open_file(path, *args, **kwargs):
            if path == worker.root/'application.lock':
                events.put((role, 'open-entered', MONOTONIC()))
                opened.set()
                assert release_open.wait(20)
                if fault == 'open-error':
                    raise OSError(5, 'synthetic application open failure')
            return original_open(path, *args, **kwargs)
        def accept(*args, **kwargs):
            events.put((role, 'owns-application-lock', MONOTONIC()))
            owned.set()
            assert release_owner.wait(6)
            return original_accept(*args, **kwargs)
        def stop():
            events.put((role, 'async-stop-request', MONOTONIC()))
        worker.stop_all = stop
        if role == 'B':
            Path.open = open_file
        else:
            worker.accept = accept
        live['calls'].clear()
        output, failure = io.StringIO(), None
        with contextlib.redirect_stdout(output):
            try:
                entrypoint.register()
            except BaseException as error:
                failure = str(error)
        events.put((role, 'operation-exited', MONOTONIC()))
        results.put(dict(role=role, ack=output.getvalue(), error=failure,
            queries=len([command for command in live['calls'] if command[0] != 'systemctl'])))
        if role == 'A':
            finished.set()
            assert exit_owner.wait(10)

    early = context.Process(target=participant, args=('B',))
    later = context.Process(target=participant, args=('A',))
    early.start()
    try:
        assert opened.wait(5)
        if fault == 'deadline':
            time.sleep(8.15)
        later.start()
        assert owned.wait(5)
        release_open.set()
        early.join(5)
        assert early.exitcode == 0
        first = (gateway.root/'transport-failure.json').read_bytes()
        assert module.read(gateway.root/'transport-attempt.json')['result'] == 'error'
        release_owner.set()
        assert finished.wait(5)
        observed = {result['role']: result for result in [results.get(timeout=2), results.get(timeout=2)]}
        trace = []
        while len(trace) < (5 if observed['A']['ack'] else 6):
            trace.append(events.get(timeout=2))
        status = collector()['status']
        print(json.dumps(dict(fault=fault, participants=observed, events=sorted(trace, key=lambda value:value[2]),
            collector=status, incomplete=(gateway.root/'application-incomplete').exists(),
            emergency=(gateway.root/'application-failed').exists()), sort_keys=True))
        assert not observed['B']['ack'] and observed['B']['queries'] == 0
        assert 'TRANSPORT_OPERATION_DEADLINE' in observed['B']['error'] if fault == 'deadline' else 'synthetic application open failure' in observed['B']['error']
        assert not observed['A']['ack']
        assert observed['A']['error'] == 'TRANSPORT_RECOVERY_REQUIRED'
        assert status == 'unavailable'
        assert (gateway.root/'transport-failure.json').read_bytes() == first
        entrypoint = entrypoint_for(monkeypatch, gateway, registry, initial, 'reconcile')
        with pytest.raises(ValueError, match='TRANSPORT_RECOVERY_REQUIRED'):
            entrypoint.register()
    finally:
        release_open.set()
        release_owner.set()
        exit_owner.set()
        for process in (early, later):
            if process.pid is not None:
                process.join(3)
                if process.is_alive():
                    process.kill()
                    process.join()
        results.close()
        events.close()


@pytest.mark.parametrize('owner', ['registration', 'watch', 'recovery'])
@pytest.mark.parametrize('expire', [False, True])
@pytest.mark.parametrize('fallback', [False, True])
def test_outcome_orders_later_failure_publication(candidate, registry, collector, monkeypatch, owner, expire, fallback):
    gateway, current, live, initial = candidate
    gateway.accept(envelope(registry))
    gateway.apply()
    context = multiprocessing.get_context('fork')
    held, release, publishing, stopped = [context.Event() for _ in range(4)]
    results = context.Queue()

    def completing():
        worker = module.Gateway(gateway.gateway, clock=gateway.clock, monotonic=gateway.monotonic, run=gateway.run)
        original_rmdir = Path.rmdir
        def remove(path):
            original_rmdir(path)
            if path == worker.fence_path:
                held.set()
                assert release.wait(4)
                if expire:
                    module.CURRENT_OPERATION.get().deadline -= 9
        Path.rmdir = remove
        worker.stop_all = lambda: None
        entrypoint = entrypoint_for(monkeypatch, worker, registry, initial, 'reconcile')
        output, failure = io.StringIO(), None
        with contextlib.redirect_stdout(output):
            try:
                if owner == 'registration':
                    entrypoint.register()
                elif owner == 'watch':
                    worker.apply()
                else:
                    worker.run = lambda command: b'LoadState=loaded\nActiveState=inactive\nMainPID=0\nControlPID=0\nJob=\n'
                    worker.recover()
            except BaseException as error:
                failure = str(error)
        results.put(dict(role='owner', error=failure, ack=output.getvalue(), progress=worker.metrics['result']))

    def failing():
        worker = module.Gateway(gateway.gateway, clock=gateway.clock, monotonic=gateway.monotonic, run=gateway.run)
        original_open, original_outcome = Path.open, worker.outcome_lock
        def open_file(path, *args, **kwargs):
            if path == worker.root/'application.lock':
                raise OSError(5, 'synthetic competing open failure')
            if fallback and path == worker.root/'application-outcome.lock':
                raise OSError(5, 'synthetic outcome open failure')
            return original_open(path, *args, **kwargs)
        @contextlib.contextmanager
        def outcome():
            publishing.set()
            with original_outcome():
                yield
        Path.open, worker.outcome_lock, worker.stop_all = open_file, outcome, stopped.set
        entrypoint = entrypoint_for(monkeypatch, worker, registry, initial, 'reconcile')
        with pytest.raises(OSError, match='synthetic competing open failure'):
            entrypoint.register()
        results.put(dict(role='failure', published=True))

    active, failure = context.Process(target=completing), context.Process(target=failing)
    active.start()
    try:
        assert held.wait(5)
        failure.start()
        assert publishing.wait(5)
        if fallback:
            assert stopped.wait(3)
            failure.join(3)
            assert failure.exitcode == 0
            assert gateway.failed_path.exists()
        else:
            assert not stopped.wait(.15)
            assert not gateway.failed_path.exists()
        assert collector()['status'] == 'unavailable'
        release.set()
        for process in (active, failure):
            process.join(5)
            assert process.exitcode == 0
        observed = {result['role']:result for result in [results.get(timeout=2), results.get(timeout=2)]}
        expected = 'TRANSPORT_OPERATION_DEADLINE' if expire else 'TRANSPORT_RECOVERY_REQUIRED' if fallback else None
        assert observed['owner']['error'] == expected
        assert observed['owner']['progress'] == ('error' if expected else 'complete')
        assert bool(observed['owner']['ack']) == (owner == 'registration' and not expected)
        assert stopped.is_set() and gateway.failed_path.exists()
        assert collector()['status'] == 'unavailable'
        with pytest.raises(ValueError, match='TRANSPORT_RECOVERY_REQUIRED'):
            gateway.apply()
        gateway.run = lambda command: b'LoadState=loaded\nActiveState=inactive\nMainPID=0\nControlPID=0\nJob=\n'
        gateway.recover()
        assert not gateway.failed_path.exists() and not gateway.fence_path.exists()
    finally:
        release.set()
        for process in (active, failure):
            if process.pid is not None:
                process.join(3)
                if process.is_alive():
                    process.kill()
                    process.join()
        results.close()


def test_failed_outcome_open_preserves_emergency(candidate, registry, monkeypatch):
    gateway, current, live, initial = candidate
    gateway.accept(envelope(registry))
    original = Path.open
    def open_file(path, *args, **kwargs):
        if path.name in ('application.lock', 'application-outcome.lock'):
            raise OSError(5, 'synthetic lock open failure')
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'open', open_file)
    with pytest.raises(OSError, match='synthetic lock open failure'):
        gateway.apply()
    assert gateway.failed_path.exists()
    assert module.read(gateway.root/'transport-failure.json')['reason'] == 'FILESYSTEM_OR_OS_ERROR'


def test_completion_latch_check_is_inside_original_deadline(candidate, registry, monkeypatch, capsys):
    gateway, current, live, initial = candidate
    gateway.accept(envelope(registry))
    gateway.apply()
    original = gateway.require_no_failure
    entered = []
    def check():
        original()
        if entered and not gateway.fence_path.exists():
            module.CURRENT_OPERATION.get().deadline -= 9
        entered.append(True)
    monkeypatch.setattr(gateway, 'require_no_failure', check)
    entrypoint = entrypoint_for(monkeypatch, gateway, registry, initial, 'reconcile')
    with pytest.raises(TimeoutError, match='TRANSPORT_OPERATION_DEADLINE'):
        entrypoint.register()
    assert not capsys.readouterr().out
    assert gateway.failed_path.exists() and gateway.fence_path.exists()
    assert gateway.metrics['result'] == 'error'
