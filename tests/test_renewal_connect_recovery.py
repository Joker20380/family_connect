from types import SimpleNamespace
import sys

import pytest

from scripts.renewal_connect_recovery import bounded_connections
from scripts import renewal_connect_recovery as recovery


def test_connect_attempts_do_not_repeat_dispatch_or_swallow_first_failure():
    calls = []

    def original(route, *, executable):
        calls.append(route)
        return [executable, '-F', '/dev/null', '-o', 'ConnectTimeout=8',
                '-o', 'StrictHostKeyChecking=yes', route, 'restricted-sync']

    transport = SimpleNamespace(snapshot_command=original)
    failure = ValueError('REMOTE_OUTCOME_UNKNOWN_READBACK_REQUIRED')
    with pytest.raises(ValueError) as result:
        with bounded_connections(transport):
            command = transport.snapshot_command('root@192.0.2.1')
            assert command == ['/usr/bin/ssh', '-o', 'ConnectionAttempts=3', '-F',
                '/dev/null', '-o', 'ConnectTimeout=8', '-o', 'StrictHostKeyChecking=yes',
                'root@192.0.2.1', 'restricted-sync']
            raise failure
    assert result.value is failure
    assert calls == ['root@192.0.2.1']
    assert transport.snapshot_command is original


@pytest.mark.parametrize('option', ['ConnectionAttempts=2', 'ProxyCommand=ssh',
                                  'ProxyJump=example', 'ControlMaster=auto'])
def test_unknown_transport_shape_refuses_before_dispatch(option):
    def original(route, *, executable):
        return [executable, '-F', '/dev/null', '-o', 'ConnectTimeout=8', '-o', option]

    transport = SimpleNamespace(snapshot_command=original)
    with bounded_connections(transport):
        with pytest.raises(ValueError, match='RECOVERY_SSH_COMMAND'):
            transport.snapshot_command('root@192.0.2.1')
    assert transport.snapshot_command is original


def test_nonstandard_executable_refuses_before_builder():
    def original(*args, **kwargs):
        pytest.fail('builder called')

    transport = SimpleNamespace(snapshot_command=original)
    with bounded_connections(transport):
        with pytest.raises(ValueError, match='RECOVERY_SSH_EXECUTABLE'):
            transport.snapshot_command('root@192.0.2.1', executable='/tmp/ssh')


@pytest.fixture
def invocation(tmp_path, monkeypatch):
    sources = {'runtime_controller.py': b'controller', 'production_transport.py': b'transport'}
    hashes = {name: recovery.digest(raw) for name, raw in sources.items()}
    source_sha = recovery.digest(recovery.canonical(hashes))
    values = {tmp_path / name: raw for name, raw in sources.items()}
    config = dict(approved_leaf_crl_schedule=True, node_config=str(tmp_path / 'node.json'),
                  coordinator_state=str(tmp_path))
    transaction = dict(state='COMMITTED', commit_decided=True, operation_id='previous-operation-0001')
    values[tmp_path / 'config.json'] = recovery.canonical(config)
    values[tmp_path / 'node.json'] = recovery.canonical(dict(source_files=hashes, source_sha256=source_sha))
    values[tmp_path / 'transaction.json'] = recovery.canonical(transaction)
    arguments = ['recovery', '--runtime', str(tmp_path), '--config', str(tmp_path / 'config.json'),
        '--config-sha256', recovery.digest(values[tmp_path / 'config.json']), '--source-sha256', source_sha,
        '--transaction-sha256', recovery.digest(values[tmp_path / 'transaction.json']),
        '--operation', 'fresh-operation-0002', '--journal', str(tmp_path / 'journal')]
    calls = []
    transport = SimpleNamespace(snapshot_command=lambda *args, **kwargs: None)
    controller = SimpleNamespace(main=lambda: calls.append(list(sys.argv)))
    monkeypatch.setitem(sys.modules, 'production_transport', transport)
    monkeypatch.setitem(sys.modules, 'runtime_controller', controller)
    monkeypatch.setattr(sys, 'path', list(sys.path))
    monkeypatch.setattr(recovery.os, 'geteuid', lambda: 0)
    monkeypatch.setattr(recovery.resource, 'setrlimit', lambda *args: None)
    monkeypatch.setattr(recovery, 'pinned', lambda path: values[path])
    monkeypatch.setattr(recovery, 'quiescent_units', lambda: None)

    def run():
        monkeypatch.setattr(sys, 'argv', list(arguments))
        recovery.main()

    return tmp_path, values, arguments, calls, run


def test_fresh_launcher_once_and_existing_journal_refusal(invocation):
    root, values, arguments, calls, run = invocation
    run()
    assert calls == [['runtime_controller.py', '--config', str(root / 'config.json'),
                      '--mode', 'scheduled', '--operation', 'fresh-operation-0002']]
    with pytest.raises(FileExistsError):
        run()
    assert len(calls) == 1


@pytest.mark.parametrize('name,reason', [('config.json', 'CONFIG_CHANGED'),
    ('runtime_controller.py', 'SOURCE_CHANGED'), ('transaction.json', 'FRESH_STATE_REQUIRED')])
def test_changed_pins_refuse_before_import_or_dispatch(invocation, name, reason):
    root, values, arguments, calls, run = invocation
    values[root / name] += b'\n'
    with pytest.raises(ValueError, match=reason):
        run()
    assert not calls and not (root / 'journal').exists()


@pytest.mark.parametrize('phase', ['ACQUIRING', 'FAILED', 'COMMIT_DECIDED'])
def test_nonterminal_predecessor_cannot_be_retried(invocation, phase):
    root, values, arguments, calls, run = invocation
    values[root / 'transaction.json'] = recovery.canonical(dict(state=phase, commit_decided=True,
                                                              operation_id='old-operation-001'))
    arguments[arguments.index('--transaction-sha256') + 1] = recovery.digest(values[root / 'transaction.json'])
    with pytest.raises(ValueError, match='FRESH_STATE_REQUIRED'):
        run()
    assert not calls and not (root / 'journal').exists()
