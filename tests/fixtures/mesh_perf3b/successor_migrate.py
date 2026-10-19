import argparse
import ast
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import stat
import subprocess
import sys
import time
import zipfile


UNIT = 'family-connect-friends-http-candidate.service'
BASE = '12ca0c72a89ff20c1b3c70a1182a2d5d98d4d78d25e7a079bb4d75bdf34060ed'


def require(condition, reason):
    if not condition:
        raise RuntimeError(reason)


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def private(file):
    info = file.lstat()
    require(stat.S_ISREG(info.st_mode) and info.st_uid == os.geteuid()
            and stat.S_IMODE(info.st_mode) == 0o600 and info.st_nlink == 1, 'PRIVATE_FILE_REQUIRED')
    return file.read_bytes()


def durable(file, value):
    descriptor = os.open(file, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'wb') as handle:
        handle.write(encoded(value))
        handle.flush()
        os.fsync(handle.fileno())
    descriptor = os.open(file.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


@contextlib.contextmanager
def locked(file):
    descriptor = os.open(file, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        info = os.fstat(descriptor)
        require(stat.S_ISREG(info.st_mode) and info.st_uid == os.geteuid()
                and stat.S_IMODE(info.st_mode) == 0o600 and info.st_nlink == 1, 'LOCK_PERMISSIONS')
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally:
        os.close(descriptor)


def service_state():
    raw = subprocess.check_output(['systemctl', 'show', UNIT,
        '--property=ActiveState,SubState,MainPID,InvocationID,NRestarts'], text=True, timeout=15)
    return dict(line.split('=', 1) for line in raw.splitlines())


def database_path(arguments, archive):
    with zipfile.ZipFile(archive) as package:
        tree = ast.parse(package.read('friends_http.py'))
    assignments = [node.value for node in tree.body if isinstance(node, ast.Assign)
                   and any(isinstance(target, ast.Name) and target.id == 'ROOT' for target in node.targets)]
    require(len(assignments) == 1, 'API_ROOT_DEFAULT_AMBIGUOUS')
    value = assignments[0]
    require(isinstance(value, ast.Call) and isinstance(value.func, ast.Name)
            and value.func.id == 'Path' and len(value.args) == 1 and not value.keywords, 'API_ROOT_DEFAULT_UNSUPPORTED')
    default = ast.literal_eval(value.args[0])
    require(isinstance(default, str), 'API_ROOT_DEFAULT_TYPE')
    require(arguments.count('--root') <= 1, 'API_ROOT_ARGUMENT_AMBIGUOUS')
    selected = arguments[arguments.index('--root')+1] if '--root' in arguments else default
    root = Path(selected)
    require(root.is_absolute(), 'API_ROOT_MUST_BE_ABSOLUTE')
    return root/'access.db'


def connection(file):
    database = sqlite3.connect('file:'+str(file)+'?mode=ro', uri=True, timeout=15)
    database.row_factory = sqlite3.Row
    return database


def canonical_legacy(database):
    return [dict(row) for row in database.execute('SELECT * FROM restricted_owner_handoff ORDER BY slot')]


def readback(file, expected):
    with contextlib.closing(connection(file)) as database:
        require(database.execute('PRAGMA integrity_check').fetchone()[0] == 'ok', 'DATABASE_INTEGRITY')
        legacy = canonical_legacy(database)
        require(digest(encoded(legacy)) == expected, 'LEGACY_HISTORY_CHANGED')
        schema = database.execute('SELECT * FROM restricted_owner_handoff_schema WHERE version=2').fetchone()
        require(schema is not None and schema['legacy_sha256'] == expected, 'SCHEMA_MISMATCH')
        current = database.execute('SELECT h.* FROM restricted_owner_handoff_current c JOIN restricted_owner_handoff_operations h '
            'ON c.operation=h.operation AND c.generation=h.generation WHERE c.slot=1').fetchone()
        require(current is not None and current['phase'] == 'CLEANED', 'UNFINISHED_OPERATION')
        require(database.execute("SELECT COUNT(*) FROM restricted_owner_handoff_operations WHERE phase!='CLEANED'").fetchone()[0] == 0,
                'CONFLICTING_OPERATION')
        historical = database.execute('SELECT * FROM restricted_owner_handoff_operations WHERE operation=?', (legacy[0]['operation'],)).fetchone()
        require(historical is not None and {name:historical[name] for name in legacy[0]} == legacy[0], 'HISTORY_COPY_CHANGED')
        security = database.execute('SELECT * FROM restricted_owner_handoff_security WHERE device=?', (legacy[0]['device'],)).fetchone()
        require(security is not None and security['floor'] == legacy[0]['floor']
                and security['family'] == legacy[0]['family'] and security['gateway'] == legacy[0]['gateway'], 'SECURITY_STATE_CHANGED')
        schema_rows = [tuple(row) for row in database.execute("SELECT type,name,tbl_name,sql FROM sqlite_master WHERE name LIKE 'restricted_owner_handoff%' ORDER BY type,name")]
        return dict(schema_version=2, schema_sha256=digest(encoded(schema_rows)), legacy_sha256=expected,
            canonical_history_preserved=True, retained_security_preserved=True, unfinished_count=0,
            current_operation=current['operation'], current_generation=current['generation'], phase=current['phase'],
            operation_count=database.execute('SELECT COUNT(*) FROM restricted_owner_handoff_operations').fetchone()[0])


def commit_migration(access, handoff, expected):
    with access.db() as database:
        require(digest(encoded(canonical_legacy(database))) == expected, 'LEGACY_CHANGED_BEFORE_COMMIT')
        result = handoff.migrate(database)
        require(result['legacy_sha256'] == expected, 'MIGRATION_HISTORY_MISMATCH')
    return result


def allocation_probe(file, destination, access_type, handoff, expected):
    descriptor = os.open(destination, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    os.close(descriptor)
    with contextlib.closing(connection(file)) as source, contextlib.closing(sqlite3.connect(destination)) as target:
        source.backup(target)
    access = access_type(destination)
    now = int(time.time())
    with access.db() as database:
        original = dict(handoff.current(database))
        require(original['phase'] == 'CLEANED', 'PROBE_REQUIRES_CLEANED_BASELINE')
        allocated = handoff.prepare(database, 'snapshot-only-successor-probe', original['device'], original['family'], original['gateway'], now+2400, now)
        row = handoff.current(database)
        require(row['floor'] == original['floor'] and row['captured'] == 0 and row['predecessor'] == original['operation'], 'PROBE_FLOOR_LOSS')
    with access.db() as database:
        repeated = handoff.prepare(database, 'snapshot-only-successor-probe', original['device'], original['family'], original['gateway'], now+2400, now)
        require(repeated == allocated, 'PROBE_NOT_IDEMPOTENT')
        require(digest(encoded(canonical_legacy(database))) == expected, 'PROBE_CHANGED_HISTORY')
    return dict(result='PASS_ON_FULL_DB_COPY_ONLY', generation=allocated['generation'], retained_floor=True,
                original_database_unchanged=readback(file, expected)['unfinished_count'] == 0)


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('apply', 'readback'))
    parser.add_argument('--stage', type=Path, required=True)
    parser.add_argument('--manifest-sha256', required=True)
    arguments = parser.parse_args()
    stage = arguments.stage
    require(os.geteuid() == 0 and stage.is_absolute() and not stage.is_symlink(), 'ROOT_PRIVATE_STAGE_REQUIRED')
    require(stage.stat().st_uid == 0 and stat.S_IMODE(stage.stat().st_mode) == 0o700, 'STAGE_PERMISSIONS')
    manifest_raw = private(stage/'manifest.json')
    require(digest(manifest_raw) == arguments.manifest_sha256, 'MANIFEST_MISMATCH')
    manifest = json.loads(manifest_raw)
    candidate = stage/'friends-http-successor.pyz'
    require(digest(private(candidate)) == manifest['candidate_sha256'] and manifest['original_api_sha256'] == BASE, 'CANDIDATE_MISMATCH')
    require(digest(private(stage/'successor_migrate.py')) == manifest['successor_migrate.py_sha256'], 'OPERATOR_MISMATCH')
    before = service_state()
    require(before['ActiveState'] == 'active' and before['SubState'] == 'running' and before['NRestarts'] == '0', 'API_NOT_STABLE')
    process = Path('/proc')/before['MainPID']
    args = [part.decode() for part in (process/'cmdline').read_bytes().split(b'\0') if part]
    archives = [Path(part) for part in args if part.endswith('.pyz')]
    require(len(archives) == 1 and digest(archives[0].read_bytes()) == BASE, 'INCOMPATIBLE_API_WRITER')
    dropin = Path('/etc/systemd/system')/(UNIT+'.d/97-mesh-perf-3b.conf')
    require(not dropin.exists(), 'API_OVERRIDE_PRESENT')
    environment = dict(part.decode().split('=', 1) for part in (process/'environ').read_bytes().split(b'\0') if part)
    material = Path(environment['FC_FRIENDS_RESTRICTED_DIR'])
    file = database_path(args, archives[0])
    renewal = json.loads(private(material/'renewal/controller.json'))
    with locked(Path(renewal['coordinator_state'])/'operation.lock'), locked(stage/'migration.lock'):
        require(service_state() == before, 'API_CHANGED_RETRY_READBACK')
        if arguments.action == 'readback':
            intent = json.loads(private(stage/'migration-intent.json'))
            result = readback(file, intent['legacy_sha256'])
            result.update(result='READBACK_CONFIRMED', receipt_exists=(stage/'migration-receipt.json').exists(), api_unchanged=True)
            print(json.dumps(result, sort_keys=True))
            return
        require(not (stage/'migration-intent.json').exists(), 'READBACK_REQUIRED_NO_BLIND_RETRY')
        with contextlib.closing(connection(file)) as database:
            legacy = canonical_legacy(database)
            require(len(legacy) == 1 and legacy[0]['phase'] == 'CLEANED'
                    and legacy[0]['canary'] is None and legacy[0]['return_view'] is None, 'EXPECTED_CLEANED_STATE_REQUIRED')
            require(database.execute("SELECT 1 FROM sqlite_master WHERE name='restricted_owner_handoff_schema'").fetchone() is None,
                    'SCHEMA_ALREADY_PRESENT_READBACK_REQUIRED')
            snapshot = stage/'access.before.db'
            descriptor = os.open(snapshot, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
            os.close(descriptor)
            with contextlib.closing(sqlite3.connect(snapshot)) as backup:
                database.backup(backup)
            descriptor = os.open(snapshot, os.O_RDONLY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
        expected = digest(encoded(legacy))
        durable(stage/'migration-intent.json', dict(utc_epoch=time.time(), baseline_api=BASE, state=before,
            snapshot_sha256=digest(private(snapshot)), legacy_sha256=expected, manifest_sha256=arguments.manifest_sha256))
        sys.path.insert(0, str(candidate))
        from control.friends.access import Access
        from control.friends import owner_handoff
        require(owner_handoff.__file__.startswith(str(candidate)+'/'), 'WRONG_MIGRATION_MODULE')
        commit_migration(Access(file), owner_handoff, expected)
        result = readback(file, expected)
        result['successor_probe'] = allocation_probe(file, stage/'allocation-probe.db', Access, owner_handoff, expected)
        require(service_state() == before and not dropin.exists(), 'API_CHANGED_AFTER_COMMIT_READBACK_REQUIRED')
        result.update(result='COMMITTED', utc_epoch=time.time(), snapshot_sha256=digest(private(snapshot)),
            candidate_sha256=manifest['candidate_sha256'], manifest_sha256=arguments.manifest_sha256,
            api_unchanged=True, api_restart=False, runtime_overlay_active=False, live_operation_created=False)
        durable(stage/'migration-receipt.json', result)
        print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
