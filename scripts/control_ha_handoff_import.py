"""Retain closed installed handoff history; never enable its administrative writers."""
import json
from pathlib import Path

from control.friends.restricted import timestamp_ns
from scripts.control_ha_import import Table, MAX_ROWS, MAX_BYTES, encoded, digest, require, unique, ImportRejected

MANIFEST = Path(__file__).resolve().parents[1] / 'deploy/control-ha/sqlite-handoff-v2.json'
FIELDS = 'slot:int operation:text device:text family:text gateway:text phase:text deadline:int invocation:text canary:text? return_view:text? floor:text? fetch_id:text?'
TABLES = (
    Table('registry', 'restricted_owner_handoff', FIELDS),
    Table('registry', 'restricted_owner_handoff_operations', FIELDS +
          ' generation:int predecessor:text? prepared_at:int? prepare_inputs:text captured:int'),
    Table('registry', 'restricted_owner_handoff_current', 'slot:int operation:text generation:int'),
    Table('registry', 'restricted_owner_handoff_security', 'device:text family:text gateway:text floor:text operation:text generation:int fetch_id:text?'),
    Table('registry', 'restricted_owner_handoff_schema', 'version:int legacy_sha256:text'),
)
LEGACY_FIELDS = ('slot BIGINT PRIMARY KEY CHECK(slot=1),operation TEXT UNIQUE NOT NULL,device TEXT NOT NULL,'
    'family TEXT NOT NULL,gateway TEXT NOT NULL,phase TEXT NOT NULL CHECK(phase=\'CLEANED\'),deadline BIGINT NOT NULL,'
    'invocation TEXT NOT NULL,canary TEXT,return_view TEXT,floor TEXT,fetch_id TEXT')
DDL = (
    'CREATE TABLE restricted_owner_handoff(' + LEGACY_FIELDS + ')',
    'CREATE TABLE restricted_owner_handoff_operations(slot BIGINT NOT NULL CHECK(slot=1),operation TEXT PRIMARY KEY,'
    'device TEXT NOT NULL,family TEXT NOT NULL,gateway TEXT NOT NULL,phase TEXT NOT NULL CHECK(phase=\'CLEANED\'),'
    'deadline BIGINT NOT NULL,invocation TEXT NOT NULL,canary TEXT,return_view TEXT,floor TEXT,fetch_id TEXT,'
    'generation BIGINT UNIQUE NOT NULL CHECK(generation>0),predecessor TEXT,prepared_at BIGINT,prepare_inputs TEXT NOT NULL,'
    'captured BIGINT NOT NULL CHECK(captured IN (0,1)),UNIQUE(operation,generation))',
    'CREATE TABLE restricted_owner_handoff_current(slot BIGINT PRIMARY KEY CHECK(slot=1),operation TEXT UNIQUE NOT NULL,'
    'generation BIGINT NOT NULL,FOREIGN KEY(operation,generation) REFERENCES restricted_owner_handoff_operations(operation,generation))',
    'CREATE TABLE restricted_owner_handoff_security(device TEXT PRIMARY KEY,family TEXT NOT NULL,gateway TEXT NOT NULL,'
    'floor TEXT NOT NULL,operation TEXT NOT NULL,generation BIGINT NOT NULL,fetch_id TEXT,'
    'FOREIGN KEY(operation,generation) REFERENCES restricted_owner_handoff_operations(operation,generation))',
    'CREATE TABLE restricted_owner_handoff_schema(version BIGINT PRIMARY KEY CHECK(version=2),legacy_sha256 TEXT NOT NULL)',
)


def manifest():
    value = json.loads(MANIFEST.read_bytes())
    require(value['version'] == 2 and value['purpose'] ==
            'family-connect/installed-handoff-schema/v2/observation-only', 'HANDOFF_MANIFEST')
    return value


def read(database):
    collected = []
    for table in TABLES:
        rows = database.execute('SELECT ' + ','.join(table.columns) + ' FROM ' + table.name).fetchmany(MAX_ROWS + 1)
        require(len(rows) <= MAX_ROWS, 'HANDOFF_ROW_BOUNDS')
        for row in rows:
            for value, kind in zip(row, table.types, strict=True):
                valid = value is None and kind.endswith('?')
                valid |= (type(value) is int and -(2**63) <= value < 2**63) if kind.rstrip('?') == 'int' else (
                    type(value) is str and '\x00' not in value and len(value.encode()) <= MAX_BYTES)
                require(valid, 'HANDOFF_VALUE_TYPE')
        collected.append(tuple(sorted((tuple(row) for row in rows), key=encoded)))
    return tuple(collected)


def floor(raw, row):
    value = json.loads(raw, object_pairs_hook=unique)
    require(type(value) is dict and set(value) == {'issued_at', 'revision', 'minimum_crl', 'sequence', 'issuer', 'directory'},
            'HANDOFF_FLOOR_SHAPE')
    require(all(type(value[key]) is int and 0 <= value[key] < 2**63
                for key in ('issued_at', 'revision', 'minimum_crl', 'sequence')), 'HANDOFF_FLOOR_VALUE')
    require(type(value['issuer']) is dict and type(value['issuer']['sequence']) is int and
            value['issuer']['sequence'] == value['sequence'], 'HANDOFF_ISSUER_SEQUENCE')
    directory = value['directory']
    require(type(directory) is dict and directory['family'] == row['family'] and type(directory['seeds']) is list and
            bool(directory['seeds']) and all(seed['gateway'] == row['gateway'] for seed in directory['seeds']), 'HANDOFF_FLOOR_SCOPE')
    require(timestamp_ns(directory['issued_at']) < timestamp_ns(directory['expires_at']), 'HANDOFF_DIRECTORY_ORDER')
    return value


def preserves(current, previous):
    current_time = timestamp_ns(current['directory']['issued_at'])
    previous_time = timestamp_ns(previous['directory']['issued_at'])
    return (all(current[key] >= previous[key] for key in ('issued_at', 'revision', 'minimum_crl', 'sequence')) and
            (current['sequence'] > previous['sequence'] or current['issuer'] == previous['issuer']) and
            (current_time > previous_time or current_time == previous_time and current['directory'] == previous['directory']))


def validate(rows, devices):
    try:
        records = [[dict(zip(table.columns, row, strict=True)) for row in values]
                   for table, values in zip(TABLES, rows, strict=True)]
        legacy, operations, pointer, security, schema = records
        require(len(legacy) <= 1 and schema == [dict(version=2, legacy_sha256=digest(encoded(legacy)))], 'HANDOFF_LEGACY_BINDING')
        ordered = sorted(operations, key=lambda row: row['generation'])
        require([row['generation'] for row in ordered] == list(range(1, len(ordered) + 1)), 'HANDOFF_GENERATION_CHAIN')
        require(len({row['operation'] for row in operations}) == len(operations), 'HANDOFF_OPERATION_ID')
        require(pointer == ([dict(slot=1, operation=ordered[-1]['operation'], generation=len(ordered))] if ordered else []),
                'HANDOFF_CURRENT_BINDING')
        for index, row in enumerate(ordered):
            require(row['predecessor'] == (ordered[index-1]['operation'] if index else None), 'HANDOFF_PREDECESSOR')
            require(row['prepare_inputs'] == encoded({key: row[key] for key in
                    ('operation', 'device', 'family', 'gateway', 'deadline')}).decode(), 'HANDOFF_INPUT_BINDING')
            require(row['captured'] in (0, 1), 'HANDOFF_CAPTURE_FLAG')
        for row in legacy + operations:
            require(row['slot'] == 1 and row['phase'] == 'CLEANED', 'HANDOFF_UNSETTLED_OPERATION')
            require(row['device'] in devices, 'HANDOFF_DEVICE_BINDING')
            require(row['floor'] is not None, 'HANDOFF_CLOSED_FLOOR_MISSING')
            floor(row['floor'], row)
        if legacy:
            require(bool(ordered) and all(ordered[0][key] == legacy[0][key] for key in TABLES[0].columns) and
                    ordered[0]['prepared_at'] is None and ordered[0]['captured'] == 1 and legacy[0]['floor'] is not None,
                    'HANDOFF_MIGRATED_LEGACY')
        by_operation = {row['operation']: row for row in operations}
        history_by_device = {}
        for row in operations:
            history_by_device.setdefault(row['device'], []).append(row)
        require(len({row['device'] for row in security}) == len(security), 'HANDOFF_SECURITY_DUPLICATE')
        by_device = {row['device']: row for row in security}
        for row in security:
            previous = by_operation.get(row['operation'])
            require(previous is not None and all(previous[key] == row[key] for key in
                    ('device', 'family', 'gateway', 'generation')), 'HANDOFF_SECURITY_BINDING')
            current_floor = floor(row['floor'], row)
            for historical in history_by_device[row['device']]:
                require(historical['family'] == row['family'] and historical['gateway'] == row['gateway'], 'HANDOFF_SECURITY_SCOPE')
                require(historical['captured'] == 0 or row['generation'] >= historical['generation'], 'HANDOFF_SECURITY_GENERATION')
                if historical['floor'] is not None:
                    require(preserves(current_floor, floor(historical['floor'], historical)), 'HANDOFF_SECURITY_REGRESSION')
        require(all(row['floor'] is None or row['device'] in by_device for row in operations), 'HANDOFF_SECURITY_MISSING')
    except ImportRejected:
        raise
    except (ValueError, TypeError, KeyError, IndexError, RecursionError, UnicodeError):
        raise ImportRejected('HANDOFF_STATE_INVALID') from None


def retain(database, rows, fault):
    for statement in DDL:
        database.execute(statement)
    for table, values in zip(TABLES, rows, strict=True):
        with database.cursor() as cursor:
            cursor.executemany('INSERT INTO ' + table.name + '(' + ','.join(table.columns) + ') VALUES (' +
                               ','.join(['%s'] * len(table.columns)) + ')', values)
        fault(table.name)
    database.execute("CREATE FUNCTION ha_handoff_frozen_v2() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN "
                     "RAISE EXCEPTION 'handoff recovery retention is read-only' USING ERRCODE='23514'; END $$")
    for table in TABLES:
        database.execute('CREATE TRIGGER ha_handoff_frozen_v2 BEFORE INSERT OR UPDATE OR DELETE OR TRUNCATE ON ' +
                         table.name + ' FOR EACH STATEMENT EXECUTE FUNCTION ha_handoff_frozen_v2()')


def verify(database, rows):
    for table, expected in zip(TABLES, rows, strict=True):
        actual = database.execute('SELECT ' + ','.join(table.columns) + ' FROM ' + table.name).fetchmany(MAX_ROWS + 1)
        require(tuple(sorted((tuple(row[key] for key in table.columns) for row in actual), key=encoded)) == expected,
                'HANDOFF_TARGET_CHANGED')
