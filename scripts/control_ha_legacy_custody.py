"""Opaque journal custody only: no database import, filesystem restore or activation."""
import base64
from dataclasses import dataclass, field
import hmac
import os
from pathlib import Path, PurePosixPath
import re
import secrets
import stat

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from scripts.control_ha_import import ImportRejected, digest, encoded, require
from scripts.control_ha_installed_inventory import KNOWN_FILES, STATES, Reader, Refused, shape, token
from scripts.control_ha_recovery_bundle import parse

PURPOSE = 'family-connect/legacy-journal-custody/v1/not-for-recovery'
MAGIC = b'FC-HA-CUSTODY\x00\x01'
SLOTS = frozenset(('RU', 'NL1', 'NL2', 'coordinator'))
MAX_FILE = 1024 * 1024
MAX_TOTAL = 64 * 1024 * 1024
MAX_PLAINTEXT = 128 * 1024 * 1024
MAX_ENTRIES = 32768
META = ('device', 'inode', 'uid', 'gid', 'mode', 'nlink', 'size', 'mtime_ns', 'ctime_ns')


@dataclass(frozen=True, repr=False)
class CustodyCheckpoint:
    identifier: str
    bundle_sha256: str
    manifest_sha256: str
    inventory_sha256: str


@dataclass(frozen=True, repr=False)
class PreservedJournals:
    trees: dict = field(repr=False)
    manifest_sha256: str

    def summary(self):
        return dict(result='OPAQUE_CUSTODY_VERIFIED', activation='FORBIDDEN',
            host_resume='NOT_AUTHORIZED', database_import='NOT_AUTHORIZED',
            history_validation='NOT_PERFORMED', approval_custody='NOT_ESTABLISHED',
            live_barrier='NOT_IMPLEMENTED', current_state_recovery='NOT_QUALIFIED',
            roles=len(self.trees), files=sum(entry['kind'] == 'file'
                for tree in self.trees.values() for entry in tree['entries'].values()),
            directories=sum(entry['kind'] == 'directory'
                for tree in self.trees.values() for entry in tree['entries'].values()) + len(self.trees))


def metadata(information):
    return dict(zip(META, (information.st_dev, information.st_ino, information.st_uid,
        information.st_gid, stat.S_IMODE(information.st_mode), information.st_nlink,
        information.st_size, information.st_mtime_ns, information.st_ctime_ns), strict=True))


def safe_path(value, *, absolute=False):
    require(type(value) is str and 0 < len(value.encode('utf-8')) <= 4096, 'CUSTODY_PATH')
    path = PurePosixPath(value)
    require(path.is_absolute() == absolute and str(path) == value and value != '/'
            and path.parts and len(path.parts) <= (64 if absolute else 8)
            and not any(part in ('.', '..') for part in path.parts)
            and '\\' not in value and not any(ord(character) < 32 for character in value), 'CUSTODY_PATH')
    return path


def capture_trees(roots):
    reader = Reader()
    total = 0
    trees = {}

    def visit(path, entries, prefix=''):
        nonlocal total
        for name in reader.names(path):
            relative = prefix + name
            safe_path(relative)
            require(sum(len(tree['entries']) for tree in trees.values()) < MAX_ENTRIES, 'CUSTODY_ENTRY_LIMIT')
            child = path / name
            with reader.opened(child) as descriptor:
                information = os.fstat(descriptor)
                directory = stat.S_ISDIR(information.st_mode)
                entry = dict(kind='directory' if directory else 'file', metadata=metadata(information))
                if not directory:
                    require(information.st_size <= MAX_FILE, 'CUSTODY_FILE_LIMIT')
                    with os.fdopen(os.dup(descriptor), 'rb') as stream:
                        raw = stream.read(MAX_FILE + 1)
                    total += len(raw)
                    require(len(raw) <= MAX_FILE and total <= MAX_TOTAL, 'CUSTODY_BYTE_LIMIT')
                    entry.update(sha256=digest(raw), body=base64.b64encode(raw).decode())
                entries[relative] = entry
            if directory:
                visit(child, entries, relative + '/')

    for slot, path in sorted(roots.items()):
        with reader.opened(path) as descriptor:
            require(stat.S_ISDIR(os.fstat(descriptor).st_mode), 'CUSTODY_ROOT_DIRECTORY')
            tree = dict(path=str(path), metadata=metadata(os.fstat(descriptor)), entries={})
            trees[slot] = tree
        visit(path, tree['entries'])
    reader.verify()
    return trees


def checked_metadata(value, *, directory):
    require(type(value) is dict and set(value) == set(META), 'CUSTODY_METADATA')
    require(all(type(item) is int and 0 <= item < 2**64 for item in value.values()), 'CUSTODY_METADATA')
    require(value['mode'] <= 0o7777 and value['nlink'] >= 1
            and (directory or value['nlink'] == 1), 'CUSTODY_METADATA')


def decode_body(value):
    require(type(value) is str and len(value) <= 4 * ((MAX_FILE + 2) // 3), 'CUSTODY_BODY_LIMIT')
    try:
        raw = base64.b64decode(value, validate=True)
    except (ValueError, UnicodeError):
        raise ImportRejected('CUSTODY_BODY_ENCODING') from None
    require(len(raw) <= MAX_FILE and base64.b64encode(raw).decode() == value, 'CUSTODY_BODY_ENCODING')
    return raw


def checked_trees(trees):
    require(type(trees) is dict and set(trees) == SLOTS, 'CUSTODY_ROLE_COVERAGE')
    paths, identities = [], set()
    restored, manifests = {}, {}
    total, count = 0, 0
    for slot, tree in sorted(trees.items()):
        require(type(tree) is dict and set(tree) == {'path', 'metadata', 'entries'}, 'CUSTODY_TREE_FIELDS')
        paths.append(safe_path(tree['path'], absolute=True))
        checked_metadata(tree['metadata'], directory=True)
        root_identity = (tree['metadata']['device'], tree['metadata']['inode'])
        require(root_identity not in identities, 'CUSTODY_ALIASED_OBJECT')
        identities.add(root_identity)
        require(type(tree['entries']) is dict, 'CUSTODY_TREE_ENTRIES')
        restored[slot] = dict(path=tree['path'], metadata=tree['metadata'], entries={})
        manifests[slot] = dict(path=tree['path'], metadata=tree['metadata'], entries={})
        for name, entry in tree['entries'].items():
            count += 1
            require(count <= MAX_ENTRIES, 'CUSTODY_ENTRY_LIMIT')
            path = safe_path(name)
            require(type(entry) is dict and entry.get('kind') in ('directory', 'file'), 'CUSTODY_ENTRY_FIELDS')
            directory = entry['kind'] == 'directory'
            require(set(entry) == ({'kind', 'metadata'} if directory else
                    {'kind', 'metadata', 'sha256', 'body'}), 'CUSTODY_ENTRY_FIELDS')
            checked_metadata(entry['metadata'], directory=directory)
            identity = (entry['metadata']['device'], entry['metadata']['inode'])
            require(identity not in identities, 'CUSTODY_ALIASED_OBJECT')
            identities.add(identity)
            for parent in path.parents:
                if str(parent) != '.':
                    ancestor = tree['entries'].get(str(parent))
                    require(type(ancestor) is dict and ancestor.get('kind') == 'directory', 'CUSTODY_PARENT')
            projection = {key: value for key, value in entry.items() if key != 'body'}
            manifests[slot]['entries'][name] = projection
            restored[slot]['entries'][name] = dict(projection)
            if not directory:
                raw = decode_body(entry['body'])
                total += len(raw)
                require(total <= MAX_TOTAL, 'CUSTODY_BYTE_LIMIT')
                require(len(raw) == entry['metadata']['size'] and entry['sha256'] == digest(raw), 'CUSTODY_FILE_DIGEST')
                restored[slot]['entries'][name]['body'] = raw
    require(all(left != right and left not in right.parents and right not in left.parents
                for index, left in enumerate(paths) for right in paths[index + 1:]), 'CUSTODY_OVERLAPPING_ROOTS')
    return restored, digest(encoded(manifests))


def children(tree, prefix=''):
    return sorted(name[len(prefix):] for name in tree['entries']
                  if name.startswith(prefix) and '/' not in name[len(prefix):])


def json_file(tree, name):
    entry = tree['entries'].get(name)
    require(entry is not None and entry['kind'] == 'file', 'CUSTODY_EXPECTED_DOCUMENT')
    value = parse(entry['body'])
    require(type(value) is dict, 'CUSTODY_DOCUMENT_SHAPE')
    return value


def bind_inventory(trees, inventory):
    require(type(inventory) is dict and set(inventory) == SLOTS - {'coordinator'}, 'CUSTODY_INVENTORY_COHORT')
    for slot, census in inventory.items():
        require(type(census) is dict and census.get('schema') == 1
                and census.get('purpose') == 'installed-shape-census/not-for-recovery'
                and census.get('observation') == 'NO_OBSERVED_CHANGE', 'CUSTODY_INVENTORY_STATUS')
        expected = census['node']
        tree = trees[slot]
        require(shape(children(tree)) == expected['root_shape'], 'CUSTODY_ROOT_COVERAGE')
        ledger = json_file(tree, 'completed.json') if expected['ledger_present'] else {}
        results = {}
        for operation, receipt in ledger.items():
            require(type(receipt) is dict, 'CUSTODY_LEDGER_SHAPE')
            result = receipt.get('result')
            results[token(operation)] = result if type(result) is str and result in (
                'CLEANED', 'CLEANED_FENCED_ROLLBACK') else 'OTHER'
        require(results == expected['ledger'], 'CUSTODY_LEDGER_COVERAGE')
        archives = {}
        for operation in children(tree, 'archive/'):
            prefix = 'archive/' + operation + '/'
            require(tree['entries'][prefix[:-1]]['kind'] == 'directory', 'CUSTODY_ARCHIVE_DIRECTORY')
            require(all(tree['entries'][prefix + name]['kind'] == 'file'
                        for name in children(tree, prefix)), 'CUSTODY_ARCHIVE_SHAPE')
            archives[token(operation)] = shape(children(tree, prefix))
        require(archives == expected['archives'], 'CUSTODY_ARCHIVE_COVERAGE')
    coordinator = trees['coordinator']
    expected = inventory['RU']['coordinator']
    require(shape(children(coordinator)) == expected['root_shape'], 'CUSTODY_COORDINATOR_COVERAGE')
    if expected['current'] is not None:
        current = json_file(coordinator, 'transaction.json')
        mode, state, gate = current.get('mode'), current.get('state'), current.get('gate', {})
        authorization = gate.get('authorization') if type(gate) is dict else None
        projection = dict(operation=token(current.get('operation_id')),
            state=state if type(state) is str and state in STATES else 'OTHER',
            mode=mode if type(mode) is str and mode in ('online', 'expired', 'offline', 'stopped') else 'ABSENT_OR_OTHER',
            gate_authorization=authorization if type(authorization) is str and authorization in
                ('OPERATOR_APPROVED_OUTAGE', 'FRESH_ZERO_SESSION_INVENTORY', 'OPERATOR_APPROVED_LEAF_CRL_SCHEDULE') else 'ABSENT_OR_OTHER',
            approval_field_present='approval' in current, handoff_field_present='authority_handoff' in current)
        require(projection == expected['current'], 'CUSTODY_CURRENT_MISMATCH')
    retained = []
    for name in children(coordinator, 'history/'):
        require(name.endswith('.json'), 'CUSTODY_HISTORY_NAME')
        retained.append(token(name[:-5]))
    require(sorted(retained) == sorted(expected['history_name_tokens']), 'CUSTODY_HISTORY_COVERAGE')
    require(('history' in coordinator['entries']) == expected['history_present'], 'CUSTODY_HISTORY_COVERAGE')
    adjuncts = []
    for name in children(coordinator):
        if name.endswith('.json') and name not in KNOWN_FILES:
            document = json_file(coordinator, name)
            operation = document.get('operation_id')
            adjuncts.append(dict(operation=token(operation) if type(operation) is str and 0 < len(operation) <= 256 else None,
                record_fields=sorted(set(document) & {'operation_id', 'state', 'files', 'sha256', 'plan', 'transaction', 'gate'})))
    require(adjuncts == expected['adjunct_json'], 'CUSTODY_ADJUNCT_COVERAGE')


def checked_document(document, expected):
    require(type(document) is dict and set(document) == {'version', 'purpose', 'identifier', 'inventory', 'trees'},
            'CUSTODY_FIELDS')
    require(type(document['version']) is int and document['version'] == 1 and document['purpose'] == PURPOSE,
            'CUSTODY_PURPOSE')
    require(document['identifier'] == expected.identifier, 'CUSTODY_IDENTIFIER')
    require(digest(encoded(document['inventory'])) == expected.inventory_sha256, 'CUSTODY_INVENTORY_DIGEST')
    trees, fingerprint = checked_trees(document['trees'])
    require(fingerprint == expected.manifest_sha256, 'CUSTODY_MANIFEST_DIGEST')
    bind_inventory(trees, document['inventory'])
    return PreservedJournals(trees, fingerprint)


def seal(roots, inventory, key, identifier):
    require(type(key) is bytes and len(key) == 32, 'CUSTODY_KEY_REQUIRED')
    require(type(identifier) is str and re.fullmatch('[a-f0-9]{32}', identifier), 'CUSTODY_IDENTIFIER')
    require(type(roots) is dict and set(roots) == SLOTS, 'CUSTODY_ROLE_COVERAGE')
    try:
        roots = {slot: Path(safe_path(str(path), absolute=True)) for slot, path in roots.items()}
        paths = list(roots.values())
        require(all(left != right and left not in right.parents and right not in left.parents
                    for index, left in enumerate(paths) for right in paths[index + 1:]), 'CUSTODY_OVERLAPPING_ROOTS')
        trees = capture_trees(roots)
        restored, fingerprint = checked_trees(trees)
        bind_inventory(restored, inventory)
        document = dict(version=1, purpose=PURPOSE, identifier=identifier, inventory=inventory, trees=trees)
        plaintext = encoded(document)
        require(len(plaintext) <= MAX_PLAINTEXT, 'CUSTODY_PLAINTEXT_LIMIT')
        nonce = secrets.token_bytes(12)
        bundle = MAGIC + nonce + AESGCM(key).encrypt(nonce, plaintext, MAGIC + PURPOSE.encode())
        return bundle, CustodyCheckpoint(identifier, digest(bundle), fingerprint, digest(encoded(inventory)))
    except ImportRejected:
        raise
    except (OSError, Refused, ValueError, TypeError, KeyError, RecursionError):
        raise ImportRejected('CUSTODY_SOURCE_REFUSED') from None


def inspect(bundle, key, expected):
    require(type(expected) is CustodyCheckpoint and type(expected.identifier) is str
            and re.fullmatch('[a-f0-9]{32}', expected.identifier), 'CUSTODY_CHECKPOINT_REQUIRED')
    require(all(type(value) is str and re.fullmatch('[a-f0-9]{64}', value) for value in
            (expected.bundle_sha256, expected.manifest_sha256, expected.inventory_sha256)), 'CUSTODY_CHECKPOINT_REQUIRED')
    require(type(key) is bytes and len(key) == 32, 'CUSTODY_KEY_REQUIRED')
    require(type(bundle) is bytes and len(MAGIC) + 28 < len(bundle) <= MAX_PLAINTEXT + len(MAGIC) + 28
            and bundle.startswith(MAGIC), 'CUSTODY_FORMAT')
    require(hmac.compare_digest(digest(bundle), expected.bundle_sha256), 'CUSTODY_CHECKPOINT_MISMATCH')
    offset = len(MAGIC)
    try:
        plaintext = AESGCM(key).decrypt(bundle[offset:offset + 12], bundle[offset + 12:], MAGIC + PURPOSE.encode())
        return checked_document(parse(plaintext), expected)
    except ImportRejected:
        raise
    except InvalidTag:
        raise ImportRejected('CUSTODY_AUTHENTICATION_FAILED') from None
    except (Refused, ValueError, TypeError, KeyError, RecursionError):
        raise ImportRejected('CUSTODY_DOCUMENT_REFUSED') from None
