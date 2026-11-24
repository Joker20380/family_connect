import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from control.capture_gate import Busy, GateError
from control.capture_renewal import RenewalState, validate
from control import capture_group as group, capture_launch as launch
from test_capture_launch import inputs, save


@pytest.fixture
def settlement(tmp_path):
    state = tmp_path / 'renewal'
    state.mkdir(mode=0o700)
    (state / 'operation.lock').touch(mode=0o600)
    config = tmp_path / 'node.json'
    raw = json.dumps(dict(schema=1, role='NL', state=str(state))).encode()
    config.write_bytes(raw)
    config.chmod(0o600)
    return dict(config=str(config), config_sha256=hashlib.sha256(raw).hexdigest(), state=str(state),
                pins={name: [info.st_dev, info.st_ino] for name in ('.', 'operation.lock')
                      for info in [(state / name).stat()]})


def native_lock(binding):
    return subprocess.run([sys.executable, '-I', '-B', '-c',
        'import fcntl,sys\nwith open(sys.argv[1],"rb") as source:\n'
        ' try: fcntl.flock(source,fcntl.LOCK_EX|fcntl.LOCK_NB)\n'
        ' except BlockingIOError: sys.exit(75)\n',
        str(Path(binding['state']) / 'operation.lock')], capture_output=True, timeout=3)


def test_guard_is_read_only_and_holds_native_lock(settlement):
    state = Path(settlement['state'])
    before = {item.name: item.read_bytes() for item in state.iterdir()}
    guard = RenewalState(settlement)
    with guard.hold():
        assert native_lock(settlement).returncode == 75
        guard.verify()
    assert native_lock(settlement).returncode == 0
    assert {item.name: item.read_bytes() for item in state.iterdir()} == before
    with pytest.raises(GateError, match='NOT_HELD'):
        guard.verify()


@pytest.mark.parametrize('name', ['owner.json', 'directory.pending', 'start-intent-0.json', '.pending-crash', 'unknown'])
def test_successful_rpc_or_resumed_state_does_not_settle_transaction(settlement, name):
    target = Path(settlement['state']) / name
    target.write_bytes(b'{"state":"RESUMED","result":"PASS"}')
    target.chmod(0o600)
    with pytest.raises(GateError, match='TRANSACTION_UNSETTLED'), RenewalState(settlement).hold():
        pytest.fail('unfinished transaction accepted')
    assert native_lock(settlement).returncode == 0
    assert target.exists()


def test_running_native_operation_refuses_without_wait(settlement):
    with open(Path(settlement['state']) / 'operation.lock', 'rb') as locked:
        fcntl.flock(locked, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(Busy, match='OPERATION_RUNNING'), RenewalState(settlement).hold():
            pytest.fail('native operation ignored')


@pytest.mark.parametrize('fault', ['owner', 'lock', 'directory', 'config', 'ledger'])
def test_final_check_refuses_changes_and_releases_lock(settlement, fault):
    state = Path(settlement['state'])
    with pytest.raises((GateError, FileNotFoundError)), RenewalState(settlement).hold():
        if fault == 'owner':
            (state / 'owner.json').touch(mode=0o600)
        elif fault == 'lock':
            (state / 'operation.lock').rename(state / 'old')
            (state / 'operation.lock').touch(mode=0o600)
        elif fault == 'directory':
            state.rename(state.with_name('old'))
            state.mkdir(mode=0o700)
            (state / 'operation.lock').touch(mode=0o600)
        elif fault == 'config':
            Path(settlement['config']).write_bytes(b'{}')
        else:
            (state / 'completed.json').write_bytes(b'{}')
    assert native_lock(settlement).returncode == 0


@pytest.mark.parametrize('fault', ['missing-lock', 'lock-mode', 'directory-mode', 'hardlink', 'symlink',
    'config-mode', 'config-digest', 'config-state', 'duplicate-json', 'ledger-symlink', 'archive-file'])
def test_unsafe_state_is_not_repaired_or_created(settlement, tmp_path, fault):
    state = Path(settlement['state'])
    lock = state / 'operation.lock'
    config = Path(settlement['config'])
    if fault == 'missing-lock':
        lock.unlink()
    elif fault == 'lock-mode':
        lock.chmod(0o640)
    elif fault == 'directory-mode':
        state.chmod(0o750)
    elif fault == 'hardlink':
        os.link(lock, tmp_path / 'linked')
    elif fault == 'symlink':
        lock.rename(tmp_path / 'original')
        lock.symlink_to(tmp_path / 'original')
    elif fault == 'config-mode':
        config.chmod(0o644)
    elif fault == 'config-digest':
        settlement['config_sha256'] = '0' * 64
    elif fault in ('config-state', 'duplicate-json'):
        raw = b'{"schema":1,"role":"NL","state":"/elsewhere"}' if fault == 'config-state' else b'{"schema":1,"schema":1}'
        config.write_bytes(raw)
        settlement['config_sha256'] = hashlib.sha256(raw).hexdigest()
    elif fault == 'ledger-symlink':
        (state / 'completed.json').symlink_to(config)
    else:
        (state / 'archive').touch(mode=0o700)
    before = sorted(item.name for item in state.iterdir())
    with pytest.raises((OSError, ValueError)), RenewalState(settlement).hold():
        pytest.fail('unsafe state accepted')
    assert sorted(item.name for item in state.iterdir()) == before


def test_historical_archive_is_preserved_not_treated_as_open_transaction(settlement):
    state = Path(settlement['state'])
    (state / 'archive').mkdir(mode=0o700)
    (state / 'completed.json').write_bytes(b'{}')
    (state / 'completed.json').chmod(0o600)
    with RenewalState(settlement).hold():
        pass
    assert (state / 'completed.json').read_bytes() == b'{}'


def test_guard_uses_immutable_binding_copy(settlement):
    guard = RenewalState(settlement)
    settlement['state'] = '/invalid'
    settlement['pins']['.'][1] = 0
    with guard.hold():
        guard.verify()


def test_native_fixture_refuses_host_before_inventory():
    fixture = Path(__file__).parent / 'fixtures/capture_launch/renewal.py'
    result = subprocess.run([sys.executable, '-I', '-B', str(fixture)], input=b'not an inventory',
                            env={}, capture_output=True, timeout=3)
    assert result.returncode != 0 and not result.stdout and b'NATIVE_SETTLEMENT_REFUSED' in result.stderr


@pytest.mark.parametrize('change', [lambda value: value.update(extra=True),
    lambda value: value.update(state='/tmp/../state'), lambda value: value.update(config='relative'),
    lambda value: value.update(config_sha256='A' * 64),
    lambda value: value['pins'].update(extra=[1, 2]),
    lambda value: value['pins'].update({'.': [True, 2]}),
    lambda value: value['pins'].update({'operation.lock': value['pins']['.']})])
def test_binding_is_closed(settlement, change):
    change(settlement)
    with pytest.raises(GateError):
        validate(settlement)


def enable(inputs, settlement):
    inputs[2]['schema'] = 2
    for item in inputs[2]['guardians']:
        item['renewal'] = None
    inputs[2]['guardians'][0]['renewal'] = settlement


def test_pinned_guardians_hold_renewal_through_joint_interval(inputs, settlement):
    enable(inputs, settlement)
    with launch.launch(*save(inputs)) as participants:
        with group.joint(participants) as window:
            assert native_lock(settlement).returncode == 75
        assert window.receipt['status'] == 'LOCAL_INTERVAL_CONFIRMED'
        assert not window.receipt['capture_permitted']
    assert native_lock(settlement).returncode == 0


def test_pinned_guardians_refuse_successful_but_open_rpc(inputs, settlement):
    enable(inputs, settlement)
    (Path(settlement['state']) / 'owner.json').write_bytes(b'{"state":"ACQUIRED"}')
    with launch.launch(*save(inputs)) as participants:
        with pytest.raises(OSError), group.joint(participants):
            pytest.fail('joint capture entered an open transaction')


def test_final_joint_ack_refuses_manual_state_change(inputs, settlement):
    enable(inputs, settlement)
    with launch.launch(*save(inputs)) as participants:
        with pytest.raises(OSError), group.joint(participants) as window:
            (Path(settlement['state']) / 'owner.json').touch(mode=0o600)
        assert window.receipt is None


@pytest.mark.parametrize('fault', ['missing', 'alias', 'unknown-schema'])
def test_launch_refuses_bad_settlement_before_spawning(inputs, settlement, monkeypatch, fault):
    enable(inputs, settlement)
    if fault == 'missing':
        del inputs[2]['guardians'][1]['renewal']
    elif fault == 'alias':
        inputs[2]['guardians'][1]['renewal'] = settlement
    else:
        inputs[2]['schema'] = 3
    monkeypatch.setattr(subprocess, 'Popen', lambda *args, **kwargs: pytest.fail('spawned'))
    with pytest.raises(GateError), launch.launch(*save(inputs)):
        pytest.fail('invalid settlement accepted')


@pytest.mark.parametrize('fault', ['coordinator', 'groups', 'no-settlement', 'partial-root'])
def test_root_guardian_requires_explicit_root_settlement_binding(inputs, settlement, fault):
    enable(inputs, settlement)
    item = inputs[2]['guardians'][0]
    inputs[2]['coordinator'] = [0, 0]
    item.update(uid=0, gid=0, groups=[])
    if fault == 'coordinator':
        inputs[2]['coordinator'] = [1000, 1000]
    elif fault == 'groups':
        item['groups'] = [1000]
    elif fault == 'no-settlement':
        item['renewal'] = None
    else:
        item['gid'] = 1000
    with pytest.raises(GateError):
        launch.validate(inputs[2])
