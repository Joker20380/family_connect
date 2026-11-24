import base64
from dataclasses import replace
import secrets

import pytest
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from scripts import control_ha_recovery_bundle as recovery
from scripts.control_ha_bundle_fixture import artifacts_for
from scripts.control_ha_handoff_fixture import closed_handoff_fixture
from scripts.control_ha_import import ImportRejected, digest, encoded
from scripts.control_ha_import_fixture import CHECKPOINT
from scripts.control_ha_sqlite_fixture import joint_fixture
from scripts.referral_postgres_rehearsal import NOW
from test_control_ha_handoff_import import mutate


@pytest.fixture
def source(tmp_path):
    fixture = closed_handoff_fixture(tmp_path)
    return fixture, artifacts_for(fixture), secrets.token_bytes(32)


def capture(source, sealer=recovery.seal_handoff):
    fixture, artifacts, key = source
    return sealer(fixture.stores, fixture.external, artifacts, CHECKPOINT,
                  fixture.bootstrap, fixture.service.anchor, key, now=NOW)


def recover(source, bundle, checkpoint, **overrides):
    arguments = dict(key=source[2], expected=checkpoint, anchor=source[0].service.anchor, now=NOW)
    return recovery.preflight_bundle(bundle, **(arguments | overrides))


def rewrite(source, bundle, checkpoint, change):
    offset = len(recovery.HANDOFF_MAGIC)
    nonce, ciphertext = bundle[offset:offset + 12], bundle[offset + 12:]
    associated = recovery.HANDOFF_MAGIC + recovery.HANDOFF_PURPOSE.encode()
    document = recovery.parse(AESGCM(source[2]).decrypt(nonce, ciphertext, associated))
    change(document)
    changed = recovery.HANDOFF_MAGIC + nonce + AESGCM(source[2]).encrypt(nonce, encoded(document), associated)
    return changed, replace(checkpoint, bundle_sha256=digest(changed))


def test_explicit_v2_preserves_closed_history_and_issuer_without_relaxing_v1(source):
    with pytest.raises(ImportRejected, match='SOURCE_SCHEMA_UNSUPPORTED'):
        capture(source, recovery.seal)
    bundle, checkpoint = capture(source)
    restored = recover(source, bundle, checkpoint)
    assert bundle.startswith(recovery.HANDOFF_MAGIC)
    assert restored.stores == source[0].stores
    assert restored.artifacts == source[1]
    assert tuple(map(len, restored.snapshot.handoff)) == (1, 2, 1, 1, 1)
    assert restored.snapshot.fingerprint == checkpoint.snapshot_sha256
    assert restored.snapshot.fingerprint != replace(restored.snapshot, handoff=()).fingerprint
    assert restored.summary()['activation'] == 'FORBIDDEN'
    assert ('bundle-format', digest(recovery.HANDOFF_PURPOSE.encode())) in restored.snapshot.external_digests
    assert source[1]['issuer_material']['runtime-key'] not in bundle
    assert source[1]['issuer_material']['referral-secret'] not in bundle


def test_v2_does_not_accept_the_legacy_schema(tmp_path):
    fixture = joint_fixture(tmp_path)
    with pytest.raises(ImportRejected, match='SOURCE_SCHEMA_UNSUPPORTED|BUNDLE_HANDOFF_REQUIRED'):
        capture((fixture, artifacts_for(fixture), secrets.token_bytes(32)))


@pytest.mark.parametrize('field,value', [('version', 1), ('version', True), ('version', 3),
                                      ('purpose', recovery.PURPOSE), ('purpose', 'activation')])
def test_authenticated_profile_confusion_is_rejected(source, field, value):
    bundle, checkpoint = capture(source)
    changed, repinned = rewrite(source, bundle, checkpoint, lambda document: document.update({field: value}))
    with pytest.raises(ImportRejected, match='BUNDLE_VERSION'):
        recover(source, changed, repinned)


@pytest.mark.parametrize('header', [recovery.MAGIC, b'FC-HA-RECOVERY\x00\x03'])
def test_header_cannot_downgrade_even_with_new_ciphertext_hash(source, header):
    bundle, checkpoint = capture(source)
    changed = header + bundle[len(recovery.HANDOFF_MAGIC):]
    with pytest.raises(ImportRejected, match='BUNDLE_AUTHENTICATION_FAILED|BUNDLE_FORMAT'):
        recover(source, changed, replace(checkpoint, bundle_sha256=digest(changed)))


@pytest.mark.parametrize('statement,reason', [
    ('CREATE TABLE unknown(value TEXT)', 'SOURCE_SCHEMA_UNSUPPORTED'),
    ("UPDATE restricted_owner_handoff_operations SET phase='RETURN' WHERE generation=2", 'HANDOFF_UNSETTLED_OPERATION'),
    ('DELETE FROM restricted_owner_handoff_security', 'HANDOFF_SECURITY'),
])
def test_v2_revalidates_retained_rows_after_decryption(source, statement, reason):
    bundle, checkpoint = capture(source)
    mutate(source[0], statement)
    changed, repinned = rewrite(source, bundle, checkpoint, lambda document:
        document['stores'].update(registry=base64.b64encode(source[0].stores['registry']).decode()))
    with pytest.raises(ImportRejected, match=reason):
        recover(source, changed, repinned)
    with pytest.raises(ImportRejected, match=reason):
        capture(source)


@pytest.mark.parametrize('part', sorted(recovery.ISSUER_PARTS))
def test_v2_keeps_issuer_and_referral_validation(source, part):
    source[1]['issuer_material'][part] = secrets.token_bytes(32)
    with pytest.raises(ImportRejected):
        capture(source)


def test_independent_key_anchor_and_snapshot_pins_are_required(source):
    bundle, checkpoint = capture(source)
    for overrides, reason in [({'key': secrets.token_bytes(32)}, 'AUTHENTICATION_FAILED'),
                              ({'anchor': secrets.token_bytes(32)}, 'ANCHOR_MISMATCH'),
                              ({'expected': replace(checkpoint, snapshot_sha256='0' * 64)}, 'SNAPSHOT_MISMATCH')]:
        with pytest.raises(ImportRejected, match=reason):
            recover(source, bundle, checkpoint, **overrides)
    mutate(source[0], "UPDATE restricted_owner_handoff_security SET fetch_id='new-retained-receipt'")
    newer, new_checkpoint = capture(source)
    assert newer != bundle and new_checkpoint.snapshot_sha256 != checkpoint.snapshot_sha256
    with pytest.raises(ImportRejected, match='CHECKPOINT_MISMATCH'):
        recover(source, bundle, new_checkpoint)
