"""Bounded external-file custody; never a writer fence or host activation tool."""
import base64
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import time

from scripts.control_ha_installed_inventory import Reader, pairs, require, stamp

PURPOSE = 'family-connect/external-file-custody/v1/not-for-activation'
MAGIC = b'FCFILES\x00\x01'
MAX_FILE = 1024 * 1024
MAX_BYTES = 64 * MAX_FILE
MAX_DOCUMENT = 96 * MAX_FILE
MAX_ENTRIES = 32768
ROOTS = tuple(Path(value) for value in ('/opt/apps/family_connect',
    '/var/lib/fc-profile-control', '/etc/fc-canonical-pinned-venv', '/etc/fc-canonical-mesh2'))
TREE_SUFFIXES = ('friends-restricted/renewal-state', 'friends-restricted/renewal-coordinator',
                 'friends-access/gateway-routing', 'operations')


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def logical(value):
    require(type(value) is str and re.fullmatch(r'[a-zA-Z0-9_.-]+(?:/[a-zA-Z0-9_.-]+)*', value)
            and len(value) <= 512 and len(value.split('/')) <= 12
            and not any(part in ('.', '..') for part in value.split('/')), 'LOGICAL_PATH')
    return PurePosixPath(value)


def source_path(value):
    require(type(value) is str and len(value) <= 4096, 'SOURCE_PATH')
    path = Path(value)
    require(path.is_absolute() and str(path) == value and '..' not in path.parts
            and all(ord(character) >= 32 for character in value)
            and any(root in path.parents for root in ROOTS), 'SOURCE_SCOPE')
    require(not any(word in path.name.lower() for word in ('metadata', '.sqlite', '.db', '-wal', '-shm')),
            'DATABASE_OR_OBSERVATIONS_EXCLUDED')
    return path


def checked_plan(plan):
    require(type(plan) is dict and set(plan) == {'slot', 'files', 'trees'}
            and plan['slot'] in ('RU', 'NL1', 'NL2'), 'PLAN_SHAPE')
    paths, names = [], []
    for kind in ('files', 'trees'):
        require(type(plan[kind]) is dict and len(plan[kind]) <= 128, 'PLAN_BOUNDS')
        for name, value in plan[kind].items():
            names.append(logical(name))
            path = source_path(value)
            require(kind == 'files' or any(str(path).endswith('/' + suffix) for suffix in TREE_SUFFIXES),
                    'TREE_SCOPE')
            paths.append(path)
    require(names and len(set(names)) == len(names) and len(set(paths)) == len(paths), 'DUPLICATE_PLAN_PATH')
    for values in (names, paths):
        require(not any(left in right.parents for left in values for right in values if left != right),
                'OVERLAPPING_PLAN_PATH')
    return plan


def capture(plan):
    plan = checked_plan(plan)
    reader, entries, total = Reader(), {}, 0
    started = time.time_ns()

    def visit(name, value, directory=False):
        nonlocal total
        logical(name)
        path = source_path(str(value))
        require(name not in entries and len(entries) < MAX_ENTRIES, 'CAPTURE_ENTRY_LIMIT')
        with reader.opened(path) as descriptor:
            information = os.fstat(descriptor)
            require(stat.S_ISDIR(information.st_mode) if directory else stat.S_ISREG(information.st_mode),
                    'CAPTURE_FILE_TYPE')
            entry = dict(path=str(path), stamp=list(stamp(information)), kind='directory' if directory else 'file')
            if not directory:
                require(information.st_size <= MAX_FILE, 'CAPTURE_FILE_LIMIT')
                with os.fdopen(os.dup(descriptor), 'rb') as stream:
                    raw = stream.read(MAX_FILE + 1)
                total += len(raw)
                require(len(raw) <= MAX_FILE and total <= MAX_BYTES, 'CAPTURE_BYTE_LIMIT')
                entry.update(body=base64.b64encode(raw).decode(), sha256=digest(raw))
            entries[name] = entry
        if directory:
            for child in reader.names(path):
                with reader.opened(path / child) as descriptor:
                    child_directory = stat.S_ISDIR(os.fstat(descriptor).st_mode)
                visit(name + '/' + child, path / child, child_directory)

    for name, value in sorted(plan['files'].items()):
        visit(name, value)
    for name, value in sorted(plan['trees'].items()):
        visit(name, value, True)
    reader.verify()
    document = dict(purpose=PURPOSE, plan=plan, started_at_ns=started, finished_at_ns=time.time_ns(),
                    entries=entries, writer_fence=False, recovery_authorized=False)
    require(len(encoded(document)) <= MAX_DOCUMENT, 'DOCUMENT_LIMIT')
    return document


def validate(document):
    require(type(document) is dict and set(document) == {'purpose', 'plan', 'started_at_ns', 'finished_at_ns',
            'entries', 'writer_fence', 'recovery_authorized'} and document['purpose'] == PURPOSE
            and document['writer_fence'] is False and document['recovery_authorized'] is False, 'DOCUMENT_SCOPE')
    require(all(type(document[key]) is int for key in ('started_at_ns', 'finished_at_ns'))
            and 0 < document['started_at_ns'] <= document['finished_at_ns'], 'DOCUMENT_TIME')
    plan, entries = checked_plan(document['plan']), document['entries']
    require(type(entries) is dict and 0 < len(entries) <= MAX_ENTRIES, 'DOCUMENT_ENTRIES')
    total = 0
    for name, entry in entries.items():
        logical(name)
        require(type(entry) is dict and entry.get('kind') in ('directory', 'file'), 'ENTRY_SHAPE')
        directory = entry['kind'] == 'directory'
        require(set(entry) == ({'path', 'stamp', 'kind'} if directory else
                              {'path', 'stamp', 'kind', 'body', 'sha256'}), 'ENTRY_FIELDS')
        path = source_path(entry['path'])
        expected = plan['files'].get(name) or plan['trees'].get(name)
        if expected is None:
            parents = [root for root in plan['trees'] if name.startswith(root + '/')]
            require(len(parents) == 1, 'ENTRY_OUTSIDE_PLAN')
            expected = str(Path(plan['trees'][parents[0]]) / name[len(parents[0])+1:])
            parent = str(PurePosixPath(name).parent)
            require(parent in entries and entries[parent].get('kind') == 'directory', 'ENTRY_PARENT')
        require(str(path) == expected and (name not in plan['files'] or not directory)
                and (name not in plan['trees'] or directory), 'ENTRY_PLAN_BINDING')
        observed = entry['stamp']
        require(type(observed) is list and len(observed) == 9
                and all(type(item) is int and 0 <= item < 2**64 for item in observed), 'ENTRY_STAMP')
        require((stat.S_ISDIR(observed[4]) if directory else stat.S_ISREG(observed[4]))
                and (observed[5] >= 1 if directory else observed[5] == 1), 'ENTRY_MODE')
        if not directory:
            require(type(entry['body']) is str and len(entry['body']) <= (MAX_FILE + 2) // 3 * 4, 'ENTRY_BODY')
            raw = base64.b64decode(entry['body'], validate=True)
            require(len(raw) <= MAX_FILE and len(raw) == observed[6] and digest(raw) == entry['sha256'], 'ENTRY_DIGEST')
            total += len(raw)
            require(total <= MAX_BYTES, 'DOCUMENT_BYTE_LIMIT')
    require(set(plan['files']) | set(plan['trees']) <= set(entries), 'MISSING_PLAN_ENTRY')
    return dict(files=sum(entry['kind'] == 'file' for entry in entries.values()), bytes=total,
                directories=sum(entry['kind'] == 'directory' for entry in entries.values()))


def witness(document):
    validate(document)
    return {entry['path']: entry['stamp'] for entry in document['entries'].values()}


def verify_witness(observations):
    require(type(observations) is dict and 0 < len(observations) <= MAX_ENTRIES, 'WITNESS_BOUNDS')
    reader = Reader()
    for value, expected in observations.items():
        path = source_path(value)
        require(type(expected) is list and len(expected) == 9, 'WITNESS_STAMP')
        reader.observed[str(path)] = tuple(expected)
    reader.verify()
    return dict(result='UNCHANGED_FILE_OBSERVATIONS', entries=len(observations), writer_fence=False)


def seal(document, key):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    validate(document)
    raw = encoded(document)
    require(len(raw) <= MAX_DOCUMENT and type(key) is bytes and len(key) == 32, 'SEAL_BOUNDS')
    nonce = os.urandom(12)
    capsule = MAGIC + nonce + AESGCM(key).encrypt(nonce, raw, PURPOSE.encode())
    return capsule, dict(ciphertext_sha256=digest(capsule), document_sha256=digest(raw))


def unseal(capsule, key, checkpoint):
    from cryptography.exceptions import InvalidTag
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    require(type(checkpoint) is dict and set(checkpoint) == {'ciphertext_sha256', 'document_sha256'}
            and all(type(value) is str and re.fullmatch('[a-f0-9]{64}', value)
                    for value in checkpoint.values()), 'CHECKPOINT_SHAPE')
    require(type(capsule) is bytes and len(MAGIC) + 28 <= len(capsule) <= MAX_DOCUMENT + 64
            and digest(capsule) == checkpoint['ciphertext_sha256'], 'STALE_OR_CHANGED_CAPSULE')
    require(capsule.startswith(MAGIC) and type(key) is bytes and len(key) == 32, 'CAPSULE_FORMAT')
    try:
        raw = AESGCM(key).decrypt(capsule[len(MAGIC):len(MAGIC)+12], capsule[len(MAGIC)+12:], PURPOSE.encode())
    except InvalidTag:
        raise ValueError('CAPSULE_AUTHENTICATION') from None
    require(digest(raw) == checkpoint['document_sha256'], 'DOCUMENT_PIN')
    document = json.loads(raw, object_pairs_hook=pairs)
    validate(document)
    require(encoded(document) == raw, 'DOCUMENT_ENCODING')
    return document


def restore(document, destination):
    summary = validate(document)
    destination = Path(destination)
    require(destination.is_absolute() and '..' not in destination.parts, 'RESTORE_PATH')
    reader = Reader()
    with reader.opened(destination.parent) as descriptor:
        information = os.fstat(descriptor)
        require(stat.S_ISDIR(information.st_mode) and information.st_uid == os.getuid()
                and stat.S_IMODE(information.st_mode) == 0o700, 'RESTORE_PARENT')
    destination.mkdir(mode=0o700)
    for name, entry in sorted(document['entries'].items()):
        target = destination / name
        parent = destination
        for part in PurePosixPath(name).parts[:-1]:
            parent /= part
            parent.mkdir(mode=0o700, exist_ok=True)
        if entry['kind'] == 'directory':
            target.mkdir(mode=0o700, exist_ok=True)
        else:
            raw = base64.b64decode(entry['body'], validate=True)
            descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            with os.fdopen(descriptor, 'wb') as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            require(target.read_bytes() == raw, 'RESTORE_READBACK')
    for root, directories, files in os.walk(destination, topdown=False):
        descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    descriptor = os.open(destination.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return dict(result='OFFLINE_FILE_READBACK_PASS', **summary, activation=False, full_recovery=False)
