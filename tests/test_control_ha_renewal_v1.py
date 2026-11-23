import base64
from copy import deepcopy
from dataclasses import dataclass
import json
from pathlib import Path
import shutil
import stat

import pytest

from scripts.control_ha_import import ImportRejected, digest, encoded
from scripts.control_ha_renewal_v1 import (PARTS, PURPOSE, SLOTS, compare_same_host, evidence_digest,
                                         inspect_renewal)
from test_multi_gateway_renewal import make_fleet
from test_online_renewal import Crash, enable
from credential_renewal import Rejected

OPERATION = 'ha-online-renewal-fixture'


def capture(fleet, operation=OPERATION, *, purpose=PURPOSE):
    parts = {'capture.json': encoded(dict(schema=1, purpose=purpose, operation_id=operation,
        captured_at=fleet.now, anchor_sha256=digest(fleet.validator.anchor), nodes=sorted(SLOTS)))}
    roots = dict(coordinator=fleet.controller.root, **{slot: node.state for slot, node in fleet.nodes.items()})
    for slot, root in roots.items():
        information = root.lstat()
        metadata, files = {}, {}
        for path in root.rglob('*'):
            assert not path.is_symlink()
            if not path.is_file():
                continue
            item = path.lstat()
            name = str(path.relative_to(root))
            files[name] = base64.b64encode(path.read_bytes()).decode()
            metadata[name] = dict(uid=item.st_uid, gid=item.st_gid, device=item.st_dev, inode=item.st_ino,
                                  mode=stat.S_IMODE(item.st_mode), nlink=item.st_nlink)
        host = dict(path=str(root), device=information.st_dev, inode=information.st_ino, uid=information.st_uid,
                    gid=information.st_gid, mode=stat.S_IMODE(information.st_mode))
        parts[slot + '.json'] = encoded(dict(schema=1, slot=slot, host=host, files=files, metadata=metadata))
    return parts


@dataclass(repr=False)
class Source:
    fleet: object
    parts: dict

    def inspect(self, parts=None):
        chosen = self.parts if parts is None else parts
        return inspect_renewal(chosen, evidence_digest(chosen), self.fleet.validator.anchor, self.fleet.now)


@pytest.fixture(scope='module')
def original(tmp_path_factory):
    fleet = make_fleet(tmp_path_factory.mktemp('online-renewal'))
    enable(fleet)
    assert fleet.controller.run_online(OPERATION, schedule_seconds=0)['result'] == 'COMMITTED'
    return Source(fleet, capture(fleet))


@pytest.fixture
def source(original):
    return Source(original.fleet, deepcopy(original.parts))


@pytest.fixture(scope='module')
def interrupted(tmp_path_factory):
    fleet = make_fleet(tmp_path_factory.mktemp('interrupted-renewal'))
    enable(fleet)
    fail_at(fleet, 'ONLINE_COMMIT_DECIDED')
    return Source(fleet, capture(fleet))


def change_file(parts, slot, name, mutate):
    document = json.loads(parts[slot + '.json'])
    value = json.loads(base64.b64decode(document['files'][name]))
    mutate(value)
    document['files'][name] = base64.b64encode(encoded(value)).decode()
    parts[slot + '.json'] = encoded(document)


def change_document(parts, slot, mutate):
    document = json.loads(parts[slot + '.json'])
    mutate(document)
    parts[slot + '.json'] = encoded(document)


def remove_file(parts, slot, name):
    def mutate(document):
        del document['files'][name]
        del document['metadata'][name]
    change_document(parts, slot, mutate)


def fail_at(fleet, phase):
    def crash(event):
        if event == phase:
            raise Crash()
    fleet.controller.fault = crash
    with pytest.raises(Crash):
        fleet.controller.run_online(OPERATION, schedule_seconds=0)
    fleet.controller.fault = lambda event: None


def test_native_terminal_evidence_is_not_import_or_resume_authority(source, monkeypatch):
    before = deepcopy(source.parts)
    def forbidden(*args, **kwargs):
        raise AssertionError('host access or operation attempted')
    monkeypatch.setattr(Path, 'open', forbidden)
    monkeypatch.setattr(source.fleet.controller, 'run_online', forbidden)
    result = source.inspect()
    assert result.parts == before == source.parts
    assert result.summary()['nodes'] == {slot: 'CLEANED' for slot in SLOTS}
    assert result.summary()['host_resume'] == 'NOT_AUTHORIZED'
    assert result.summary()['import_status'] == 'NOT_INTEGRATED_WITH_CANONICAL_CAPSULE'
    assert 'private_key' not in repr(result) and 'BEGIN' not in repr(result)
    receipt = compare_same_host(before, source.parts, result.checkpoint, source.fleet.validator.anchor, source.fleet.now)
    assert receipt['automatic_retry'] is False
    assert receipt['host_resume'] == 'NOT_AUTHORIZED'


@pytest.mark.parametrize('part', sorted(PARTS))
def test_missing_capture_part_is_not_an_empty_ledger(source, part):
    del source.parts[part]
    with pytest.raises(ImportRejected, match='RENEWAL_PARTS'):
        source.inspect()


@pytest.mark.parametrize('value', [b'{}', b'{"schema":1,"schema":1}', b'{"schema":NaN}', b'[]'])
def test_invalid_capture(source, value):
    source.parts['capture.json'] = value
    with pytest.raises(ImportRejected):
        source.inspect()


@pytest.mark.parametrize('key,value', [('purpose', 'live'), ('schema', True), ('captured_at', True),
    ('captured_at', 2**63), ('nodes', ['NL', 'NL2']), ('operation_id', '../../another-operation'),
    ('anchor_sha256', '0' * 64)])
def test_capture_binding(source, key, value):
    change_document(source.parts, 'capture', lambda data: data.update({key: value}))
    with pytest.raises(ImportRejected):
        source.inspect()


def test_checkpoint_is_independent_of_untrusted_capture(source):
    checkpoint = evidence_digest(source.parts)
    change_file(source.parts, 'coordinator', 'transaction.json', lambda data: data.update(fence=100))
    with pytest.raises(ImportRejected, match='CHECKPOINT_MISMATCH'):
        inspect_renewal(source.parts, checkpoint, source.fleet.validator.anchor, source.fleet.now)


@pytest.mark.parametrize('slot', ['coordinator', 'RU', 'NL', 'NL2'])
@pytest.mark.parametrize('key,value', [('path', '/other-host/state'), ('inode', 42), ('uid', 999), ('mode', 0o777)])
def test_same_host_comparison_rejects_relocation_or_metadata_change(source, slot, key, value):
    previous = deepcopy(source.parts)
    change_document(source.parts, slot, lambda data: data['host'].update({key: value}))
    with pytest.raises(ImportRejected, match='HOST_OR_EVIDENCE_CHANGED'):
        compare_same_host(previous, source.parts, evidence_digest(previous), source.fleet.validator.anchor, source.fleet.now)


@pytest.mark.parametrize('slot', sorted(SLOTS))
@pytest.mark.parametrize('name', ['completed.json', 'archive-manifest.json', 'plan.json', 'online-prepared.json',
                                  'online-published.json', 'reconciliation.json', 'files.json'])
def test_terminal_archive_is_complete_on_every_node(source, slot, name):
    path = name if name == 'completed.json' else 'archive/' + OPERATION + '/' + name
    remove_file(source.parts, slot, path)
    with pytest.raises(ImportRejected):
        source.inspect()


@pytest.mark.parametrize('slot', sorted(SLOTS))
@pytest.mark.parametrize('key,value', [('manifest_sha256', '0' * 64), ('timestamp', True),
                                      ('timestamp', 2**63), ('result', 'CLEANED_FENCED_ROLLBACK')])
def test_terminal_ledger_binding(source, slot, key, value):
    change_file(source.parts, slot, 'completed.json', lambda data: data[OPERATION].update({key: value}))
    with pytest.raises(ImportRejected):
        source.inspect()


@pytest.mark.parametrize('key,value', [('commit_decided', False), ('decision', 'ABORT'), ('fence', True),
    ('cleaned', ['NL', 'NL2']), ('acquired', ['RU', 'NL', 'NL']), ('prepared', {}), ('published', {}),
    ('before_sha256', '0' * 64), ('plan_sha256', '0' * 64), ('mode', 'maintenance'), ('state', 'UNKNOWN')])
def test_coordinator_decision_binding(source, key, value):
    change_file(source.parts, 'coordinator', 'transaction.json', lambda data: data.update({key: value}))
    with pytest.raises(ImportRejected):
        source.inspect()


@pytest.mark.parametrize('slot', sorted(SLOTS))
def test_history_is_not_silently_dropped(source, slot):
    change_file(source.parts, slot, 'completed.json', lambda data: data.update({'another-renewal-operation': data[OPERATION]}))
    with pytest.raises(ImportRejected, match='HISTORY_VARIANT'):
        source.inspect()


@pytest.mark.parametrize('slot', ['coordinator', 'RU', 'NL', 'NL2'])
@pytest.mark.parametrize('field,value', [('mode', 0o644), ('nlink', 2), ('inode', 0)])
def test_private_file_metadata(source, slot, field, value):
    change_document(source.parts, slot, lambda data: data['metadata']['operation.lock'].update({field: value}))
    with pytest.raises(ImportRejected, match='METADATA'):
        source.inspect()


@pytest.mark.parametrize('boundary', ['ONLINE_ACQUIRING', 'ONLINE_FENCING', 'ONLINE_RU_ACQUIRED',
    'ONLINE_PREPARED', 'ONLINE_NL2_STAGED', 'ONLINE_COMMIT_DECIDED', 'ONLINE_RU_DECIDED',
    'ONLINE_NL_PUBLISHED', 'ONLINE_RUNTIME_CONFIRMED', 'ONLINE_CLEANING'])
def test_interrupted_native_controller_retains_decision_and_resumes_same_host(tmp_path, boundary):
    fleet = make_fleet(tmp_path)
    enable(fleet)
    fail_at(fleet, boundary)
    parts = capture(fleet)
    result = Source(fleet, parts).inspect()
    assert result.state == boundary
    assert result.parts == parts
    assert compare_same_host(parts, capture(fleet), result.checkpoint, fleet.validator.anchor, fleet.now)[
        'host_resume'] == 'NOT_AUTHORIZED'
    decision = json.loads((fleet.controller.root / 'transaction.json').read_bytes())
    assert fleet.controller.run_online(OPERATION, schedule_seconds=0, resume=True)['result'] == 'COMMITTED'
    after = json.loads((fleet.controller.root / 'transaction.json').read_bytes())
    if decision['commit_decided']:
        assert after['plan_sha256'] == decision['plan_sha256']
    assert Source(fleet, capture(fleet)).inspect().state == 'COMMITTED'
    assert not any(node.barrier.starts or node.barrier.stopped() for node in fleet.nodes.values())


@pytest.mark.parametrize('slot,event', [('RU', 'online-acquired'), ('NL', 'online-prepared'),
    ('NL2', 'online-decision'), ('NL2', 'online-after-rename-gateway.json'),
    ('RU', 'online-delivery-fenced'), ('RU', 'online-sequence'), ('RU', 'online-delivery-ready'),
    ('NL', 'archive-plan.json'), ('RU', 'completed-ledger')])
def test_lost_node_reply_and_partial_cleanup_are_not_terminal(tmp_path, slot, event):
    fleet = make_fleet(tmp_path)
    enable(fleet)
    fired = []
    def crash(actual):
        if actual == event and not fired:
            fired.append(True)
            raise OSError('injected lost response')
    fleet.nodes[slot].fault = crash
    result = fleet.controller.run_online(OPERATION, schedule_seconds=0)
    assert fired and result['result'] == 'ONLINE_RECOVERY_REQUIRED'
    parts = capture(fleet)
    evidence = Source(fleet, parts).inspect()
    assert evidence.state in ('ONLINE_RECOVERY_REQUIRED', 'ONLINE_CLEANING')
    assert evidence.summary()['host_resume'] == 'NOT_AUTHORIZED'
    fleet.nodes[slot].fault = lambda event: None
    assert fleet.controller.run_online(OPERATION, schedule_seconds=0, resume=True)['result'] == 'COMMITTED'
    assert Source(fleet, capture(fleet)).inspect().state == 'COMMITTED'


@pytest.mark.parametrize('boundary', ['ONLINE_ACQUIRING', 'ONLINE_PREPARED', 'ONLINE_NL2_STAGED'])
def test_native_abort_does_not_invent_committed_state(tmp_path, boundary):
    fleet = make_fleet(tmp_path)
    enable(fleet)
    fail_at(fleet, boundary)
    assert fleet.controller.abort_online(OPERATION)['result'] == 'ABORTED'
    evidence = Source(fleet, capture(fleet)).inspect()
    assert evidence.state == 'ABORTED' and evidence.committed is False
    assert evidence.summary()['activation'] == 'FORBIDDEN'


def test_copied_node_directory_is_not_same_host_reconciliation(tmp_path):
    fleet = make_fleet(tmp_path)
    enable(fleet)
    fail_at(fleet, 'ONLINE_COMMIT_DECIDED')
    before = capture(fleet)
    old = fleet.nodes['NL'].state
    copied = tmp_path / 'relocated-ledger'
    shutil.copytree(old, copied)
    fleet.nodes['NL'].state = copied
    with pytest.raises(ImportRejected, match='HOST_OR_EVIDENCE_CHANGED'):
        compare_same_host(before, capture(fleet), evidence_digest(before), fleet.validator.anchor, fleet.now)
    assert old.exists()


@pytest.mark.parametrize('slot', sorted(SLOTS))
@pytest.mark.parametrize('key,value', [('fence', 0), ('fence', 99), ('fence', True), ('mode', 'maintenance'),
    ('operation_id', 'different-operation'), ('state', 'COMMITTED'), ('expected_state', {}),
    ('commit_decided', True), ('state', 'ABORTED'), ('state', 'RESUMED'), ('state', 'ONLINE_PUBLISHED')])
def test_pending_node_identity_cannot_be_rebound(interrupted, slot, key, value):
    parts = deepcopy(interrupted.parts)
    change_file(parts, slot, 'owner.json', lambda data: data.update({key: value}))
    with pytest.raises(ImportRejected):
        interrupted.inspect(parts)


@pytest.mark.parametrize('slot', sorted(SLOTS))
def test_acknowledged_pending_preparation_cannot_lose_its_receipt(interrupted, slot):
    parts = deepcopy(interrupted.parts)
    remove_file(parts, slot, 'online-prepared.json')
    with pytest.raises(ImportRejected, match='RENEWAL_RECEIPT_MISSING'):
        interrupted.inspect(parts)


@pytest.mark.parametrize('mutation', ['schema', 'grant', 'grant-model', 'cloned-gateway', 'signature',
                                     'issuer', 'profile-hash', 'predecessor'])
def test_recomputed_hashes_do_not_replace_native_plan_validation(tmp_path, mutation):
    fleet = make_fleet(tmp_path)
    enable(fleet)
    fail_at(fleet, 'ONLINE_PREPARED')
    parts = capture(fleet)
    def mutate(plan):
        if mutation == 'schema':
            plan['schema'] = True
        elif mutation == 'grant':
            plan['grant_plan']['after_grants'] = [{'device': 'not-a-valid-grant'}]
        elif mutation == 'grant-model':
            plan['grant_plan']['model'] = 'FORGED'
        elif mutation == 'cloned-gateway':
            plan['gateway_ids']['NL2'] = plan['gateway_ids']['NL']
        elif mutation == 'signature':
            plan['candidate']['authority']['signature'] = base64.b64encode(bytes(64)).decode()
        elif mutation == 'issuer':
            plan['candidate']['crl'] = plan['previous']['crl']
        elif mutation == 'profile-hash':
            plan['secondary']['nl_profile_sha256'] = '0' * 64
        else:
            plan['grant_plan']['predecessors'] = [1]
    change_file(parts, 'coordinator', 'plan.json', mutate)
    change_file(parts, 'RU', 'prepared-plan.json', mutate)
    document = json.loads(parts['coordinator.json'])
    plan_hash = digest(base64.b64decode(document['files']['plan.json']))
    change_file(parts, 'coordinator', 'transaction.json', lambda data: data.update(plan_sha256=plan_hash))
    with pytest.raises(ImportRejected):
        Source(fleet, parts).inspect()


def test_revocation_during_commit_stays_fenced_and_requires_emergency(tmp_path):
    fleet = make_fleet(tmp_path)
    enable(fleet)
    def revoke(event):
        if event == 'ONLINE_COMMIT_DECIDED':
            with fleet.service.access.db() as database:
                database.execute('UPDATE devices SET revoked=1 WHERE device=?', (fleet.device.reference,))
    fleet.controller.fault = revoke
    assert fleet.controller.run_online(OPERATION, schedule_seconds=0)['result'] == 'ONLINE_EMERGENCY_REQUIRED'
    evidence = Source(fleet, capture(fleet)).inspect()
    assert evidence.state == 'ONLINE_EMERGENCY_REQUIRED' and evidence.committed
    assert all(node.barrier.stopped() for node in fleet.nodes.values())
    with pytest.raises(Rejected, match='ONLINE_DECISION_IMMUTABLE'):
        fleet.controller.abort_online(OPERATION)
    with pytest.raises(Rejected, match='ONLINE_EMERGENCY_REQUIRED'):
        fleet.controller.run_online(OPERATION, schedule_seconds=0, resume=True)
    assert not (fleet.nodes['RU'].live / 'online-delivery.json').exists()


def test_source_removal_retains_exact_private_evidence_but_forbids_resume(tmp_path):
    from scripts.control_ha_rehearsal import private_file
    root = tmp_path / 'source'
    root.mkdir(mode=0o700)
    fleet = make_fleet(root)
    enable(fleet)
    fail_at(fleet, 'ONLINE_COMMIT_DECIDED')
    parts = capture(fleet)
    checkpoint = evidence_digest(parts)
    destination = tmp_path / 'retained'
    destination.mkdir(mode=0o700)
    for name, raw in parts.items():
        private_file(destination / name, raw)
    shutil.rmtree(root)
    recovered = {name: (destination / name).read_bytes() for name in PARTS}
    evidence = inspect_renewal(recovered, checkpoint, fleet.validator.anchor, fleet.now)
    assert evidence.parts == parts
    assert evidence.committed and evidence.state == 'ONLINE_COMMIT_DECIDED'
    assert evidence.summary()['host_resume'] == 'NOT_AUTHORIZED'
    assert not root.exists() and stat.S_IMODE(destination.stat().st_mode) == 0o700
    assert all(stat.S_IMODE(path.stat().st_mode) == 0o600 for path in destination.iterdir())
