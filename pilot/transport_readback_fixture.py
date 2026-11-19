"""Disposable namespace only: installed-bundle readback qualification and fault hooks."""
import fcntl
import contextlib
import hashlib
import importlib.util
import io
import json
import multiprocessing
import os
from pathlib import Path
import shutil
import signal
import sqlite3
import stat
import subprocess
import sys
import time
import uuid

ROOT = Path('/opt/apps/family_connect/friends-awg')
UNITS = ('family-connect-paid-watch.service', 'family-connect-friends-awg.service', 'family-connect-friends-tcp.service')
TRIGGER = Path('/run/readback-fault')
EVENTS = Path('/run/readback-notify.jsonl')


def command(arguments, **kwargs):
    return subprocess.run(arguments, capture_output=True, timeout=35, check=True, **kwargs)


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


def installed_engine():
    sys.path.insert(0, str(ROOT/'paid-transport.pyz'))
    gateway = load_module('installed_gateway', ROOT/'awg-gateway.py')
    from control.friends import transport_gateway
    assert transport_gateway.__loader__.archive == str(ROOT/'paid-transport.pyz')
    return gateway, transport_gateway


def properties(unit):
    output = command(['systemctl', 'show', unit, '-p', 'ActiveState', '-p', 'MainPID',
        '-p', 'ControlPID', '-p', 'Job', '-p', 'Restart', '-p', 'WatchdogUSec', '-p', 'Result', '-p', 'ExecStart',
        '-p', 'TimeoutStopUSec', '-p', 'KillMode', '-p', 'BindsTo', '-p', 'After', '-p', 'User',
        '-p', 'FragmentPath', '-p', 'DropInPaths', '-p', 'ExecStartPre', '-p', 'NRestarts']).stdout.decode()
    return dict(line.split('=', 1) for line in output.strip().splitlines())


def wait_for(predicate, timeout=15):
    deadline = time.monotonic()+timeout
    while not predicate():
        if time.monotonic() >= deadline:
            raise AssertionError('READBACK_FIXTURE_BOUNDARY_TIMEOUT')
        time.sleep(.05)


def observation():
    try:
        value = json.loads((ROOT/'transport-observation.json').read_text())
        return value if value['producer']['pid'] == int(properties(UNITS[0])['MainPID']) else None
    except (OSError, ValueError, KeyError):
        return None


def collect():
    collector = load_module('installed_collector', ROOT/'collectors/transport_collector.py')
    return collector.collect_transport('gateway-ru', b'k'*32,
        hashlib.sha256((ROOT/'paid-transport.pyz').read_bytes()).hexdigest(), ROOT)['status']


def snapshot():
    state = json.loads((ROOT/'transport-state.json').read_text())
    return {device: {key: value for key, value in record.items() if key != 'applied'}
        for device, record in state['records'].items()}


def envelope(seconds=120):
    current = int(time.time())
    state = json.loads((ROOT/'transport-state.json').read_text())
    return dict(schema=1, profile='paid-transports-v2', node='gateway-ru', observed_at=current,
        decisions=[dict(value['decision'], observed_at=current, valid_until=current+seconds)
            for value in state['records'].values()])


def register(payload):
    return subprocess.run(['/usr/bin/python3', str(ROOT/'awg-gateway.py'), 'register'],
        input=json.dumps(payload).encode(), capture_output=True, timeout=12)


def prelock_race(fault, baseline=False):
    gateway, module = installed_engine()
    context = multiprocessing.get_context('fork')
    opened, release_open, owned, release_owner, finished, exit_owner = [context.Event() for _ in range(6)]
    results, events = context.Queue(), context.Queue()
    request = dict(operation='reconcile', paid=envelope())
    first_path = ROOT/'transport-failure.json'
    previous = first_path.read_bytes() if first_path.exists() else None
    for unit in UNITS[1:]:
        (Path('/etc/systemd/system')/(unit+'.d')/'99-pending-stop.conf').write_text('[Service]\nExecStop=/bin/sleep 4\n')
    command(['systemctl', 'daemon-reload'])

    def participant(role):
        worker = module.Gateway(gateway)
        gateway.paid_engine = lambda: worker
        gateway.sys.stdin = io.TextIOWrapper(io.BytesIO(json.dumps(request).encode()))
        original_open, original_accept, original_stop, original_run = Path.open, worker.accept, worker.stop_all, worker.run
        queries = []
        def open_file(path, *args, **kwargs):
            if path == ROOT/'application.lock':
                events.put((role, 'open-entered', time.monotonic()))
                opened.set()
                assert release_open.wait(20)
                if fault == 'open-error':
                    raise OSError(5, 'synthetic application open failure')
            return original_open(path, *args, **kwargs)
        def accept(*args, **kwargs):
            events.put((role, 'owns-application-lock', time.monotonic()))
            owned.set()
            assert release_owner.wait(6)
            return original_accept(*args, **kwargs)
        def stop():
            original_stop()
            events.put((role, 'async-stop-request', time.monotonic()))
        def run(arguments):
            if arguments[0] != 'systemctl':
                queries.append(arguments[0])
            return original_run(arguments)
        worker.stop_all, worker.run = stop, run
        if role == 'B':
            Path.open = open_file
        else:
            worker.accept = accept
        output, failure = io.StringIO(), None
        with contextlib.redirect_stdout(output):
            try:
                gateway.register()
            except BaseException as error:
                failure = str(error)
        events.put((role, 'operation-exited', time.monotonic()))
        results.put(dict(role=role, ack=output.getvalue(), error=failure, queries=len(queries)))
        if role == 'A':
            finished.set()
            assert exit_owner.wait(10)

    early = context.Process(target=participant, args=('B',))
    later = context.Process(target=participant, args=('A',))
    watcher = int(properties(UNITS[0])['MainPID'])
    early.start()
    try:
        assert opened.wait(5)
        if fault == 'deadline':
            time.sleep(8.15)
        with (ROOT/'application.lock').open('a') as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            os.kill(watcher, signal.SIGSTOP)
        later.start()
        assert owned.wait(5)
        release_open.set()
        early.join(5)
        assert early.exitcode == 0
        first = first_path.read_bytes()
        assert json.loads((ROOT/'transport-attempt.json').read_text())['result'] == 'error'
        wait_for(lambda: all(properties(unit)['ActiveState'] == 'deactivating' for unit in UNITS[1:]), timeout=2)
        pending = {unit:properties(unit) for unit in UNITS[1:]}
        assert all(value['MainPID'] != '0' and value['Job'] for value in pending.values())
        release_owner.set()
        assert finished.wait(4)
        observed = {result['role']:result for result in [results.get(timeout=2), results.get(timeout=2)]}
        trace = [events.get(timeout=2) for index in range(5 if observed['A']['ack'] else 6)]
        result = dict(result='REPRODUCED_UNSAFE_ACK' if baseline else 'PASS', fault=fault,
            participants=observed, events=sorted(trace, key=lambda value:value[2]), stop_pending=pending,
            collector=collect(), incomplete=(ROOT/'application-incomplete').exists(),
            emergency=(ROOT/'application-failed').exists())
        assert not observed['B']['ack'] and observed['B']['queries'] == 0
        assert 'TRANSPORT_OPERATION_DEADLINE' in observed['B']['error'] if fault == 'deadline' else 'synthetic application open failure' in observed['B']['error']
        assert first_path.read_bytes() == (previous or first)
        if baseline:
            assert json.loads(observed['A']['ack'])['result'] == 'applied' and observed['A']['queries'] == 3
            assert result['collector'] == 'ok' and not result['incomplete']
        else:
            assert not observed['A']['ack'] and observed['A']['error'] == 'TRANSPORT_RECOVERY_REQUIRED'
            assert result['collector'] == 'unavailable' and result['emergency']
            subsequent = register(request)
            assert subsequent.returncode != 0 and not subsequent.stdout
            assert (ROOT/'application-failed').exists()
            recovery = subprocess.run(['/usr/bin/python3', str(ROOT/'awg-gateway.py'), 'paid-recover'], capture_output=True, timeout=12)
            assert recovery.returncode != 0 and not recovery.stdout
            assert (ROOT/'application-failed').exists()
            result['pending_recovery_rejected'] = True
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
        os.kill(watcher, signal.SIGCONT)
        command(['systemctl', 'stop', *UNITS])
        for unit in UNITS[1:]:
            (Path('/etc/systemd/system')/(unit+'.d')/'99-pending-stop.conf').unlink()
        command(['systemctl', 'daemon-reload'])
        results.close()
        events.close()
    assert all(properties(unit)['MainPID'] == '0' and properties(unit)['ControlPID'] == '0' and properties(unit)['Job'] == '' for unit in UNITS)
    if not baseline:
        assert (ROOT/'application-failed').exists() and collect() == 'unavailable'
        start()
        assert not (ROOT/'application-failed').exists()
        assert json.loads(register(dict(operation='reconcile', paid=envelope())).stdout)['result'] == 'applied'
        wait_for(lambda: observation() and collect() == 'ok')
        assert first_path.read_bytes() == first
        result['stopped_then_explicitly_recovered'] = True
    return result


def start(legacy=False):
    command(['systemctl', 'stop', *UNITS])
    assert all(properties(unit)['MainPID'] == '0' and properties(unit)['Job'] == '' for unit in UNITS)
    if not legacy and any((ROOT/name).exists() for name in ('application-incomplete', 'application-failed')):
        command(['/usr/bin/python3', str(ROOT/'awg-gateway.py'), 'paid-recover'])
    for unit in UNITS:
        command(['systemctl', 'start', unit])
    if not legacy:
        wait_for(lambda: observation() and collect() == 'ok')
    assert all(properties(unit)['NRestarts'] == '0' for unit in UNITS), 'UNEXPECTED_AUTOMATIC_RESTART'


def instrumented_watch():
    gateway, module = installed_engine()
    original_apply, original_sync, original_notify = module.Gateway.apply_serialized, os.fsync, module.notify
    def apply(engine):
        if TRIGGER.exists():
            fault = TRIGGER.read_text()
            if fault == 'readback':
                TRIGGER.unlink()
                raise ValueError('ENGINE_READBACK_MISMATCH')
            engine.producer['generation'] = uuid.uuid4().hex
        return original_apply(engine)
    def sync(descriptor):
        if TRIGGER.exists() and 'transport-state' in os.readlink('/proc/self/fd/'+str(descriptor)):
            fault = TRIGGER.read_text()
            TRIGGER.unlink()
            if fault == 'write-error':
                raise OSError(5, 'synthetic durable write fault')
            if fault == 'write-delay':
                time.sleep(9)
            if fault == 'write-hang':
                time.sleep(30)
        return original_sync(descriptor)
    def notify(value):
        current = observation() if value == 'WATCHDOG=1' else None
        with EVENTS.open('a') as output:
            output.write(json.dumps(dict(value=value, at=time.monotonic(),
                observation=bool(current), fenced=any((ROOT/name).exists() for name in ('application-incomplete', 'application-failed'))))+'\n')
        original_notify(value)
    module.Gateway.apply_serialized, os.fsync, module.notify = apply, sync, notify
    module.watch(gateway)


def cost():
    gateway, module = installed_engine()
    engine = module.Gateway(gateway)
    engine.apply()
    counts = dict(engine_queries=0, durable_writes=0, file_fsync=0, directory_fsync=0, collector_ok=0)
    original_run, original_write, original_sync = engine.run, module.write, os.fsync
    def run(arguments):
        counts['engine_queries'] += 1
        return original_run(arguments)
    def write(*args, **kwargs):
        counts['durable_writes'] += 1
        return original_write(*args, **kwargs)
    def sync(descriptor):
        counts['directory_fsync' if stat.S_ISDIR(os.fstat(descriptor).st_mode) else 'file_fsync'] += 1
        return original_sync(descriptor)
    engine.run, module.write, os.fsync = run, write, sync
    for cycle in range(6):
        engine.apply()
        assert collect() == 'ok'
        counts['collector_ok'] += 1
    expected = 0 if getattr(engine, 'observation_mode', False) else 12
    assert counts == dict(engine_queries=18, durable_writes=expected, file_fsync=expected,
        directory_fsync=expected, collector_ok=6), counts
    print(json.dumps(dict(counts=counts, archive=hashlib.sha256((ROOT/'paid-transport.pyz').read_bytes()).hexdigest(),
        loader=module.__loader__.archive)))


def paused_cost():
    pid = int(properties(UNITS[0])['MainPID'])
    with (ROOT/'application.lock').open('a') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        os.kill(pid, signal.SIGSTOP)
    try:
        return json.loads(command(['/usr/bin/python3', '/readback_fixture.py', 'cost']).stdout)
    finally:
        os.kill(pid, signal.SIGCONT)


def qualify(fixture, phase):
    if phase.startswith('prelock-'):
        return json.loads(command(['/usr/bin/python3', '/readback_fixture.py', phase]).stdout)
    if phase == 'installed':
        manifest = json.loads(Path('/kit/manifest.json').read_text())
        for name in ('paid-transport.pyz', 'awg-gateway.py', 'collectors/transport_collector.py'):
            path = ROOT/name
            assert hashlib.sha256(path.read_bytes()).hexdigest() == manifest['files'][name]['sha256']
            assert path.stat().st_uid == 0 and path.stat().st_mode & 0o777 == 0o600
        for name in ('family-connect-paid-watch.service', 'paid-dependency.conf', 'paid-tcp-preflight.conf'):
            expected = manifest['files'][name]['sha256']
            paths = ([Path('/etc/systemd/system')/name] if name.endswith('.service') else
                [Path('/etc/systemd/system')/(unit+'.d')/('90-paid.conf' if name == 'paid-dependency.conf' else '91-paid-preflight.conf')
                    for unit in (UNITS[1:] if name == 'paid-dependency.conf' else UNITS[2:])])
            assert all(hashlib.sha256(path.read_bytes()).hexdigest() == expected for path in paths)
        current = properties(UNITS[0])
        assert current['Restart'] == 'no' and current['WatchdogUSec'] == '12s'
        assert current['TimeoutStopUSec'] == '5s' and current['KillMode'] == 'control-group'
        assert str(ROOT/'awg-gateway.py')+' paid-watch' in current['ExecStart']
        for unit in UNITS[1:]:
            effective = properties(unit)
            assert UNITS[0] in effective['BindsTo'].split() and UNITS[0] in effective['After'].split()
            assert effective['TimeoutStopUSec'] == '5s' and effective['KillMode'] == 'control-group'
        assert properties(UNITS[2])['User'] == 'fc-friends'
        assert all(properties(unit)['NRestarts'] == '0' for unit in UNITS), 'UNEXPECTED_AUTOMATIC_RESTART'
        wait_for(lambda: observation() and collect() == 'ok')
        result = dict(result='PASS', effective={unit:properties(unit) for unit in UNITS}, candidate_cost=paused_cost())
        result['native_sha256'] = {name:hashlib.sha256((Path('/native')/name).read_bytes()).hexdigest()
            for name in ('awg', 'amneziawg-go', 'xray')}
        config_path = ROOT/'transport-enforcement.json'
        original = config_path.read_bytes()
        try:
            for mode in ('unknown', 'legacy'):
                config = json.loads(original)
                config['readback_mode'] = mode
                config_path.write_text(json.dumps(config))
                process = subprocess.run(['/usr/bin/python3', '/readback_fixture.py', 'mode-check'], capture_output=True, timeout=8)
                assert process.returncode != 0 and not process.stdout
                assert collect() == 'unavailable'
        finally:
            config_path.write_bytes(original)
        result['unknown_or_incompatible_mode_rejected'] = True
        return result
    if phase in ('race', 'race-baseline'):
        command(['systemctl', 'stop', *UNITS])
        drop = Path('/etc/systemd/system')/(UNITS[0]+'.d')
        drop.mkdir(exist_ok=True)
        (drop/'99-readback-fixture.conf').write_text('[Service]\nExecStart=\nExecStart=/usr/bin/python3 /readback_fixture.py watch\n')
        for unit in UNITS[1:]:
            (Path('/etc/systemd/system')/(unit+'.d')/'99-pending-stop.conf').write_text('[Service]\nExecStop=/bin/sleep 4\n')
        command(['systemctl', 'daemon-reload'])
        start()
        request = dict(operation='reconcile', paid=envelope())
        TRIGGER.write_text('readback')
        wait_for(lambda: properties(UNITS[0])['MainPID'] == '0' and properties(UNITS[2])['ActiveState'] == 'deactivating')
        pending = {unit: properties(unit) for unit in UNITS[1:]}
        assert all(value['MainPID'] != '0' and value['Job'] != '' for value in pending.values()), pending
        attempt = register(request)
        if phase == 'race-baseline':
            assert attempt.returncode == 0 and json.loads(attempt.stdout)['result'] == 'applied'
            return dict(result='REPRODUCED_UNSAFE_ACK', stop_pending=pending, concurrent_ack=True,
                archive=hashlib.sha256((ROOT/'paid-transport.pyz').read_bytes()).hexdigest())
        assert attempt.returncode != 0 and not attempt.stdout
        assert collect() == 'unavailable'
        first = (ROOT/'transport-failure.json').read_bytes()
        assert json.loads(first)['reason'] == 'ENGINE_READBACK_MISMATCH'
        command(['systemctl', 'stop', *UNITS])
        assert all(properties(unit)['MainPID'] == '0' for unit in UNITS)
        assert not (ROOT/'transport-observation.json').exists()
        stopped_state = (ROOT/'transport-state.json').read_bytes()
        time.sleep(2)
        assert (ROOT/'transport-state.json').read_bytes() == stopped_state
        assert not (ROOT/'transport-observation.json').exists()
        events = [json.loads(line) for line in EVENTS.read_text().splitlines()]
        assert events[0]['value'] == 'READY=1' and not events[0]['observation']
        assert any(event['value'] == 'WATCHDOG=1' for event in events)
        assert all(event['observation'] and not event['fenced'] for event in events if event['value'] == 'WATCHDOG=1')
        for unit in UNITS[1:]:
            (Path('/etc/systemd/system')/(unit+'.d')/'99-pending-stop.conf').unlink()
        command(['systemctl', 'daemon-reload'])
        start()
        assert (ROOT/'transport-failure.json').read_bytes() == first
        return dict(result='PASS', stop_pending=pending, concurrent_ack=False, collector='unavailable',
            processes_stopped=True, no_late_application=True, notify_events=events, explicit_recovery=True)
    if phase == 'collector':
        wait_for(lambda: observation() and collect() == 'ok')
        previous = observation()['producer']
        start()
        assert observation()['producer'] != previous
        pid = int(properties(UNITS[0])['MainPID'])
        with (ROOT/'application.lock').open('a') as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            os.kill(pid, signal.SIGSTOP)
        path = ROOT/'transport-observation.json'
        original = path.read_bytes()
        results = {}
        try:
            for kind in ('missing', 'corrupt', 'old-generation', 'expired'):
                value = json.loads(original)
                if kind == 'missing':
                    path.unlink()
                elif kind == 'corrupt':
                    path.write_text('{')
                else:
                    if kind == 'old-generation':
                        value['producer'] = previous
                    else:
                        value['observed_at'] -= 13
                        value['monotonic'] -= 13
                    path.write_text(json.dumps(value))
                results[kind] = collect()
                path.write_bytes(original)
            with (ROOT/'application.lock').open('a') as handle:
                fcntl.flock(handle, fcntl.LOCK_EX)
                results['active-writer'] = collect()
        finally:
            path.write_bytes(original)
            os.kill(pid, signal.SIGCONT)
        assert set(results.values()) == {'unavailable'}
        return dict(result='PASS', generation_changed=True, collector=results)
    if phase == 'durable':
        first = (ROOT/'transport-failure.json').read_bytes()
        results = {}
        for fault in ('write-error', 'write-delay', 'write-hang'):
            before = snapshot()
            TRIGGER.write_text(fault)
            wait_for(lambda: not TRIGGER.exists())
            notified = EVENTS.read_bytes()
            assert collect() == 'unavailable'
            wait_for(lambda: all(properties(unit)['MainPID'] == '0' for unit in UNITS), timeout=20)
            assert EVENTS.read_bytes() == notified
            assert snapshot() == before
            assert collect() == 'unavailable' and not (ROOT/'transport-observation.json').exists()
            assert (ROOT/'transport-failure.json').read_bytes() == first
            termination = properties(UNITS[0])['Result']
            if fault == 'write-hang':
                assert termination == 'watchdog'
            results[fault] = dict(stopped=True, authority_preserved=True, collector='unavailable', watcher_result=termination)
            start()
        return dict(result='PASS', faults=results)
    if phase == 'expire':
        response = register(dict(operation='reconcile', paid=envelope(4)))
        assert response.returncode == 0
        time.sleep(7)
        return dict(result='PASS', live_short_lease_expired=True)
    if phase in ('rollback', 'return'):
        if phase == 'rollback':
            request = envelope()
            with sqlite3.connect(ROOT/'peers.db') as database:
                registered = {row[0] for row in database.execute('SELECT public FROM peers')}
            request['decisions'] = [next(value for value in request['decisions']
                if not value['cohort'] and value['public_key'] not in registered)]
            assert register(dict(operation='prepare', paid=request, token='c'*64)).returncode == 0
        command(['systemctl', 'stop', *UNITS])
        before = snapshot()
        assert any(value['decision']['state'] == 'revoked' for value in before.values())
        assert any(value['prepared'] == 'c'*64 for value in before.values())
        if any((ROOT/name).exists() for name in ('application-incomplete', 'application-failed')):
            command(['/usr/bin/python3', str(ROOT/'awg-gateway.py'), 'paid-recover'])
        source = Path('/kit/legacy' if phase == 'rollback' else '/kit')
        for name in ('paid-transport.pyz', 'awg-gateway.py'):
            shutil.copyfile(source/name, ROOT/name)
            (ROOT/name).chmod(0o600)
        shutil.copyfile(source/UNITS[0], Path('/etc/systemd/system')/UNITS[0])
        drop = Path('/etc/systemd/system')/(UNITS[0]+'.d')/'99-readback-fixture.conf'
        drop.unlink(missing_ok=True)
        config = json.loads((ROOT/'transport-enforcement.json').read_text())
        config.pop('readback_mode', None)
        if phase == 'return':
            config['readback_mode'] = 'observations-v1'
        (ROOT/'transport-enforcement.json').write_text(json.dumps(config))
        command(['systemctl', 'daemon-reload'])
        start(legacy=phase == 'rollback')
        wait_for(lambda: collect() == 'ok')
        assert snapshot() == before
        result = dict(result='PASS', all_authority_fields_preserved=True, actual_readback='ok',
            state_restored_from_backup=False, archive=hashlib.sha256((ROOT/'paid-transport.pyz').read_bytes()).hexdigest())
        if phase == 'rollback':
            result['baseline_cost'] = paused_cost()
        return result
    raise ValueError('UNKNOWN_READBACK_PHASE')


if __name__ == '__main__':
    if sys.argv[1:] == ['watch']:
        instrumented_watch()
    elif sys.argv[1:] == ['cost']:
        cost()
    elif sys.argv[1:] == ['mode-check']:
        gateway, module = installed_engine()
        module.Gateway(gateway)
    elif len(sys.argv) == 2 and sys.argv[1].startswith('prelock-'):
        phase = sys.argv[1]
        print(json.dumps(prelock_race(phase.removeprefix('prelock-').removesuffix('-baseline'), phase.endswith('-baseline'))))
    else:
        raise ValueError('ISOLATED_FIXTURE_ACTION_REQUIRED')
