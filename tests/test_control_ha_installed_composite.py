import base64
from copy import deepcopy
import json
import sqlite3

import pytest
from cryptography.hazmat.primitives import serialization

from scripts import control_ha_installed_composite as installed
from scripts.control_ha_external_fixture import artifacts_for_external
from scripts.control_ha_external_v1 import alias_check, records
from scripts.control_ha_handoff_fixture import closed_handoff_fixture
from scripts.control_ha_import import ImportRejected, digest, encoded
from scripts.control_ha_import_fixture import CHECKPOINT
from scripts.control_ha_sqlite_import import preflight_installed_sqlite
from scripts.referral_postgres_rehearsal import NOW


@pytest.fixture
def source(tmp_path):
    fixture = closed_handoff_fixture(tmp_path)
    with sqlite3.connect(':memory:') as database:
        database.deserialize(fixture.stores['metadata'])
        database.execute("UPDATE device_metadata SET payload='{}'")
        database.commit()
        fixture.stores['metadata'] = database.serialize()
    artifacts = artifacts_for_external(fixture, sqlite_preflight=preflight_installed_sqlite)
    files = dict(zip(('access/pseudonym-aliases.json', 'access/support-inventory-hmac.key', 'access/referral.key',
                     'access/chat-support.json', 'authority/anchor.pub', 'authority/issuer.json',
                     'authority/issuer.key', 'authority/revocations.pem', 'authority/admission.json'),
        (artifacts['aliases']['manifest'], artifacts['aliases']['current-hmac'], fixture.referral_secret,
         artifacts['sender_policy']['support.json'], base64.b64encode(fixture.service.anchor),
         encoded(fixture.service.manifest), fixture.service.signing_key.private_bytes(
            serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()),
         fixture.service.crl_source(), encoded(dict(version=2, eligibility='all_activated'))), strict=True))
    files.update({'routing/' + name: raw for name, raw in artifacts['routing_files'].items()})
    return fixture.stores, files


def prepared(source, *, store_pins=None, file_pins=None):
    stores, files = source
    return installed.preflight(stores, files, store_pins or {name:digest(raw) for name, raw in stores.items()},
                               file_pins or {name:digest(raw) for name, raw in files.items()}, CHECKPOINT, now=NOW)


def test_native_profile_preserves_exact_authority_and_handoff(source):
    before = deepcopy(source)
    result = prepared(source)
    assert result.summary()['full_recovery'] is False
    assert result.summary()['independent_forward_trust'] is False
    assert result.snapshot.handoff
    assert result.snapshot.fingerprint == prepared(source).snapshot.fingerprint
    assert source == before
    assert 'private' not in repr(result) and 'rows=' not in repr(result)


def test_cold_probe_uses_native_reference_format_without_new_authority(source):
    from scripts.control_ha_recovery_probe import prepare_canonical
    result = prepare_canonical(*source, now=NOW)
    assert len(result.snapshot.checkpoint) == 32
    assert len(bytes.fromhex(result.snapshot.checkpoint)) == 16
    assert result.snapshot.checkpoint == prepare_canonical(*source, now=NOW).snapshot.checkpoint
    assert result.snapshot.rows == prepared(source).snapshot.rows
    assert result.summary()['independent_forward_trust'] is False


def test_new_native_entity_is_explicit_and_does_not_regenerate_alias_history(source):
    files = source[1]
    original = prepared(source)
    document = json.loads(files['access/pseudonym-aliases.json'])
    document['entities']['device'].pop()
    files['access/pseudonym-aliases.json'] = encoded(document)
    changed = prepared(source)
    assert changed.checks['aliases']['device']['new'] == 1
    assert changed.snapshot.fingerprint != original.snapshot.fingerprint
    assert files['access/pseudonym-aliases.json'] == encoded(document)
    with pytest.raises(ValueError):
        alias_check({'manifest':files['access/pseudonym-aliases.json'], 'current-hmac':files['access/support-inventory-hmac.key']},
                    records(changed.snapshot))


@pytest.mark.parametrize('kind', ('hmac','issuer','referral','sender','admission','alias_duplicate',
                                 'routing','schema','metadata','handoff','extra','missing'))
def test_native_mismatch_never_becomes_importable(source, kind):
    stores, files = source
    if kind == 'hmac': files['access/support-inventory-hmac.key'] = b'x' * 32
    elif kind == 'issuer': files['authority/issuer.key'] = b'not-a-key'
    elif kind == 'referral': files['access/referral.key'] = b'x' * 32
    elif kind == 'sender': files['access/chat-support.json'] = b'{}'
    elif kind == 'admission': files['authority/admission.json'] = encoded(dict(version=2,eligibility='everyone'))
    elif kind == 'alias_duplicate':
        document = json.loads(files['access/pseudonym-aliases.json'])
        document['entities']['device'].append(deepcopy(document['entities']['device'][0]))
        files['access/pseudonym-aliases.json'] = encoded(document)
    elif kind == 'routing': files['routing/anchor.pub'] = base64.b64encode(b'x' * 32)
    elif kind in ('schema','metadata','handoff'):
        store = 'metadata' if kind == 'metadata' else 'registry'
        with sqlite3.connect(':memory:') as database:
            database.deserialize(stores[store])
            statement = {'schema':'CREATE TABLE unexpected(value)', 'metadata':"UPDATE device_metadata SET payload='[1]'",
                         'handoff':'DELETE FROM restricted_owner_handoff_security'}[kind]
            if kind == 'handoff':
                for row in database.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name='restricted_owner_handoff_security'").fetchall():
                    database.execute('DROP TRIGGER ' + row[0])
            database.execute(statement)
            database.commit()
            stores[store] = database.serialize()
    elif kind == 'extra': files['unexpected/secret'] = b'not-authorized'
    elif kind == 'missing': del files['authority/issuer.key']
    with pytest.raises(ImportRejected): prepared(source)


@pytest.mark.parametrize('kind', ('file', 'store', 'alias-history'))
def test_custody_pin_mismatch_refuses_even_valid_replacements(source, kind):
    store_pins = {name:digest(raw) for name, raw in source[0].items()}
    file_pins = {name:digest(raw) for name, raw in source[1].items()}
    if kind == 'store': store_pins['registry'] = '0' * 64
    elif kind == 'file': file_pins['access/referral.key'] = '0' * 64
    else:
        value = json.loads(source[1]['access/pseudonym-aliases.json']);value['entities']['device'].pop()
        source[1]['access/pseudonym-aliases.json'] = encoded(value)
    with pytest.raises(ImportRejected, match='INSTALLED_INPUT_PIN'):
        prepared(source, store_pins=store_pins, file_pins=file_pins)
