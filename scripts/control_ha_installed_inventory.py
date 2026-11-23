"""Read-only shape census, not a recovery capsule, signature check or writer barrier."""
import argparse
from collections import Counter
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import stat


MAX_ENTRIES = 4096
MAX_DOCUMENT = 1024 * 1024
MAX_READ = 16 * MAX_DOCUMENT
MAX_OBSERVED = 32768
KNOWN_FILES = frozenset(('operation.lock completed.json owner.json transaction.json plan.json '
    'last-receipt.json prepared-plan.json files.json reconciliation.json directory-before.json '
    'directory-accepted.json authority-request.json online-origin.json archive-manifest.json '
    'manifest.json origin.json owner-before-cleanup.json rollback-terminal.json rollback-registry-overlay.json services-before.json '
    'online-prepared.json online-published.json revocations.pem.before revocations.pem.staged '
    'issuer.json.before issuer.json.staged issuer-NL2.json.before issuer-NL2.json.staged '
    'gateway.json.before gateway.json.staged').split())
RESULTS = frozenset(('CLEANED', 'CLEANED_FENCED_ROLLBACK'))
STATES = frozenset(('COMMITTED', 'ABORTED', 'ACQUIRING', 'PREPARED', 'CLEANING', 'RECOVERY_REQUIRED',
                    'ONLINE_RECOVERY_REQUIRED', 'ONLINE_EMERGENCY_REQUIRED', 'ABORTED_FENCED'))


class Refused(Exception):
    pass


def require(condition, code):
    if not condition:
        raise Refused(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def token(value):
    require(type(value) is str and 0 < len(value) <= 256, 'IDENTIFIER_SHAPE')
    return sha(value.encode())


def pairs(items):
    result = {}
    for key, value in items:
        require(key not in result, 'DUPLICATE_JSON_KEY')
        result[key] = value
    return result


def stamp(information):
    return tuple(getattr(information, name) for name in
                 ('st_dev', 'st_ino', 'st_uid', 'st_gid', 'st_mode', 'st_nlink',
                  'st_size', 'st_mtime_ns', 'st_ctime_ns'))


class Reader:
    def __init__(self):
        self.observed = {}
        self.bytes_read = 0

    @contextmanager
    def opened(self, path):
        path = Path(path)
        require(path.is_absolute() and '..' not in path.parts and len(path.parts) > 1, 'PATH_SHAPE')
        descriptor = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
        try:
            for index, part in enumerate(path.parts[1:]):
                flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
                if index < len(path.parts) - 2:
                    flags |= os.O_DIRECTORY
                successor = os.open(part, flags, dir_fd=descriptor)
                os.close(descriptor)
                descriptor = successor
            information = os.fstat(descriptor)
            require(stat.S_ISREG(information.st_mode) or stat.S_ISDIR(information.st_mode), 'FILE_TYPE')
            require(not stat.S_ISREG(information.st_mode) or information.st_nlink == 1, 'HARDLINK')
            before = stamp(information)
            require(str(path) not in self.observed or self.observed[str(path)] == before, 'OBSERVATION_CHANGED')
            require(str(path) in self.observed or len(self.observed) < MAX_OBSERVED, 'METADATA_LIMIT')
            self.observed[str(path)] = before
            yield descriptor
            require(stamp(os.fstat(descriptor)) == before, 'OBSERVATION_CHANGED')
        finally:
            os.close(descriptor)

    def names(self, path, limit=MAX_ENTRIES):
        with self.opened(path) as descriptor:
            require(stat.S_ISDIR(os.fstat(descriptor).st_mode), 'DIRECTORY_REQUIRED')
            with os.scandir(descriptor) as entries:
                names = []
                for entry in entries:
                    require(len(names) < limit, 'ENTRY_LIMIT')
                    names.append(entry.name)
            return sorted(names)

    def raw(self, path):
        with self.opened(path) as descriptor:
            information = os.fstat(descriptor)
            require(stat.S_ISREG(information.st_mode), 'REGULAR_FILE_REQUIRED')
            require(information.st_size <= MAX_DOCUMENT, 'DOCUMENT_LIMIT')
            with os.fdopen(os.dup(descriptor), 'rb') as stream:
                raw = stream.read(MAX_DOCUMENT + 1)
            self.bytes_read += len(raw)
            require(len(raw) <= MAX_DOCUMENT and self.bytes_read <= MAX_READ, 'READ_LIMIT')
            return raw

    def document(self, path):
        document = json.loads(self.raw(path), object_pairs_hook=pairs)
        require(type(document) is dict, 'DOCUMENT_SHAPE')
        return document

    def verify(self):
        for path in tuple(self.observed):
            with self.opened(path):
                pass


def shape(names):
    known = [name for name in names if name in KNOWN_FILES or re.fullmatch(r'start-intent-[0-9]{1,3}\.json', name)]
    return dict(known=known, other_count=len(names) - len(known))


def node_inventory(reader, root):
    names = reader.names(root, 128)
    ledger = reader.document(root / 'completed.json') if 'completed.json' in names else {}
    require(len(ledger) <= MAX_ENTRIES, 'LEDGER_LIMIT')
    results = {}
    for operation, receipt in ledger.items():
        require(type(receipt) is dict, 'LEDGER_SHAPE')
        value = receipt.get('result')
        results[token(operation)] = value if type(value) is str and value in RESULTS else 'OTHER'
    archives, histogram = {}, Counter()
    if 'archive' in names:
        for operation in reader.names(root / 'archive'):
            directory = root / 'archive' / operation
            files = reader.names(directory, 128)
            for name in files:
                with reader.opened(directory / name) as descriptor:
                    require(stat.S_ISREG(os.fstat(descriptor).st_mode), 'ARCHIVE_FILE_TYPE')
            summary = shape(files)
            archives[token(operation)] = summary
            histogram[json.dumps(summary, sort_keys=True)] += 1
    return dict(root_shape=shape(names), ledger_present='completed.json' in names,
        owner_present='owner.json' in names, ledger=results, archives=archives,
        result_counts=dict(Counter(results.values())), archive_count=len(archives),
        missing_archives=len(set(results) - set(archives)),
        unledgered_archives=len(set(archives) - set(results)),
        shapes=[dict(count=count, **json.loads(value)) for value, count in sorted(histogram.items())])


def coordinator_inventory(reader, root):
    names = reader.names(root, 128)
    current = reader.document(root / 'transaction.json') if 'transaction.json' in names else None
    retained = []
    if 'history' in names:
        for name in reader.names(root / 'history'):
            require(name.endswith('.json'), 'HISTORY_NAME')
            with reader.opened(root / 'history' / name) as descriptor:
                require(stat.S_ISREG(os.fstat(descriptor).st_mode), 'HISTORY_FILE_TYPE')
            retained.append(token(name[:-5]))
    summary = None
    if current is not None:
        mode = current.get('mode')
        state = current.get('state')
        gate = current.get('gate', {})
        authorization = gate.get('authorization') if type(gate) is dict else None
        summary = dict(operation=token(current.get('operation_id')),
            state=state if type(state) is str and state in STATES else 'OTHER',
            mode=mode if type(mode) is str and mode in ('online', 'expired', 'offline', 'stopped') else 'ABSENT_OR_OTHER',
            gate_authorization=authorization if type(authorization) is str and authorization in
                ('OPERATOR_APPROVED_OUTAGE', 'FRESH_ZERO_SESSION_INVENTORY', 'OPERATOR_APPROVED_LEAF_CRL_SCHEDULE') else 'ABSENT_OR_OTHER',
            approval_field_present='approval' in current,
            handoff_field_present='authority_handoff' in current)
    adjuncts = []
    for name in names:
        if name.endswith('.json') and name not in KNOWN_FILES:
            document = reader.document(root / name)
            operation = document.get('operation_id')
            adjuncts.append(dict(operation=token(operation) if type(operation) is str and 0 < len(operation) <= 256 else None,
                record_fields=sorted(set(document) & {'operation_id', 'state', 'files', 'sha256', 'plan', 'transaction', 'gate'})))
    return dict(root_shape=shape(names), current=summary, history_present='history' in names,
                history_name_tokens=retained, history_count=len(retained), adjunct_json=adjuncts)


def installed_source(reader, config_path, runtime):
    config = reader.document(config_path)
    declared = config.get('source_files')
    require(type(declared) is dict and 1 <= len(declared) <= 128, 'SOURCE_MANIFEST')
    actual = {}
    for name, expected in declared.items():
        require(re.fullmatch(r'[a-z][a-z0-9_]*\.py', name) is not None
                and type(expected) is str and re.fullmatch('[a-f0-9]{64}', expected), 'SOURCE_MANIFEST')
        actual[name] = sha(reader.raw(runtime / name))
    canonical = json.dumps(actual, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
    runtime_names = reader.names(runtime, 256)
    return dict(actual_source_sha256=sha(canonical), files_match=actual == declared,
        aggregate_matches=sha(canonical) == config.get('source_sha256'),
        history_module_present='online_history.py' in runtime_names,
        history_module_declared='online_history.py' in declared,
        source_file_count=len(actual), state_path_matches=config.get('state') == str(STATE_ROOT))


STATE_ROOT = Path('/opt/apps/family_connect/friends-restricted/renewal-state')


def collect(root, coordinator=None, config=None, runtime=None):
    require((config is None) == (runtime is None), 'SOURCE_ARGUMENTS')
    reader = Reader()
    result = dict(schema=1, purpose='installed-shape-census/not-for-recovery',
        node=node_inventory(reader, Path(root)),
        activation='FORBIDDEN', snapshot_barrier=False, archive_payloads_read=False,
        signatures_verified=False, approval_custody='NOT_ESTABLISHED')
    if coordinator is not None:
        result['coordinator'] = coordinator_inventory(reader, Path(coordinator))
    if config is not None:
        result['source'] = installed_source(reader, Path(config), Path(runtime))
    reader.verify()
    result.update(observation='NO_OBSERVED_CHANGE', metadata_entries_checked=len(reader.observed),
                  bytes_read=reader.bytes_read)
    return result


def reconcile(documents):
    require(set(documents) == {'RU', 'NL1', 'NL2'}, 'FLEET_MEMBERS')
    for document in documents.values():
        require(document.get('schema') == 1 and document.get('purpose') == 'installed-shape-census/not-for-recovery'
                and document.get('observation') == 'NO_OBSERVED_CHANGE', 'INCOMPLETE_OBSERVATION')
    ledgers = {slot: set(document['node']['ledger']) for slot, document in documents.items()}
    common = set.intersection(*ledgers.values())
    union = set.union(*ledgers.values())
    coordinator = documents['RU']['coordinator']
    current = coordinator['current']
    names = set(coordinator['history_name_tokens']) | ({current['operation']} if current else set())
    return dict(schema=1, activation='FORBIDDEN', recovery_ready=False, snapshot_barrier=False,
        common_operations=len(common), union_operations=len(union),
        current_in_all_ledgers=current is not None and current['operation'] in common,
        common_result_disagreements=sum(len({document['node']['ledger'][operation]
            for document in documents.values()}) != 1 for operation in common),
        coordinator_history_count=coordinator['history_count'],
        coordinator_adjunct_json_count=len(coordinator['adjunct_json']),
        coordinator_adjuncts_are_validated_history=False,
        ru_ledger_without_current_or_history_name=len(ledgers['RU'] - names),
        approval_custody='NOT_ESTABLISHED', hosts={slot: dict(
            ledger_count=len(ledgers[slot]), archive_count=document['node']['archive_count'],
            outside_common=len(ledgers[slot] - common), result_counts=document['node']['result_counts'],
            missing_archives=document['node']['missing_archives'],
            unledgered_archives=document['node']['unledgered_archives'],
            owner_present=document['node']['owner_present'], shape_count=len(document['node']['shapes']),
            service_bearing_archives=sum('services-before.json' in archive['known']
                for archive in document['node']['archives'].values()),
            unknown_file_archives=sum(archive['other_count'] > 0
                for archive in document['node']['archives'].values())) for slot, document in documents.items()})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=STATE_ROOT)
    parser.add_argument('--coordinator', type=Path)
    parser.add_argument('--config', type=Path)
    parser.add_argument('--runtime', type=Path)
    args = parser.parse_args()
    try:
        result = collect(args.root, args.coordinator, args.config, args.runtime)
    except (Refused, OSError, ValueError, RecursionError):
        print(json.dumps(dict(observation='REFUSED', activation='FORBIDDEN')))
        return 1
    print(json.dumps(result, sort_keys=True, separators=(',', ':')))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
