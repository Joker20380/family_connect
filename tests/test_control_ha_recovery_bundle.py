from dataclasses import replace
import json
import os
from pathlib import Path
import secrets
import sqlite3
import uuid

import pytest
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from control.friends.enrollment_postgres import PostgresEnrollment
from scripts import control_ha_recovery_bundle as bundle_api
from scripts.control_ha_bundle_fixture import artifacts_for, reconstruct, OPAQUE_PROBES
from scripts.control_ha_import import ImportRejected, digest, encoded, import_snapshot
from scripts.control_ha_import_fixture import CHECKPOINT
from scripts.control_ha_sqlite_fixture import joint_fixture, exercise_import
from scripts.referral_postgres_rehearsal import NOW


@pytest.fixture
def source(tmp_path):
    root = tmp_path / 'source'
    root.mkdir(mode=0o700)
    fixture = joint_fixture(root)
    return fixture, artifacts_for(fixture), secrets.token_bytes(32)


def capture(source):
    fixture, artifacts, key = source
    return bundle_api.seal(fixture.stores, fixture.external, artifacts, CHECKPOINT,
                           fixture.bootstrap, fixture.service.anchor, key, now=NOW)


def recover(source, raw, checkpoint, *, now=NOW):
    fixture, artifacts, key = source
    return bundle_api.preflight_bundle(raw, key, checkpoint, fixture.service.anchor, now=now)


def rewrite(source, raw, checkpoint, change):
    key = source[2]
    offset = len(bundle_api.MAGIC)
    nonce = raw[offset:offset + 12]
    associated = bundle_api.MAGIC + bundle_api.PURPOSE.encode()
    document = json.loads(AESGCM(key).decrypt(nonce, raw[offset + 12:], associated))
    change(document)
    changed = bundle_api.MAGIC + nonce + AESGCM(key).encrypt(nonce, encoded(document), associated)
    return changed, replace(checkpoint, bundle_sha256=digest(changed))


def test_round_trip_preserves_exact_private_bytes_and_provenance(source):
    raw, checkpoint = capture(source)
    recovered = recover(source, raw, checkpoint)
    fixture, artifacts, key = source
    assert recovered.stores == fixture.stores
    assert recovered.artifacts == artifacts
    assert recovered.references == fixture.external
    assert recovered.bootstrap == fixture.bootstrap
    assert recovered.snapshot.fingerprint == checkpoint.snapshot_sha256
    assert b'SQLite format' not in raw and key not in raw
    assert artifacts['issuer_material']['runtime-key'] not in raw
    assert artifacts['issuer_material']['referral-secret'] not in raw
    assert 'runtime-key' not in repr(recovered) and 'runtime-key' not in json.dumps(recovered.summary())
    assert recovered.summary()['activation'] == 'FORBIDDEN'
    assert set(recovered.summary()['exact_bytes_only']) == bundle_api.EXTERNAL_ROLES - {'issuer_material'}
    assert len(OPAQUE_PROBES) == 4


def test_sealing_uses_fresh_nonce_but_stable_input_fingerprint(source):
    first, first_checkpoint = capture(source)
    second, second_checkpoint = capture(source)
    assert first != second
    assert first_checkpoint.snapshot_sha256 == second_checkpoint.snapshot_sha256
    with pytest.raises(ImportRejected, match='CHECKPOINT_MISMATCH'):
        recover(source, first, second_checkpoint)


def test_preflight_does_not_open_writable_databases(source, monkeypatch):
    raw, expected = capture(source)
    connect = sqlite3.connect
    def memory_only(path, *args, **kwargs):
        assert path == ':memory:'
        return connect(path, *args, **kwargs)
    monkeypatch.setattr(sqlite3, 'connect', memory_only)
    monkeypatch.setattr(PostgresEnrollment, 'connect', lambda *args: pytest.fail('No PostgreSQL I/O in dry run'))
    assert recover(source, raw, expected).summary()['activation'] == 'FORBIDDEN'


@pytest.mark.parametrize('kind', ['key', 'anchor', 'checkpoint', 'snapshot', 'missing-checkpoint',
                                  'changed', 'truncated', 'appended', 'format', 'expired'])
def test_wrong_or_stale_inputs_fail_closed(source, kind):
    raw, expected = capture(source)
    key, anchor, now = source[2], source[0].service.anchor, NOW
    if kind == 'key':
        key = secrets.token_bytes(32)
    elif kind == 'anchor':
        anchor = secrets.token_bytes(32)
    elif kind == 'checkpoint':
        expected = replace(expected, checkpoint='f' * 32)
    elif kind == 'snapshot':
        expected = replace(expected, snapshot_sha256='f' * 64)
    elif kind == 'missing-checkpoint':
        expected = None
    elif kind == 'changed':
        raw = raw[:-1] + bytes([raw[-1] ^ 1])
    elif kind == 'truncated':
        raw = raw[:-1]
    elif kind == 'appended':
        raw += b'\x00'
    elif kind == 'format':
        raw = b'unknown' + raw
    elif kind == 'expired':
        now += 86400
    with pytest.raises(ImportRejected):
        bundle_api.preflight_bundle(raw, key, expected, anchor, now=now)


def test_hash_repin_does_not_bypass_aead(source):
    raw, expected = capture(source)
    raw = raw[:-1] + bytes([raw[-1] ^ 1])
    with pytest.raises(ImportRejected, match='AUTHENTICATION_FAILED'):
        recover(source, raw, replace(expected, bundle_sha256=digest(raw)))


@pytest.mark.parametrize('role', sorted(bundle_api.EXTERNAL_ROLES))
@pytest.mark.parametrize('missing', [True, False])
def test_missing_and_empty_roles_refuse_at_capture_and_preflight(source, role, missing):
    raw, expected = capture(source)
    def change(document):
        if missing:
            del document['artifacts'][role]
        else:
            document['artifacts'][role] = {}
    changed, repinned = rewrite(source, raw, expected, change)
    with pytest.raises(ImportRejected, match='ROLE_COVERAGE|EMPTY_ROLE'):
        recover(source, changed, repinned)
    change(dict(artifacts=source[1]))
    with pytest.raises(ImportRejected, match='ROLE_COVERAGE|EMPTY_ROLE'):
        capture(source)


@pytest.mark.parametrize('name', ['../key', '/absolute', 'a/b', 'a\\b', '..', 'a..b', '', 'x' * 97])
def test_artifact_names_cannot_be_paths(source, name):
    source[1]['admission'] = {name: b'synthetic'}
    with pytest.raises(ImportRejected, match='ARTIFACT_NAME'):
        capture(source)


@pytest.mark.parametrize('part', sorted(bundle_api.ISSUER_PARTS))
def test_wrong_issuer_or_referral_material_refuses(source, part):
    source[1]['issuer_material'][part] = secrets.token_bytes(32)
    with pytest.raises(ImportRejected):
        capture(source)


@pytest.mark.parametrize('kind', ['version', 'purpose', 'extra', 'stores', 'references', 'base64', 'mixed-store'])
def test_authenticated_but_invalid_documents_refuse(source, kind):
    raw, expected = capture(source)
    def change(document):
        if kind == 'version':
            document['version'] = True
        elif kind == 'purpose':
            document['purpose'] = 'production'
        elif kind == 'extra':
            document['unexpected'] = 'private-canary'
        elif kind == 'stores':
            del document['stores']['notices']
        elif kind == 'references':
            del document['references']['aliases']
        elif kind == 'base64':
            document['bootstrap'] = 'bad encoding!'
        elif kind == 'mixed-store':
            document['stores']['notices'] = document['stores']['metadata']
    changed, repinned = rewrite(source, raw, expected, change)
    with pytest.raises(ImportRejected) as failure:
        recover(source, changed, repinned)
    assert 'private-canary' not in str(failure.value)


@pytest.mark.parametrize('limit', ['MAX_ARTIFACT', 'MAX_ARTIFACTS', 'MAX_PLAINTEXT'])
def test_capture_and_read_limits(source, monkeypatch, limit):
    raw, expected = capture(source)
    monkeypatch.setattr(bundle_api, limit, 1)
    with pytest.raises(ImportRejected):
        capture(source)
    with pytest.raises(ImportRejected):
        recover(source, raw, expected)


@pytest.mark.parametrize('raw', [b'{"secret":1,"secret":2}', b'{"secret":NaN}', b'\xff', b'[' * 2000])
def test_invalid_json_errors_are_sanitized(raw):
    with pytest.raises(ImportRejected, match='^BUNDLE_DOCUMENT_INVALID$'):
        bundle_api.parse(raw)


def test_opaque_artifact_drift_changes_snapshot_even_with_same_db(source):
    raw, expected = capture(source)
    source[1]['receiver_state']['opaque-probe'] += b'new synthetic floor'
    newer, current = capture(source)
    assert current.snapshot_sha256 != expected.snapshot_sha256
    with pytest.raises(ImportRejected, match='CHECKPOINT_MISMATCH'):
        recover(source, raw, current)
    assert recover(source, newer, current).stores == source[0].stores


@pytest.fixture
def repository():
    if not os.environ.get('FC_HA_PG_PORT'):
        pytest.skip('Run scripts.control_ha_bundle_rehearsal for real PostgreSQL qualification')
    return PostgresEnrollment(port=int(os.environ['FC_HA_PG_PORT']), schema='ha_enrollment_' + uuid.uuid4().hex,
        password=Path(os.environ['FC_HA_PG_PASSWORD_FILE']).read_text().strip())


def test_fresh_authority_objects_continue_after_import(source, repository, tmp_path):
    raw, expected = capture(source)
    recovered = recover(source, raw, expected)
    fixture = source[0]
    anchor = fixture.service.anchor
    fixture.service, fixture.access, fixture.referral_secret = None, None, b''
    fixture.paths, fixture.pending['routing'] = {}, None
    import_snapshot(repository, recovered.snapshot)
    restored = reconstruct(fixture, recovered, anchor, tmp_path / 'recovered')
    assert all(exercise_import(restored, repository).values())


def test_changed_external_bytes_cannot_reimport_over_same_db(source, repository):
    raw, expected = capture(source)
    original = recover(source, raw, expected)
    import_snapshot(repository, original.snapshot)
    source[1]['receiver_state']['opaque-probe'] += b'changed'
    changed, current = capture(source)
    with pytest.raises(ImportRejected, match='TARGET_NOT_SAME_IMPORT'):
        import_snapshot(repository, recover(source, changed, current).snapshot)
    assert import_snapshot(repository, original.snapshot)['result'] == 'EXACT_RETRY'
