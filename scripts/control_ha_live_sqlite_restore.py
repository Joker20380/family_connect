"""Authenticate and restore four live SQLite images to a NEW private offline directory.

No remote connections, application execution, PostgreSQL import or external-file
recovery. The key and checkpoint must come from independent owner-held custody.
"""
import argparse
from contextlib import closing
import hashlib
import hmac
import io
import json
import os
from pathlib import Path
import re
import resource
import sqlite3
import stat
import tarfile

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from scripts import control_ha_handoff_import as handoff
from scripts import control_ha_live_sqlite as live
from scripts.control_ha_import import MAX_ROWS, unique
from scripts.control_ha_sqlite_import import MANIFEST, definitions

MAGIC = b'FCLIVE4\x00\x02'
AAD = b'family-connect/live-four-store-custody/v2/consent-floors/not-for-activation'
LIMIT = 4 * live.LIMIT + 65536


def require(condition, code):
    live.require(condition, code)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def document(raw):
    return json.loads(raw, object_pairs_hook=unique,
                      parse_constant=lambda value: require(False, 'NONFINITE_JSON'))


def unpack(ciphertext, key, checkpoint):
    require(type(ciphertext) is bytes and 37 <= len(ciphertext) <= LIMIT, 'CAPSULE_BOUNDS')
    require(type(key) is bytes and len(key) == 32, 'KEY_BOUNDS')
    require(type(checkpoint) is dict and set(checkpoint) ==
            {'source_commit', 'source_sha256', 'ciphertext_sha256', 'archive_sha256'}, 'CHECKPOINT_SHAPE')
    for name, value in checkpoint.items():
        require(type(value) is str and re.fullmatch('[a-f0-9]{' +
                ('40' if name == 'source_commit' else '64') + '}', value), 'CHECKPOINT_PIN')
    require(hmac.compare_digest(digest(ciphertext), checkpoint['ciphertext_sha256']), 'STALE_OR_CHANGED_CAPSULE')
    require(ciphertext.startswith(MAGIC), 'CAPSULE_FORMAT')
    try:
        plaintext = AESGCM(key).decrypt(ciphertext[len(MAGIC):len(MAGIC)+12],
                                       ciphertext[len(MAGIC)+12:], AAD)
    except InvalidTag:
        raise ValueError('CAPSULE_AUTHENTICATION') from None
    require(hmac.compare_digest(digest(plaintext), checkpoint['archive_sha256']), 'ARCHIVE_PIN')
    expected = {name + '.sqlite' for name in live.STORES} | {'manifest.json'}
    with tarfile.open(fileobj=io.BytesIO(plaintext), mode='r:') as archive:
        members = archive.getmembers()
        require(len(members) == 5 and {member.name for member in members} == expected, 'ARCHIVE_COVERAGE')
        require(all(member.isfile() and member.sparse is None and not member.pax_headers and
                    0 < member.size <= (16384 if member.name == 'manifest.json' else live.LIMIT)
                    for member in members), 'ARCHIVE_ENTRY')
        files = {member.name: archive.extractfile(member).read() for member in members}
    manifest = document(files.pop('manifest.json'))
    require(type(manifest) is dict and set(manifest) == {'purpose', 'common_locked_at_ns',
            'captured_at_ns', 'barrier_seconds', 'deadline_seconds', 'stores',
            'external_files_captured', 'fleet_barrier', 'full_recovery', 'metadata_projection'}, 'MANIFEST_SHAPE')
    require(manifest['purpose'] == live.PURPOSE and manifest['metadata_projection'] == 'consent-floors-only' and
            all(manifest[name] is False for name in ('external_files_captured', 'fleet_barrier', 'full_recovery')),
            'CAPTURE_SCOPE')
    require(type(manifest['barrier_seconds']) in (int, float) and
            type(manifest['deadline_seconds']) in (int, float) and
            0 <= manifest['barrier_seconds'] < live.SECONDS and manifest['deadline_seconds'] == live.SECONDS,
            'CAPTURE_DEADLINE')
    require(all(type(manifest[name]) is int for name in ('common_locked_at_ns', 'captured_at_ns')) and
            0 < manifest['common_locked_at_ns'] <= manifest['captured_at_ns'] and
            manifest['captured_at_ns'] - manifest['common_locked_at_ns'] < live.SECONDS * 1000000000,
            'CAPTURE_TIME')
    require(type(manifest['stores']) is dict and set(manifest['stores']) == set(live.STORES), 'STORE_COVERAGE')
    images = {name: files[name + '.sqlite'] for name in live.STORES}
    for name, raw in images.items():
        record = manifest['stores'][name]
        require(type(record) is dict and set(record) == {'bytes', 'sha256', 'tables'} and
                type(record['bytes']) is int and record['bytes'] == len(raw) and
                record['sha256'] == digest(raw), 'STORE_PIN')
    return images, manifest


def validate(images, manifest):
    profile = json.loads(MANIFEST.read_bytes())
    overlay = handoff.manifest()['definitions']
    counts = {}
    for name, raw in images.items():
        with closing(sqlite3.connect(':memory:')) as database:
            database.deserialize(raw)
            database.execute('PRAGMA trusted_schema=OFF')
            database.execute('PRAGMA query_only=ON')
            database.set_progress_handler(lambda: 1, 2000000)
            expected = sorted(profile['stores'][name] + (overlay if name == 'registry' else []),
                              key=lambda row: row[1])
            require(definitions(database) == expected, 'SOURCE_SCHEMA_UNSUPPORTED')
            require(database.execute('PRAGMA quick_check').fetchall() == [('ok',)] and
                    not database.execute('PRAGMA foreign_key_check').fetchall(), 'SOURCE_INTEGRITY')
            require(database.execute('PRAGMA user_version').fetchone() == (0,) and
                    database.execute('PRAGMA application_id').fetchone() == (0,) and
                    database.execute('PRAGMA encoding').fetchone() == ('UTF-8',), 'SOURCE_PRAGMA')
            tables = [row[1] for row in expected if row[0] == 'table' and not row[1].startswith('sqlite_')]
            require(type(manifest['stores'][name]['tables']) is int and
                    len(tables) == manifest['stores'][name]['tables'], 'TABLE_COUNT')
            counts[name] = {table: database.execute('SELECT count(*) FROM "' + table + '"').fetchone()[0]
                            for table in tables}
            require(all(value <= MAX_ROWS for value in counts[name].values()), 'ROW_BOUNDS')
            if name == 'metadata':
                require(database.execute("SELECT count(*) FROM device_metadata WHERE payload!='{}'").fetchone() == (0,),
                        'METADATA_OBSERVATIONS_FORBIDDEN')
            if name == 'registry':
                handoff.validate(handoff.read(database),
                                 {row[0] for row in database.execute('SELECT device FROM devices')})
    return counts


def restore(ciphertext, key, checkpoint, output):
    images, manifest = unpack(ciphertext, key, checkpoint)
    counts = validate(images, manifest)
    require(output.is_absolute() and '..' not in output.parts and
            all(not parent.is_symlink() for parent in (output, *output.parents)), 'UNSAFE_OUTPUT')
    parent = output.parent.stat()
    require(parent.st_uid == os.geteuid() and stat.S_IMODE(parent.st_mode) == 0o700, 'PRIVATE_PARENT_REQUIRED')
    output.mkdir(mode=0o700, exist_ok=False)
    for name, raw in images.items():
        descriptor = os.open(output / (name + '.sqlite'), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        require(digest((output / (name + '.sqlite')).read_bytes()) == digest(raw), 'RESTORE_READBACK')
    directory = os.open(output, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)
    return dict(result='FOUR_STORE_OFFLINE_RESTORE_PASS', activation='FORBIDDEN',
                source_commit=checkpoint['source_commit'], ciphertext_sha256=digest(ciphertext),
                stores=len(images), tables=sum(len(value) for value in counts.values()),
                rows=sum(sum(value.values()) for value in counts.values()),
                retained_handoff_rows=[counts['registry'][table.name] for table in handoff.TABLES],
                exact_image_readback=True, external_files=False, full_recovery=False)


def private_read(path, limit):
    require(path.is_absolute() and '..' not in path.parts and
            all(not parent.is_symlink() for parent in (path, *path.parents)), 'UNSAFE_INPUT')
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as stream:
        metadata = os.fstat(stream.fileno())
        require(stat.S_ISREG(metadata.st_mode) and metadata.st_nlink == 1 and
                metadata.st_uid == os.geteuid() and stat.S_IMODE(metadata.st_mode) == 0o600,
                'PRIVATE_INPUT_REQUIRED')
        require(metadata.st_size <= limit, 'INPUT_BOUNDS')
        raw = stream.read(limit + 1)
        after = os.fstat(stream.fileno())
        require(len(raw) == metadata.st_size and
                (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) ==
                (metadata.st_dev, metadata.st_ino, metadata.st_size, metadata.st_mtime_ns), 'INPUT_CHANGED')
        require(path.stat().st_ino == metadata.st_ino, 'INPUT_REPLACED')
    return raw


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('capsule', 'key', 'checkpoint', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    os.umask(0o077)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    try:
        result = restore(private_read(args.capsule, LIMIT), private_read(args.key, 32),
                         document(private_read(args.checkpoint, 4096)), args.output)
    except Exception:
        print(json.dumps(dict(result='FOUR_STORE_OFFLINE_RESTORE_REFUSED', full_recovery=False)))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
