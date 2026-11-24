"""Encrypted closed-scope OWNER runtime custody, never live restore or dispatch."""
import base64
from contextlib import closing
import json
import os
from pathlib import Path
import re
import shlex
import sqlite3
import stat
from urllib.parse import urlsplit

from control.friends.pseudonyms import Aliases
from scripts import control_ha_owner_capture as capture
from scripts.backup_paid_registry import inventory
from scripts.control_ha_installed_inventory import Reader, pairs
from scripts.control_ha_live_sqlite import require

PURPOSE = 'family-connect/owner-runtime-custody/v1/no-dispatch'
MAGIC = b'FCORUN1\x00'
LIMIT = 8 * capture.LIMIT
IMAGES = {
    'console': 'sha256:5ce824159e9f206c27ba92185097857382aa5fec71678ce5e728423509d1446a',
    'postgres': 'sha256:18cfe3ef5e6815560c98237d6216d1e5119702fb0f3894c8785dd58b8bbe5d73',
    'system_publisher': 'sha256:50de6f25a04c1127b127b3278314619c69eddeec229d0d4ad9b7e67c1d2ffeab',
}
FILES = frozenset(('synthetic.sqlite', 'panel-aliases.json', 'containers.json', 'origins.json',
    'env-original', 'env-runtime', 'subscriptions-source.json', 'technical-metadata-source.json',
    'transport-source.json', 'inventory-hmac.key', 'collector-aliases.json', 'publisher.token',
    *(f'compose-{number}.config' for number in range(8))))


def document(raw):
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda value: require(False, 'NONFINITE_JSON'))


def build(snapshot, extra_files, started_at_ns, finished_at_ns):
    require(type(snapshot) is dict and set(snapshot) == {'purpose', 'locked_at_ns', 'captured_at_ns',
            'barrier_seconds', 'files', 'activation', 'pg_pair_fence'} and snapshot['purpose'] == capture.PURPOSE and
            snapshot['activation'] is False and snapshot['pg_pair_fence'] is False, 'SNAPSHOT_SCOPE')
    require(set(snapshot['files']) == {'synthetic.sqlite', 'panel-aliases.json'} and
            set(extra_files) == FILES - snapshot['files'].keys(), 'FILE_COVERAGE')
    value = dict(snapshot, purpose=PURPOSE, started_at_ns=started_at_ns, finished_at_ns=finished_at_ns,
                 files=snapshot['files'] | {name: base64.b64encode(raw).decode() for name, raw in extra_files.items()})
    validate(value)
    return value


def unpack(value):
    require(type(value) is dict and set(value) == {'purpose', 'locked_at_ns', 'captured_at_ns', 'barrier_seconds',
            'files', 'activation', 'pg_pair_fence', 'started_at_ns', 'finished_at_ns'} and
            value['purpose'] == PURPOSE and value['activation'] is False and value['pg_pair_fence'] is False,
            'DOCUMENT_SCOPE')
    require(all(type(value[name]) is int for name in ('started_at_ns', 'locked_at_ns', 'captured_at_ns', 'finished_at_ns')) and
            0 < value['started_at_ns'] <= value['locked_at_ns'] <= value['captured_at_ns'] <= value['finished_at_ns'] and
            value['finished_at_ns'] - value['started_at_ns'] < 300 * 1000000000 and
            value['captured_at_ns'] - value['locked_at_ns'] < capture.SECONDS * 1000000000 and
            type(value['barrier_seconds']) in (int, float) and 0 < value['barrier_seconds'] < capture.SECONDS,
            'CAPTURE_DEADLINE')
    require(type(value['files']) is dict and set(value['files']) == FILES, 'FILE_COVERAGE')
    files = {}
    for name, body in value['files'].items():
        require(type(body) is str and len(body) <= 2 * capture.LIMIT, 'FILE_BOUNDS')
        raw = base64.b64decode(body, validate=True)
        require(base64.b64encode(raw).decode() == body and 0 < len(raw) <= capture.LIMIT, 'FILE_ENCODING')
        files[name] = raw
    require(len(capture.encoded(value)) <= LIMIT, 'DOCUMENT_BOUNDS')
    return files


def environments(files):
    containers = document(files['containers.json'])
    require(type(containers) is dict and set(containers) == set(IMAGES), 'CONTAINER_COVERAGE')
    environments = {}
    for role, value in containers.items():
        require(type(value) is dict and set(value) == {'name', 'id', 'image', 'started', 'environment', 'command',
                'entrypoint', 'mounts', 'labels'} and value['name'] == f'/fc-control-plane-0-{role}-1' and
                value['image'] == IMAGES[role] and type(value['id']) is str and re.fullmatch('[a-f0-9]{64}', value['id']),
                'CONTAINER_BINDING')
        require(type(value['environment']) is list and len(value['environment']) <= 64, 'ENVIRONMENT_BOUNDS')
        entries = [entry.split('=', 1) for entry in value['environment']]
        require(all(len(entry) == 2 for entry in entries) and len({entry[0] for entry in entries}) == len(entries),
                'ENVIRONMENT_SHAPE')
        environments[role] = dict(entries)
    require(all(environments[role].get('CONTROL_PLANE_MODE') == 'synthetic' for role in ('console', 'system_publisher')),
            'SYNTHETIC_MODE_REQUIRED')
    password = environments['postgres'].get('POSTGRES_PASSWORD')
    secret = environments['console'].get('DJANGO_SECRET_KEY')
    require(type(password) is str and len(password) >= 20 and not password.startswith('REPLACE_') and
            type(secret) is str and len(secret) >= 48 and not secret.startswith('REPLACE_') and
            all(environments[role].get('POSTGRES_PASSWORD') == password for role in IMAGES) and
            environments['system_publisher'].get('DJANGO_SECRET_KEY') == secret, 'CREDENTIAL_BINDING')
    for name in ('env-original', 'env-runtime'):
        selected = {}
        for line in files[name].decode().splitlines():
            if not line.strip() or line.lstrip().startswith('#'):
                continue
            key, raw = line.split('=', 1)
            values = shlex.split(raw)
            require(key not in selected and len(values) == 1, 'ENV_FILE_SHAPE')
            selected[key] = values[0]
        require(selected == dict(CONTROL_PLANE_MODE='synthetic', POSTGRES_PASSWORD=password, DJANGO_SECRET_KEY=secret),
                'ENV_FILE_BINDING')
    origin = urlsplit(environments['system_publisher'].get('FC_SYSTEM_PUBLISHER_ORIGIN', ''))
    require(origin.scheme == 'https' and origin.hostname and origin.username is None and origin.password is None and
            origin.path in ('', '/') and not origin.query and not origin.fragment, 'PUBLISHER_ORIGIN')
    require(re.fullmatch(b'[a-f0-9]{64}\n?', files['publisher.token']), 'PUBLISHER_TOKEN')
    return environments


def validate(value):
    files = unpack(value)
    environments(files)
    aliases = Aliases(document(files['collector-aliases.json']))
    aliases.check_key(files['inventory-hmac.key'])
    require(document(files['panel-aliases.json']) == aliases.document, 'PANEL_COLLECTOR_ALIASES')
    for name in ('subscriptions-source.json', 'technical-metadata-source.json'):
        config = document(files[name])
        require(type(config) is dict and set(config) == {'archive', 'archive_sha256', 'python'} and
                all(type(config[field]) is str and config[field].startswith('/') and '..' not in Path(config[field]).parts
                    for field in ('archive', 'python')) and re.fullmatch('[a-f0-9]{64}', config['archive_sha256']),
                'COLLECTOR_RUNTIME_BINDING')
    transport = document(files['transport-source.json'])
    require(type(transport) is dict and set(transport) == {'archives'} and type(transport['archives']) is dict,
            'TRANSPORT_CONFIGURATION')
    origins = document(files['origins.json'])
    require(type(origins) is dict and set(origins) == FILES - {'origins.json'} and
            all(type(source) is str and 0 < len(source) <= 4096 and
                not any(ord(character) < 32 for character in source) for source in origins.values()), 'ORIGIN_COVERAGE')
    with closing(sqlite3.connect(':memory:')) as database:
        database.deserialize(files['synthetic.sqlite'])
        database.execute('PRAGMA trusted_schema=OFF')
        database.execute('PRAGMA query_only=ON')
        database.set_progress_handler(lambda: 1, 2000000)
        require(capture.digest(capture.encoded(database.execute(capture.SCHEMA_QUERY).fetchall())) == capture.SCHEMA,
                'STORE_SCHEMA')
        require(database.execute('PRAGMA integrity_check').fetchall() == [('ok',)] and
                database.execute('PRAGMA foreign_key_check').fetchall() == [], 'STORE_INTEGRITY')
        require(database.execute('SELECT version FROM control_plane_fixture WHERE singleton=1').fetchone() ==
                ('CONTROL-PLANE-1-SYNTHETIC-v2',) and
                database.execute('SELECT count(*) FROM devices').fetchone() == (50,) and
                database.execute('SELECT count(*) FROM control_plane_devices').fetchone() == (50,) and
                database.execute('SELECT device FROM devices EXCEPT SELECT device FROM control_plane_devices').fetchone() is None,
                'SYNTHETIC_FIXTURE_REQUIRED')
        rows = inventory(database)
    return dict(result='OWNER_RUNTIME_OFFLINE_CUSTODY_PASS', files=len(files), tables=rows,
                alias_generation=aliases.generation, images=len(IMAGES), activation=False, pg_pair_fence=False)


def seal(value, key):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    validate(value)
    require(type(key) is bytes and len(key) == 32, 'KEY_BOUNDS')
    raw, nonce = capture.encoded(value), os.urandom(12)
    capsule = MAGIC + nonce + AESGCM(key).encrypt(nonce, raw, PURPOSE.encode())
    return capsule, dict(ciphertext_sha256=capture.digest(capsule), document_sha256=capture.digest(raw))


def unseal(capsule, key, checkpoint):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.exceptions import InvalidTag
    require(type(checkpoint) is dict and set(checkpoint) == {'ciphertext_sha256', 'document_sha256'} and
            all(type(pin) is str and re.fullmatch('[a-f0-9]{64}', pin) for pin in checkpoint.values()), 'CHECKPOINT_SHAPE')
    require(type(capsule) is bytes and len(MAGIC) + 28 <= len(capsule) <= LIMIT + 64 and
            capture.digest(capsule) == checkpoint['ciphertext_sha256'], 'STALE_OR_CHANGED_CAPSULE')
    require(capsule.startswith(MAGIC) and type(key) is bytes and len(key) == 32, 'CAPSULE_FORMAT')
    try:
        raw = AESGCM(key).decrypt(capsule[len(MAGIC):len(MAGIC)+12], capsule[len(MAGIC)+12:], PURPOSE.encode())
    except InvalidTag:
        raise ValueError('CAPSULE_AUTHENTICATION') from None
    require(capture.digest(raw) == checkpoint['document_sha256'], 'DOCUMENT_PIN')
    value = document(raw)
    require(capture.encoded(value) == raw, 'DOCUMENT_ENCODING')
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
        descriptor = os.open(destination / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        require((destination / name).read_bytes() == raw, 'RESTORE_READBACK')
    for path in (destination, destination.parent):
        descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    return summary
