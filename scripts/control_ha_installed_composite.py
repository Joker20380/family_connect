"""Retained installed canonical/native-format checks for isolated PG only, not activation."""
import base64
from contextlib import closing
from dataclasses import dataclass, field, replace
import sqlite3

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from control.friends import pseudonyms, restricted
from control.friends.access import Access
from control.friends.referrals import Referrals
from scripts.control_ha_external_v1 import records, routing_check, sender_check
from scripts.control_ha_import import TABLES, STORES, MAX_ROWS, VERSION, PURPOSE, ImportRejected
from scripts.control_ha_import import reference_sets, digest, encoded, require
from scripts.control_ha_recovery_bundle import parse
from scripts.control_ha_sqlite_import import NEW_EMPTY, preflight_installed_sqlite

ADAPTER = 'family-connect/installed-canonical-native/v1/offline-only'
FIXED = frozenset(('access/pseudonym-aliases.json', 'access/support-inventory-hmac.key',
    'access/referral.key', 'access/chat-support.json', 'authority/anchor.pub', 'authority/issuer.json',
    'authority/issuer.key', 'authority/revocations.pem', 'authority/admission.json'))


@dataclass(frozen=True, repr=False)
class Prepared:
    snapshot: object = field(repr=False)
    checks: dict = field(repr=False)

    def summary(self):
        return dict(result='INSTALLED_CANONICAL_NATIVE_PREFLIGHT_PASS', adapter=ADAPTER,
                    tables=len(self.snapshot.counts), rows=sum(self.snapshot.counts.values()), checks=self.checks,
                    external_references='DERIVED_NOT_AUTHORIZATION', handoff='RETAINED_READ_ONLY',
                    fleet_pair_fence=False, independent_forward_trust=False, activation=False,
                    full_recovery=False)


def native_alias_check(manifest, key, rows):
    aliases = pseudonyms.Aliases(parse(manifest))
    aliases.check_key(key)
    original = encoded(aliases.document)
    values = dict(device=[row['device'] for row in rows['devices']],
                  panel_event=[row['event_id'] for row in rows['paid_beta_events']])
    canonical = {domain: {value: pseudonyms.pseudonym(key, domain, value) for value in items}
                 for domain, items in values.items()}
    payload = dict(devices=[dict(pseudonym=canonical['device'][row['device']]) for row in rows['devices']],
                   history=dict(events=[dict(pseudonym=canonical['device'][row['device']],
                                             event_id=canonical['panel_event'][row['event_id']])
                                        for row in rows['paid_beta_events']]))
    envelope = pseudonyms.seal(payload, 'subscriptions', key, aliases)
    fresh = {domain: sorted(value for value in values.values() if value not in aliases.index[domain])
             for domain, values in canonical.items()}
    require(envelope['new_entities'] == fresh, 'NATIVE_ALIAS_NEW_ENTITIES')
    recovered = pseudonyms.unseal(envelope, 'subscriptions', aliases)
    expected = parse(encoded(payload))
    for row, name, domain in pseudonyms.references(expected, 'subscriptions'):
        if row[name] in aliases.index[domain]:
            row[name] = aliases.resolve(domain, row[name], current=True)
    require(recovered == expected and encoded(aliases.document) == original, 'NATIVE_ALIAS_HISTORY_CHANGED')
    for domain, entities in aliases.document['entities'].items():
        for entity in entities:
            require(all(aliases.resolve(domain, value) == entity['handle'] for value in entity['aliases'].values()),
                    'NATIVE_ALIAS_HISTORICAL_BINDING')
    return {domain: dict(mapped=len(canonical[domain]) - len(fresh[domain]), new=len(fresh[domain])) for domain in canonical}


def references(stores, checkpoint):
    collected = {}
    for store, raw in stores.items():
        with closing(sqlite3.connect(':memory:')) as database:
            database.deserialize(raw)
            database.execute('PRAGMA trusted_schema=OFF')
            database.execute('PRAGMA query_only=ON')
            database.set_progress_handler(lambda: 1, 2000000)
            for table in TABLES:
                if table.store != store:
                    continue
                columns = ['rowid' if table.name == 'events' and name == 'position' else name for name in table.columns]
                collected[table.name] = () if table.name in NEW_EMPTY else tuple(database.execute(
                    'SELECT ' + ','.join(columns) + ' FROM ' + table.name).fetchmany(MAX_ROWS + 1))
                require(len(collected[table.name]) <= MAX_ROWS, 'ROW_LIMIT')
    return {role: encoded(dict(schema=VERSION, purpose=PURPOSE, checkpoint=checkpoint, role=role,
                              references=sorted(items))) for role, items in reference_sets(collected, checkpoint).items()}


def preflight(stores, files, store_pins, file_pins, checkpoint, *, now):
    require(type(stores) is dict and set(stores) == STORES and type(store_pins) is dict and
            set(store_pins) == STORES, 'INSTALLED_STORE_COVERAGE')
    require(type(files) is dict and type(file_pins) is dict and set(files) == set(file_pins) and
            FIXED <= files.keys() and all(name in FIXED or name.startswith('routing/') for name in files) and
            len(files) <= 256, 'INSTALLED_FILE_COVERAGE')
    require(all(type(raw) is bytes and 0 < len(raw) <= 8 * 1024 * 1024 and digest(raw) == store_pins[name]
                for name, raw in stores.items()) and
            all(type(raw) is bytes and 0 < len(raw) <= 1024 * 1024 and digest(raw) == file_pins[name]
                for name, raw in files.items()), 'INSTALLED_INPUT_PIN')
    try:
        reference_documents = references(stores, checkpoint)
        anchor = base64.b64decode(files['authority/anchor.pub'].strip(), validate=True)
        bootstrap = encoded(dict(version=1, checkpoint=checkpoint, manifest=parse(files['authority/issuer.json']),
                                 crl=files['authority/revocations.pem'].decode('ascii')))
        snapshot = preflight_installed_sqlite(stores, reference_documents,
            {role: digest(raw) for role, raw in reference_documents.items()}, checkpoint, bootstrap, anchor, now=now)
        rows = records(snapshot)
        require(all(row['payload'] == '{}' for row in rows['device_metadata']), 'METADATA_OBSERVATIONS_FORBIDDEN')
        aliases = native_alias_check(files['access/pseudonym-aliases.json'], files['access/support-inventory-hmac.key'], rows)
        eligible, all_activated = restricted.admission_policy(files['authority/admission.json'])
        require(all_activated and eligible is None, 'INSTALLED_ADMISSION_PROFILE')
        _, authority = restricted.delegation(parse(files['authority/issuer.json']), anchor, now)
        signer = serialization.load_pem_private_key(files['authority/issuer.key'], password=None)
        require(isinstance(signer, Ed25519PrivateKey) and
                signer.public_key().public_bytes_raw() == authority.public_key().public_bytes_raw(), 'INSTALLED_ISSUER_KEY')
        referral = Referrals(None, files['access/referral.key'])
        for row in rows['referral_links']:
            require(digest(referral.digest('referral-v1:' + row['sponsor']).encode()) == row['token'], 'INSTALLED_REFERRAL_LINK')
        for row in rows['referral_claims']:
            raw = referral.digest('invite-v1:' + row['request'])[:32].upper()
            invitation = 'FC-' + '-'.join(raw[index:index+4] for index in range(0, 32, 4))
            require(Access.code_hash(invitation) == row['invite'], 'INSTALLED_REFERRAL_CLAIM')
        sender_check({'support.json': files['access/chat-support.json']}, rows)
        routing_check({name.removeprefix('routing/'): raw for name, raw in files.items() if name.startswith('routing/')}, rows)
    except ImportRejected:
        raise
    except (ValueError, TypeError, KeyError, IndexError, StopIteration, sqlite3.Error, OverflowError, RecursionError):
        raise ImportRejected('INSTALLED_NATIVE_INPUT_INVALID') from None
    provenance = (('installed-native-adapter', digest(ADAPTER.encode())),) + tuple(
        ('installed-file:' + name, digest(raw)) for name, raw in sorted(files.items()))
    snapshot = replace(snapshot, external_digests=snapshot.external_digests + provenance)
    return Prepared(snapshot, dict(aliases=aliases, admission='ALL_ACTIVATED_RETAINED_NOT_EXECUTED',
        issuer_key='MATCH', referral_links=len(rows['referral_links']), referral_claims=len(rows['referral_claims']),
        sender='MATCH', routing='MATCH', metadata_observations=0))
