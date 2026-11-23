from copy import deepcopy
from dataclasses import replace
from pathlib import Path
import base64
import secrets
import shutil
import subprocess

import pytest

from scripts import control_ha_legacy_custody as custody
from scripts.control_ha_current_audit import audit_current, project
from scripts.control_ha_import import ImportRejected, TABLES, digest, encoded
from scripts.control_ha_maintenance_fixture import artifacts_for_maintenance
from scripts.control_ha_online_fixture import native_fixture
from scripts.control_ha_receiver_v1 import preflight_receivers
from scripts.control_ha_recovery_bundle import parse
from scripts.control_ha_renewal_v1 import SLOTS
from scripts.control_ha_sqlite_fixture import refresh_fixture
from scripts.control_ha_stopped_v1 import CURRENT_PURPOSE, inspect_stopped
from scripts.referral_postgres_rehearsal import NOW
from test_control_ha_legacy_custody import IDENTIFIER, inventory, write
from test_control_ha_online_capsule import Source, capture
from test_control_ha_renewal_v1 import OPERATION
from production_transport import SystemdBarrier

UNITS = {'RU': ('test-ru.service', 'test-writer.timer', 'test-writer.service',
                'test-refresh.timer', 'test-refresh.service'),
         'NL': ('test-nl.service',), 'NL2': ('test-nl2.service',)}


class NativeServiceBarrier(SystemdBarrier):
    def __init__(self, node, slot, clock):
        super().__init__(node.role, node.state, units=UNITS[slot], clock=clock)
        self.native = node.barrier
        self.states = {unit: dict(ActiveState='inactive' if slot == 'RU' and index in (2, 4) else 'active',
            SubState='running', MainPID='11', InvocationID='a' * 32, NRestarts='0', Result='success')
            for index, unit in enumerate(self.units)}

    def state(self, unit):
        return dict(self.states[unit])

    def invoke(self, action, unit):
        assert action in ('stop', 'start') and unit in self.units
        if action == 'stop':
            self.native.quiesce()
            self.states[unit].update(ActiveState='inactive', SubState='dead', MainPID='0')
        else:
            self.native.resume(commit_decided=True, equality_verified=True)
            self.states[unit].update(ActiveState='active', SubState='running', MainPID='12')


@pytest.fixture(scope='module')
def native_current(tmp_path_factory):
    root = tmp_path_factory.mktemp('scheduled-native')
    fixture, fleet = native_fixture(root)
    for slot, node in fleet.nodes.items():
        node.barrier = NativeServiceBarrier(node, slot, fleet.clock)
    result = fleet.controller.run(OPERATION, scheduled=True, approved_leaf_crl_schedule=True)
    assert result['result'] == 'COMMITTED'
    fixture.service.manifest = parse(fleet.nodes['RU'].read('issuer.json')[0])
    refresh_fixture(fixture)
    artifacts, bounded = artifacts_for_maintenance(fixture)
    source = Source(fixture, artifacts, bounded['pending'], secrets.token_bytes(32))
    bundle, checkpoint = capture(source)
    recovered = preflight_receivers(bundle, source.key, checkpoint, fixture.service.anchor, now=NOW)
    roots = dict(coordinator=fleet.controller.root, RU=fleet.nodes['RU'].state,
                 NL1=fleet.nodes['NL'].state, NL2=fleet.nodes['NL2'].state)
    for slot in ('RU', 'NL1'):
        ledger = parse((roots[slot] / 'completed.json').read_bytes())
        ledger['legacy-fenced-operation'] = dict(result='CLEANED_FENCED_ROLLBACK')
        write(roots[slot] / 'completed.json', encoded(ledger))
        write(roots[slot] / 'archive/legacy-fenced-operation/opaque.bin', b'\xffLEGACY\x00')
    write(roots['coordinator'] / 'old-adjunct.json', b'{"state":"UNKNOWN"}')
    publications = {slot: fleet.nodes['RU'].directory_destination(slot).read_bytes() for slot in ('NL', 'NL2')}
    return roots, recovered, publications, fixture.service.anchor


@pytest.fixture
def current(native_current, tmp_path):
    roots, recovered, publications, anchor = native_current
    copied = {slot: Path(shutil.copytree(path, tmp_path / slot)) for slot, path in roots.items()}
    return dict(roots=copied, recovered=deepcopy(recovered), publications=dict(publications),
                anchor=anchor, units=deepcopy(UNITS), key=secrets.token_bytes(32))


def sealed(current):
    return custody.seal(current['roots'], inventory(current['roots']), current['key'], IDENTIFIER)


def audit(current, packed=None, *, now=NOW):
    bundle, checkpoint = sealed(current) if packed is None else packed
    return audit_current(bundle, current['key'], checkpoint, current['recovered'], current['publications'],
        current['anchor'], captured_at=NOW, now=now, units=current['units'])


def rewrite(current, slot, name, change):
    path = current['roots'][slot] / name
    document = parse(path.read_bytes())
    change(document)
    write(path, encoded(document))


def refresh_archive(current, slot):
    root = current['roots'][slot]
    archive = root / 'archive' / OPERATION
    manifest = {path.name: digest(path.read_bytes()) for path in archive.iterdir()
                if path.name != 'archive-manifest.json'}
    write(archive / 'archive-manifest.json', encoded(manifest))
    rewrite(current, slot, 'completed.json', lambda value: value[OPERATION].update(manifest_sha256=digest(encoded(manifest))))


def test_native_schedule_content_after_source_removal_is_still_not_acceptance(current, monkeypatch):
    packed = sealed(current)
    before = custody.inspect(packed[0], current['key'], packed[1])
    for path in current['roots'].values():
        shutil.rmtree(path)
    def forbidden(*args, **kwargs):
        raise AssertionError('host execution or file access attempted')
    monkeypatch.setattr(Path, 'open', forbidden)
    monkeypatch.setattr(subprocess, 'run', forbidden)
    result = audit(current, packed)
    assert result['result'] == 'CURRENT_CONTENT_CHECKED_RECOVERY_BLOCKED'
    assert result['recovery_acceptance'] == 'BLOCKED'
    assert result['original_gate_provenance'] == 'NOT_ESTABLISHED'
    assert result['service_liveness'] == 'NOT_OBSERVED'
    assert result['ledger_entries'] == dict(RU=2, NL1=2, NL2=1)
    assert result['activation'] == 'FORBIDDEN'
    assert result['host_resume'] == result['database_import'] == 'NOT_AUTHORIZED'
    assert custody.inspect(packed[0], current['key'], packed[1]).trees == before.trees
    assert 'LEGACY' not in repr(result) and OPERATION not in repr(result)


@pytest.mark.parametrize('slot', ['RU', 'NL1', 'NL2'])
@pytest.mark.parametrize('name', ['services-before.json', 'start-intent-0.json'])
def test_required_service_evidence_cannot_be_pruned_even_with_rebound_manifest(current, slot, name):
    (current['roots'][slot] / 'archive' / OPERATION / name).unlink()
    refresh_archive(current, slot)
    with pytest.raises(ImportRejected):
        audit(current)


@pytest.mark.parametrize('mutation', ['unit', 'schema', 'time-early', 'time-late', 'bool-time', 'unknown'])
def test_rebound_start_intent_contradictions_refuse(current, mutation):
    def change(value):
        if mutation == 'unit': value['unit'] = 'other.service'
        elif mutation == 'schema': value['schema'] = True
        elif mutation == 'time-early': value['timestamp'] = NOW - 1
        elif mutation == 'time-late': value['timestamp'] = NOW + 1
        elif mutation == 'bool-time': value['timestamp'] = True
        else: value['approved'] = True
    rewrite(current, 'RU', 'archive/' + OPERATION + '/start-intent-0.json', change)
    refresh_archive(current, 'RU')
    with pytest.raises(ImportRejected):
        audit(current)


def test_native_subsecond_intent_before_integer_receipt_boundary(current):
    rewrite(current, 'NL1', 'archive/' + OPERATION + '/start-intent-0.json', lambda value: value.update(timestamp=NOW + .25))
    refresh_archive(current, 'NL1')
    assert audit(current)['recovery_acceptance'] == 'BLOCKED'


@pytest.mark.parametrize('mutation', ['extra-intent', 'state', 'pid', 'unit', 'extra-state-field', 'missing-timer'])
def test_service_scope_and_native_resume_policy_are_checked(current, mutation):
    if mutation == 'extra-intent':
        write(current['roots']['RU'] / 'archive' / OPERATION / 'start-intent-1.json',
            encoded(dict(schema=1, unit=UNITS['RU'][1], timestamp=NOW)))
    else:
        def change(value):
            if mutation == 'state': value[UNITS['RU'][0]]['ActiveState'] = 'unknown'
            elif mutation == 'pid': value[UNITS['RU'][0]]['MainPID'] = '-1'
            elif mutation == 'unit': value['other.service'] = value.pop(UNITS['RU'][0])
            elif mutation == 'extra-state-field': value[UNITS['RU'][0]]['approved'] = 'yes'
            else: value.pop(UNITS['RU'][3])
        rewrite(current, 'RU', 'archive/' + OPERATION + '/services-before.json', change)
    refresh_archive(current, 'RU')
    with pytest.raises(ImportRejected):
        audit(current)


@pytest.mark.parametrize('mutation', ['pending', 'gate', 'zero', 'decision', 'unknown'])
def test_current_coordinator_not_history_must_be_settled(current, mutation):
    def change(value):
        if mutation == 'pending': value['state'] = 'CLEANING'
        elif mutation == 'gate': value['gate']['authorization'] = 'OPERATOR_APPROVED_OUTAGE'
        elif mutation == 'zero': value['gate']['pre_stop_sessions'] = 0
        elif mutation == 'decision': value['commit_decided'] = False
        else: value['mode'] = 'unknown'
    rewrite(current, 'coordinator', 'transaction.json', change)
    with pytest.raises(ImportRejected):
        audit(current)


@pytest.mark.parametrize('name', ['owner.json', 'pending.json'])
def test_pending_or_unknown_node_root_is_not_skipped(current, name):
    write(current['roots']['NL2'] / name, b'{}')
    with pytest.raises(ImportRejected, match='CURRENT_PENDING_OR_UNKNOWN_ROOT'):
        audit(current)


@pytest.mark.parametrize('table', ['devices', 'invites', 'restricted_grants', 'restricted_certificates', 'restricted_crl_sequence'])
def test_current_five_table_state_must_match_native_plan(current, table):
    recovered = current['recovered']
    rows = list(recovered.snapshot.rows)
    index = next(index for index, item in enumerate(TABLES) if item.name == table)
    rows[index] = ()
    current['recovered'] = replace(recovered, snapshot=replace(recovered.snapshot, rows=tuple(rows)))
    with pytest.raises(ImportRejected, match='ONLINE_CAPSULE_DATABASE_MISMATCH'):
        audit(current)


@pytest.mark.parametrize('slot', ['NL', 'NL2'])
def test_both_actual_publications_must_match(current, slot):
    current['publications'][slot] = b'{}'
    with pytest.raises(ImportRejected):
        audit(current)


def test_stale_signed_material_refuses(current):
    with pytest.raises(ImportRejected):
        audit(current, now=NOW + 100000)


@pytest.mark.parametrize('slot', ['RU', 'NL1', 'NL2'])
@pytest.mark.parametrize('mutation', ['missing', 'pending', 'fenced', 'future'])
def test_current_ledger_entry_must_be_the_exact_completed_operation(current, slot, mutation):
    def change(value):
        if mutation == 'missing': value.pop(OPERATION)
        elif mutation == 'pending': value[OPERATION]['result'] = 'UNKNOWN'
        elif mutation == 'fenced': value[OPERATION]['result'] = 'CLEANED_FENCED_ROLLBACK'
        else: value[OPERATION]['timestamp'] = NOW + 1
    rewrite(current, slot, 'completed.json', change)
    with pytest.raises(ImportRejected):
        audit(current)


def test_old_ciphertext_cannot_satisfy_new_independent_checkpoint(current):
    old_bundle, _ = sealed(current)
    _, new_checkpoint = sealed(current)
    with pytest.raises(ImportRejected, match='CUSTODY_CHECKPOINT_MISMATCH'):
        audit(current, (old_bundle, new_checkpoint))


@pytest.mark.parametrize('name', ['delegation', 'crl', 'directory'])
def test_current_issuer_is_not_only_a_custody_digest(current, name):
    current['recovered'].artifacts['issuer_material'][name] = b'{}'
    with pytest.raises(ImportRejected):
        audit(current)


@pytest.mark.parametrize('mutation', ['order', 'duplicate', 'missing', 'wrong-type'])
def test_unproven_unit_configuration_is_still_structurally_strict(current, mutation):
    units = list(current['units']['RU'])
    if mutation == 'order': units[0], units[2] = units[2], units[0]
    elif mutation == 'duplicate': units[2] = units[0]
    elif mutation == 'missing': units.pop()
    else: units[0] = None
    current['units']['RU'] = units
    with pytest.raises(ImportRejected):
        audit(current)


def test_no_stopped_recovery_gate_is_relaxed(current):
    packed = sealed(current)
    preserved = custody.inspect(packed[0], current['key'], packed[1])
    parts = {'capture.json': encoded(dict(schema=1, purpose=CURRENT_PURPOSE, operation_id=OPERATION,
        captured_at=NOW, anchor_sha256=digest(current['anchor']), nodes=sorted(SLOTS)))}
    for slot in ('coordinator', 'RU', 'NL', 'NL2'):
        parts[slot + '.json'] = project(preserved.trees['NL1' if slot == 'NL' else slot], slot, OPERATION)
    publication = encoded(dict(schema=1, directories={slot: base64.b64encode(raw).decode()
        for slot, raw in current['publications'].items()}))
    with pytest.raises(ImportRejected, match='STOPPED_CAPTURE'):
        inspect_stopped(parts, publication, current['anchor'], NOW)
