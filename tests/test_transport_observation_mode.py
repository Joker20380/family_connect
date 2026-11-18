import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import select
import stat
import subprocess
import threading

import pytest

from control.friends import transport_gateway as module
from test_transport_enforcement import engine, envelope, event, registry


@pytest.fixture
def candidate(engine):
    gateway, current, live, initial = engine
    config_path = gateway.root/'transport-enforcement.json'
    config = module.read(config_path)
    config['readback_mode'] = 'observations-v1'
    module.write(config_path, config)
    gateway = module.Gateway(gateway.gateway, clock=gateway.clock, monotonic=gateway.monotonic, run=gateway.run)
    return gateway, current, live, initial


@pytest.fixture
def collector(candidate, monkeypatch):
    gateway, current, live, initial = candidate
    filename = Path(__file__).resolve().parents[1]/'control_plane/apps/console/transport_collector.py'
    spec = importlib.util.spec_from_file_location('isolated_transport_collector', filename)
    collector = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(collector)
    raw = b'synthetic runtime archive; no production credentials'
    (gateway.root/'paid-transport.pyz').write_bytes(raw)
    monkeypatch.setattr(collector.time, 'time', lambda: current[0])
    monkeypatch.setattr(collector.time, 'monotonic', lambda: current[0])
    return lambda: collector.collect_transport(gateway.node, b'k'*32, hashlib.sha256(raw).hexdigest(), gateway.root)


def count_io(monkeypatch):
    counts = dict(writes=0, file_fsync=0, directory_fsync=0, observations=0)
    original_write, original_sync, original_replace = module.write, os.fsync, os.replace
    def write(path, value, *args):
        if path.name in ('transport-state.json', 'transport-attempt.json'):
            counts['writes'] += 1
        return original_write(path, value, *args)
    def sync(descriptor):
        counts['directory_fsync' if stat.S_ISDIR(os.fstat(descriptor).st_mode) else 'file_fsync'] += 1
        return original_sync(descriptor)
    def replace(source, target):
        if target.name == 'transport-observation.json':
            counts['observations'] += 1
        return original_replace(source, target)
    monkeypatch.setattr(module, 'write', write)
    monkeypatch.setattr(module.os, 'fsync', sync)
    monkeypatch.setattr(module.os, 'replace', replace)
    return counts


@pytest.mark.parametrize('mode', ['legacy', 'candidate'])
def test_same_cycles_keep_all_engine_queries_and_only_candidate_skips_sync(engine, candidate, registry, monkeypatch, mode):
    gateway, current, live, initial = engine if mode == 'legacy' else candidate
    gateway.accept(envelope(registry))
    gateway.apply()
    counts = count_io(monkeypatch)
    live['calls'].clear()
    original = gateway.path.read_bytes()
    for iteration in range(6):
        current[0] += 2
        gateway.apply()
    assert len(live['calls']) == 18
    expected = 12 if mode == 'legacy' else 0
    assert counts == dict(writes=expected, file_fsync=expected, directory_fsync=expected,
        observations=0 if mode == 'legacy' else 6)
    if mode == 'candidate':
        assert gateway.path.read_bytes() == original
        assert module.read(gateway.observation_path)['observed_at'] == current[0]


def test_collector_uses_completed_readback_not_collection_time(candidate, registry, collector):
    gateway, current, live, initial = candidate
    gateway.accept(envelope(registry))
    gateway.apply()
    finished = current[0]
    current[0] += 3
    value = collector()
    assert value['status'] == 'ok' and value['observed_at'] == finished
    assert value['devices'][0]['applied_at'] == finished
    assert value['devices'][0]['awg_allowed'] is True
    current[0] += 10
    assert collector()['status'] == 'unavailable'


@pytest.mark.parametrize('mutation', ['missing', 'partial', 'duplicate', 'state', 'boot', 'generation', 'pid', 'start', 'future', 'monotonic', 'nan', 'records', 'applied', 'attempt', 'unsafe'])
def test_no_fresh_applied_from_invalid_observation(candidate, registry, collector, mutation):
    gateway, current, live, initial = candidate
    gateway.accept(envelope(registry))
    gateway.apply()
    value = module.read(gateway.observation_path)
    if mutation == 'missing':
        gateway.observation_path.unlink()
    elif mutation == 'partial':
        gateway.observation_path.write_text('{')
    elif mutation == 'duplicate':
        gateway.observation_path.write_text('{"schema":2,"schema":2}')
    elif mutation == 'state':
        state = gateway.load()
        state['observed_at'] += 1
        module.write(gateway.path, state)
    elif mutation == 'attempt':
        gateway.failure()
    elif mutation == 'unsafe':
        gateway.observation_path.chmod(0o644)
    else:
        if mutation == 'boot': value['boot'] = 'other-boot'
        if mutation == 'generation': value['producer']['generation'] = 'a'*32
        if mutation == 'pid': value['producer']['pid'] = 2**30
        if mutation == 'start': value['producer']['start'] = '0'
        if mutation == 'future': value['observed_at'] += 1
        if mutation == 'monotonic': value['monotonic'] -= 13
        if mutation == 'nan': value['monotonic'] = float('nan')
        if mutation == 'records': value['records'] = {}
        if mutation == 'applied': value['records'][initial['device']]['allowed'] = False
        gateway.observation_path.write_text(json.dumps(value))
    result = collector()
    assert result['status'] == 'unavailable' and result['devices'] == []


@pytest.mark.parametrize('transition', ['permit', 'renew', 'revoke', 'deny', 'prepare'])
def test_security_transitions_and_confirmations_are_durable(candidate, registry, collector, monkeypatch, transition):
    gateway, current, live, initial = candidate
    gateway.accept(envelope(registry))
    gateway.apply()
    if transition in ('renew', 'revoke', 'deny'):
        event(registry)
        gateway.accept(envelope(registry))
        gateway.apply()
    counts = count_io(monkeypatch)
    current[0] += 2
    if transition == 'permit': event(registry, now=current[0])
    if transition == 'revoke': event(registry, 'revoke', 'fixture-revoke', now=current[0])
    if transition == 'deny': event(registry, 'expire', 'fixture-deny', now=current[0])
    with gateway.serialized():
        with gateway.lock():
            if transition == 'prepare': gateway.prepare(envelope(registry, current[0]), 'b'*64)
            else: gateway.accept(envelope(registry, current[0]))
        assert collector()['status'] == 'unavailable'
        gateway.apply_serialized()
        expected = 4 if transition == 'prepare' else 3
        config_writes = 1 if transition in ('revoke', 'deny', 'prepare') else 0
        assert counts['writes'] == expected
        assert counts['file_fsync'] == counts['directory_fsync'] == expected + config_writes
    value = collector()
    assert value['status'] == 'ok'
    assert value['devices'][0]['awg_allowed'] is (transition in ('permit', 'renew'))
    assert gateway.load()['records'][initial['device']]['prepared'] == ('b'*64 if transition == 'prepare' else None)


@pytest.mark.parametrize('boundary', ['json', 'file', 'replace-before', 'replace-after', 'directory'])
@pytest.mark.parametrize('phase', ['accept', 'state-confirmation', 'attempt-confirmation'])
def test_crash_reload_has_no_completed_readback(candidate, registry, collector, boundary, phase):
    gateway, current, live, initial = candidate
    gateway.accept(envelope(registry))
    gateway.apply()
    child = os.fork()
    if child == 0:
        original_sync, original_replace, original_dump = os.fsync, os.replace, json.dump
        original_write = module.write
        injecting = [phase == 'accept']
        try:
            event(registry)
            if phase != 'accept':
                with gateway.serialized(), gateway.lock(): gateway.accept(envelope(registry))
            def write(path, value, *args):
                injecting[0] = phase == 'accept' or path.name == (
                    'transport-state.json' if phase == 'state-confirmation' else 'transport-attempt.json')
                return original_write(path, value, *args)
            def sync(descriptor):
                original_sync(descriptor)
                directory = stat.S_ISDIR(os.fstat(descriptor).st_mode)
                if injecting[0] and boundary == ('directory' if directory else 'file'): os._exit(81)
            def replace(source, target):
                if injecting[0] and boundary == 'replace-before': os._exit(81)
                original_replace(source, target)
                if injecting[0] and boundary == 'replace-after': os._exit(81)
            def dump(*args, **kwargs):
                result = original_dump(*args, **kwargs)
                if injecting[0] and boundary == 'json': os._exit(81)
                return result
            os.fsync, os.replace, json.dump = sync, replace, dump
            module.write = write
            if phase == 'accept':
                with gateway.serialized(), gateway.lock(): gateway.accept(envelope(registry))
            else: gateway.apply()
            os._exit(82)
        except BaseException:
            os._exit(83)
    assert os.waitpid(child, 0)[1] == 81 << 8
    assert collector()['status'] == 'unavailable'
    reloaded = module.Gateway(gateway.gateway, clock=gateway.clock, monotonic=gateway.monotonic, run=gateway.run)
    reloaded.load()
    with pytest.raises(ValueError, match='TRANSPORT_RECOVERY_REQUIRED'):
        reloaded.apply()
    original_run = reloaded.run
    reloaded.run = lambda command: b'LoadState=loaded\nActiveState=inactive\nMainPID=0\nControlPID=0\nJob=\n'
    reloaded.recover()
    reloaded.run = original_run
    reloaded.apply()
    assert collector()['status'] == 'ok'


@pytest.mark.parametrize('boundary', ['file', 'directory', 'observation'])
def test_late_completion_has_no_ack_or_observation(candidate, registry, collector, monkeypatch, boundary):
    gateway, current, live, initial = candidate
    gateway.accept(envelope(registry))
    original_sync, original_replace = os.fsync, os.replace
    def sync(descriptor):
        original_sync(descriptor)
        directory = stat.S_ISDIR(os.fstat(descriptor).st_mode)
        if boundary == ('directory' if directory else 'file'): current[0] += 9
    def replace(source, target):
        original_replace(source, target)
        if boundary == 'observation' and target == gateway.observation_path: current[0] += 9
    monkeypatch.setattr(module.os, 'fsync', sync)
    monkeypatch.setattr(module.os, 'replace', replace)
    acknowledged = []
    with pytest.raises(TimeoutError, match='TRANSPORT_OPERATION_DEADLINE') as error:
        with gateway.operation():
            gateway.apply()
        acknowledged.append(True)
    assert acknowledged == [] and not gateway.observation_path.exists()
    monkeypatch.undo()
    gateway.fail_closed(error.value, 'isolated')
    assert ['systemctl', '--no-block', 'stop', *module.SERVICES] in live['calls']
    assert module.read(gateway.root/'transport-attempt.json')['result'] == 'error'


def test_expiry_during_commit_cannot_ack_allow(candidate, registry, collector, monkeypatch):
    gateway, current, live, initial = candidate
    event(registry)
    gateway.accept(envelope(registry))
    current[0] += 119
    original = os.fsync
    delayed = []
    def sync(descriptor):
        original(descriptor)
        if not delayed:
            current[0] += 2
            delayed.append(True)
    monkeypatch.setattr(module.os, 'fsync', sync)
    gateway.apply()
    assert initial['public_key'] not in live['awg']
    assert collector()['devices'][0]['awg_allowed'] is False


def test_runtime_recreation_reconfirms_and_monotonic_expiry_denies(candidate, registry, collector, monkeypatch):
    gateway, current, live, initial = candidate
    event(registry)
    gateway.accept(envelope(registry))
    gateway.apply()
    previous = module.read(gateway.root/'transport-attempt.json')['producer']
    replacement = module.Gateway(gateway.gateway, clock=gateway.clock, monotonic=gateway.monotonic, run=gateway.run)
    replacement.apply()
    assert module.read(gateway.root/'transport-attempt.json')['producer'] != previous
    assert collector()['status'] == 'ok'
    replacement.monotonic = lambda: current[0] + 120
    replacement.apply()
    assert initial['public_key'] not in live['awg']


def test_collector_does_not_read_through_active_registration(candidate, registry, collector):
    gateway, current, live, initial = candidate
    gateway.accept(envelope(registry))
    gateway.apply()
    with gateway.serialized():
        assert collector()['status'] == 'unavailable'
    with gateway.lock():
        assert collector()['status'] == 'unavailable'
    assert collector()['status'] == 'ok'


def test_revoke_between_plan_and_readback_never_overwrites_new_state(candidate, registry, collector):
    gateway, current, live, initial = candidate
    event(registry)
    gateway.accept(envelope(registry))
    gateway.apply()
    with gateway.serialized(), gateway.lock():
        state, peers, observations, changed = gateway.plan()
        event(registry, 'revoke', 'isolated-revoke')
        gateway.accept(envelope(registry))
        assert gateway.readback(state, peers, observations) is False
    gateway.apply()
    assert collector()['devices'][0]['awg_allowed'] is False
    assert gateway.load()['records'][initial['device']]['decision']['state'] == 'revoked'


@pytest.mark.parametrize('boundary', [1, 2, 3, 4, 5, 6])
def test_no_ack_before_every_required_sync(candidate, registry, monkeypatch, boundary):
    gateway, current, live, initial = candidate
    entered, release = threading.Event(), threading.Event()
    original = os.fsync
    calls, acknowledged, errors = [], [], []
    def sync(descriptor):
        calls.append(stat.S_ISDIR(os.fstat(descriptor).st_mode))
        if len(calls) == boundary:
            entered.set()
            assert release.wait(3)
        original(descriptor)
    def register():
        try:
            with gateway.serialized():
                with gateway.lock(): gateway.accept(envelope(registry))
                gateway.apply_serialized()
            acknowledged.append(True)
        except BaseException as error:
            errors.append(error)
    monkeypatch.setattr(module.os, 'fsync', sync)
    worker = threading.Thread(target=register)
    worker.start()
    try:
        assert entered.wait(3)
        assert acknowledged == [] and not gateway.observation_path.exists()
    finally:
        release.set()
        worker.join(3)
    assert not worker.is_alive() and errors == [] and acknowledged == [True]
    assert calls == [False, True]*3


def test_revoke_waiting_for_watch_lock_wins_after_delay(candidate, registry, collector, monkeypatch):
    gateway, current, live, initial = candidate
    event(registry)
    gateway.accept(envelope(registry))
    gateway.apply()
    event(registry, 'revoke', 'concurrent-revoke')
    started, errors = threading.Event(), []
    def revoke():
        started.set()
        try:
            with gateway.serialized():
                with gateway.lock(): gateway.accept(envelope(registry))
                gateway.apply_serialized()
        except BaseException as error: errors.append(error)
    with gateway.serialized():
        worker = threading.Thread(target=revoke)
        worker.start()
        assert started.wait(2)
        gateway.apply_serialized()
        assert collector()['status'] == 'unavailable'
    worker.join(3)
    assert not worker.is_alive() and errors == []
    assert gateway.load()['records'][initial['device']]['decision']['state'] == 'revoked'
    assert collector()['devices'][0]['awg_allowed'] is False


@pytest.mark.parametrize('clock_change', ['backwards', 'forward', 'boot'])
def test_clock_and_boot_changes_never_extend_lease(candidate, registry, collector, monkeypatch, clock_change):
    gateway, current, live, initial = candidate
    event(registry)
    gateway.accept(envelope(registry))
    gateway.apply()
    if clock_change == 'boot': monkeypatch.setattr(module, 'boot_id', lambda: 'replacement-boot')
    elif clock_change == 'forward': current[0] += 121
    else:
        current[0] -= 1
        assert collector()['status'] == 'unavailable'
        gateway.monotonic = lambda: current[0]+122
    gateway.apply()
    assert initial['public_key'] not in live['awg']


@pytest.mark.parametrize('fail', [False, True])
def test_watchdog_follows_enforcement_and_never_failed_commit(candidate, registry, collector, monkeypatch, fail):
    gateway, current, live, initial = candidate
    gateway.accept(envelope(registry))
    notices = []
    original = gateway.apply
    def apply(*, starting=False):
        if starting: return original(starting=True)
        if fail:
            raise TimeoutError('TRANSPORT_OPERATION_DEADLINE')
        original()
    def notify(value):
        if value == 'WATCHDOG=1':
            assert collector()['status'] == 'ok'
            assert len([call for call in live['calls'] if call[1] in ('api', 'show')]) == 3
            notices.append(value)
            raise InterruptedError('bounded-watch-complete')
    monkeypatch.setattr(gateway, 'apply', apply)
    monkeypatch.setattr(module, 'Gateway', lambda *args, **kwargs: gateway)
    monkeypatch.setattr(module, 'notify', notify)
    with pytest.raises(TimeoutError if fail else InterruptedError): module.watch(gateway.gateway)
    assert notices == ([] if fail else ['WATCHDOG=1'])
    assert not gateway.observation_path.exists()


@pytest.mark.parametrize('operation', ['reconcile', 'prepare', 'register'])
def test_real_registration_entrypoint_commit_timeout_stops_without_ack(candidate, registry, collector, monkeypatch, capsys, operation):
    gateway, current, live, initial = candidate
    spec = importlib.util.spec_from_file_location('isolated_awg_entrypoint', Path(__file__).resolve().parents[1]/'deploy/friends/awg-gateway.py')
    entrypoint = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(entrypoint)
    monkeypatch.setattr(entrypoint, 'paid_engine', lambda: gateway)
    request = dict(operation=operation, paid=envelope(registry))
    if operation == 'prepare': request['token'] = 'c'*64
    if operation == 'register':
        request = {key:initial[key] for key in ('public_key', 'tcp_id', 'device')}
        request['paid'] = envelope(registry)
    monkeypatch.setattr(entrypoint.sys, 'stdin', io.TextIOWrapper(io.BytesIO(json.dumps(request).encode())))
    original = os.fsync
    once = []
    def sync(descriptor):
        original(descriptor)
        if not once:
            current[0] += 9
            once.append(True)
    monkeypatch.setattr(module.os, 'fsync', sync)
    with pytest.raises(TimeoutError, match='TRANSPORT_OPERATION_DEADLINE'):
        entrypoint.register()
    assert capsys.readouterr().out == ''
    assert ['systemctl', '--no-block', 'stop', *module.SERVICES] in live['calls']
    assert module.read(gateway.root/'transport-attempt.json')['result'] == 'error'
    assert collector()['status'] == 'unavailable'


def test_no_watchdog_during_candidate_engine_startup_wait(candidate, registry, collector, monkeypatch):
    gateway, current, live, initial = candidate
    gateway.accept(envelope(registry))
    original = gateway.run
    waiting, notices = [], []
    def run(arguments):
        if arguments[:2] == ['systemctl', 'is-active'] and not waiting:
            waiting.append(True)
            raise subprocess.CalledProcessError(3, arguments)
        return original(arguments)
    def notify(value):
        notices.append(value)
        if value == 'WATCHDOG=1':
            assert collector()['status'] == 'ok'
            raise InterruptedError('bounded-end')
    monkeypatch.setattr(gateway, 'run', run)
    monkeypatch.setattr(module, 'Gateway', lambda *args, **kwargs: gateway)
    monkeypatch.setattr(module, 'notify', notify)
    monkeypatch.setattr(module.time, 'sleep', lambda seconds: None)
    with pytest.raises(InterruptedError): module.watch(gateway.gateway)
    assert waiting == [True] and notices == ['READY=1', 'WATCHDOG=1']


@pytest.mark.parametrize('defect', ['dead', 'reused'])
def test_consistently_bound_dead_or_reused_producer_is_rejected(candidate, registry, collector, defect):
    gateway, current, live, initial = candidate
    gateway.accept(envelope(registry))
    gateway.apply()
    for filename in (gateway.root/'transport-attempt.json', gateway.observation_path):
        record = module.read(filename)
        record['producer']['pid' if defect == 'dead' else 'start'] = 2**30 if defect == 'dead' else '0'
        module.write(filename, record)
    assert collector()['status'] == 'unavailable'


def test_observation_cleanup_error_preserves_first_failure_and_stops(candidate, registry, monkeypatch):
    gateway, current, live, initial = candidate
    gateway.accept(envelope(registry))
    gateway.apply()
    original = Path.unlink
    def unlink(path, *args, **kwargs):
        if path == gateway.observation_path: raise PermissionError('synthetic cleanup failure')
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'unlink', unlink)
    with pytest.raises(TimeoutError, match='TRANSPORT_OPERATION_DEADLINE') as caught:
        with gateway.operation(): raise TimeoutError('TRANSPORT_OPERATION_DEADLINE')
    gateway.fail_closed(caught.value, 'isolated')
    assert ['systemctl', '--no-block', 'stop', *module.SERVICES] in live['calls']
    assert module.read(gateway.root/'transport-attempt.json')['result'] == 'error'


def test_unknown_mode_is_not_silently_enabled(engine):
    gateway = engine[0]
    config = module.read(gateway.root/'transport-enforcement.json')
    config['readback_mode'] = 'unknown'
    module.write(gateway.root/'transport-enforcement.json', config)
    with pytest.raises(ValueError, match='INVALID_GATEWAY_POLICY'):
        module.Gateway(gateway.gateway)


def test_forked_producer_is_live_then_rejected_after_exit(candidate, registry, collector):
    gateway, current, live, initial = candidate
    gateway.accept(envelope(registry))
    gateway.apply()
    before = gateway.producer.copy()
    signal_read, signal_write = os.pipe()
    release_read, release_write = os.pipe()
    child = os.fork()
    if child == 0:
        os.close(signal_read); os.close(release_write)
        try:
            gateway.apply()
            os.write(signal_write, b'R')
            os.read(release_read, 1)
            os._exit(0)
        except BaseException: os._exit(1)
    os.close(signal_write); os.close(release_read)
    try:
        assert select.select([signal_read], [], [], 3)[0]
        assert os.read(signal_read, 1) == b'R'
        producer = module.read(gateway.root/'transport-attempt.json')['producer']
        assert producer['pid'] == child and producer['generation'] != before['generation']
        assert collector()['status'] == 'ok'
    finally:
        os.close(signal_read)
        try: os.write(release_write, b'R')
        except BrokenPipeError: pass
        os.close(release_write)
        assert os.waitpid(child, 0)[1] == 0
    assert collector()['status'] == 'unavailable'
