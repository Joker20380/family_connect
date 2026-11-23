"""Validate retained native history without rewriting or executing recovery inputs."""
import base64
import re

from cryptography import x509

from scripts.control_ha_import import ImportRejected, digest, encoded, require
from scripts.control_ha_recovery_bundle import parse
from scripts.control_ha_renewal_v1 import (NODE_FILES, SLOTS, decode_document, evidence_digest,
                                         file_map, inspect_renewal, integer)

MAX_OPERATIONS = 8
COORDINATOR_FILES = {'transaction.json', 'plan.json', 'last-receipt.json'}


def projection(document, files, metadata):
    return encoded(dict(document, files={name: base64.b64encode(raw).decode() for name, raw in files.items()},
                        metadata=metadata))


def crl_number(snapshot):
    return x509.load_pem_x509_crl(snapshot['crl'].encode()).extensions.get_extension_for_class(x509.CRLNumber).value.crl_number


def inspect_history(parts, expected_checkpoint, anchor, now):
    require(evidence_digest(parts) == expected_checkpoint, 'RENEWAL_CHECKPOINT_MISMATCH')
    try:
        capture = parse(parts['capture.json'])
        current = capture['operation_id']
        spelling = parse(parts['coordinator.json'])['files']
        history_paths = {name for name in spelling if re.fullmatch('history/[a-z0-9-]{16,96}\\.json', name)}
        require(1 <= len(history_paths) < MAX_OPERATIONS, 'RENEWAL_HISTORY_CAPACITY')
        coordinator, files = decode_document(parts['coordinator.json'], 'coordinator', current,
            allowed_files=COORDINATOR_FILES | {'operation.lock'} | history_paths)
        history = {}
        for path in history_paths:
            item = parse(files[path])
            operation = path.removeprefix('history/').removesuffix('.json')
            require(set(item) == {'schema', 'operation_id', 'files', 'sha256'} and
                    type(item['schema']) is int and item['schema'] == 1 and item['operation_id'] == operation and
                    operation != current, 'RENEWAL_HISTORY_RECORD')
            retained = file_map(item['files'], COORDINATOR_FILES)
            require(set(retained) == COORDINATOR_FILES and item['sha256'] ==
                    {name: digest(raw) for name, raw in retained.items()}, 'RENEWAL_HISTORY_HASH')
            history[operation] = (retained, {name: coordinator['metadata'][path] for name in retained})
        require(COORDINATOR_FILES <= set(files), 'RENEWAL_HISTORY_CURRENT_MISSING')
        history[current] = ({name: files[name] for name in COORDINATOR_FILES},
                            {name: coordinator['metadata'][name] for name in COORDINATOR_FILES})
        operations = set(history)
        nodes = {}
        for slot in sorted(SLOTS):
            allowed = {'operation.lock', 'completed.json'} | {
                'archive/' + operation + '/' + name for operation in operations
                for name in NODE_FILES | {'archive-manifest.json'}}
            document, node_files = decode_document(parts[slot + '.json'], slot, current, allowed_files=allowed)
            ledger = parse(node_files['completed.json'])
            require(type(ledger) is dict and set(ledger) == operations, 'RENEWAL_HISTORY_COHORT')
            nodes[slot] = document, node_files, ledger
        ordered = []
        for operation, (retained, _) in history.items():
            receipt = parse(retained['last-receipt.json'])
            require(integer(receipt['timestamp'], 1) and receipt['timestamp'] <= capture['captured_at'],
                    'RENEWAL_HISTORY_TIME')
            ordered.append((receipt['timestamp'], operation))
        ordered.sort()
        require(ordered[-1][1] == current and len({at for at, _ in ordered}) == len(ordered),
                'RENEWAL_HISTORY_ORDER')
        previous = None
        for at, operation in ordered:
            retained, metadata = history[operation]
            retained = dict(retained, **{'operation.lock': files['operation.lock']})
            metadata = dict(metadata, **{'operation.lock': coordinator['metadata']['operation.lock']})
            projected = {'capture.json': encoded(dict(capture, operation_id=operation,
                captured_at=capture['captured_at'] if operation == current else at)),
                'coordinator.json': projection(coordinator, retained, metadata)}
            for slot, (document, node_files, ledger) in nodes.items():
                prefix = 'archive/' + operation + '/'
                selected_files = {name: raw for name, raw in node_files.items() if name.startswith(prefix)
                                  or name == 'operation.lock'}
                selected_files['completed.json'] = encoded({operation: ledger[operation]})
                projected[slot + '.json'] = projection(document, selected_files,
                    {name: document['metadata'][name] for name in selected_files})
            evidence = inspect_renewal(projected, evidence_digest(projected), anchor, now)
            require(evidence.state == 'COMMITTED', 'RENEWAL_HISTORY_UNSETTLED')
            plan = parse(retained['plan.json'])
            if previous is not None:
                require(plan['gateway_ids'] == previous['gateway_ids'] and all(
                    plan['secondary']['previous'][key] == previous['secondary']['candidate'][key]
                    for key in ('certificate', 'authority')) and all(
                    plan['previous'][key] == previous['candidate'][key] for key in ('certificate', 'authority')),
                    'RENEWAL_HISTORY_PREDECESSOR')
                require(crl_number(plan['previous']) >= crl_number(previous['candidate']), 'RENEWAL_HISTORY_FLOOR')
                before_crl = x509.load_pem_x509_crl(previous['candidate']['crl'].encode())
                after_crl = x509.load_pem_x509_crl(plan['previous']['crl'].encode())
                require({entry.serial_number for entry in before_crl} <= {entry.serial_number for entry in after_crl}
                        and (crl_number(plan['previous']) != crl_number(previous['candidate']) or
                             plan['previous']['crl'] == previous['candidate']['crl']), 'RENEWAL_HISTORY_REVOCATION')
            previous = plan
        return evidence, projected, len(ordered)
    except ImportRejected:
        raise
    except (KeyError, TypeError, ValueError, AttributeError, OverflowError, RecursionError):
        raise ImportRejected('RENEWAL_HISTORY_INVALID') from None
