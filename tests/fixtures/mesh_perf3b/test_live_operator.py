import importlib.util
import json
from pathlib import Path
import sqlite3
import sys
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'state-client-build/mesh-perf-3b/api'))
from control.friends.access import Access
from control.friends import owner_handoff

spec = importlib.util.spec_from_file_location('live_operator', Path(__file__).with_name('live_operator.py'))
operator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(operator)


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    stage = tmp_path / 'stage'
    material = tmp_path / 'material'
    coordinator = tmp_path / 'coordinator'
    for directory in (stage, material, material / 'renewal', coordinator):
        directory.mkdir(mode=0o700)
    original = tmp_path / 'original.pyz'
    original.write_bytes(b'baseline')
    candidate = stage / 'friends-http-owner-candidate.pyz'
    candidate.write_bytes(b'candidate')
    monkeypatch.setattr(operator, 'BASE_API', operator.sha(original))
    monkeypatch.setattr(operator, 'CANDIDATE_API', operator.sha(candidate))
    operator.exclusive(material / 'renewal/controller.json', operator.encode(dict(coordinator_state=str(coordinator))))
    operator.exclusive(material / 'directory.json', b'{}')
    database = tmp_path / 'access.db'
    sqlite3.connect(database).close()
    service = SimpleNamespace(access=Access(database))
    monkeypatch.setattr(operator, 'require_root', lambda: None)
    monkeypatch.setattr(operator, 'load_service', lambda *_: (service, owner_handoff, dict(family='a'*32, gateway='b'*32)))
    dropin = tmp_path / 'api.d' / '97-mesh-perf-3b.conf'
    dropin.parent.mkdir()
    monkeypatch.setattr(operator, 'dropin_path', lambda: dropin)
    before = dict(MainPID='1', InvocationID='c'*32, ActiveState='active', SubState='running', NRestarts='0')
    process = dict(state=before.copy(), current=str(original))
    arguments = ['/python', '-B', str(original)]
    environment = dict(FC_FRIENDS_RESTRICTED_DIR=str(material), FC_FRIENDS_RESTRICTED_DELIVERY_LIFETIME='14400')
    monkeypatch.setattr(operator, 'process_inputs', lambda _: (['/python', '-B', process['current']], environment))
    monkeypatch.setattr(operator, 'state', lambda unit: process['state'].copy() if unit == operator.API_UNIT else before.copy())
    calls = []

    def run(arguments, timeout=15):
        calls.append(arguments)
        if arguments[:2] == ['systemctl', 'restart']:
            assert arguments[2] == operator.API_UNIT
            process['current'] = str(candidate if dropin.exists() else original)
            process['state']['MainPID'] = str(int(process['state']['MainPID'])+1)
            process['state']['InvocationID'] = 'd'*32
        return 'original-unit' if arguments[:2] == ['systemctl', 'cat'] else ''

    monkeypatch.setattr(operator, 'run', run)
    config = dict(operation=operator.OPERATION, archive=str(original), material=str(material), database=str(database),
                  state=before, args=arguments, directory_sha256=operator.sha(material/'directory.json'),
                  owner_guard_identity=dict(device='e'*32), deadline=int(operator.time.time())+7200)
    return stage, config, calls, dropin, service, process


def test_prepare_inspect_and_unarmed_abort(prepared):
    stage, config, calls, dropin, _, _ = prepared
    assert operator.prepare_api(stage, config)['result'] == 'PREPARED_NOT_ARMED'
    assert dropin.exists()
    status = operator.inspect(stage, config)
    assert status['phase'] == 'PREPARED' and not status['floor_captured']
    assert operator.abort_unarmed(stage, config)['result'] == 'UNARMED_ABORTED'
    assert not dropin.exists()
    assert operator.inspect(stage, config)['phase'] == 'CLEANED'
    assert [call for call in calls if call[:2] == ['systemctl','restart']] == [['systemctl','restart',operator.API_UNIT]]*2


def test_prepare_receipt_prevents_blind_retry(prepared):
    stage, config, calls, *_ = prepared
    operator.prepare_api(stage, config)
    before = list(calls)
    with pytest.raises(RuntimeError, match='READBACK_REQUIRED'):
        operator.prepare_api(stage, config)
    assert calls == before


def test_candidate_hash_mismatch_makes_no_changes(prepared):
    stage, config, calls, dropin, *_ = prepared
    (stage / 'friends-http-owner-candidate.pyz').write_bytes(b'changed')
    with pytest.raises(RuntimeError, match='HASH_MISMATCH'):
        operator.prepare_api(stage, config)
    assert not calls and not dropin.exists() and not (stage/'prepare-intent.json').exists()


def test_changed_directory_stops_before_intent(prepared):
    stage, config, _, dropin, *_ = prepared
    (Path(config['material'])/'directory.json').write_bytes(b'new-directory')
    with pytest.raises(RuntimeError, match='DIRECTORY_CHANGED'):
        operator.prepare_api(stage, config)
    assert not dropin.exists() and not (stage/'prepare-intent.json').exists()


def test_conflicting_dropin_is_preserved(prepared):
    stage, config, _, dropin, *_ = prepared
    dropin.write_bytes(b'other')
    with pytest.raises(RuntimeError, match='DROPIN_CONFLICT'):
        operator.prepare_api(stage, config)
    assert dropin.read_bytes() == b'other'


def test_active_or_returning_canary_cannot_code_rollback(prepared):
    stage, config, calls, dropin, service, _ = prepared
    operator.prepare_api(stage, config)
    with service.access.db() as database:
        database.execute("UPDATE restricted_owner_handoff SET phase='RETURN',canary='{}'")
    before = list(calls)
    with pytest.raises(RuntimeError, match='FORWARD_RETURN_REQUIRED'):
        operator.abort_unarmed(stage, config)
    assert dropin.exists() and calls == before and not (stage/'abort-intent.json').exists()


def test_interrupted_restart_has_reconcilable_unarmed_state(prepared, monkeypatch):
    stage, config, _, dropin, _, _ = prepared
    original_run = operator.run

    def failed(arguments, timeout=15):
        if arguments[:2] == ['systemctl','restart']:
            raise RuntimeError('COMMAND_FAILED_systemctl')
        return original_run(arguments, timeout)

    monkeypatch.setattr(operator, 'run', failed)
    with pytest.raises(RuntimeError, match='COMMAND_FAILED'):
        operator.prepare_api(stage, config)
    assert dropin.exists() and operator.inspect(stage, config)['phase'] == 'PREPARED'
    assert (stage/'prepare-intent.json').exists() and not (stage/'prepare-receipt.json').exists()
    monkeypatch.setattr(operator, 'run', original_run)
    assert operator.abort_unarmed(stage, config)['result'] == 'UNARMED_ABORTED'


def test_execstart_escaping_rejects_unreviewed_substitution():
    with pytest.raises(RuntimeError, match='UNSUPPORTED_SYSTEMD_ARGUMENT'):
        operator.replacement_unit(['/python','/old','%n'], Path('/old'), Path('/candidate'))


def test_exclusive_receipt_cannot_overwrite(tmp_path):
    path = tmp_path/'receipt'
    operator.exclusive(path, b'first')
    with pytest.raises(FileExistsError):
        operator.exclusive(path, b'second')
    assert operator.private(path) == b'first'


def test_arm_without_actual_material_receipt_is_rejected(prepared):
    stage, config, _, _, _, _ = prepared
    operator.prepare_api(stage, config)
    with pytest.raises(FileNotFoundError):
        operator.transition(stage, config, 'arm')
    assert operator.inspect(stage, config)['phase'] == 'PREPARED'
    assert not (stage/'arm-intent.json').exists()


def test_unarmed_return_does_not_enable_canary(prepared):
    stage, config, _, _, _, _ = prepared
    operator.prepare_api(stage, config)
    result = operator.transition(stage, config, 'return')
    assert result['phase'] == 'RETURN'
    assert not result['floor_captured']
    assert operator.abort_unarmed(stage, config)['result'] == 'UNARMED_ABORTED'


def test_delayed_process_exec_does_not_restart_again(prepared, monkeypatch):
    stage, config, calls, _, _, _ = prepared
    original_inputs = operator.process_inputs
    observations = []

    def inputs(pid):
        if pid == '2' and not observations:
            observations.append(pid)
            return ['/lib/systemd/systemd'], {}
        return original_inputs(pid)

    monkeypatch.setattr(operator, 'process_inputs', inputs)
    assert operator.prepare_api(stage, config)['result'] == 'PREPARED_NOT_ARMED'
    assert observations == ['2']
    assert len([call for call in calls if call[:2] == ['systemctl','restart']]) == 1


def test_lost_prepare_receipt_reconciles_without_mutation(prepared):
    stage, config, calls, _, _, _ = prepared
    operator.prepare_api(stage, config)
    (stage/'prepare-receipt.json').unlink()
    before = list(calls)
    result = operator.reconcile_prepare(stage, config)
    assert result['additional_restarts'] == 0 and result['result'] == 'PREPARED_NOT_ARMED_RECONCILED'
    assert calls == before
