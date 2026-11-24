"""Offline canonical/panel bindings; retained stores never become dispatch authority."""
from contextlib import closing
import io
import json
import re
import sqlite3
import tarfile

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from control.friends import paid_beta, pseudonyms, subscription
from scripts import control_ha_owner_runtime as owner
from scripts import control_ha_worker_custody as worker
from scripts.control_ha_external_v1 import records
from scripts.control_ha_import import digest, encoded
from scripts.control_ha_installed_composite import Prepared
from scripts.control_ha_rehearsal import require

PURPOSE = 'family-connect/owner-postgres-custody/v1/floors-only/no-dispatch'
MAGIC = b'FCOWNER1\0'
LIMIT = 512 * 1024 * 1024
EXCLUDED = ['console_technicalmetadata', 'console_technicalmetadatasource']


def owner_archive(capsule, key, checkpoint):
    require(type(checkpoint) is dict and set(checkpoint) == {'ciphertext_sha256', 'archive_sha256', 'source_image'}
            and checkpoint['source_image'] == owner.IMAGES['postgres'] and
            all(type(checkpoint[name]) is str and re.fullmatch('[a-f0-9]{64}', checkpoint[name])
                for name in ('ciphertext_sha256', 'archive_sha256')), 'OWNER_CHECKPOINT')
    require(type(capsule) is bytes and 37 <= len(capsule) <= LIMIT and capsule.startswith(MAGIC) and
            digest(capsule) == checkpoint['ciphertext_sha256'] and type(key) is bytes and len(key) == 32,
            'OWNER_CAPSULE_PIN')
    raw = AESGCM(key).decrypt(capsule[9:21], capsule[21:], PURPOSE.encode())
    require(digest(raw) == checkpoint['archive_sha256'], 'OWNER_ARCHIVE_PIN')
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:') as archive:
        members = archive.getmembers()
        require(len(members) == 3 and {entry.name for entry in members} == {'database.dump', 'manifest.json', 'floors.json'}
                and all(entry.isfile() and not entry.pax_headers and entry.sparse is None and
                        0 < entry.size <= (LIMIT if entry.name == 'database.dump' else 1024*1024) for entry in members),
                'OWNER_ARCHIVE_MEMBERS')
        files = {entry.name: archive.extractfile(entry).read() for entry in members}
    manifest, floors = owner.document(files['manifest.json']), owner.document(files['floors.json'])
    require(manifest['purpose'] == PURPOSE and manifest['image'] == checkpoint['source_image'] and
            manifest['excluded_row_tables'] == EXCLUDED and manifest['application_dispatch'] is False and
            manifest['full_recovery'] is False and manifest['metadata_projection'] == 'consent-epoch-sequence-status-only'
            and files['database.dump'].startswith(b'PGDMP') and digest(files['database.dump']) == manifest['dump_sha256'],
            'OWNER_ARCHIVE_SCOPE')
    require(type(manifest['fingerprints']) is dict and len(manifest['fingerprints']) == 37 and
            not set(EXCLUDED) & manifest['fingerprints'].keys(), 'OWNER_TABLE_COVERAGE')
    for name, value in manifest['fingerprints'].items():
        require(re.fullmatch('[a-z_][a-z0-9_]{0,62}', name) and type(value) is dict and
                set(value) == {'rows', 'sha256'} and type(value['rows']) is int and value['rows'] >= 0 and
                re.fullmatch('[a-f0-9]{64}', value['sha256']), 'OWNER_TABLE_PIN')
    require(type(floors) is list and len(floors) == manifest['metadata_floor_rows'] and len(floors) <= 10000,
            'OWNER_FLOOR_COUNT')
    seen = set()
    for row in floors:
        require(type(row) is dict and set(row) == {'pseudonym','consent_epoch','sequence','consent','received_at'} and
                re.fullmatch('[a-f0-9]{64}', row['pseudonym']) and row['pseudonym'] not in seen and
                row['consent'] in ('enabled', 'revoked') and all(type(row[name]) is int and row[name] >= 0
                for name in ('consent_epoch', 'sequence', 'received_at')), 'OWNER_PRIVACY_FLOOR')
        seen.add(row['pseudonym'])
    return files['database.dump'], manifest, floors


def bindings(canonical, owner_value, worker_value):
    require(type(canonical) is Prepared, 'CANONICAL_PREFLIGHT_REQUIRED')
    owner.validate(owner_value)
    worker.validate(worker_value)
    owner_files, worker_files = owner.unpack(owner_value), worker.unpack(worker_value)
    pins = dict(canonical.snapshot.external_digests)
    for source, target in (('panel-aliases.json', 'access/pseudonym-aliases.json'),
                           ('inventory-hmac.key', 'access/support-inventory-hmac.key')):
        require(digest(owner_files[source]) == pins['installed-file:' + target], 'CANONICAL_OWNER_ALIAS_BINDING')
    canonical_devices = {row['device']: row['wg'] for row in records(canonical.snapshot)['devices']}
    with closing(sqlite3.connect(':memory:')) as database:
        database.deserialize(owner_files['synthetic.sqlite'])
        synthetic = dict(database.execute('SELECT device,wg FROM devices'))
    with closing(sqlite3.connect(':memory:')) as database:
        database.deserialize(worker_files['product.sqlite'])
        legacy = dict(database.execute('SELECT device_identity,public_key FROM transport_keys'))
        intents = {row[0] for row in database.execute('SELECT public_key FROM peer_outbox')}
    for left, right in ((canonical_devices, synthetic), (canonical_devices, legacy), (synthetic, legacy)):
        require(not left.keys() & right.keys() and not set(left.values()) & set(right.values()), 'STORE_NAMESPACE_COLLISION')
    require(not intents & (set(canonical_devices.values()) | set(synthetic.values())), 'LEGACY_INTENT_COLLISION')
    return dict(canonical=len(canonical_devices), owner_synthetic=len(synthetic), legacy_keys=len(legacy),
                legacy_intent_keys=len(intents), namespaces='DISJOINT', aliases='EXACT', activation=False,
                dispatcher_fence=False, full_recovery=False)


def projection(database, key, aliases, observed, runtime):
    require(type(observed) is int and observed > 0 and re.fullmatch('[a-f0-9]{64}', runtime), 'PROJECTION_PROVENANCE')
    database = paid_beta.transaction(database)
    require(paid_beta.schema_present(database), 'PAID_SCHEMA_REQUIRED')
    devices = database.devices()
    require(len(devices) <= 10000, 'DEVICE_LIMIT')
    rows = []
    for device in devices:
        value = subscription.snapshot(database, device['device'], observed)
        row = dict(pseudonym=pseudonyms.pseudonym(key, 'device', device['device']), cohort=value['cohort'],
                   subscription=None, event=None)
        if value['subscription'] is not None:
            row['subscription'] = {name:value['subscription'][name] for name in ('state','period_start','paid_until',
                'grace_until','version','effective_state','paid_allow','entitlement_until')}
            if value['event'] is not None:
                row['event'] = dict(value['event'], event_id=pseudonyms.pseudonym(key, 'panel_event', value['event']['event_id']))
        rows.append(row)
    events = database.database.execute('SELECT event_id,device,event_type,occurred_at,previous_state,new_state,result '
        "FROM paid_beta_events WHERE result='APPLIED' ORDER BY occurred_at DESC,event_id DESC LIMIT 1001").fetchall()
    history = []
    for event in events[:1000]:
        row = dict(event)
        row['pseudonym'] = pseudonyms.pseudonym(key, 'device', row.pop('device'))
        row['event_id'] = pseudonyms.pseudonym(key, 'panel_event', row['event_id'])
        history.append(row)
    payload = dict(schema=2, scope='production', source='gateway-ru', observed_at=observed, status='ok',
        runtime_sha256=runtime, devices=rows, history=dict(events=history, truncated=len(events)>1000))
    return pseudonyms.seal(payload, 'subscriptions', key, aliases)
