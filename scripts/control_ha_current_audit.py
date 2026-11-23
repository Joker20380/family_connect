"""Read-only current content audit, explicitly blocked on historical gate provenance."""
import base64

from scripts import control_ha_legacy_custody as custody
from scripts.control_ha_import import ImportRejected, digest, encoded, require
from scripts.control_ha_online_capsule import bind_current
from scripts.control_ha_renewal_v1 import SLOTS, integer
from scripts.control_ha_stopped_v1 import CURRENT_PURPOSE, inspect_scheduled

COORDINATOR_FILES = {'operation.lock', 'transaction.json', 'plan.json', 'last-receipt.json'}
HOST_FIELDS = ('device', 'inode', 'uid', 'gid', 'mode')
FILE_FIELDS = HOST_FIELDS + ('nlink',)


def project(tree, slot, operation):
    entries = tree['entries']
    if slot == 'coordinator':
        names = COORDINATOR_FILES
        require('owner.json' not in entries, 'CURRENT_PENDING_OWNER')
    else:
        require(set(custody.children(tree)) == {'operation.lock', 'completed.json', 'archive'},
                'CURRENT_PENDING_OR_UNKNOWN_ROOT')
        prefix = 'archive/' + operation + '/'
        names = {'operation.lock', 'completed.json'} | {name for name in entries if name.startswith(prefix)}
        require(len(names) > 2, 'CURRENT_ARCHIVE_MISSING')
    files, metadata = {}, {}
    for name in names:
        entry = entries.get(name)
        require(entry is not None and entry['kind'] == 'file', 'CURRENT_FILE_REQUIRED')
        files[name] = base64.b64encode(entry['body']).decode()
        metadata[name] = {field: entry['metadata'][field] for field in FILE_FIELDS}
    host = dict(path=tree['path'], **{field: tree['metadata'][field] for field in HOST_FIELDS})
    return encoded(dict(schema=1, slot=slot, host=host, files=files, metadata=metadata))


def audit_current(bundle, key, checkpoint, recovered, publications, anchor, *, captured_at, now, units):
    try:
        require(integer(captured_at, 1) and integer(now, captured_at), 'CURRENT_CAPTURE_TIME')
        preserved = custody.inspect(bundle, key, checkpoint)
        record = custody.json_file(preserved.trees['coordinator'], 'transaction.json')
        operation = record['operation_id']
        require(type(operation) is str, 'CURRENT_OPERATION')
        parts = {'capture.json': encoded(dict(schema=1, purpose=CURRENT_PURPOSE, operation_id=operation,
            captured_at=captured_at, anchor_sha256=digest(anchor), nodes=sorted(SLOTS)))}
        for slot in ('coordinator', 'RU', 'NL', 'NL2'):
            parts[slot + '.json'] = project(preserved.trees['NL1' if slot == 'NL' else slot], slot, operation)
        require(type(publications) is dict and set(publications) == {'NL', 'NL2'} and
            all(type(raw) is bytes and len(raw) <= 1024 * 1024 for raw in publications.values()),
            'CURRENT_PUBLICATIONS')
        publication = encoded(dict(schema=1, directories={slot: base64.b64encode(raw).decode()
            for slot, raw in publications.items()}))
        plan, directories, _ = inspect_scheduled(parts, publication, anchor, now, units)
        bind_current(recovered, plan, directories['NL'])
        return dict(result='CURRENT_CONTENT_CHECKED_RECOVERY_BLOCKED', nodes=3, database_tables=5,
            custody_sha256=checkpoint.bundle_sha256, manifest_sha256=preserved.manifest_sha256,
            operation_sha256=digest(operation.encode()), history_validation='NOT_PERFORMED',
            ledger_entries={slot: len(custody.json_file(preserved.trees[slot], 'completed.json'))
                for slot in ('RU', 'NL1', 'NL2')},
            gate='RECORDED_SCHEDULE_RESULT_ONLY', original_gate_provenance='NOT_ESTABLISHED',
            unit_order_provenance='CALLER_SUPPLIED_NOT_ATTESTED', service_liveness='NOT_OBSERVED',
            capture_consistency='NOT_ATOMIC', activation='FORBIDDEN', host_resume='NOT_AUTHORIZED',
            database_import='NOT_AUTHORIZED', recovery_acceptance='BLOCKED')
    except ImportRejected:
        raise
    except (ValueError, KeyError, TypeError, AttributeError, OverflowError, RecursionError):
        raise ImportRejected('CURRENT_AUDIT_INVALID') from None
