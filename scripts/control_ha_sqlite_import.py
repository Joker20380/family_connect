"""Pinned application SQLite schemas to synthetic PG; no live reader or cutover."""
from contextlib import closing
from dataclasses import replace
import json
from pathlib import Path
import sqlite3

from cryptography import x509
from cryptography.exceptions import InvalidSignature
from control.friends.crl_postgres import IMPORT_PURPOSE
from control.friends.restricted import delegation, utc
from scripts.control_ha_import import TABLES, STORES, MAX_BYTES, MAX_ROWS, SOURCE_MARKER, VERSION, PURPOSE
from scripts.control_ha_import import ImportRejected, digest, encoded, preflight, require, source_ddl, unique

ADAPTER = 'family-connect/application-sqlite/v1/not-for-activation'
MANIFEST = Path(__file__).resolve().parents[1] / 'deploy/control-ha/sqlite-source-v1.json'
NEW_EMPTY = frozenset(('restricted_crl_publications',))


def definitions(database):
    return [list(row) for row in database.execute('SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY name')]


def cross_store_bindings(snapshot):
    records = {table.name: [dict(zip(table.columns, row, strict=True)) for row in rows]
               for table, rows in zip(TABLES, snapshot.rows, strict=True)}
    devices = {row['device'] for row in records['devices']}
    for table, rows in records.items():
        if table == 'challenges':
            continue
        for row in rows:
            for column in ('device', 'sponsor'):
                if table == 'gateway_assignment_events' and column == 'device' and row[column] == '':
                    continue
                if row.get(column) is not None:
                    require(row[column] in devices, 'SOURCE_DEVICE_BINDING')
    aliases = {row['device']: row['support_id'] for row in records['device_support']}
    for row in records['snapshots']:
        require(aliases.get(row['device']) == row['support'], 'SOURCE_SUPPORT_BINDING')


def crl_anchor(snapshot, bootstrap, trust_anchor, now):
    require(type(bootstrap) is bytes and 0 < len(bootstrap) <= 65536 and
            type(trust_anchor) is bytes and len(trust_anchor) == 32 and type(now) is int, 'CRL_BOOTSTRAP_REQUIRED')
    try:
        envelope = json.loads(bootstrap, object_pairs_hook=unique)
        require(type(envelope) is dict and set(envelope) == {'version', 'checkpoint', 'manifest', 'crl'} and
                type(envelope['version']) is int and envelope['version'] == 1 and
                envelope['checkpoint'] == snapshot.checkpoint, 'CRL_BOOTSTRAP_VERSION')
        require(type(envelope['crl']) is str and len(envelope['crl'].encode()) <= 16384, 'CRL_BOOTSTRAP_BOUNDS')
        _, authority = delegation(envelope['manifest'], trust_anchor, now)
        parsed = x509.load_pem_x509_crl(envelope['crl'].encode())
        require(parsed.is_signature_valid(authority.public_key()) and parsed.issuer == authority.subject and
                parsed.last_update_utc <= utc(now) < parsed.next_update_utc, 'CRL_BOOTSTRAP_TRUST')
        number = parsed.extensions.get_extension_for_class(x509.CRLNumber).value.crl_number
        records = dict(zip((table.name for table in TABLES), snapshot.rows, strict=True))
        require(records['restricted_crl_sequence'] == ((1, number),) and not records['restricted_crl_publications'], 'CRL_BOOTSTRAP_FLOOR')
        for device, revision, serial, expires, certificate in records['restricted_certificates']:
            parsed_certificate = x509.load_pem_x509_certificate(certificate.encode())
            parsed_certificate.verify_directly_issued_by(authority)
            require(str(parsed_certificate.serial_number) == serial and
                    int(parsed_certificate.not_valid_after_utc.timestamp()) == expires, 'CERTIFICATE_ROW_MISMATCH')
        return (1, 1, IMPORT_PURPOSE, number, digest(envelope['crl'].encode()))
    except ImportRejected:
        raise
    except (ValueError, TypeError, KeyError, UnicodeError, RecursionError, InvalidSignature, x509.ExtensionNotFound):
        raise ImportRejected('CRL_BOOTSTRAP_INVALID') from None


def preflight_sqlite(stores, external, expected_external, checkpoint, bootstrap, trust_anchor, *, now):
    return _preflight_sqlite(stores, external, expected_external, checkpoint, bootstrap, trust_anchor, now=now,
                             retain_handoff=False)


def preflight_installed_sqlite(stores, external, expected_external, checkpoint, bootstrap, trust_anchor, *, now):
    return _preflight_sqlite(stores, external, expected_external, checkpoint, bootstrap, trust_anchor, now=now,
                             retain_handoff=True)


def _preflight_sqlite(stores, external, expected_external, checkpoint, bootstrap, trust_anchor, *, now, retain_handoff):
    from scripts import control_ha_handoff_import as handoff
    require(type(stores) is dict and set(stores) == STORES, 'STORE_COVERAGE')
    manifest = json.loads(MANIFEST.read_bytes())
    require(manifest['version'] == 1 and manifest['adapter'] == ADAPTER and
            set(manifest['stores']) == STORES and set(manifest['new_empty_tables']) == NEW_EMPTY, 'ADAPTER_MANIFEST')
    overlay = handoff.manifest() if retain_handoff else None
    retained = ()
    converted, provenance = {}, []
    for store in sorted(STORES):
        raw = stores[store]
        require(type(raw) is bytes and 0 < len(raw) <= MAX_BYTES, 'STORE_BOUNDS')
        with closing(sqlite3.connect(':memory:')) as database, closing(sqlite3.connect(':memory:')) as target:
            try:
                database.deserialize(raw)
                database.execute('PRAGMA trusted_schema=OFF')
                database.execute('PRAGMA query_only=ON')
                database.set_progress_handler(lambda: 1, 2000000)
                require(database.execute('PRAGMA quick_check').fetchall() == [('ok',)], 'SOURCE_INTEGRITY')
                expected_schema = manifest['stores'][store] + (overlay['definitions'] if overlay and store == 'registry' else [])
                expected_schema = sorted(expected_schema, key=lambda row: row[1])
                require(definitions(database) == expected_schema, 'SOURCE_SCHEMA_UNSUPPORTED')
                require(database.execute('PRAGMA user_version').fetchone() == (0,) and
                        database.execute('PRAGMA application_id').fetchone() == (0,) and
                        database.execute('PRAGMA encoding').fetchone() == ('UTF-8',), 'SOURCE_PRAGMA_UNSUPPORTED')
                require(not database.execute('PRAGMA foreign_key_check').fetchall(), 'SOURCE_FOREIGN_KEYS')
                if overlay and store == 'registry':
                    retained = handoff.read(database)
                target.execute(SOURCE_MARKER)
                target.execute('INSERT INTO ha_import_source VALUES (?,?,?,?)', (VERSION, PURPOSE, store, checkpoint))
                for table in TABLES:
                    if table.store != store:
                        continue
                    target.execute(source_ddl(table))
                    if table.name in NEW_EMPTY:
                        continue
                    columns = ['rowid' if table.name == 'events' and name == 'position' else name for name in table.columns]
                    rows = database.execute('SELECT ' + ','.join(columns) + ' FROM ' + table.name).fetchmany(MAX_ROWS + 1)
                    require(len(rows) <= MAX_ROWS, 'ROW_LIMIT')
                    target.executemany('INSERT INTO ' + table.name + '(' + ','.join(columns) + ') VALUES (' +
                                       ','.join(['?'] * len(columns)) + ')', rows)
                target.commit()
                converted[store] = target.serialize()
            except ImportRejected:
                raise
            except (sqlite3.Error, UnicodeError, ValueError, OverflowError):
                raise ImportRejected('SOURCE_UNREADABLE') from None
        provenance.append(('source:' + store, digest(raw)))
    snapshot = preflight(converted, external, expected_external, checkpoint)
    cross_store_bindings(snapshot)
    if overlay:
        devices = next(rows for table, rows in zip(TABLES, snapshot.rows, strict=True) if table.name == 'devices')
        handoff.validate(retained, {row[0] for row in devices})
        provenance.append(('closed-handoff-retention-v2', digest(encoded(overlay))))
    provenance.append(('adapter:' + ADAPTER, digest(encoded(manifest))))
    anchor = crl_anchor(snapshot, bootstrap, trust_anchor, now)
    provenance.extend((('crl-bootstrap', digest(bootstrap)), ('issuer-anchor', digest(trust_anchor))))
    return replace(snapshot, external_digests=snapshot.external_digests + tuple(provenance), crl_anchor=anchor, handoff=retained)
