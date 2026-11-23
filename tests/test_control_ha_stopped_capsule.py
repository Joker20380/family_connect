from copy import deepcopy
from dataclasses import replace
import base64
import secrets
import shutil
import sqlite3

import pytest

from scripts.control_ha_import_fixture import CHECKPOINT
from scripts.control_ha_import import TABLES, ImportRejected, digest, encoded, import_snapshot
from scripts.control_ha_online_capsule import DATABASE_TABLES, MAPPING, preflight_online
from scripts.control_ha_recovery_bundle import parse, preflight_bundle
from scripts.control_ha_receiver_v1 import preflight_receivers
from scripts.control_ha_stopped_fixture import stopped_fixture
from scripts.control_ha_stopped_capsule import binding, declaration, inspect_stopped_inputs, preflight_stopped
from scripts.control_ha_maintenance_v1 import PARTS as BOUNDED_PARTS
from scripts.referral_postgres_rehearsal import NOW
from test_control_ha_online_capsule import Source, capture, repository
from test_control_ha_renewal_v1 import OPERATION, change_document, change_file, remove_file


@pytest.fixture(scope='module', params=['stopped', 'offline', 'emergency'])
def stopped_original(tmp_path_factory, request):
    fixture, artifacts, bounded = stopped_fixture(tmp_path_factory.mktemp(request.param), mode=request.param)
    return Source(fixture, artifacts, bounded['pending'], secrets.token_bytes(32)), request.param


@pytest.fixture
def stopped_source(stopped_original):
    original, mode = stopped_original
    return Source(replace(original.fixture, stores=dict(original.fixture.stores)), deepcopy(original.artifacts),
                  deepcopy(original.pending), secrets.token_bytes(32)), mode


def recover(source):
    raw, checkpoint = capture(source)
    return preflight_stopped(raw, source.key, checkpoint, source.fixture.service.anchor, now=NOW)


def test_native_settled_variant_has_exact_current_state(stopped_source):
    source, mode = stopped_source
    recovered = recover(source)
    assert recovered.artifacts == source.artifacts
    assert recovered.summary()['approval_replay'] == 'NOT_AUTHORIZED'
    assert inspect_stopped_inputs(recovered, CHECKPOINT, source.fixture.service.anchor, now=NOW)['mode'] == mode


def parts(source):
    return {name: source.artifacts['maintenance_state'][path] for name, path in MAPPING.items()}


def rebind(source, renewal):
    retained = source.artifacts['maintenance_state']
    retained.update({MAPPING[name]: raw for name, raw in renewal.items()})
    manifest = binding(source.fixture.stores, source.artifacts['issuer_material'], CHECKPOINT,
                       renewal, retained['publication.json'])
    retained['binding.json'] = encoded(manifest)
    for name in BOUNDED_PARTS - {'capture.json'}:
        document = parse(retained[name])
        document['renewal'] = declaration(manifest)
        retained[name] = encoded(document)


def refresh_manifest(renewal, slot, prefix=None):
    prefix = prefix or 'archive/' + OPERATION + '/'
    document = parse(renewal[slot + '.json'])
    manifest_name = 'manifest.json' if prefix.startswith('archive/online-') else 'archive-manifest.json'
    excluded = {manifest_name, 'origin.json', 'owner.json'} if manifest_name == 'manifest.json' else {manifest_name}
    manifest = {name.removeprefix(prefix): digest(base64.b64decode(raw)) for name, raw in document['files'].items()
                if name.startswith(prefix) and name.removeprefix(prefix) not in excluded}
    change_file(renewal, slot, prefix + manifest_name, lambda value: (value.clear(), value.update(manifest)))
    if manifest_name == 'archive-manifest.json':
        change_file(renewal, slot, 'completed.json', lambda value: value[OPERATION].update(manifest_sha256=digest(encoded(manifest))))


@pytest.mark.parametrize('slot', ['RU', 'NL', 'NL2'])
@pytest.mark.parametrize('name', ['plan.json', 'reconciliation.json', 'files.json'])
def test_missing_native_archives_are_not_empty_journals(stopped_source, slot, name):
    source, _ = stopped_source
    renewal = parts(source)
    remove_file(renewal, slot, 'archive/' + OPERATION + '/' + name)
    rebind(source, renewal)
    with pytest.raises(ImportRejected):
        recover(source)


@pytest.mark.parametrize('mutation', ['pending', 'decision', 'gate', 'cohort', 'unknown', 'receipt-time'])
def test_terminal_coordinator_contradictions_refuse(stopped_source, mutation):
    source, _ = stopped_source
    renewal = parts(source)
    def mutate(value):
        if mutation == 'pending': value['state'] = 'CLEANING'
        elif mutation == 'decision': value['commit_decided'] = False
        elif mutation == 'gate': value['gate']['zero_downtime'] = True
        elif mutation == 'cohort': value['acquired'].remove('RU')
        elif mutation == 'unknown': value['assume_safe'] = True
        else: value['timestamp'] = NOW + 1
    change_file(renewal, 'coordinator', 'last-receipt.json' if mutation == 'receipt-time' else 'transaction.json', mutate)
    rebind(source, renewal)
    with pytest.raises(ImportRejected):
        recover(source)


@pytest.mark.parametrize('slot', ['RU', 'NL', 'NL2'])
def test_fenced_rollback_ledger_is_not_completed_commit(stopped_source, slot):
    source, _ = stopped_source
    renewal = parts(source)
    change_file(renewal, slot, 'completed.json', lambda value: value[OPERATION].update(result='CLEANED_FENCED_ROLLBACK'))
    rebind(source, renewal)
    with pytest.raises(ImportRejected, match='STOPPED_LEDGER'):
        recover(source)


@pytest.mark.parametrize('name', ['owner.json', 'archive/../escape', 'services-before.json'])
def test_unknown_pending_or_installed_service_files_refuse(stopped_source, name):
    source, _ = stopped_source
    renewal = parts(source)
    change_document(renewal, 'RU', lambda value: value['files'].update({name: 'e30='}))
    rebind(source, renewal)
    with pytest.raises(ImportRejected):
        recover(source)


@pytest.mark.parametrize('table', DATABASE_TABLES)
def test_current_canonical_projection_must_match(stopped_source, table):
    source, _ = stopped_source
    recovered = recover(source)
    index = next(index for index, item in enumerate(TABLES) if item.name == table)
    rows = list(recovered.snapshot.rows)
    rows[index] = ()
    changed = replace(recovered, snapshot=replace(recovered.snapshot, rows=tuple(rows)))
    with pytest.raises(ImportRejected, match='ONLINE_CAPSULE_DATABASE_MISMATCH'):
        inspect_stopped_inputs(changed, CHECKPOINT, source.fixture.service.anchor, now=NOW)


def test_both_gateway_publications_are_bound_not_only_primary(stopped_source):
    source, _ = stopped_source
    renewal = parts(source)
    publication = parse(source.artifacts['maintenance_state']['publication.json'])
    publication['directories']['NL2'] = publication['directories']['NL']
    source.artifacts['maintenance_state']['publication.json'] = encoded(publication)
    checksum = digest(base64.b64decode(publication['directories']['NL']))
    change_file(renewal, 'RU', 'archive/' + OPERATION + '/directory-accepted.json',
                lambda value: value['directories'].update(NL2=checksum))
    refresh_manifest(renewal, 'RU')
    rebind(source, renewal)
    with pytest.raises(ImportRejected):
        recover(source)


def test_private_key_changes_refuse_even_with_resealed_manifests(stopped_source):
    source, _ = stopped_source
    renewal = parts(source)
    change_file(renewal, 'NL', 'archive/' + OPERATION + '/gateway.json.staged',
                lambda value: value.update(private_key='not-a-key'))
    document = parse(renewal['NL.json'])
    checksum = digest(base64.b64decode(document['files']['archive/' + OPERATION + '/gateway.json.staged']))
    change_file(renewal, 'NL', 'archive/' + OPERATION + '/files.json',
                lambda value: value['gateway.json'].update(after=checksum))
    refresh_manifest(renewal, 'NL')
    rebind(source, renewal)
    with pytest.raises(ImportRejected):
        recover(source)

def test_expired_current_material_is_not_revived(stopped_source):
    source, _ = stopped_source
    raw, checkpoint = capture(source)
    with pytest.raises(ImportRejected):
        preflight_stopped(raw, source.key, checkpoint, source.fixture.service.anchor, now=NOW + 20000)


def test_preflight_is_read_only(stopped_source, monkeypatch):
    source, _ = stopped_source
    raw, checkpoint = capture(source)
    connect = sqlite3.connect
    def memory_only(path, *args, **kwargs):
        assert path == ':memory:'
        return connect(path, *args, **kwargs)
    monkeypatch.setattr(sqlite3, 'connect', memory_only)
    monkeypatch.setattr('subprocess.run', lambda *args, **kwargs: pytest.fail('No host command'))
    monkeypatch.setattr('control.friends.enrollment_postgres.PostgresEnrollment.connect',
                        lambda *args, **kwargs: pytest.fail('No DB writes'))
    assert preflight_stopped(raw, source.key, checkpoint, source.fixture.service.anchor, now=NOW).summary()['activation'] == 'FORBIDDEN'


def test_old_online_gate_cannot_silently_accept_variant(stopped_source):
    source, _ = stopped_source
    raw, checkpoint = capture(source)
    with pytest.raises(ImportRejected):
        preflight_online(raw, source.key, checkpoint, source.fixture.service.anchor, now=NOW)


def test_unsettled_evidence_is_preserved_but_not_imported(stopped_source):
    source, _ = stopped_source
    renewal = parts(source)
    change_file(renewal, 'coordinator', 'transaction.json', lambda value: value.update(state='RECONCILIATION_REQUIRED'))
    rebind(source, renewal)
    raw, checkpoint = capture(source)
    retained = preflight_bundle(raw, source.key, checkpoint, source.fixture.service.anchor, now=NOW)
    assert retained.artifacts == source.artifacts
    with pytest.raises(ImportRejected):
        preflight_stopped(raw, source.key, checkpoint, source.fixture.service.anchor, now=NOW)


@pytest.mark.parametrize('mode,mutation', [('offline', 'request'), ('offline', 'expires'),
    ('emergency', 'owner'), ('emergency', 'origin'), ('emergency', 'handoff'), ('emergency', 'missing'), ('emergency', 'parent-cleanup')])
def test_variant_native_evidence_cannot_be_rebound(tmp_path, mode, mutation):
    fixture, artifacts, bounded = stopped_fixture(tmp_path, mode=mode)
    source = Source(fixture, artifacts, bounded['pending'], secrets.token_bytes(32))
    renewal = parts(source)
    if mode == 'offline':
        def corrupt(value):
            item = value['requests']['NL2']
            if mutation == 'request':
                item['operation_id'] = 'another-operation'
            else:
                item['request_expires_at'] = 0
        change_file(renewal, 'RU', 'archive/' + OPERATION + '/authority-request.json', corrupt)
        refresh_manifest(renewal, 'RU')
    elif mutation == 'handoff':
        change_file(renewal, 'coordinator', 'transaction.json', lambda value: value['handoffs']['NL2'].update(stopped=False))
    elif mutation == 'parent-cleanup':
        change_file(renewal, 'coordinator', 'transaction.json', lambda value: value.update(cleaned=['unknown-node']))
    else:
        prefix = 'archive/online-' + digest(OPERATION.encode()) + '/'
        if mutation == 'missing':
            remove_file(renewal, 'NL2', prefix + 'online-prepared.json')
        elif mutation == 'owner':
            change_file(renewal, 'NL2', prefix + 'owner.json', lambda value: value['expected_state'].update(role='RU'))
        else:
            change_file(renewal, 'NL2', prefix + 'origin.json', lambda value: value.update(decision='ABORT'))
        refresh_manifest(renewal, 'NL2', prefix)
    rebind(source, renewal)
    with pytest.raises(ImportRejected):
        recover(source)


@pytest.mark.parametrize('mode', ['stopped', 'offline', 'emergency'])
def test_actual_sources_removed_before_evidence_recovery(tmp_path, mode):
    original = tmp_path / 'originals'
    original.mkdir(mode=0o700)
    fixture, artifacts, bounded = stopped_fixture(original, mode=mode)
    source = Source(fixture, artifacts, bounded['pending'], secrets.token_bytes(32))
    raw, checkpoint = capture(source)
    anchor, expected = fixture.service.anchor, deepcopy(artifacts)
    source.fixture.service = source.fixture.access = None
    source.artifacts = source.fixture.stores = {}
    shutil.rmtree(original)
    recovered = preflight_stopped(raw, source.key, checkpoint, anchor, now=NOW)
    assert recovered.artifacts == expected and not original.exists()


@pytest.mark.parametrize('boundary', ['ONLINE_COMMIT_DECIDED', 'ONLINE_NL2_PUBLISHED'])
def test_emergency_parent_publication_boundaries(tmp_path, boundary):
    fixture, artifacts, bounded = stopped_fixture(tmp_path, mode='emergency', emergency_boundary=boundary)
    source = Source(fixture, artifacts, bounded['pending'], secrets.token_bytes(32))
    assert recover(source).summary()['approval_replay'] == 'NOT_AUTHORIZED'


@pytest.mark.parametrize('boundary', ['schema', 'restricted_certificates', 'before_commit', 'after_commit'])
def test_pg_crash_and_lost_reply(stopped_source, repository, boundary):
    source, _ = stopped_source
    recovered = recover(source)
    def crash(phase):
        if phase == boundary:
            raise RuntimeError('synthetic-interruption')
    with pytest.raises(ImportRejected, match='IMPORT_OUTCOME_REQUIRES_READBACK'):
        import_snapshot(repository, recovered.snapshot, fault=crash)
    assert import_snapshot(repository, recovered.snapshot)['result'] == ('EXACT_RETRY' if boundary == 'after_commit' else 'IMPORTED')


def test_weaker_import_receipt_cannot_promote_to_stopped(stopped_source, repository):
    source, _ = stopped_source
    raw, checkpoint = capture(source)
    weaker = preflight_receivers(raw, source.key, checkpoint, source.fixture.service.anchor, now=NOW)
    assert import_snapshot(repository, weaker.snapshot)['result'] == 'IMPORTED'
    with pytest.raises(ImportRejected):
        import_snapshot(repository, recover(source).snapshot)
