import base64
from copy import deepcopy
from dataclasses import replace
import secrets
import shutil

import pytest

from scripts.control_ha_import import ImportRejected, digest, encoded, import_snapshot
from scripts.control_ha_import_fixture import CHECKPOINT
from scripts.control_ha_online_capsule import MAPPING, binding_for, inspect_online_inputs, preflight_online
from scripts.control_ha_online_fixture import online_fixture
from scripts.control_ha_recovery_bundle import parse
from scripts.control_ha_renewal_history import inspect_history
from scripts.control_ha_renewal_v1 import evidence_digest, inspect_renewal
from scripts.referral_postgres_rehearsal import NOW
from test_control_ha_online_capsule import Source, capture, repository
from test_control_ha_renewal_v1 import OPERATION, change_document, change_file, remove_file
from test_multi_gateway_renewal import make_fleet
from test_online_renewal import Crash, enable
from credential_renewal import Rejected, atomic

FIRST = 'ha-online-history-0001'
SECOND = 'ha-online-history-0002'


@pytest.fixture(scope='module')
def history_original(tmp_path_factory):
    fixture, artifacts, bounded = online_fixture(tmp_path_factory.mktemp('renewal-history'), history=True)
    return Source(fixture, artifacts, bounded['pending'], secrets.token_bytes(32))


@pytest.fixture
def history_source(history_original):
    return Source(replace(history_original.fixture, stores=dict(history_original.fixture.stores)),
                  deepcopy(history_original.artifacts), deepcopy(history_original.pending), secrets.token_bytes(32))


def renewal(source):
    return {name: source.artifacts['maintenance_state'][path] for name, path in MAPPING.items()}


def check(source, parts=None):
    parts = renewal(source) if parts is None else parts
    return inspect_history(parts, evidence_digest(parts), source.fixture.service.anchor, NOW)


def recover(source):
    raw, checkpoint = capture(source)
    return preflight_online(raw, source.key, checkpoint, source.fixture.service.anchor, now=NOW, history=True)


def test_three_real_operations_restore_exact_history(history_source):
    evidence, current, count = check(history_source)
    assert count == 3 and evidence.operation == OPERATION and evidence.state == 'COMMITTED'
    assert inspect_renewal(current, evidence_digest(current), history_source.fixture.service.anchor, NOW).committed
    recovered = recover(history_source)
    assert recovered.artifacts == history_source.artifacts
    assert recovered.summary()['history'] == 'RETAINED_COMPLETED_ONLINE_CHAIN'
    assert inspect_online_inputs(recovered, CHECKPOINT, history_source.fixture.service.anchor,
                                 now=NOW, history=True)['operations'] == 3


def test_history_survives_removal_of_real_original_sources(tmp_path):
    root = tmp_path / 'originals'
    root.mkdir(mode=0o700)
    fixture, artifacts, bounded = online_fixture(root, history=True)
    source = Source(fixture, artifacts, bounded['pending'], secrets.token_bytes(32))
    raw, checkpoint = capture(source)
    anchor, expected = fixture.service.anchor, deepcopy(artifacts)
    source.fixture.service = source.fixture.access = None
    source.artifacts = source.fixture.stores = {}
    shutil.rmtree(root)
    restored = preflight_online(raw, source.key, checkpoint, anchor, now=NOW, history=True)
    assert restored.artifacts == expected and not root.exists()


def test_history_gate_is_read_only(history_source, monkeypatch):
    raw, checkpoint = capture(history_source)
    monkeypatch.setattr('subprocess.run', lambda *args, **kwargs: pytest.fail('No host commands'))
    monkeypatch.setattr('control.friends.enrollment_postgres.PostgresEnrollment.connect',
                        lambda *args, **kwargs: pytest.fail('No PG writes'))
    assert preflight_online(raw, history_source.key, checkpoint, history_source.fixture.service.anchor,
                            now=NOW, history=True).summary()['activation'] == 'FORBIDDEN'


def test_single_operation_gate_refuses_history(history_source):
    parts = renewal(history_source)
    with pytest.raises(ImportRejected):
        inspect_renewal(parts, evidence_digest(parts), history_source.fixture.service.anchor, NOW)
    raw, checkpoint = capture(history_source)
    with pytest.raises(ImportRejected, match='ONLINE_CAPSULE_BINDING'):
        preflight_online(raw, history_source.key, checkpoint, history_source.fixture.service.anchor, now=NOW)


@pytest.mark.parametrize('slot', ['RU', 'NL', 'NL2'])
@pytest.mark.parametrize('operation', [FIRST, SECOND, OPERATION])
def test_no_completed_ledger_entry_can_be_dropped(history_source, slot, operation):
    parts = renewal(history_source)
    change_file(parts, slot, 'completed.json', lambda value: value.pop(operation))
    with pytest.raises(ImportRejected, match='RENEWAL_HISTORY_COHORT'):
        check(history_source, parts)


@pytest.mark.parametrize('slot', ['RU', 'NL', 'NL2'])
@pytest.mark.parametrize('operation', [FIRST, SECOND, OPERATION])
def test_no_archive_can_be_dropped(history_source, slot, operation):
    parts = renewal(history_source)
    remove_file(parts, slot, 'archive/' + operation + '/plan.json')
    with pytest.raises(ImportRejected):
        check(history_source, parts)


@pytest.mark.parametrize('operation', [FIRST, SECOND])
def test_missing_coordinator_history_is_not_empty_history(history_source, operation):
    parts = renewal(history_source)
    remove_file(parts, 'coordinator', 'history/' + operation + '.json')
    with pytest.raises(ImportRejected):
        check(history_source, parts)


def test_removing_middle_operation_from_all_sources_breaks_chain(history_source):
    parts = renewal(history_source)
    remove_file(parts, 'coordinator', 'history/' + SECOND + '.json')
    for slot in ('RU', 'NL', 'NL2'):
        change_file(parts, slot, 'completed.json', lambda value: value.pop(SECOND))
        names = list(parse(parts[slot + '.json'])['files'])
        for name in names:
            if name.startswith('archive/' + SECOND + '/'):
                remove_file(parts, slot, name)
    with pytest.raises(ImportRejected, match='RENEWAL_HISTORY_PREDECESSOR'):
        check(history_source, parts)


@pytest.mark.parametrize('mutation', ['hash', 'schema', 'operation', 'extra', 'time', 'mode'])
def test_corrupt_resealed_history_is_refused(history_source, mutation):
    parts = renewal(history_source)
    def mutate(item):
        if mutation == 'hash':
            item['sha256']['plan.json'] = '0' * 64
        elif mutation == 'schema':
            item['schema'] = True
        elif mutation == 'operation':
            item['operation_id'] = OPERATION
        elif mutation == 'extra':
            item['unknown'] = True
        else:
            name = 'last-receipt.json' if mutation == 'time' else 'transaction.json'
            value = parse(base64.b64decode(item['files'][name]))
            value['timestamp' if mutation == 'time' else 'mode'] = NOW + 1 if mutation == 'time' else 'offline'
            item['files'][name] = base64.b64encode(encoded(value)).decode()
            item['sha256'][name] = digest(encoded(value))
    change_file(parts, 'coordinator', 'history/' + FIRST + '.json', mutate)
    for name, raw in parts.items():
        history_source.artifacts['maintenance_state'][MAPPING[name]] = raw
    binding = binding_for(history_source.fixture.stores, history_source.artifacts['issuer_material'],
                          CHECKPOINT, parts, history=True)
    history_source.artifacts['maintenance_state']['binding.json'] = encoded(binding)
    with pytest.raises(ImportRejected):
        recover(history_source)


@pytest.mark.parametrize('name', ['history/../escape.json', 'history/unknown.json', 'owner.json'])
def test_unknown_or_pending_files_refuse(history_source, name):
    parts = renewal(history_source)
    change_document(parts, 'coordinator', lambda value: value['files'].update({name: 'e30='}))
    with pytest.raises(ImportRejected):
        check(history_source, parts)


def test_historical_expiry_is_not_current_authority(history_source):
    parts = renewal(history_source)
    evidence, current, _ = check(history_source, parts)
    assert evidence.state == 'COMMITTED'
    with pytest.raises(ImportRejected):
        inspect_history(parts, evidence_digest(parts), history_source.fixture.service.anchor, NOW - 1)
    current_capture = parse(current['capture.json'])
    assert current_capture['captured_at'] == NOW


@pytest.mark.parametrize('boundary', ['schema', 'restricted_certificates', 'before_commit', 'after_commit'])
def test_history_import_crash_and_retry(history_source, repository, boundary):
    recovered = recover(history_source)
    def crash(phase):
        if phase == boundary:
            raise RuntimeError('synthetic-interruption')
    with pytest.raises(ImportRejected, match='IMPORT_OUTCOME_REQUIRES_READBACK'):
        import_snapshot(repository, recovered.snapshot, fault=crash)
    assert import_snapshot(repository, recovered.snapshot)['result'] == (
        'EXACT_RETRY' if boundary == 'after_commit' else 'IMPORTED')


def test_weaker_import_receipt_cannot_impersonate_history_gate(history_source, repository):
    from scripts.control_ha_receiver_v1 import preflight_receivers
    raw, checkpoint = capture(history_source)
    weaker = preflight_receivers(raw, history_source.key, checkpoint, history_source.fixture.service.anchor, now=NOW)
    assert import_snapshot(repository, weaker.snapshot)['result'] == 'IMPORTED'
    with pytest.raises(ImportRejected):
        import_snapshot(repository, recover(history_source).snapshot)


def test_native_predecessor_retention_survives_crash_before_new_transaction(tmp_path):
    fleet = make_fleet(tmp_path)
    enable(fleet)
    assert fleet.controller.run_online(FIRST, schedule_seconds=0)['result'] == 'COMMITTED'
    before = {name: (fleet.controller.root / name).read_bytes()
              for name in ('transaction.json', 'plan.json', 'last-receipt.json')}
    enable(fleet)
    def crash(phase):
        if phase == 'ONLINE_PREDECESSOR_RETAINED':
            raise Crash()
    fleet.controller.fault = crash
    with pytest.raises(Crash):
        fleet.controller.run_online(SECOND, schedule_seconds=0)
    assert all((fleet.controller.root / name).read_bytes() == raw for name, raw in before.items())
    retained = (fleet.controller.root / 'history' / (FIRST + '.json')).read_bytes()
    assert {name: base64.b64decode(raw) for name, raw in parse(retained)['files'].items()} == before
    fleet.controller.fault = lambda phase: None
    assert fleet.controller.run_online(SECOND, schedule_seconds=0)['result'] == 'COMMITTED'
    assert (fleet.controller.root / 'history' / (FIRST + '.json')).read_bytes() == retained
    with pytest.raises(Rejected, match='ONLINE_HISTORY_OPERATION_REUSED'):
        fleet.controller.run_online(FIRST, schedule_seconds=0)


def test_not_due_attempt_creates_no_false_predecessor(tmp_path):
    fleet = make_fleet(tmp_path)
    enable(fleet)
    assert fleet.controller.run_online(FIRST, schedule_seconds=0)['result'] == 'COMMITTED'
    with pytest.raises(Rejected, match='ONLINE_REFRESH_NOT_DUE'):
        fleet.controller.run_online(SECOND, schedule_seconds=0)
    assert not (fleet.controller.root / 'history').exists()


@pytest.mark.parametrize('bad', ['conflict', 'symlink', 'permissions'])
def test_native_history_failure_leaves_current_operation_intact(tmp_path, bad):
    fleet = make_fleet(tmp_path)
    enable(fleet)
    assert fleet.controller.run_online(FIRST, schedule_seconds=0)['result'] == 'COMMITTED'
    marker = fleet.controller.root / 'transaction.json'
    before = marker.read_bytes()
    history = fleet.controller.root / 'history'
    history.mkdir(mode=0o700)
    destination = history / (FIRST + '.json')
    if bad == 'symlink':
        destination.symlink_to(marker)
    else:
        atomic(destination, b'{}')
        if bad == 'permissions':
            destination.chmod(0o644)
    enable(fleet)
    with pytest.raises((Rejected, OSError)):
        fleet.controller.run_online(SECOND, schedule_seconds=0)
    assert marker.read_bytes() == before
