from contextlib import closing
import io
import os
import sqlite3
import tarfile

import pytest
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from scripts import control_ha_live_sqlite as live
from scripts import control_ha_live_sqlite_restore as recovery
from scripts.control_ha_handoff_fixture import closed_handoff_fixture


def seal(plaintext):
    key, nonce = AESGCM.generate_key(bit_length=256), os.urandom(12)
    capsule = recovery.MAGIC + nonce + AESGCM(key).encrypt(nonce, plaintext, recovery.AAD)
    checkpoint = dict(source_commit='1' * 40, source_sha256='2' * 64,
                      ciphertext_sha256=recovery.digest(capsule), archive_sha256=recovery.digest(plaintext))
    return capsule, key, checkpoint


@pytest.fixture
def fixture(tmp_path):
    root = tmp_path / 'source'
    root.mkdir(mode=0o700)
    source = closed_handoff_fixture(root)
    with closing(sqlite3.connect(':memory:')) as database:
        database.deserialize(source.stores['metadata'])
        source.stores['metadata'] = live.metadata_image(database)
    records = {}
    for name, raw in source.stores.items():
        with closing(sqlite3.connect(':memory:')) as database:
            database.deserialize(raw)
            count = database.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchone()[0]
        records[name] = dict(bytes=len(raw), sha256=recovery.digest(raw), tables=count)
    manifest = dict(purpose=live.PURPOSE, common_locked_at_ns=1, captured_at_ns=2,
                    barrier_seconds=.01, deadline_seconds=1.0, stores=records,
                    external_files_captured=False, fleet_barrier=False, full_recovery=False)
    manifest['metadata_projection'] = 'consent-floors-only'
    return source.stores, manifest


def test_independent_restoration_is_exact_and_private(fixture, tmp_path):
    images, manifest = fixture
    args = seal(live.archive(images, manifest))
    target = tmp_path / 'restored'
    result = recovery.restore(*args, target)
    assert result['tables'] == 34 and result['stores'] == 4
    assert result['retained_handoff_rows'] == [1, 2, 1, 1, 1]
    assert not result['full_recovery'] and result['activation'] == 'FORBIDDEN'
    for name, raw in images.items():
        path = target / (name + '.sqlite')
        assert path.read_bytes() == raw
        assert path.stat().st_mode & 0o777 == 0o600
    with pytest.raises(FileExistsError):
        recovery.restore(*args, target)


@pytest.mark.parametrize('fault', ['tampered', 'key', 'stale', 'archive-pin', 'source-pin', 'scope', 'hash', 'tables', 'deadline'])
def test_untrusted_or_mismatched_capture_never_creates_output(fixture, tmp_path, fault):
    images, manifest = fixture
    if fault == 'scope':
        manifest['full_recovery'] = True
    elif fault == 'hash':
        manifest['stores']['registry']['sha256'] = '0' * 64
    elif fault == 'tables':
        manifest['stores']['registry']['tables'] += 1
    elif fault == 'deadline':
        manifest['barrier_seconds'] = 5
    capsule, key, checkpoint = seal(live.archive(images, manifest))
    if fault == 'tampered':
        capsule = capsule[:-1] + bytes([capsule[-1] ^ 1])
    elif fault == 'key':
        key = bytes(32)
    elif fault == 'stale':
        checkpoint['ciphertext_sha256'] = '0' * 64
    elif fault == 'archive-pin':
        checkpoint['archive_sha256'] = '0' * 64
    elif fault == 'source-pin':
        checkpoint['source_sha256'] = 'invalid'
    target = tmp_path / 'restored'
    with pytest.raises(ValueError):
        recovery.restore(capsule, key, checkpoint, target)
    assert not target.exists()


@pytest.mark.parametrize('fault', ['extra', 'duplicate', 'symlink', 'traversal'])
def test_archive_is_not_extracted_with_untrusted_paths(fixture, tmp_path, fault):
    images, manifest = fixture
    output = io.BytesIO(live.archive(images, manifest))
    with tarfile.open(fileobj=output, mode='a') as archive:
        entry = tarfile.TarInfo('registry.sqlite' if fault == 'duplicate' else '../escape' if fault == 'traversal' else 'extra')
        if fault == 'symlink':
            entry.type, entry.linkname = tarfile.SYMTYPE, '/etc/passwd'
        archive.addfile(entry)
    with pytest.raises(ValueError):
        recovery.restore(*seal(output.getvalue()), tmp_path / 'restored')
    assert not (tmp_path / 'restored').exists()


def test_unknown_schema_refuses_before_writing(fixture, tmp_path):
    images, manifest = fixture
    with closing(sqlite3.connect(':memory:')) as database:
        database.deserialize(images['registry'])
        database.execute('CREATE TABLE unknown(value TEXT)')
        images['registry'] = database.serialize()
    manifest['stores']['registry'].update(bytes=len(images['registry']), sha256=recovery.digest(images['registry']))
    with pytest.raises(ValueError, match='SOURCE_SCHEMA_UNSUPPORTED'):
        recovery.restore(*seal(live.archive(images, manifest)), tmp_path / 'restored')


def test_authenticated_capsule_cannot_reintroduce_metadata_observations(fixture, tmp_path):
    images, manifest = fixture
    with closing(sqlite3.connect(':memory:')) as database:
        database.deserialize(images['metadata'])
        database.execute("UPDATE device_metadata SET payload=?", ('{"private":"observation"}',))
        database.commit()
        images['metadata'] = database.serialize()
    manifest['stores']['metadata'].update(bytes=len(images['metadata']), sha256=recovery.digest(images['metadata']))
    with pytest.raises(ValueError, match='METADATA_OBSERVATIONS_FORBIDDEN'):
        recovery.restore(*seal(live.archive(images, manifest)), tmp_path / 'restored')


def test_public_parent_refuses_private_restore(fixture, tmp_path):
    images, manifest = fixture
    parent = tmp_path / 'public'
    parent.mkdir(mode=0o755)
    parent.chmod(0o755)
    with pytest.raises(ValueError, match='PRIVATE_PARENT_REQUIRED'):
        recovery.restore(*seal(live.archive(images, manifest)), parent / 'restored')


@pytest.mark.parametrize('fault', ['mode', 'symlink', 'hardlink', 'size'])
def test_private_inputs_reject_unsafe_metadata(tmp_path, fault):
    path = tmp_path / 'key'
    path.write_bytes(bytes(32))
    path.chmod(0o600)
    if fault == 'mode':
        path.chmod(0o644)
    elif fault == 'symlink':
        link = tmp_path / 'link'
        link.symlink_to(path)
        path = link
    elif fault == 'hardlink':
        (tmp_path / 'link').hardlink_to(path)
    with pytest.raises(ValueError):
        recovery.private_read(path, 31 if fault == 'size' else 32)
