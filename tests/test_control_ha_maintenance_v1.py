import base64
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import hmac
import os
from pathlib import Path
import secrets
import sqlite3
import uuid
from types import SimpleNamespace

import pytest

from control.friends.enrollment_postgres import PostgresEnrollment
from scripts.control_ha_import import ImportRejected, encoded, import_snapshot
from scripts.control_ha_import_fixture import CHECKPOINT
from scripts.control_ha_maintenance_fixture import artifacts_for_maintenance, packed, retain_evidence
from scripts import control_ha_maintenance_fixture as native_fixture
from scripts.control_ha_maintenance_v1 import PARTS, inspect_maintenance, preflight_maintenance
from scripts.control_ha_receiver_v1 import preflight_receivers
from scripts.control_ha_recovery_bundle import parse, seal
from scripts.control_ha_sqlite_fixture import joint_fixture
from scripts.control_ha_sqlite_import import MANIFEST
from scripts.referral_postgres_rehearsal import NOW


@dataclass(repr=False)
class Source:
    fixture: object
    artifacts: dict
    pending: dict
    behavior: dict
    key: bytes


@pytest.fixture(scope='module')
def original(tmp_path_factory):
    fixture = joint_fixture(tmp_path_factory.mktemp('maintenance-source'))
    artifacts, capture = artifacts_for_maintenance(fixture)
    return Source(fixture, artifacts, capture['pending'], capture['behavior'], secrets.token_bytes(32))


@pytest.fixture
def source(original):
    return Source(original.fixture, deepcopy(original.artifacts), deepcopy(original.pending),
                  deepcopy(original.behavior), secrets.token_bytes(32))


def capture(source):
    fixture = source.fixture
    return seal(fixture.stores, fixture.external, source.artifacts, CHECKPOINT, fixture.bootstrap,
                fixture.service.anchor, source.key, now=NOW)


def recover(source, bundle, checkpoint, *, now=NOW):
    return preflight_maintenance(bundle, source.key, checkpoint, source.fixture.service.anchor, now=now)


def checked(source):
    return recover(source, *capture(source))


def node(source):
    return parse(source.artifacts['maintenance_state']['gateway-ru.json'])


def save_node(source, value):
    source.artifacts['maintenance_state']['gateway-ru.json'] = encoded(value)


def operation(value):
    return next(iter(value['operations'].values()))


def journal(value):
    return parse(base64.b64decode(operation(value)['journal.json']))['journal']


def save_journal(value, record):
    key = base64.b64decode(value['files']['journal-key'])
    operation(value)['journal.json'] = packed(encoded(dict(journal=record,
        mac=hmac.new(key, encoded(record), hashlib.sha256).hexdigest())))


def test_native_capture_and_exact_private_evidence(source, tmp_path):
    recovered = checked(source)
    summary = recovered.summary()
    assert summary['artifacts'] == 38 and summary['maintenance_nodes'] == 3
    assert summary['activation'] == 'FORBIDDEN' and summary['exact_bytes_only'] == []
    assert summary['full_external_recovery'] == 'NOT_QUALIFIED'
    assert all(source.behavior.values()) and source.behavior['relocated_operations_refused']
    root = tmp_path / 'evidence'
    receipt = retain_evidence(recovered, root)
    assert receipt['exact_private_evidence'] and not receipt['native_activation']
    assert receipt['states'] == {'COMMITTED': 3}
    assert root.stat().st_mode & 0o777 == 0o700
    assert all(item.stat().st_mode & 0o777 == 0o600 for item in root.iterdir())


def test_expired_permit_does_not_refresh_archived_profile_or_journal(source):
    bundle, checkpoint = capture(source)
    recovered = recover(source, bundle, checkpoint, now=NOW + 301)
    assert recovered.artifacts['maintenance_state'] == source.artifacts['maintenance_state']
    assert journal(node(source))['applied_at'] == NOW


def test_readonly_preflight_no_host_metadata_or_pg_io(source, monkeypatch):
    bundle, checkpoint = capture(source)
    connect = sqlite3.connect
    def memory_only(database, *args, **kwargs):
        assert database == ':memory:'
        return connect(database, *args, **kwargs)
    monkeypatch.setattr(sqlite3, 'connect', memory_only)
    monkeypatch.setattr(PostgresEnrollment, 'connect', lambda *args: pytest.fail('No PostgreSQL preflight writes'))
    read_bytes = Path.read_bytes
    def only_schema_manifest(path):
        assert path == MANIFEST
        return read_bytes(path)
    monkeypatch.setattr(Path, 'read_bytes', only_schema_manifest)
    recover(source, bundle, checkpoint)


@pytest.mark.parametrize('part', sorted(PARTS))
def test_all_three_nodes_and_capture_are_mandatory(source, part):
    del source.artifacts['maintenance_state'][part]
    with pytest.raises(ImportRejected, match='MAINTENANCE_PARTS'):
        checked(source)


@pytest.mark.parametrize('kind', ['opaque', 'extra', 'schema', 'purpose', 'future', 'nodes', 'duplicate', 'nonfinite'])
def test_strict_capture_format(source, kind):
    parts = source.artifacts['maintenance_state']
    value = parse(parts['capture.json'])
    if kind == 'opaque':
        source.artifacts['maintenance_state'] = {'opaque-probe': b'private-canary'}
    elif kind == 'extra':
        parts['extra'] = b'private-canary'
    elif kind == 'schema':
        value['schema'] = True
    elif kind == 'purpose':
        value['purpose'] = 'live-attested'
    elif kind == 'future':
        value['captured_at'] = NOW + 1
    elif kind == 'nodes':
        value['nodes'].pop()
    elif kind == 'duplicate':
        parts['capture.json'] = parts['capture.json'].replace(b'"schema":1', b'"schema":1,"schema":1')
    else:
        parts['capture.json'] = parts['capture.json'].replace(str(NOW).encode(), b'1e999')
    if kind not in ('duplicate', 'nonfinite'):
        parts['capture.json'] = encoded(value)
    with pytest.raises(ImportRejected) as failure:
        checked(source)
    assert 'private-canary' not in str(failure.value)


@pytest.mark.parametrize('kind', ['schema', 'node', 'unknown', 'empty', 'multiple', 'coordinator', 'online', 'legacy'])
def test_unknown_variants_and_missing_operations_never_mean_empty(source, kind):
    value = node(source)
    if kind == 'schema':
        value['schema'] = True
    elif kind == 'node':
        value['node'] = 'nl-amsterdam-1'
    elif kind == 'unknown':
        value['unknown'] = 'private-canary'
    elif kind == 'empty':
        value['operations'] = {}
    elif kind == 'multiple':
        value['operations']['restricted_maintenance_' + 'f' * 32] = deepcopy(operation(value))
    elif kind == 'coordinator':
        value['renewal']['coordinator'].append({'state': 'COMMITTED'})
    elif kind == 'online':
        value['renewal']['node'].append({'state': 'ONLINE_ACQUIRED'})
    else:
        value['contract']['schema'] = 1
    save_node(source, value)
    with pytest.raises(ImportRejected):
        checked(source)


@pytest.mark.parametrize('kind', ['path', 'double-root', 'parent', 'owner', 'publisher', 'lock', 'inode', 'contract', 'duplicate-node'])
def test_paths_ownership_and_exact_contracts(source, kind):
    value = node(source)
    if kind == 'path':
        value['locator']['profile'] = '/lab/../private-canary'
    elif kind == 'double-root':
        value['locator']['profile'] = '//lab/private-canary'
    elif kind == 'parent':
        next(iter(value['metadata']['parents'].values()))['/'][2] = 1000
    elif kind == 'owner':
        value['locator']['reader_gid'] = 0
    elif kind == 'publisher':
        value['locator']['directory']['metadata']['uid'] = 0
    elif kind == 'lock':
        value['files']['lock'] = packed(b'changed-lock')
    elif kind == 'inode':
        value['metadata']['operations_inode'] += 1
    elif kind == 'contract':
        value['files']['publisher'] = packed(b'changed-publisher')
    else:
        value = parse(source.artifacts['maintenance_state']['nl-amsterdam-1.json'])
        value['node'] = 'gateway-ru'
    save_node(source, value)
    with pytest.raises(ImportRejected):
        checked(source)


@pytest.mark.parametrize('name', ['profile', 'directory', 'journal-key', 'lock', 'publisher'])
def test_missing_private_material_is_refused(source, name):
    value = node(source)
    del value['files'][name]
    save_node(source, value)
    with pytest.raises(ImportRejected, match='MAINTENANCE_FILES'):
        checked(source)


@pytest.mark.parametrize('name', ['permit.json', 'request.json', 'journal.json', 'before-profile.json',
                                  'before-directory.json', 'target-profile.json', 'response.json'])
def test_missing_operation_evidence_is_refused(source, name):
    value = node(source)
    del operation(value)[name]
    save_node(source, value)
    with pytest.raises(ImportRejected):
        checked(source)


@pytest.mark.parametrize('kind', ['key', 'mac', 'unbound-state'])
def test_authentication_is_required_even_with_new_bundle_checkpoint(source, kind):
    value = node(source)
    envelope = parse(base64.b64decode(operation(value)['journal.json']))
    if kind == 'key':
        value['files']['journal-key'] = packed(secrets.token_bytes(32))
    elif kind == 'mac':
        envelope['mac'] = 'f' * 64
    else:
        envelope['journal']['state'] = 'UNKNOWN'
    operation(value)['journal.json'] = packed(encoded(envelope))
    save_node(source, value)
    with pytest.raises(ImportRejected, match='MAINTENANCE_MAC'):
        checked(source)


@pytest.mark.parametrize('field,value', [('schema', True), ('state', 'FORGOTTEN'), ('attempt_count', 2),
    ('attempt_count', True), ('committed_write', False), ('replace_started', False), ('applied_at', NOW + 1),
    ('target_minimum_crl', 0), ('target_crl_number', True), ('configuration_sha256', '0' * 64),
    ('request_sha256', '0' * 64), ('before_profile_sha256', '0' * 64), ('directory_checkpoint', None),
    ('material_metadata', {})])
def test_authenticated_journal_still_requires_semantic_consistency(source, field, value):
    document = node(source)
    record = journal(document)
    record[field] = value
    save_journal(document, record)
    save_node(source, document)
    with pytest.raises(ImportRejected):
        checked(source)


@pytest.mark.parametrize('state', ['PREPARED', 'APPLYING', 'UNKNOWN', 'CONFLICT', 'ROLLED_BACK'])
def test_unsettled_evidence_can_be_authenticated_but_never_imported(source, state, monkeypatch):
    source.artifacts['maintenance_state'] = source.pending
    value = node(source)
    record = journal(value)
    record.update(state=state, attempt_count=0 if state == 'PREPARED' else 1,
                  replace_started=state not in ('PREPARED', 'CONFLICT'))
    save_journal(value, record)
    save_node(source, value)
    parts = deepcopy(source.artifacts['maintenance_state'])
    receipt = inspect_maintenance(parts, source.artifacts['issuer_material'], now=NOW)
    assert receipt['states'][state] == 1 and not receipt['settled']
    monkeypatch.setattr(PostgresEnrollment, 'connect', lambda *args: pytest.fail('Unsettled state reached PostgreSQL'))
    with pytest.raises(ImportRejected, match='MAINTENANCE_UNSETTLED_REQUIRES_RECONCILIATION'):
        checked(source)
    assert source.artifacts['maintenance_state'] == parts


@pytest.mark.parametrize('kind', ['key', 'certificate', 'floor', 'response', 'directory'])
def test_current_profile_and_response_cannot_be_reconstructed_from_rows(source, kind):
    value = node(source)
    current = parse(base64.b64decode(value['files']['profile']))
    if kind in ('key', 'certificate'):
        current['private_key' if kind == 'key' else 'certificate'] = 'private-canary'
    elif kind == 'floor':
        current['minimum_crl'] = 0
    elif kind == 'response':
        operation(value)['response.json'] = packed(encoded(dict(schema=1, result='PASS')))
    else:
        value['files']['directory'] = packed(b'private-canary')
    value['files']['profile'] = packed(encoded(current))
    save_node(source, value)
    with pytest.raises(ImportRejected) as failure:
        checked(source)
    assert 'private-canary' not in str(failure.value)


def test_pending_exact_crl_retains_older_before_profile_without_import(source):
    parts = source.artifacts['maintenance_state']
    value = parse(parts['nl-amsterdam-1.json'])
    record = journal(value)
    record.update(state='PREPARED', attempt_count=0, replace_started=False, committed_write=False, applied_at=None)
    value['files']['profile'] = operation(value)['before-profile.json']
    del operation(value)['response.json']
    save_journal(value, record)
    parts['nl-amsterdam-1.json'] = encoded(value)
    receipt = inspect_maintenance(parts, source.artifacts['issuer_material'], now=NOW)
    assert not receipt['settled'] and receipt['states'] == {'COMMITTED': 2, 'PREPARED': 1}
    with pytest.raises(ImportRejected, match='MAINTENANCE_UNSETTLED_REQUIRES_RECONCILIATION'):
        checked(source)


@pytest.mark.parametrize('kind', ['private-exclusion', 'symlink', 'traversal'])
def test_root_child_receives_only_selected_source_not_checkout_state(tmp_path, monkeypatch, kind):
    root = tmp_path / 'checkout'
    root.mkdir()
    source_files = ['scripts/control_ha_maintenance_fixture.py', 'scripts/control_ha_maintenance_v1.py',
                    'deploy/control-ha/rehearsal-maintenance.json']
    for name in source_files:
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b'source-only')
    (root / 'private.key').write_bytes(b'private-canary')
    selected = 'scripts/control_ha_maintenance_v1.py'
    if kind == 'symlink':
        (root / selected).unlink()
        (root / selected).symlink_to(root / 'private.key')
    elif kind == 'traversal':
        selected = '../private.py'
    monkeypatch.setattr(native_fixture, 'ROOT', root)
    monkeypatch.setattr(native_fixture.subprocess, 'run', lambda *args, **kwargs:
                        SimpleNamespace(stdout=selected.encode() + b'\x00'))
    destination = tmp_path / 'snapshot'
    destination.mkdir()
    if kind == 'private-exclusion':
        native_fixture.source_snapshot(destination)
        assert sorted(str(item.relative_to(destination)) for item in destination.rglob('*') if item.is_file()) == sorted(source_files)
        assert not (destination / 'private.key').exists()
    else:
        with pytest.raises(ValueError, match='ROOT_FIXTURE_UNSAFE_SOURCE'):
            native_fixture.source_snapshot(destination)


@pytest.fixture
def repository():
    if not os.environ.get('FC_HA_PG_PORT'):
        pytest.skip('Run scripts.control_ha_maintenance_rehearsal for real PostgreSQL qualification')
    return PostgresEnrollment(port=int(os.environ['FC_HA_PG_PORT']), schema='ha_enrollment_' + uuid.uuid4().hex,
        password=Path(os.environ['FC_HA_PG_PASSWORD_FILE']).read_text().strip())


def test_maintenance_import_and_exact_retry(source, repository):
    recovered = checked(source)
    assert import_snapshot(repository, recovered.snapshot)['result'] == 'IMPORTED'
    assert import_snapshot(repository, recovered.snapshot)['result'] == 'EXACT_RETRY'


def test_receiver_receipt_cannot_claim_maintenance_qualification(source, repository):
    bundle, checkpoint = capture(source)
    previous = preflight_receivers(bundle, source.key, checkpoint, source.fixture.service.anchor, now=NOW)
    import_snapshot(repository, previous.snapshot)
    with pytest.raises(ImportRejected, match='TARGET_NOT_SAME_IMPORT'):
        import_snapshot(repository, recover(source, bundle, checkpoint).snapshot)


def test_old_trusted_checkpoint_and_import_reject_replaced_journal(source, repository):
    bundle, checkpoint = capture(source)
    accepted = recover(source, bundle, checkpoint)
    import_snapshot(repository, accepted.snapshot)
    value = node(source)
    record = journal(value)
    record['state'] = 'IDEMPOTENT'
    response = parse(base64.b64decode(operation(value)['response.json']))
    response['result'] = 'IDEMPOTENT'
    operation(value)['response.json'] = packed(encoded(response))
    save_journal(value, record)
    save_node(source, value)
    changed_bundle, changed_checkpoint = capture(source)
    with pytest.raises(ImportRejected):
        recover(source, changed_bundle, checkpoint)
    changed = recover(source, changed_bundle, changed_checkpoint)
    with pytest.raises(ImportRejected, match='TARGET_NOT_SAME_IMPORT'):
        import_snapshot(repository, changed.snapshot)
    assert import_snapshot(repository, accepted.snapshot)['result'] == 'EXACT_RETRY'
