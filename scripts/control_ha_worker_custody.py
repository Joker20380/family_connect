"""Bounded legacy-worker custody; never an external-command fence or activation."""
import base64
from contextlib import ExitStack, closing
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import signal
import sqlite3
import stat
import time

from scripts.control_ha_installed_inventory import Reader, pairs
from scripts.control_ha_live_sqlite import identity, require

ROOT = Path('/opt/apps/family_connect')
ENVIRONMENT = Path('/etc/family-connect/product.env')
UNIT = Path('/etc/systemd/system/family-connect-peer-worker.service')
SECONDS = 0.25
LIMIT = 1024 * 1024
PURPOSE = 'family-connect/legacy-worker-custody/v1/no-dispatch'
MAGIC = b'FCWORK1\x00'
PINS = {
    'control/migrations/001_product.sql': 'deec6fb6af80c730f98a180a68e38e1d0a1d67b473f42e98cbd39b48fd68a54f',
    'control/migrations/002_provisioning.sql': '02a3b8a20b32b0167f034ad6e11f0ffeb35457b50c5dfc8ca1d4e54d0a90ac59',
    'control/migrations/003_gateway.sql': '094e0c5d54bfe50c772ee522b9df5461b0c3525bd128c0b105903674901c7586',
    'control/product/admin.py': '3cd6dc9785fc487a7cc82eb2e42e28804d09ce76a0e5aef812d5984785a1f511',
    'control/product/gateway_adapter.py': '0d74bfe91ed025ca2c926f57c1a176dc46b2903f697761492df93ea3ac54ee93',
    'control/product/gateways.py': 'fa22a576de90b92abaabe7e21bf34b5ac6d0ca3e9312b72f1528e28b7f66a1ec',
    'control/product/provisioning.py': '7f4f93ea4c86dedab1304f24be2692b8eaa37e41ef124a2d444b74ac80aff7bb',
    'control/product/store.py': '1c5024e18fbf67f2f4a8ece2ededdf9dd95acfc1cef92b43da06ea40c74f21b8',
    'deploy/product-peer-worker/worker.py': '7d4413684c940c54574e8ff2e62b9b6bd31beba22192d495cbc2dad9b0418485',
    'provisioning/envelope.py': '79276eb1016279f73b2f91704aee0f9cc0929f9ea736342fb65cf605c62c9ba6',
    'provisioning/models.py': '05207b55f462c35b0c37c246a24878726b2697181fe68bd3b6f05097acc58794',
}
FILES = {name: name for name in PINS} | {
    'gateways.json': 'state-product/gateways.json',
    **{name: 'state-v2/wireguard/' + name for name in ('android.pub', 'linux.pub', 'server.pub')},
}
SCHEMA_QUERY = 'SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name'


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def document(raw):
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda value: require(False, 'NONFINITE_JSON'))


def bindings(files):
    expected = dict(FC_PROJECT_ROOT=str(ROOT), FC_PRODUCT_DB=str(ROOT / 'state-product/db/product.db'),
                    FC_PRODUCT_DB_DIRECTORY=str(ROOT / 'state-product/db'),
                    FC_GATEWAYS=str(ROOT / 'state-product/gateways.json'),
                    FC_GATEWAY_KEYS=str(ROOT / 'state-v2/wireguard'))
    actual = {}
    for line in files['product.env'].decode().splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        name, value = line.split('=', 1)
        require(name not in actual and name in expected, 'ENVIRONMENT_SHAPE')
        tokens = shlex.split(value)
        require(len(tokens) == 1, 'ENVIRONMENT_VALUE')
        actual[name] = tokens[0]
    require(actual == expected, 'WORKER_PATH_BINDINGS')
    config = document(files['gateways.json'])
    require(type(config) is dict and len(config) == 1 and
            all(type(name) is str and re.fullmatch('[a-zA-Z0-9_.-]{1,128}', name) and
                value == dict(container='family-connect-pilot-gateway-1', keys=expected['FC_GATEWAY_KEYS'])
                for name, value in config.items()), 'GATEWAY_BINDINGS')
    return config


def capture(root=ROOT, environment=ENVIRONMENT, unit=UNIT):
    require(hasattr(sqlite3.Connection, 'setconfig') and
            hasattr(sqlite3, 'SQLITE_DBCONFIG_NO_CKPT_ON_CLOSE'), 'SQLITE_UNSUPPORTED')
    reader = Reader()
    files = {name: reader.raw(root / relative) for name, relative in FILES.items()}
    files.update({'product.env': reader.raw(environment), 'worker.service': reader.raw(unit)})
    bindings(files)
    require(all(digest(files[name]) == pin for name, pin in PINS.items()), 'INSTALLED_SOURCE_CHANGED')
    path = root / 'state-product/db/product.db'
    expected = identity(path)
    for target, mode in ((path, 0o600), (path.parent, 0o700)):
        info = target.stat()
        require(info.st_uid == os.getuid() and stat.S_IMODE(info.st_mode) == mode, 'PRIVATE_DATABASE_REQUIRED')
    require(512 <= path.stat().st_size <= LIMIT, 'DATABASE_BOUNDS')
    for suffix in ('-wal', '-shm', '-journal'):
        candidate = Path(str(path) + suffix)
        require(not candidate.exists() and not candidate.is_symlink(), 'DATABASE_SIDECAR_PRESENT')
    with path.open('rb') as stream:
        header = stream.read(100)
    require(header[:16] == b'SQLite format 3\x00' and header[18:20] == b'\x01\x01', 'ROLLBACK_JOURNAL_REQUIRED')
    require(signal.getsignal(signal.SIGALRM) == signal.SIG_DFL and
            signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0), 'ALARM_NOT_EXCLUSIVE')
    started = time.monotonic()
    signal.setitimer(signal.ITIMER_REAL, SECONDS)
    try:
        with ExitStack() as stack:
            connection = stack.enter_context(closing(sqlite3.connect(
                path.as_uri() + '?mode=rw', uri=True, timeout=0, isolation_level=None)))
            connection.setconfig(sqlite3.SQLITE_DBCONFIG_NO_CKPT_ON_CLOSE, True)
            connection.execute('PRAGMA trusted_schema=OFF')
            connection.execute('BEGIN IMMEDIATE')
            stack.callback(connection.rollback)
            descriptor = stack.enter_context(reader.opened(root / 'state-v2/wireguard/.enrollment.lock'))
            info = os.fstat(descriptor)
            require(stat.S_ISREG(info.st_mode) and info.st_size == 0 and
                    info.st_uid == os.getuid() and stat.S_IMODE(info.st_mode) == 0o600, 'LOCK_FILE_SHAPE')
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            locked_at = time.time_ns()
            require(identity(path) == expected, 'DATABASE_REPLACED')
            require(connection.execute('PRAGMA journal_mode').fetchone() == ('delete',), 'JOURNAL_CHANGED')
            require(connection.execute('PRAGMA page_count').fetchone()[0] *
                    connection.execute('PRAGMA page_size').fetchone()[0] <= LIMIT, 'DATABASE_BOUNDS')
            files['product.sqlite'] = connection.serialize()
            peers = root / 'state-v2/wireguard/peers'
            for name in reader.names(peers, 128):
                require(re.fullmatch(r'[a-zA-Z0-9_-]{1,128}\.conf', name), 'PEER_FILENAME')
                with reader.opened(peers / name) as descriptor:
                    info = os.fstat(descriptor)
                    require(info.st_uid == os.getuid() and stat.S_IMODE(info.st_mode) == 0o600, 'PRIVATE_PEER_REQUIRED')
                files['peers/' + name] = reader.raw(peers / name)
                require(len(files['peers/' + name]) <= 16384, 'PEER_BOUNDS')
            reader.verify()
            require(identity(path) == expected, 'DATABASE_REPLACED')
            captured_at = time.time_ns()
        elapsed = time.monotonic() - started
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
    require(elapsed < SECONDS, 'BARRIER_DEADLINE')
    return dict(purpose=PURPOSE, locked_at_ns=locked_at, captured_at_ns=captured_at,
                barrier_seconds=elapsed, activation=False, external_command_fence=False,
                files={name: base64.b64encode(raw).decode() for name, raw in files.items()})


def unpack(value):
    require(type(value) is dict and set(value) == {'purpose', 'locked_at_ns', 'captured_at_ns',
            'barrier_seconds', 'activation', 'external_command_fence', 'files'} and
            value['purpose'] == PURPOSE and value['activation'] is False and
            value['external_command_fence'] is False, 'DOCUMENT_SCOPE')
    require(all(type(value[name]) is int for name in ('locked_at_ns', 'captured_at_ns')) and
            0 < value['locked_at_ns'] <= value['captured_at_ns'] < value['locked_at_ns'] + SECONDS * 1e9 and
            type(value['barrier_seconds']) in (int, float) and 0 < value['barrier_seconds'] < SECONDS,
            'CAPTURE_DEADLINE')
    required = set(FILES) | {'product.env', 'worker.service', 'product.sqlite'}
    require(type(value['files']) is dict and required <= value['files'].keys() and
            len(value['files']) <= len(required) + 128 and
            all(re.fullmatch(r'peers/[a-zA-Z0-9_-]{1,128}\.conf', name)
                for name in value['files'].keys() - required), 'FILE_COVERAGE')
    files = {}
    for name, body in value['files'].items():
        require(type(body) is str and len(body) <= 2 * LIMIT, 'FILE_BOUNDS')
        raw = base64.b64decode(body, validate=True)
        require(base64.b64encode(raw).decode() == body and 0 < len(raw) <= LIMIT, 'FILE_ENCODING')
        require(not name.startswith('peers/') or len(raw) <= 16384, 'PEER_BOUNDS')
        files[name] = raw
    require(len(encoded(value)) <= 8 * LIMIT, 'DOCUMENT_BOUNDS')
    require(all(digest(files[name]) == pin for name, pin in PINS.items()), 'INSTALLED_SOURCE_CHANGED')
    bindings(files)
    return files


def validate(value):
    from control.product.gateway_adapter import DockerGateway
    from provisioning.models import GatewayCandidate
    files = unpack(value)
    for name in ('android.pub', 'linux.pub', 'server.pub'):
        GatewayCandidate.valid_key(files[name].decode().strip())
    for name, raw in files.items():
        if name.startswith('peers/'):
            public, routes = DockerGateway._parse(raw.decode('ascii'))
            GatewayCandidate.valid_key(public)
            require(routes, 'PEER_ROUTES')
    with closing(sqlite3.connect(':memory:')) as expected, closing(sqlite3.connect(':memory:')) as database:
        for name in sorted(name for name in PINS if name.endswith('.sql')):
            expected.executescript(files[name].decode())
        database.deserialize(files['product.sqlite'])
        database.execute('PRAGMA trusted_schema=OFF')
        database.execute('PRAGMA query_only=ON')
        database.set_progress_handler(lambda: 1, 2000000)
        require(database.execute(SCHEMA_QUERY).fetchall() == expected.execute(SCHEMA_QUERY).fetchall() and
                database.execute('PRAGMA user_version').fetchone() == (3,), 'DATABASE_SCHEMA')
        require(database.execute('PRAGMA integrity_check').fetchall() == [('ok',)] and
                database.execute('PRAGMA foreign_key_check').fetchall() == [], 'DATABASE_INTEGRITY')
        tables = [name for kind, name, owner, sql in expected.execute(SCHEMA_QUERY) if kind == 'table']
        rows = {}
        for name in tables:
            records = [encoded([{'blob': base64.b64encode(cell).decode()} if type(cell) is bytes else cell
                               for cell in row]) for row in database.execute('SELECT * FROM "' + name + '"')]
            rows[name] = dict(count=len(records), sha256=digest(b'\n'.join(sorted(records))))
        require({row[0] for row in database.execute('SELECT DISTINCT gateway_id FROM peer_outbox')}
                <= bindings(files).keys(), 'OUTBOX_GATEWAYS')
    return dict(result='WORKER_OFFLINE_CUSTODY_PASS', files=len(files), tables=rows,
                peers=sum(name.startswith('peers/') for name in files), activation=False,
                external_command_fence=False)


def seal(value, key):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    validate(value)
    require(type(key) is bytes and len(key) == 32, 'KEY_BOUNDS')
    raw, nonce = encoded(value), os.urandom(12)
    capsule = MAGIC + nonce + AESGCM(key).encrypt(nonce, raw, PURPOSE.encode())
    return capsule, dict(ciphertext_sha256=digest(capsule), document_sha256=digest(raw))


def unseal(capsule, key, checkpoint):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.exceptions import InvalidTag
    require(type(checkpoint) is dict and set(checkpoint) == {'ciphertext_sha256', 'document_sha256'} and
            all(type(pin) is str and re.fullmatch('[a-f0-9]{64}', pin) for pin in checkpoint.values()), 'CHECKPOINT_SHAPE')
    require(type(capsule) is bytes and len(MAGIC) + 28 <= len(capsule) <= 8 * LIMIT + 64 and
            digest(capsule) == checkpoint['ciphertext_sha256'], 'STALE_OR_CHANGED_CAPSULE')
    require(capsule.startswith(MAGIC) and type(key) is bytes and len(key) == 32, 'CAPSULE_FORMAT')
    try:
        raw = AESGCM(key).decrypt(capsule[len(MAGIC):len(MAGIC)+12], capsule[len(MAGIC)+12:], PURPOSE.encode())
    except InvalidTag:
        raise ValueError('CAPSULE_AUTHENTICATION') from None
    require(digest(raw) == checkpoint['document_sha256'], 'DOCUMENT_PIN')
    value = document(raw)
    require(encoded(value) == raw, 'DOCUMENT_ENCODING')
    validate(value)
    return value


def restore(value, destination):
    summary, files = validate(value), unpack(value)
    destination = Path(destination)
    require(destination.is_absolute() and '..' not in destination.parts, 'RESTORE_PATH')
    with Reader().opened(destination.parent) as descriptor:
        info = os.fstat(descriptor)
        require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid() and
                stat.S_IMODE(info.st_mode) == 0o700, 'PRIVATE_PARENT_REQUIRED')
    destination.mkdir(mode=0o700)
    for name, raw in files.items():
        target = destination / name
        parent = destination
        for part in Path(name).parts[:-1]:
            parent /= part
            parent.mkdir(mode=0o700, exist_ok=True)
        descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        require(target.read_bytes() == raw, 'RESTORE_READBACK')
    for directory, children, names in os.walk(destination, topdown=False):
        descriptor = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    descriptor = os.open(destination.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return summary
