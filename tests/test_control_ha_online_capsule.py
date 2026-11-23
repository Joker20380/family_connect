from copy import deepcopy
from dataclasses import dataclass, replace
import os
from pathlib import Path
import secrets
import shutil
import sqlite3
import uuid

import pytest

from control.friends.enrollment_postgres import PostgresEnrollment
from scripts.control_ha_import import TABLES, ImportRejected, encoded, import_snapshot
from scripts.control_ha_import_fixture import CHECKPOINT
from scripts.control_ha_maintenance_v1 import PARTS as BOUNDED_PARTS, inspect_maintenance, preflight_maintenance
from scripts.control_ha_online_capsule import (DATABASE_TABLES, MAPPING, PARTS, assemble, binding_for,
                                             inspect_online_inputs, preflight_online)
from scripts.control_ha_online_fixture import online_fixture
from scripts.control_ha_receiver_v1 import preflight_receivers
from scripts.control_ha_recovery_bundle import parse, preflight_bundle, seal
from scripts.control_ha_rehearsal import private_file
from scripts.referral_postgres_rehearsal import NOW


@dataclass(repr=False)
class Source:
    fixture: object
    artifacts: dict
    pending: dict
    key: bytes


@pytest.fixture(scope='module')
def original(tmp_path_factory):
    fixture, artifacts, bounded = online_fixture(tmp_path_factory.mktemp('online-capsule'))
    return Source(fixture, artifacts, bounded['pending'], secrets.token_bytes(32))


@pytest.fixture
def source(original):
    fixture = replace(original.fixture, stores=dict(original.fixture.stores))
    return Source(fixture, deepcopy(original.artifacts), deepcopy(original.pending), secrets.token_bytes(32))


def capture(source):
    fixture = source.fixture
    return seal(fixture.stores, fixture.external, source.artifacts, CHECKPOINT, fixture.bootstrap,
                fixture.service.anchor, source.key, now=NOW)


def recover(source, bundle, checkpoint):
    return preflight_online(bundle, source.key, checkpoint, source.fixture.service.anchor, now=NOW)


def checked(source):
    return recover(source, *capture(source))


def renewal_parts(source):
    return {name: source.artifacts['maintenance_state'][mapped] for name, mapped in MAPPING.items()}


def update_binding(source):
    source.artifacts['maintenance_state']['binding.json'] = encoded(binding_for(source.fixture.stores,
        source.artifacts['issuer_material'], CHECKPOINT, renewal_parts(source)))


def test_complete_capsule_preserves_private_bytes_and_declares_limits(source):
    raw, checkpoint = capture(source)
    recovered = recover(source, raw, checkpoint)
    assert recovered.artifacts == source.artifacts
    assert recovered.stores == source.fixture.stores
    assert sum(len(parts) for parts in recovered.artifacts.values()) == 44
    assert b'SQLite format' not in raw
    assert all(value not in raw for value in source.artifacts['issuer_material'].values())
    summary = recovered.summary()
    assert summary['canonical_renewal_binding'] == 'EXACT'
    assert summary['activation'] == 'FORBIDDEN'
    assert summary['history'] == 'UNSUPPORTED_REFUSED'
    assert summary['full_dr'] == 'NOT_QUALIFIED'
    assert summary['exact_bytes_only'] == []
    assert 'runtime-key' not in repr(recovered)


@pytest.mark.parametrize('name', sorted(PARTS))
def test_missing_any_combined_journal_part_is_not_empty_state(source, name):
    del source.artifacts['maintenance_state'][name]
    with pytest.raises(ImportRejected, match='ONLINE_CAPSULE_PARTS'):
        checked(source)


@pytest.mark.parametrize('field', ['schema', 'format', 'checkpoint', 'stores', 'issuer', 'renewal_sha256', 'extra'])
def test_manifest_rebinding_or_unknown_field_refuses_even_with_new_checkpoint(source, field):
    binding = parse(source.artifacts['maintenance_state']['binding.json'])
    binding[field] = True if field == 'schema' else 'unrelated'
    source.artifacts['maintenance_state']['binding.json'] = encoded(binding)
    with pytest.raises(ImportRejected, match='ONLINE_CAPSULE_BINDING'):
        checked(source)


@pytest.mark.parametrize('name', sorted(BOUNDED_PARTS - {'capture.json'}))
def test_each_bounded_node_must_declare_the_exact_renewal_inventory(source, name):
    document = parse(source.artifacts['maintenance_state'][name])
    document['renewal'] = dict(format='none-declared/v1', coordinator=[], node=[])
    source.artifacts['maintenance_state'][name] = encoded(document)
    with pytest.raises(ImportRejected, match='MAINTENANCE_RENEWAL_UNSUPPORTED'):
        checked(source)


def test_old_maintenance_adapter_cannot_accept_the_combined_format(source):
    raw, checkpoint = capture(source)
    with pytest.raises(ImportRejected):
        preflight_maintenance(raw, source.key, checkpoint, source.fixture.service.anchor, now=NOW)


@pytest.mark.parametrize('declaration', [{}, {'format': 'unknown/v1', 'evidence_sha256': 'a' * 64},
                                      {'format': 'bounded-and-online-renewal/v1', 'evidence_sha256': True}])
def test_optional_inventory_declaration_does_not_allow_arbitrary_formats(source, declaration):
    with pytest.raises(ImportRejected, match='MAINTENANCE_RENEWAL_UNSUPPORTED'):
        inspect_maintenance(source.pending, source.artifacts['issuer_material'], now=NOW, renewal=declaration)


def test_pending_bounded_operation_blocks_completed_renewal(source):
    source.artifacts['maintenance_state'] = assemble(source.pending, renewal_parts(source), source.fixture.stores,
                                                    source.artifacts['issuer_material'], CHECKPOINT)
    with pytest.raises(ImportRejected, match='MAINTENANCE_UNSETTLED_REQUIRES_RECONCILIATION'):
        checked(source)


def test_pending_renewal_survives_source_removal_but_blocks_import(tmp_path):
    root = tmp_path / 'source'
    root.mkdir(mode=0o700)
    fixture, artifacts, bounded = online_fixture(root, interrupt=True)
    source = Source(fixture, artifacts, bounded['pending'], secrets.token_bytes(32))
    raw, checkpoint = capture(source)
    retained, anchor = deepcopy(artifacts), fixture.service.anchor
    shutil.rmtree(root)
    assert not root.exists()
    assert preflight_bundle(raw, source.key, checkpoint, anchor, now=NOW).artifacts == retained
    with pytest.raises(ImportRejected, match='ONLINE_CAPSULE_UNSETTLED_REQUIRES_RECONCILIATION'):
        preflight_online(raw, source.key, checkpoint, anchor, now=NOW)


@pytest.mark.parametrize('table', DATABASE_TABLES)
def test_every_native_database_projection_is_compared_not_just_crl_number(source, table):
    recovered = checked(source)
    index = next(index for index, value in enumerate(TABLES) if value.name == table)
    rows = list(recovered.snapshot.rows)
    rows[index] = ()
    changed = replace(recovered, snapshot=replace(recovered.snapshot, rows=tuple(rows)))
    with pytest.raises(ImportRejected, match='ONLINE_CAPSULE_DATABASE_MISMATCH'):
        inspect_online_inputs(changed, CHECKPOINT, source.fixture.service.anchor, now=NOW)


def test_resealed_valid_database_with_different_grant_refuses(source):
    with sqlite3.connect(':memory:') as database:
        database.deserialize(source.fixture.stores['registry'])
        database.execute('UPDATE restricted_grants SET expires=expires+1 WHERE revoked=0')
        database.commit()
        source.fixture.stores['registry'] = database.serialize()
    update_binding(source)
    with pytest.raises(ImportRejected, match='ONLINE_CAPSULE_DATABASE_MISMATCH'):
        checked(source)


def test_current_issuer_directory_is_bound_to_publication_receipt(source):
    directory = parse(source.artifacts['issuer_material']['directory'])
    directory['seeds'][0]['join_url'] = 'https://telemost.yandex.ru/j/other-synthetic'
    source.artifacts['issuer_material']['directory'] = encoded(directory)
    update_binding(source)
    with pytest.raises(ImportRejected, match='ONLINE_CAPSULE_ISSUER_MISMATCH'):
        checked(source)


def test_evidence_from_another_authority_refuses(source, tmp_path):
    other, artifacts, bounded = online_fixture(tmp_path)
    source.artifacts['maintenance_state'] = artifacts['maintenance_state']
    update_binding(source)
    with pytest.raises(ImportRejected):
        checked(source)


def test_independent_checkpoint_and_current_time_remain_mandatory(source):
    raw, checkpoint = capture(source)
    for changed in (replace(checkpoint, bundle_sha256='0' * 64), replace(checkpoint, snapshot_sha256='0' * 64), None):
        with pytest.raises(ImportRejected):
            recover(source, raw, changed)
    with pytest.raises(ImportRejected):
        preflight_online(raw, source.key, checkpoint, source.fixture.service.anchor, now=NOW + 4000)


def test_preflight_is_read_only_and_has_no_host_or_postgres_calls(source, monkeypatch):
    raw, checkpoint = capture(source)
    connect = sqlite3.connect
    def memory_only(path, *args, **kwargs):
        assert path == ':memory:'
        return connect(path, *args, **kwargs)
    monkeypatch.setattr(sqlite3, 'connect', memory_only)
    monkeypatch.setattr(PostgresEnrollment, 'connect', lambda *args: pytest.fail('No PG I/O in preflight'))
    monkeypatch.setattr('subprocess.run', lambda *args, **kwargs: pytest.fail('No host command in preflight'))
    assert recover(source, raw, checkpoint).summary()['activation'] == 'FORBIDDEN'


def test_retained_capsule_reconstructs_all_journals_without_source_paths(tmp_path):
    root = tmp_path / 'source'
    root.mkdir(mode=0o700)
    fixture, artifacts, bounded = online_fixture(root)
    source = Source(fixture, artifacts, bounded['pending'], secrets.token_bytes(32))
    raw, checkpoint = capture(source)
    anchor, retained = fixture.service.anchor, deepcopy(artifacts)
    source.fixture.service = source.fixture.access = None
    source.artifacts = source.fixture.stores = {}
    shutil.rmtree(root)
    private_file(tmp_path / 'recovery.bundle', raw)
    recovered = preflight_online((tmp_path / 'recovery.bundle').read_bytes(), source.key, checkpoint, anchor, now=NOW)
    assert recovered.artifacts == retained and not root.exists()
    assert (tmp_path / 'recovery.bundle').stat().st_mode & 0o777 == 0o600


@pytest.fixture
def repository():
    if not os.environ.get('FC_HA_PG_PORT'):
        pytest.skip('Run scripts.control_ha_online_rehearsal for real PostgreSQL qualification')
    return PostgresEnrollment(port=int(os.environ['FC_HA_PG_PORT']), schema='ha_enrollment_' + uuid.uuid4().hex,
        password=Path(os.environ['FC_HA_PG_PASSWORD_FILE']).read_text().strip())


def test_atomic_combined_import_and_exact_retry(source, repository):
    recovered = checked(source)
    assert import_snapshot(repository, recovered.snapshot)['result'] == 'IMPORTED'
    assert import_snapshot(repository, recovered.snapshot)['result'] == 'EXACT_RETRY'


def test_receiver_only_receipt_does_not_claim_online_journal_qualification(source, repository):
    raw, checkpoint = capture(source)
    weaker = preflight_receivers(raw, source.key, checkpoint, source.fixture.service.anchor, now=NOW)
    import_snapshot(repository, weaker.snapshot)
    with pytest.raises(ImportRejected, match='TARGET_NOT_SAME_IMPORT'):
        import_snapshot(repository, recover(source, raw, checkpoint).snapshot)


@pytest.mark.parametrize('boundary', ['schema', 'restricted_certificates', 'before_commit', 'after_commit'])
def test_import_fault_and_lost_reply_require_readback_not_blind_replay(source, repository, boundary):
    recovered = checked(source)
    def crash(phase):
        if phase == boundary:
            raise RuntimeError('synthetic-interruption')
    with pytest.raises(ImportRejected, match='IMPORT_OUTCOME_REQUIRES_READBACK'):
        import_snapshot(repository, recovered.snapshot, fault=crash)
    expected = 'EXACT_RETRY' if boundary == 'after_commit' else 'IMPORTED'
    assert import_snapshot(repository, recovered.snapshot)['result'] == expected
