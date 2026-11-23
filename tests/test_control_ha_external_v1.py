from contextlib import closing
from copy import deepcopy
import os
from pathlib import Path
import secrets
import sqlite3
import uuid

import pytest

from control.friends.enrollment_postgres import PostgresEnrollment
from scripts.control_ha_bundle_fixture import reconstruct
from scripts.control_ha_external_fixture import artifacts_for_external, exercise_external_files
from scripts.control_ha_external_v1 import preflight_external, records, routing_check, admission_check, sender_check
from control.friends import restricted
from scripts.control_ha_import import ImportRejected, digest, encoded, import_snapshot
from scripts.control_ha_import_fixture import CHECKPOINT
from scripts.control_ha_recovery_bundle import parse, seal, preflight_bundle
from scripts.control_ha_sqlite_fixture import joint_fixture, exercise_import
from scripts.referral_postgres_rehearsal import NOW


@pytest.fixture
def source(tmp_path):
    root = tmp_path / 'source'
    root.mkdir(mode=0o700)
    fixture = joint_fixture(root)
    return fixture, artifacts_for_external(fixture), secrets.token_bytes(32)


def capture(source):
    fixture, artifacts, key = source
    return seal(fixture.stores, fixture.external, artifacts, CHECKPOINT, fixture.bootstrap,
                fixture.service.anchor, key, now=NOW)


def recover(source, bundle, checkpoint):
    return preflight_external(bundle, source[2], checkpoint, source[0].service.anchor, now=NOW)


def checked(source):
    return recover(source, *capture(source))


def test_complete_real_five_role_inputs_bind_to_import(source):
    raw, checkpoint = capture(source)
    recovered = recover(source, raw, checkpoint)
    basic = preflight_bundle(raw, source[2], checkpoint, source[0].service.anchor, now=NOW)
    assert recovered.snapshot.rows == basic.snapshot.rows
    assert recovered.snapshot.fingerprint != basic.snapshot.fingerprint
    assert recovered.artifacts == source[1]
    summary = recovered.summary()
    assert summary['activation'] == 'FORBIDDEN'
    assert summary['exact_bytes_only'] == ['maintenance_state', 'receiver_state']
    assert summary['artifacts'] == 23 and summary['allocator_nodes'] == 3
    assert set(source[1]['aliases']) == {'manifest', 'current-hmac'}


def test_only_in_memory_sqlite_is_opened_by_strict_preflight(source, monkeypatch):
    raw, checkpoint = capture(source)
    connect = sqlite3.connect
    def memory_only(path, *args, **kwargs):
        assert path == ':memory:'
        return connect(path, *args, **kwargs)
    monkeypatch.setattr(sqlite3, 'connect', memory_only)
    monkeypatch.setattr(PostgresEnrollment, 'connect', lambda *args: pytest.fail('No PostgreSQL in dry run'))
    assert recover(source, raw, checkpoint).summary()['allocator_nodes'] == 3


@pytest.mark.parametrize('role', ['aliases', 'admission', 'sender_policy', 'routing_files', 'node_allocations'])
def test_opaque_probe_or_unknown_parts_cannot_claim_real_role_coverage(source, role):
    source[1][role] = {'opaque-probe': b'synthetic-not-runtime'}
    with pytest.raises(ImportRejected):
        checked(source)


@pytest.mark.parametrize('kind', ['key', 'missing-device', 'missing-event', 'duplicate-entity', 'extra', 'legacy-key'])
def test_alias_key_schema_and_full_db_coverage(source, kind):
    parts = source[1]['aliases']
    value = parse(parts['manifest'])
    if kind == 'key':
        parts['current-hmac'] = secrets.token_bytes(32)
    elif kind == 'missing-device':
        value['entities']['device'].pop()
    elif kind == 'missing-event':
        value['entities']['panel_event'].clear()
    elif kind == 'duplicate-entity':
        value['entities']['device'][1]['entity'] = value['entities']['device'][0]['entity']
    elif kind == 'extra':
        value['unexpected'] = True
    elif kind == 'legacy-key':
        parts['legacy-hmac'] = secrets.token_bytes(32)
    parts['manifest'] = encoded(value)
    with pytest.raises(ImportRejected):
        checked(source)


@pytest.mark.parametrize('kind', ['unknown', 'revoked', 'no-grant', 'duplicate', 'too-many', 'wrong-type', 'extra'])
def test_admission_cannot_resurrect_or_invent_grants(source, kind):
    fixture, artifacts, key = source
    frozen = checked(source)
    devices = records(frozen.snapshot)['devices']
    value = parse(artifacts['admission']['field.json'])
    if kind == 'unknown':
        value['devices'] = ['f' * 32]
    elif kind == 'revoked':
        value['devices'] = [row['device'] for row in devices if row['revoked']]
    elif kind == 'no-grant':
        value['devices'] = [fixture.child.reference]
    elif kind == 'duplicate':
        value['devices'] *= 2
    elif kind == 'too-many':
        value['devices'] = [row['device'] for row in devices]
    elif kind == 'wrong-type':
        value['devices'] = [False]
    elif kind == 'extra':
        value['all_activated'] = True
    artifacts['admission']['field.json'] = encoded(value)
    with pytest.raises(ImportRejected):
        checked(source)


@pytest.mark.parametrize('field,value', [('sender_public', 'f' * 128), ('revision', 0), ('revision', True),
    ('enabled', 1), ('schema', 1), ('schema', True), ('unexpected', 'private-canary')])
def test_sender_policy_requires_registered_sender_and_supported_schema(source, field, value):
    parts = source[1]['sender_policy']
    policy = parse(parts['support.json'])
    policy[field] = value
    parts['support.json'] = encoded(policy)
    with pytest.raises(ImportRejected) as failure:
        checked(source)
    assert 'private-canary' not in str(failure.value)


@pytest.mark.parametrize('field,value', [('family', 'f' * 32), ('revision', 0), ('expires', NOW), ('revoked', 1)])
def test_admission_grant_semantics(source, field, value):
    recovered = checked(source)
    rows = records(recovered.snapshot)
    grant = next(row for row in rows['restricted_grants'] if row['device'] == source[0].device.reference)
    grant[field] = value
    trust, authority = restricted.delegation(parse(recovered.bootstrap)['manifest'], source[0].service.anchor, NOW)
    with pytest.raises(ImportRejected, match='EXTERNAL_ADMISSION_GRANT'):
        admission_check(source[1]['admission'], rows, trust, NOW)


@pytest.mark.parametrize('kind', ['disabled-service', 'foreign-binding'])
def test_sender_db_bindings(source, kind):
    recovered = checked(source)
    rows = records(recovered.snapshot)
    if kind == 'disabled-service':
        rows['chat_service_senders'][0]['enabled'] = 0
    else:
        rows['chat_bindings'][0]['support_sender'] = 'f' * 128
    with pytest.raises(ImportRejected, match='EXTERNAL_SENDER_'):
        sender_check(source[1]['sender_policy'], rows)


@pytest.mark.parametrize('kind', ['anchor', 'missing-policy', 'missing-catalog', 'missing-selection', 'hash', 'extra'])
def test_signed_routing_file_integrity_and_coverage(source, kind):
    parts = source[1]['routing_files']
    if kind == 'anchor':
        parts['anchor.pub'] = b'AAAA'
    elif kind.startswith('missing-'):
        suffix = '.' + kind.removeprefix('missing-') + '.json'
        del parts[next(name for name in parts if name.endswith(suffix))]
    elif kind == 'hash':
        parts[next(name for name in parts if name.endswith('.policy.json'))] += b'\n'
    elif kind == 'extra':
        parts['unclassified.json'] = b'{}'
    with pytest.raises(ImportRejected):
        checked(source)


@pytest.mark.parametrize('table,column,value', [
    ('gateway_routing_state', 'generation', 99), ('gateway_assignments', 'sequence', 99),
    ('gateway_assignments', 'node', 'gateway-ru'), ('gateway_selection_events', 'sequence', 99),
    ('gateway_selection_events', 'policy_sha256', 'f' * 64),
    ('gateway_assignment_events', 'previous_sha256', 'f' * 64),
])
def test_routing_rows_cannot_disagree_with_signed_material(source, table, column, value):
    frozen = checked(source)
    rows = deepcopy(records(frozen.snapshot))
    rows[table][0][column] = value
    with pytest.raises((ValueError, KeyError)):
        routing_check(source[1]['routing_files'], rows)


@pytest.mark.parametrize('kind', ['missing-node', 'wrong-host', 'wrong-network', 'wrong-address', 'extra-setting',
                                  'corrupt', 'schema', 'version', 'floor', 'missing-sequence', 'unknown-peer', 'extra-sequence'])
def test_allocator_node_bindings_schema_and_highwater(source, kind):
    parts = source[1]['node_allocations']
    node = 'nl-amsterdam-1'
    if kind == 'missing-node':
        del parts[node + '.sqlite']
    elif kind in ('wrong-host', 'wrong-network', 'wrong-address', 'extra-setting'):
        settings = parse(parts[node + '.json'])
        field, value = {'wrong-host': ('external', '192.0.2.99'), 'wrong-network': ('network', '10.85.0.0/16'),
                        'wrong-address': ('address', '10.83.0.2/16'), 'extra-setting': ('unexpected', 'private-canary')}[kind]
        settings[field] = value
        parts[node + '.json'] = encoded(settings)
    elif kind == 'corrupt':
        parts[node + '.sqlite'] = b'not-sqlite'
    else:
        with closing(sqlite3.connect(':memory:')) as database:
            database.deserialize(parts[node + '.sqlite'])
            statement = {'schema': 'CREATE TABLE unexpected(value)', 'version': 'PRAGMA user_version=1',
                'floor': 'UPDATE sqlite_sequence SET seq=1', 'missing-sequence': 'DELETE FROM sqlite_sequence',
                'unknown-peer': "UPDATE peers SET public='unknown' WHERE id=1",
                'extra-sequence': "INSERT INTO sqlite_sequence VALUES ('other',100)"}[kind]
            database.execute(statement)
            database.commit()
            parts[node + '.sqlite'] = database.serialize()
    with pytest.raises(ImportRejected) as failure:
        checked(source)
    assert 'private-canary' not in str(failure.value)


def test_restored_actual_files_preserve_alias_history_and_node_local_allocators(source, tmp_path):
    recovered = checked(source)
    fixture = source[0]
    anchor = fixture.service.anchor
    fixture.service, fixture.access, fixture.referral_secret = None, None, b''
    fixture.paths, fixture.pending['routing'] = {}, None
    root = tmp_path / 'restored'
    restored = reconstruct(fixture, recovered, anchor, root)
    result = exercise_external_files(restored, recovered, root)
    assert all(result.values()) and result['allocator_nodes'] == 3
    assert root.stat().st_mode & 0o777 == 0o700
    assert (root / 'aliases.json').stat().st_mode & 0o777 == 0o600


@pytest.fixture
def repository():
    if not os.environ.get('FC_HA_PG_PORT'):
        pytest.skip('Run scripts.control_ha_external_rehearsal for real PostgreSQL qualification')
    return PostgresEnrollment(port=int(os.environ['FC_HA_PG_PORT']), schema='ha_enrollment_' + uuid.uuid4().hex,
        password=Path(os.environ['FC_HA_PG_PASSWORD_FILE']).read_text().strip())


def test_strict_import_and_business_continuation(source, repository, tmp_path):
    recovered = checked(source)
    assert import_snapshot(repository, recovered.snapshot)['result'] == 'IMPORTED'
    assert import_snapshot(repository, recovered.snapshot)['result'] == 'EXACT_RETRY'
    root = tmp_path / 'restored'
    fixture = reconstruct(source[0], recovered, source[0].service.anchor, root)
    assert all(exercise_external_files(fixture, recovered, root).values())
    assert all(exercise_import(fixture, repository).values())


def test_generic_bundle_receipt_cannot_claim_strict_adapter_acceptance(source, repository):
    raw, checkpoint = capture(source)
    basic = preflight_bundle(raw, source[2], checkpoint, source[0].service.anchor, now=NOW)
    import_snapshot(repository, basic.snapshot)
    with pytest.raises(ImportRejected, match='TARGET_NOT_SAME_IMPORT'):
        import_snapshot(repository, recover(source, raw, checkpoint).snapshot)


def test_semantically_valid_alias_regeneration_is_not_an_exact_recovery(source, repository):
    raw, checkpoint = capture(source)
    original = recover(source, raw, checkpoint)
    import_snapshot(repository, original.snapshot)
    value = parse(source[1]['aliases']['manifest'])
    value['entities']['device'][0]['entity'] = uuid.uuid4().hex
    source[1]['aliases']['manifest'] = encoded(value)
    changed, current = capture(source)
    assert digest(changed) != checkpoint.bundle_sha256
    with pytest.raises(ImportRejected, match='CHECKPOINT_MISMATCH'):
        recover(source, changed, checkpoint)
    newer = recover(source, changed, current)
    with pytest.raises(ImportRejected, match='TARGET_NOT_SAME_IMPORT'):
        import_snapshot(repository, newer.snapshot)
    assert import_snapshot(repository, original.snapshot)['result'] == 'EXACT_RETRY'
