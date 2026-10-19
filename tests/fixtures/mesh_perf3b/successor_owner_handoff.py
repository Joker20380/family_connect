import hashlib
import json
import re

from provisioning.friends_catalog import require


TABLE = 'restricted_owner_handoff'
OPERATIONS = 'restricted_owner_handoff_operations'
CURRENT = 'restricted_owner_handoff_current'
SECURITY = 'restricted_owner_handoff_security'
SCHEMA = 'restricted_owner_handoff_schema'
FIELDS = ('slot', 'operation', 'device', 'family', 'gateway', 'phase', 'deadline',
          'invocation', 'canary', 'return_view', 'floor', 'fetch_id')


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'))


def transaction(database):
    require(database.in_transaction and database.execute('PRAGMA synchronous').fetchone()[0] == 2)


def exists(database, table):
    return database.execute('SELECT 1 FROM sqlite_master WHERE type=? AND name=?', ('table', table)).fetchone() is not None


def legacy_rows(database):
    if not exists(database, TABLE):
        return []
    return [dict(row) for row in database.execute('SELECT * FROM restricted_owner_handoff ORDER BY slot')]


def inputs(operation, device, family, gateway, deadline):
    return encode(dict(operation=operation, device=device, family=family, gateway=gateway, deadline=deadline))


def migrate(database):
    transaction(database)
    legacy = legacy_rows(database)
    require(len(legacy) <= 1)
    require(all(set(row) == set(FIELDS) and row['phase'] == 'CLEANED' for row in legacy))
    digest = hashlib.sha256(encode(legacy).encode()).hexdigest()
    if exists(database, SCHEMA):
        row = database.execute('SELECT * FROM restricted_owner_handoff_schema WHERE version=2').fetchone()
        require(row is not None and row['legacy_sha256'] == digest)
        return dict(version=2, legacy_sha256=digest, result='ALREADY_MIGRATED')
    require(not any(exists(database, table) for table in (OPERATIONS, CURRENT, SECURITY)))
    database.execute('CREATE TABLE IF NOT EXISTS restricted_owner_handoff ('
        'slot INTEGER PRIMARY KEY CHECK(slot=1), operation TEXT UNIQUE NOT NULL, '
        'device TEXT NOT NULL, family TEXT NOT NULL, gateway TEXT NOT NULL, '
        'phase TEXT NOT NULL, deadline INTEGER NOT NULL, invocation TEXT NOT NULL, '
        'canary TEXT, return_view TEXT, floor TEXT, fetch_id TEXT)')
    database.execute('CREATE TABLE restricted_owner_handoff_operations ('
        'slot INTEGER NOT NULL CHECK(slot=1), operation TEXT PRIMARY KEY, '
        'device TEXT NOT NULL, family TEXT NOT NULL, gateway TEXT NOT NULL, '
        "phase TEXT NOT NULL CHECK(phase IN ('PREPARED','ACTIVE','RETURN','CLEANED')), "
        'deadline INTEGER NOT NULL, invocation TEXT NOT NULL, canary TEXT, return_view TEXT, floor TEXT, fetch_id TEXT, '
        'generation INTEGER NOT NULL UNIQUE CHECK(generation>0), predecessor TEXT, prepared_at INTEGER, '
        'prepare_inputs TEXT NOT NULL, captured INTEGER NOT NULL CHECK(captured IN (0,1)))')
    database.execute("CREATE UNIQUE INDEX restricted_owner_handoff_one_open ON restricted_owner_handoff_operations(slot) WHERE phase!='CLEANED'")
    database.execute('CREATE TABLE restricted_owner_handoff_current ('
        'slot INTEGER PRIMARY KEY CHECK(slot=1), operation TEXT NOT NULL UNIQUE, generation INTEGER NOT NULL)')
    database.execute('CREATE TABLE restricted_owner_handoff_security ('
        'device TEXT PRIMARY KEY, family TEXT NOT NULL, gateway TEXT NOT NULL, floor TEXT NOT NULL, '
        'operation TEXT NOT NULL, generation INTEGER NOT NULL, fetch_id TEXT)')
    database.execute('CREATE TABLE restricted_owner_handoff_schema ('
        'version INTEGER PRIMARY KEY CHECK(version=2), legacy_sha256 TEXT NOT NULL)')
    for row in legacy:
        require(row['slot'] == 1 and row['floor'] is not None)
        saved = json.loads(row['floor'])
        require(saved['directory']['family'] == row['family']
                and all(seed['gateway'] == row['gateway'] for seed in saved['directory']['seeds']))
        database.execute('INSERT INTO restricted_owner_handoff_operations VALUES (' + ','.join('?' for _ in range(17)) + ')',
            tuple(row[name] for name in FIELDS) + (1, None, None,
            inputs(row['operation'], row['device'], row['family'], row['gateway'], row['deadline']), 1))
        database.execute('INSERT INTO restricted_owner_handoff_current VALUES (1,?,1)', (row['operation'],))
        database.execute('INSERT INTO restricted_owner_handoff_security VALUES (?,?,?,?,?,?,?)',
            (row['device'], row['family'], row['gateway'], row['floor'], row['operation'], 1, row['fetch_id']))
    database.execute('INSERT INTO restricted_owner_handoff_schema VALUES (2,?)', (digest,))
    for action in ('INSERT', 'UPDATE', 'DELETE'):
        database.execute('CREATE TRIGGER restricted_owner_handoff_legacy_' + action.lower() +
            ' BEFORE ' + action + " ON restricted_owner_handoff BEGIN SELECT RAISE(ABORT,'LEGACY_HANDOFF_READ_ONLY'); END")
    for table in (OPERATIONS, CURRENT, SECURITY, SCHEMA):
        database.execute('CREATE TRIGGER ' + table + '_no_delete BEFORE DELETE ON ' + table +
            " BEGIN SELECT RAISE(ABORT,'HANDOFF_HISTORY_REQUIRED'); END")
    database.execute("CREATE TRIGGER restricted_owner_handoff_terminal BEFORE UPDATE ON restricted_owner_handoff_operations "
        "WHEN OLD.phase='CLEANED' BEGIN SELECT RAISE(ABORT,'HANDOFF_TERMINAL'); END")
    database.execute('CREATE TRIGGER restricted_owner_handoff_identity BEFORE UPDATE OF '
        'slot,operation,device,family,gateway,deadline,generation,predecessor,prepared_at,prepare_inputs '
        "ON restricted_owner_handoff_operations BEGIN SELECT RAISE(ABORT,'HANDOFF_INPUTS_IMMUTABLE'); END")
    database.execute('CREATE TRIGGER restricted_owner_handoff_security_identity BEFORE UPDATE OF device,family,gateway '
        "ON restricted_owner_handoff_security BEGIN SELECT RAISE(ABORT,'HANDOFF_SCOPE_IMMUTABLE'); END")
    database.execute('CREATE TRIGGER restricted_owner_handoff_schema_immutable BEFORE UPDATE ON restricted_owner_handoff_schema '
        "BEGIN SELECT RAISE(ABORT,'HANDOFF_SCHEMA_IMMUTABLE'); END")
    require(legacy_rows(database) == legacy)
    return dict(version=2, legacy_sha256=digest, result='MIGRATED')


def current(database):
    pointer = database.execute('SELECT * FROM restricted_owner_handoff_current WHERE slot=1').fetchone()
    if pointer is None:
        require(database.execute('SELECT COUNT(*) FROM restricted_owner_handoff_operations').fetchone()[0] == 0)
        return None
    row = database.execute('SELECT * FROM restricted_owner_handoff_operations WHERE operation=? AND generation=?',
                           (pointer['operation'], pointer['generation'])).fetchone()
    require(row is not None)
    return row


def read(database, device, operation, generation):
    row = current(database)
    require(row is not None and row['operation'] == operation and row['generation'] == generation and row['device'] == device)
    return row


def security(database, device, family, gateway):
    row = database.execute('SELECT * FROM restricted_owner_handoff_security WHERE device=?', (device,)).fetchone()
    require(row is None or (row['family'] == family and row['gateway'] == gateway))
    return row


def ordered(next_view, previous):
    from .restricted import timestamp_ns
    order = timestamp_ns(next_view['issued_at']) - timestamp_ns(previous['issued_at'])
    return order > 0 or order == 0 and next_view == previous


def floor(response):
    import base64
    issuer = json.loads(base64.b64decode(response['issuer']['payload'], validate=True))
    return dict(issued_at=response['issued_at'], revision=response['revision'],
                minimum_crl=response['minimum_crl'], sequence=issuer['sequence'],
                issuer=issuer, directory=response['directory'])


def preserves(next_floor, previous):
    return (all(next_floor[name] >= previous[name] for name in ('issued_at', 'revision', 'minimum_crl', 'sequence'))
            and (next_floor['sequence'] > previous['sequence'] or next_floor['issuer'] == previous['issuer'])
            and ordered(next_floor['directory'], previous['directory']))


def receipt(database, operation):
    row = database.execute('SELECT * FROM restricted_owner_handoff_operations WHERE operation=?', (operation,)).fetchone()
    require(row is not None)
    pointer = current(database)
    return dict(operation=operation, generation=row['generation'], predecessor=row['predecessor'], phase=row['phase'],
                deadline=row['deadline'], prepare_inputs_sha256=hashlib.sha256(row['prepare_inputs'].encode()).hexdigest(),
                current=pointer is not None and pointer['operation'] == operation)


def prepare_preflight(database, operation, device, family, gateway, deadline, now):
    require(re.fullmatch(r'[a-z0-9-]{1,96}', operation) is not None)
    require(all(re.fullmatch(r'[0-9a-f]{32}', value) for value in (device, family, gateway)))
    require(type(deadline) is int)
    encoded = inputs(operation, device, family, gateway, deadline)
    previous = database.execute('SELECT * FROM restricted_owner_handoff_operations WHERE operation=?', (operation,)).fetchone()
    if previous is not None:
        require(previous['prepare_inputs'] == encoded)
        return dict(existing=receipt(database, operation))
    require(now < deadline <= now + 14400)
    previous = current(database)
    require(previous is None or previous['phase'] == 'CLEANED')
    require(database.execute("SELECT COUNT(*) FROM restricted_owner_handoff_operations WHERE phase!='CLEANED'").fetchone()[0] == 0)
    retained = security(database, device, family, gateway)
    generation = 1 if previous is None else previous['generation'] + 1
    predecessor = None if previous is None else previous['operation']
    saved = None if retained is None else retained['floor']
    return dict(existing=None, generation=generation, predecessor=predecessor, saved=saved, encoded=encoded)


def prepare(database, operation, device, family, gateway, deadline, now):
    transaction(database)
    plan = prepare_preflight(database, operation, device, family, gateway, deadline, now)
    if plan['existing'] is not None:
        return plan['existing']
    generation, predecessor, saved, encoded = (plan[name] for name in ('generation', 'predecessor', 'saved', 'encoded'))
    database.execute('INSERT INTO restricted_owner_handoff_operations VALUES (1,?,?,?,?,?,?,?,NULL,NULL,?,NULL,?,?,?,?,0)',
        (operation, device, family, gateway, 'PREPARED', deadline, '', saved, generation, predecessor, now, encoded))
    if predecessor is None:
        database.execute('INSERT INTO restricted_owner_handoff_current VALUES (1,?,?)', (operation, generation))
    else:
        changed = database.execute('UPDATE restricted_owner_handoff_current SET operation=?,generation=? '
            'WHERE slot=1 AND operation=? AND generation=?', (operation, generation, predecessor, generation-1))
        require(changed.rowcount == 1)
    return receipt(database, operation)


def checked(raw, row, now):
    from .restricted import directory
    return directory(raw.encode(), row['family'], row['gateway'], now=now)


def arm(database, device, operation, canary, return_view, invocation, now, *, generation):
    from .restricted import timestamp
    transaction(database)
    row = read(database, device, operation, generation)
    require(row['phase'] == 'PREPARED' and row['captured'] == 1)
    require(re.fullmatch('[0-9a-f]{32}', invocation) is not None and now + 1800 <= row['deadline'])
    canary, return_view = checked(encode(canary), row, now), checked(encode(return_view), row, now)
    require(canary['seeds'] != return_view['seeds'] and ordered(return_view, canary))
    saved = security(database, device, row['family'], row['gateway'])
    require(saved is not None and saved['floor'] == row['floor'])
    require(ordered(canary, json.loads(saved['floor'])['directory']))
    require(min(timestamp(canary['expires_at']), timestamp(return_view['expires_at'])) >= row['deadline'] + 600)
    database.execute('UPDATE restricted_owner_handoff_operations SET phase=?,canary=?,return_view=?,invocation=? '
        'WHERE operation=? AND generation=?', ('ACTIVE', encode(canary), encode(return_view), invocation, operation, generation))


def return_only(database, device, operation, *, generation):
    transaction(database)
    row = read(database, device, operation, generation)
    require(row['phase'] in ('PREPARED', 'ACTIVE', 'RETURN'))
    if row['phase'] != 'RETURN':
        database.execute('UPDATE restricted_owner_handoff_operations SET phase=? WHERE operation=? AND generation=?',
                         ('RETURN', operation, generation))


def record_floor(database, response, device, family, gateway, operation, generation, fetch_id):
    retained = security(database, device, family, gateway)
    next_floor = floor(response)
    require(retained is None or preserves(next_floor, json.loads(retained['floor'])))
    encoded = encode(next_floor)
    if retained is None:
        database.execute('INSERT INTO restricted_owner_handoff_security VALUES (?,?,?,?,?,?,?)',
                         (device, family, gateway, encoded, operation, generation, fetch_id))
    else:
        database.execute('UPDATE restricted_owner_handoff_security SET floor=?,operation=?,generation=?,fetch_id=? WHERE device=?',
                         (encoded, operation, generation, fetch_id, device))
    return encoded


def for_device(database, response, device, invocation, now, fetch_id):
    transaction(database)
    if not exists(database, SCHEMA):
        require(not exists(database, TABLE))
        return response
    row = current(database)
    if row is not None and row['device'] == device and row['phase'] != 'CLEANED':
        return select(database, response, device, invocation, now, fetch_id,
                      operation=row['operation'], generation=row['generation'])
    retained = database.execute('SELECT * FROM restricted_owner_handoff_security WHERE device=?', (device,)).fetchone()
    if retained is not None:
        require(response['directory']['family'] == retained['family']
                and all(seed['gateway'] == retained['gateway'] for seed in response['directory']['seeds']))
        record_floor(database, response, device, retained['family'], retained['gateway'],
                     retained['operation'], retained['generation'], fetch_id)
    return response


def select(database, response, device, invocation, now, fetch_id, *, operation, generation):
    transaction(database)
    row = read(database, device, operation, generation)
    require(row['phase'] != 'CLEANED')
    original = response['directory']
    require(original['family'] == row['family'] and all(seed['gateway'] == row['gateway'] for seed in original['seeds']))
    previous = json.loads(row['floor']) if row['floor'] else None
    phase = row['phase']
    if phase in ('PREPARED', 'ACTIVE') and (now >= row['deadline'] or phase == 'ACTIVE' and invocation != row['invocation']):
        phase = 'RETURN'
        database.execute('UPDATE restricted_owner_handoff_operations SET phase=? WHERE operation=? AND generation=?',
                         (phase, operation, generation))
    if phase == 'PREPARED':
        require(now < row['deadline'])
        require(row['captured'] == 0 or previous is not None and original == previous['directory'])
    elif phase == 'ACTIVE':
        response['directory'] = checked(row['canary'], row, now)
    elif phase == 'RETURN':
        saved = json.loads(row['return_view']) if row['return_view'] else original
        baseline = original if ordered(original, saved) else checked(row['return_view'], row, now)
        if previous is not None:
            require(ordered(baseline, previous['directory']) or ordered(original, previous['directory']))
        response['directory'] = original if ordered(original, baseline) else baseline
    from .restricted import timestamp
    response['expires_at'] = min(response['expires_at'], timestamp(response['directory']['expires_at']))
    require(response['expires_at'] > now)
    encoded = record_floor(database, response, device, row['family'], row['gateway'], operation, generation, fetch_id)
    database.execute('UPDATE restricted_owner_handoff_operations SET floor=?,fetch_id=?,captured=1 WHERE operation=? AND generation=?',
                     (encoded, fetch_id, operation, generation))
    return response


def cleanup(database, device, operation, current_response, *, generation):
    transaction(database)
    row = read(database, device, operation, generation)
    require(row['phase'] == 'RETURN' and row['floor'] is not None)
    retained = security(database, device, row['family'], row['gateway'])
    require(retained is not None and retained['floor'] == row['floor'])
    require(floor(current_response) == json.loads(retained['floor']))
    database.execute('UPDATE restricted_owner_handoff_operations SET phase=? WHERE operation=? AND generation=?',
                     ('CLEANED', operation, generation))
