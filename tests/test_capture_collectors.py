import argparse
from contextlib import contextmanager
from contextvars import Context
import fcntl
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from types import SimpleNamespace

import pytest

from control.capture_gate import Busy, CURRENT, GateError, initialize
from control_plane import collect_inventory, monitor_inventory, probe_network
from control_plane.collector_admission import run_cli
from test_capture_gate import ROOT, line


@pytest.fixture
def gate(tmp_path, monkeypatch):
    gate = initialize(tmp_path / 'capture')
    monkeypatch.setenv('FC_CONTROL_CAPTURE_GATE', str(gate.directory))
    return gate


def pending(gate):
    return sorted((gate.directory / 'pending').iterdir())


def probe(source):
    return dict(source=source, observed_at='2026-11-24T00:00:00Z', outcome='reachable')


def completed(command, stdout=b''):
    return subprocess.CompletedProcess(command, 0, stdout=stdout)


def snapshot(base, command):
    destination = base / '.local' / (command[-1] + '-test.json')
    destination.write_text(json.dumps(dict(source=command[-1], scope='production',
        observed_at='2026-11-24T00:00:00Z', registry_status='unavailable', devices=[])))
    return completed(command, str(destination).encode())


@pytest.mark.parametrize('collector', ['monitor', 'probe', 'inventory'])
@pytest.mark.parametrize('state', ['closed', 'missing'])
def test_collector_refuses_before_local_files_or_dispatch(gate, tmp_path, monkeypatch, collector, state):
    base = tmp_path / 'work'
    base.mkdir()
    monkeypatch.setattr(collect_inventory, 'BASE', base)
    def forbidden(*args, **kwargs):
        pytest.fail('dispatch before admission')
    monkeypatch.setattr(collect_inventory.subprocess, 'run', forbidden)
    def invoke():
        if collector == 'monitor':
            return monitor_inventory.cycle(base, forbidden)
        if collector == 'probe':
            return probe_network.cycle(base, forbidden, forbidden)
        return collect_inventory.collect(SimpleNamespace(source='gateway-ru', known_hosts=None), argparse.ArgumentParser())
    with gate.drain(.1):
        if state == 'missing':
            monkeypatch.setenv('FC_CONTROL_CAPTURE_GATE', str(tmp_path / 'absent-gate'))
        with pytest.raises(Busy if state == 'closed' else GateError):
            invoke()
    assert list(base.iterdir()) == [] and not pending(gate)


@pytest.mark.parametrize('name,arguments', [('monitor_inventory.py', []), ('probe_network.py', []),
                                         ('collect_inventory.py', ['gateway-ru'])])
@pytest.mark.parametrize('state', ['closed', 'missing'])
def test_actual_cli_refuses_with_sanitized_exit(gate, tmp_path, name, arguments, state):
    environment = dict(os.environ)
    if state == 'missing':
        environment['FC_CONTROL_CAPTURE_GATE'] = str(tmp_path / 'private-missing-gate')
    with gate.drain(.1):
        result = subprocess.run([sys.executable, '-B', str(ROOT / 'control_plane' / name), *arguments],
                                cwd=tmp_path, env=environment, capture_output=True, timeout=5)
    assert result.returncode == (75 if state == 'closed' else 1)
    assert result.stderr.strip() == (b'CAPTURE_BUSY' if state == 'closed' else b'CAPTURE_UNAVAILABLE')
    assert not result.stdout and not pending(gate)


@pytest.mark.parametrize('name', ['collect_inventory.py', 'monitor_inventory.py'])
def test_argument_help_does_not_enter_gate(gate, name):
    with gate.drain(.1):
        result = subprocess.run([sys.executable, '-B', str(ROOT / 'control_plane' / name), '--help'],
                                capture_output=True, timeout=5)
    assert result.returncode == 0 and not pending(gate)


def test_monitor_holds_through_import_fallback_cleanup_and_receipt(gate, tmp_path, monkeypatch):
    calls = []
    unlink, replace = Path.unlink, Path.replace
    def admitted():
        assert CURRENT.get() is not None and len(pending(gate)) == 1
        with pytest.raises(Busy, match='DRAIN_TIMEOUT'):
            with independent_drain(gate, .01):
                pytest.fail('collector not drained')
    def run(command, **options):
        admitted()
        calls.append(command)
        return snapshot(tmp_path, command) if command[0] != 'docker' else completed(command)
    def remove(path, *args, **kwargs):
        admitted()
        return unlink(path, *args, **kwargs)
    def publish(path, target):
        admitted()
        return replace(path, target)
    monkeypatch.setattr(Path, 'unlink', remove)
    monkeypatch.setattr(Path, 'replace', publish)
    receipt = monitor_inventory.cycle(tmp_path, run)
    assert all(row['status'] == 'IMPORTED' for row in receipt['sources'])
    assert len(calls) == 6 and not pending(gate)
    assert (tmp_path / '.local/monitor-latest.json').is_file()


@contextmanager
def independent_drain(gate, timeout):
    manager = gate.drain(timeout)
    context = Context()
    context.run(manager.__enter__)
    try:
        yield
    finally:
        context.run(manager.__exit__, None, None, None)


@pytest.mark.parametrize('collector,lock_name', [('monitor', 'monitor.lock'), ('probe', 'network-probe.lock')])
def test_duplicate_cycle_is_a_clean_skip_not_uncertainty(gate, tmp_path, collector, lock_name):
    local = tmp_path / '.local'
    local.mkdir()
    with (local / lock_name).open('w') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError):
            if collector == 'monitor':
                monitor_inventory.cycle(tmp_path)
            else:
                probe_network.cycle(tmp_path)
    assert not pending(gate)
    with gate.drain(.1):
        pass


@pytest.mark.parametrize('failure', ['inventory', 'subscriptions', 'transport', 'metadata', 'metadata-fallback'])
def test_caught_monitor_dispatch_failure_survives_fallback_and_later_success(gate, tmp_path, monkeypatch, failure):
    local = tmp_path / '.local'
    local.mkdir()
    (local / 'subscriptions-source.json').write_text('{}')
    (local / 'technical-metadata-source.json').write_text('{}')
    monkeypatch.setattr(monitor_inventory, 'SOURCES', ('gateway-ru',))
    calls = []
    def run(command, **options):
        assert CURRENT.get() is not None and len(pending(gate)) == 1
        calls.append(command)
        if command[0] != 'docker':
            return (completed(command, b'{}') if 'collect_technical_metadata.py' in command[1]
                    else snapshot(tmp_path, command))
        if (('import_inventory' in command and failure in ('inventory', 'subscriptions', 'transport')) or
                ('import_subscriptions' in command and failure == 'subscriptions') or
                ('transport_failure' in command and failure == 'transport') or
                ('import_technical_metadata' in command and failure in ('metadata', 'metadata-fallback') and
                 (command[-1] != '--unavailable' or failure == 'metadata-fallback'))):
            raise subprocess.TimeoutExpired(command, options['timeout'], stderr=b'private output')
        return completed(command)
    receipt = monitor_inventory.cycle(tmp_path, run)
    assert 'private output' not in json.dumps(receipt) and len(pending(gate)) == 1
    if failure in ('inventory', 'subscriptions', 'transport'):
        assert any('import_subscriptions' in command for command in calls)
        assert any('transport_failure' in command for command in calls)
    else:
        assert any(command[-1] == '--unavailable' for command in calls)
    old = pending(gate)
    monkeypatch.setattr(monitor_inventory, 'SOURCES', ())
    monitor_inventory.cycle(tmp_path, lambda *args, **kwargs: completed(args[0], b'{}'))
    assert pending(gate) == old
    with pytest.raises(GateError, match='UNSETTLED_OPERATION'):
        with gate.drain(.1):
            pytest.fail('lost caught uncertainty')


def test_inventory_success_and_failed_local_write_are_admitted(gate, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(collect_inventory, 'BASE', tmp_path)
    local = tmp_path / '.local'
    def source_text(path, *args, **kwargs):
        assert CURRENT.get() is not None and len(pending(gate)) == 1
        return ''
    monkeypatch.setattr(Path, 'read_text', source_text)
    def run(command, **options):
        assert len(pending(gate)) == 1 and options['timeout'] == 45
        return completed(command, json.dumps(dict(source='gateway-ru', scope='production')).encode())
    monkeypatch.setattr(collect_inventory.subprocess, 'run', run)
    args = SimpleNamespace(source='gateway-ru', known_hosts=None)
    collect_inventory.collect(args, argparse.ArgumentParser())
    assert not pending(gate) and len(list(local.glob('*.json'))) == 1
    original = os.open
    def fail(path, flags, *args, **kwargs):
        if str(path).endswith('.json'):
            raise OSError('synthetic write failure')
        return original(path, flags, *args, **kwargs)
    monkeypatch.setattr(os, 'open', fail)
    with pytest.raises(OSError, match='synthetic write failure'):
        collect_inventory.collect(args, argparse.ArgumentParser())
    assert len(pending(gate)) == 1 and 'synthetic write failure' not in capsys.readouterr().out


@pytest.mark.parametrize('failure', ['cleanup', 'receipt'])
def test_monitor_local_completion_failure_keeps_pending_after_import(gate, tmp_path, monkeypatch, failure):
    monkeypatch.setattr(monitor_inventory, 'SOURCES', ('gateway-ru',))
    imports = []
    def run(command, **options):
        if command[0] != 'docker':
            return snapshot(tmp_path, command)
        imports.append(command)
        return completed(command)
    def fail(*args, **kwargs):
        assert len(pending(gate)) == 1
        raise OSError('synthetic local failure')
    monkeypatch.setattr(Path, 'unlink' if failure == 'cleanup' else 'replace', fail)
    with pytest.raises(OSError, match='synthetic local failure'):
        monitor_inventory.cycle(tmp_path, run)
    assert len(imports) == 1 and len(pending(gate)) == 1


@pytest.mark.parametrize('collector', ['monitor', 'probe'])
def test_native_collector_death_retains_committed_write_and_refuses_capture(gate, tmp_path, collector):
    process = subprocess.Popen([sys.executable, '-B', str(ROOT / 'tests/fixtures/capture_collectors/native.py'),
                                collector, str(tmp_path)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True, cwd=ROOT)
    try:
        assert line(process) == 'committed\n'
        assert len(pending(gate)) == 1
        with pytest.raises(Busy, match='DRAIN_TIMEOUT'):
            with gate.drain(.02):
                pytest.fail('active cycle drained')
        process.kill()
        process.wait(timeout=5)
        with sqlite3.connect(tmp_path / 'synthetic.db') as database:
            assert database.execute('SELECT value FROM sample').fetchall() == [('retained',)]
        with pytest.raises(GateError, match='UNSETTLED_OPERATION'):
            with gate.drain(.1):
                pytest.fail('lost killed collector')
    finally:
        if process.poll() is None:
            process.kill()
        process.communicate(timeout=5)


def test_probe_timeout_is_not_native_child_cancellation(gate, tmp_path, monkeypatch):
    monkeypatch.setattr(probe_network, 'ENDPOINTS', ('gateway-ru',))
    process = subprocess.Popen([sys.executable, '-u', '-c',
        'import sqlite3,sys;print("ready",flush=True);sys.stdin.readline();'
        'db=sqlite3.connect(sys.argv[1]);db.execute("CREATE TABLE sample(value)");'
        'db.execute("INSERT INTO sample VALUES (42)");db.commit();db.close()',
        str(tmp_path / 'late.db')], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        assert line(process) == 'ready\n'
        def timeout(command, **options):
            assert CURRENT.get() is not None
            raise subprocess.TimeoutExpired(command, options['timeout'], stderr=b'private details')
        receipt = probe_network.cycle(tmp_path, probe, timeout)
        assert receipt['sources'][0]['status'] == 'IMPORT_FAILED' and len(pending(gate)) == 1
        process.communicate('finish\n', timeout=5)
        assert process.returncode == 0
        with sqlite3.connect(tmp_path / 'late.db') as database:
            assert database.execute('SELECT value FROM sample').fetchall() == [(42,)]
        old = pending(gate)
        probe_network.cycle(tmp_path, probe, lambda *args, **kwargs: completed(args[0]))
        assert pending(gate) == old
        with pytest.raises(GateError, match='UNSETTLED_OPERATION'):
            with gate.drain(.1):
                pytest.fail('late external commit accepted')
    finally:
        if process.poll() is None:
            process.kill()
        process.communicate(timeout=5)


def test_cli_does_not_swallow_unrelated_failure():
    def fail():
        raise RuntimeError('unrelated')
    with pytest.raises(RuntimeError, match='unrelated'):
        run_cli(fail)
