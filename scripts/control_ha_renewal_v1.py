"""Inspect retained online-renewal evidence; never import, repair or execute it."""
import base64
from dataclasses import dataclass, field
import hmac
from pathlib import Path, PurePosixPath
import re
import sys

from cryptography import x509
from cryptography.exceptions import InvalidSignature, UnsupportedAlgorithm
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import load_pem_private_key

from scripts.control_ha_import import ImportRejected, digest, encoded, require
from scripts.control_ha_recovery_bundle import parse

MAINTENANCE = Path(__file__).resolve().parents[1] / 'deploy/friends/restricted/maintenance'
if str(MAINTENANCE) not in sys.path:
    sys.path.insert(0, str(MAINTENANCE))

from credential_renewal import Rejected, Validator, canonical
from gateway_set import bound_profile, membership, selected, shared, validate as validate_gateways
from grant_cutover import validate_grant_plan
from online_contract import CONTRACT, eligible, publication_receipt, window
from online_controller import prepared_receipt
from control.friends.restricted import delegation

ADAPTER = 'family-connect/online-renewal-evidence/v1/not-for-activation'
PURPOSE = 'synthetic-online-renewal/v1/not-live-attestation'
SLOTS = frozenset({'RU', 'NL', 'NL2'})
PARTS = frozenset({'capture.json', 'coordinator.json'} | {slot + '.json' for slot in SLOTS})
MAX_PART = 1024 * 1024
BASE_RECORD = frozenset(('schema mode operation_id online before before_sha256 previous gateway prepared '
    'published acquired cleaned fence first_cause commit_decided decision state').split())
OPTIONAL_RECORD = frozenset(('plan_sha256 delivery reconciliation last_cause fenced').split())
STATES = frozenset(('ONLINE_ACQUIRING ONLINE_FENCING ONLINE_PREPARED ONLINE_COMMIT_DECIDED '
    'ONLINE_RUNTIME_CONFIRMED ONLINE_CLEANING COMMITTED ONLINE_RECOVERY_REQUIRED '
    'ONLINE_EMERGENCY_REQUIRED ONLINE_ABORT_DECIDED ONLINE_ABORT_CLEANING ABORTED').split()) | frozenset(
    'ONLINE_' + slot + '_' + phase for slot in SLOTS for phase in ('ACQUIRED', 'STAGED', 'DECIDED')) | frozenset(
    {'ONLINE_NL_PUBLISHED', 'ONLINE_NL2_PUBLISHED'})
NODE_STATES = frozenset(('ONLINE_ACQUIRED ONLINE_STAGED ONLINE_PUBLISHED ONLINE_EMERGENCY_REQUIRED '
    'RESUMED ABORTED CLEANING').split())
NODE_FILES = frozenset(('plan.json prepared-plan.json files.json online-prepared.json online-published.json '
    'reconciliation.json gateway.json.before gateway.json.staged revocations.pem.before revocations.pem.staged').split())


def integer(value, minimum=0):
    return type(value) is int and minimum <= value <= 2**63 - 1


def sha(value):
    return type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None


def evidence_digest(parts):
    require(type(parts) is dict and set(parts) == PARTS and all(type(raw) is bytes and 0 < len(raw) <= MAX_PART
            for raw in parts.values()), 'RENEWAL_PARTS')
    return digest(encoded({name: digest(raw) for name, raw in parts.items()}))


def file_map(value, allowed, *, maximum=32):
    require(type(value) is dict and set(value) <= allowed and len(value) <= maximum, 'RENEWAL_FILES')
    result = {}
    for name, content in value.items():
        require(type(content) is str and len(content) <= 262144, 'RENEWAL_FILE_SIZE')
        raw = base64.b64decode(content, validate=True)
        require(len(raw) <= 196608, 'RENEWAL_FILE_SIZE')
        if name.endswith('.json'):
            require(canonical(parse(raw)) == raw, 'RENEWAL_NON_CANONICAL')
        result[name] = raw
    return result


def host_identity(value):
    require(type(value) is dict and set(value) == {'path', 'device', 'inode', 'uid', 'gid', 'mode'},
            'RENEWAL_HOST_IDENTITY')
    spelling = value['path']
    require(type(spelling) is str and len(spelling) <= 512 and spelling.isascii() and
            spelling.startswith('/') and not spelling.startswith('//') and
            str(PurePosixPath(spelling)) == spelling and '..' not in PurePosixPath(spelling).parts and
            not any(ord(character) < 32 for character in spelling), 'RENEWAL_HOST_PATH')
    require(all(integer(value[name]) for name in ('device', 'uid', 'gid')) and integer(value['inode'], 1) and
            type(value['mode']) is int and value['mode'] == 0o700, 'RENEWAL_HOST_IDENTITY')


def decode_document(raw, slot, operation, *, allowed_files=None):
    document = parse(raw)
    require(type(document) is dict and set(document) == {'schema', 'slot', 'host', 'files', 'metadata'} and
            type(document['schema']) is int and document['schema'] == 1 and document['slot'] == slot,
            'RENEWAL_DOCUMENT')
    host_identity(document['host'])
    if slot == 'coordinator':
        allowed = {'transaction.json', 'plan.json', 'operation.lock', 'last-receipt.json'}
    else:
        allowed = NODE_FILES | {'owner.json', 'completed.json', 'operation.lock'} | {
            'archive/' + operation + '/' + name for name in NODE_FILES | {'archive-manifest.json'}}
    files = file_map(document['files'], allowed if allowed_files is None else allowed_files,
                     maximum=32 if allowed_files is None else 256)
    require(type(document['metadata']) is dict and set(document['metadata']) == set(files), 'RENEWAL_METADATA')
    for name, metadata in document['metadata'].items():
        require(type(metadata) is dict and set(metadata) == {'uid', 'gid', 'mode', 'device', 'inode', 'nlink'} and
                all(integer(metadata[key]) for key in metadata) and metadata['nlink'] == 1 and
                metadata['mode'] == 0o600 and metadata['inode'] > 0 and
                all(metadata[key] == document['host'][key] for key in ('uid', 'gid', 'device')),
                'RENEWAL_METADATA')
    require('operation.lock' not in files or files['operation.lock'] == b'', 'RENEWAL_LOCK')
    return document, files


def transaction(files, operation):
    require('transaction.json' in files and 'operation.lock' in files, 'RENEWAL_COORDINATOR_MISSING')
    record = parse(files['transaction.json'])
    require(type(record) is dict and BASE_RECORD <= set(record) <= BASE_RECORD | OPTIONAL_RECORD and
            type(record['schema']) is int and record['schema'] == 1 and record['mode'] == 'online' and
            record['operation_id'] == operation and record['state'] in STATES and integer(record['fence']) and
            type(record['commit_decided']) is bool and record['decision'] in (None, 'ABORT', 'COMMIT') and
            record['commit_decided'] == (record['decision'] == 'COMMIT'), 'RENEWAL_TRANSACTION')
    for key in ('acquired', 'cleaned'):
        require(type(record[key]) is list and all(type(slot) is str for slot in record[key]) and
                len(record[key]) == len(set(record[key])) and set(record[key]) <= SLOTS, 'RENEWAL_COHORT')
    for key in ('before', 'prepared', 'published'):
        require(type(record[key]) is dict and set(record[key]) <= SLOTS, 'RENEWAL_COHORT')
    require(set(record['before']) == SLOTS and record['before_sha256'] == digest(canonical(record['before'])),
            'RENEWAL_BEFORE_HASH')
    identities = membership(record['before']['RU']['gateway_ids'])
    for slot, before in record['before'].items():
        require(before['gateway_ids'] == identities and before['gateway_slot'] == slot and
                before['role'] == ('RU' if slot == 'RU' else 'NL') and
                before['admission_mode'] == 'all_activated', 'RENEWAL_BEFORE_BINDING')
    online = record['online']
    require(type(online) is dict and set(online) == {'contract', 'timing'} and online['contract'] == CONTRACT and
            online['timing'] == window(online['timing']['rpc_seconds'], online['timing']['schedule_seconds']),
            'RENEWAL_ONLINE_CONTRACT')
    if record['commit_decided']:
        require(set(record['acquired']) == SLOTS and set(record['prepared']) == SLOTS and
                'plan.json' in files and record['fence'] > 0, 'RENEWAL_DECISION_INCOMPLETE')
    if record['state'] in {'ONLINE_COMMIT_DECIDED', 'ONLINE_RUNTIME_CONFIRMED', 'ONLINE_CLEANING', 'COMMITTED'} or \
            record['state'].endswith(('_DECIDED', '_PUBLISHED')) and record['state'] != 'ONLINE_ABORT_DECIDED':
        require(record['commit_decided'], 'RENEWAL_STATE_DECISION')
    if record['state'] in ('ONLINE_ABORT_DECIDED', 'ONLINE_ABORT_CLEANING', 'ABORTED'):
        require(record['decision'] == 'ABORT', 'RENEWAL_STATE_DECISION')
    if record['state'] in ('COMMITTED', 'ABORTED'):
        require(set(record['cleaned']) == SLOTS and
                record['decision'] == ('COMMIT' if record['state'] == 'COMMITTED' else 'ABORT'),
                'RENEWAL_TERMINAL_INCOMPLETE')
    if 'last-receipt.json' in files:
        receipt = parse(files['last-receipt.json'])
        require(set(receipt) == {'schema', 'operation_id', 'state', 'first_cause', 'before_sha256', 'timestamp',
                'remote_alert_delivery', 'grant_successor_model'} and
                all(canonical(receipt[key]) == canonical(record[key]) for key in
                    ('schema', 'operation_id', 'state', 'first_cause', 'before_sha256')) and
                integer(receipt['timestamp']), 'RENEWAL_COORDINATOR_RECEIPT')
    return record, identities


def plan_check(plan, record, validator, captured_at, identities):
    require(type(plan) is dict and set(plan) == {'schema', 'operation_id', 'previous', 'candidate', 'secondary',
            'gateway_ids', 'grant_plan', 'nl_profile_sha256', 'ru_expected', 'online'} and
            type(plan['schema']) is int and plan['schema'] == 2 and plan['operation_id'] == record['operation_id'] and
            plan['previous'] == record['previous'] and plan['online'] == record['online'] and
            plan['ru_expected'] == record['before']['RU'], 'RENEWAL_PLAN_BINDING')
    grant = plan['grant_plan']
    issued = grant['issued_at']
    require(set(grant) == {'schema', 'model', 'issued_at', 'before', 'before_sha256', 'after_grants', 'predecessors'}
            and type(grant['schema']) is int and integer(issued, 1) and issued <= captured_at and
            grant['before_sha256'] == digest(canonical(grant['before']))
            and grant['predecessors'] == [], 'RENEWAL_GRANT_BINDING')
    validate_grant_plan(grant, issued)
    require(plan['candidate']['grants'] == grant['after_grants'] and
            plan['previous']['grants'] == grant['before']['restricted_grants'], 'RENEWAL_GRANT_BINDING')
    previous_crl = x509.load_pem_x509_crl(plan['previous']['crl'].encode())
    next_crl = x509.load_pem_x509_crl(plan['candidate']['crl'].encode())
    require({item.serial_number for item in previous_crl} == {item.serial_number for item in next_crl},
            'RENEWAL_REVOCATION_CHANGED')
    validate_gateways(plan, validator, issued, identities)
    for slot in ('NL', 'NL2'):
        chosen = selected(plan, slot)
        eligible(validator, chosen['previous'], issued, plan['online']['timing'], candidate=chosen['candidate'])
        require(chosen['nl_profile_sha256'] == record['before'][slot]['files']['gateway.json'],
                'RENEWAL_PROFILE_BINDING')
    for slot, receipt in record['prepared'].items():
        prepared_receipt(receipt, slot, record['operation_id'], plan)
        if slot != 'RU':
            require(receipt['runtime']['profile_sha256'] == record['before'][slot]['files']['gateway.json'],
                    'RENEWAL_PREPARED_RUNTIME')
    require(set(record['published']) <= {'NL', 'NL2'}, 'RENEWAL_PUBLICATION')
    for slot, receipt in record['published'].items():
        publication_receipt(slot, record['operation_id'], plan, receipt, captured_at)
        require(slot in record['prepared'] and
                receipt['runtime']['instance'] == record['prepared'][slot]['runtime']['instance'] and
                receipt['runtime']['profile_sha256'] == record['prepared'][slot]['target_sha256'],
                'RENEWAL_RUNTIME_BINDING')
    expected = dict(plan_sha256=digest(canonical(plan)), crl_sha256=digest(plan['candidate']['crl'].encode()),
                    state='PROMOTED')
    if 'reconciliation' in record:
        require(record['reconciliation'] == {slot: expected for slot in SLOTS}, 'RENEWAL_RECONCILIATION')
    if 'delivery' in record:
        delivery = record['delivery']
        require(type(delivery) is dict and set(delivery) == {'operation_id', 'slot', 'plan_sha256', 'delivery_sha256'}
                and delivery['operation_id'] == record['operation_id'] and delivery['slot'] == 'RU' and
                delivery['plan_sha256'] == digest(canonical(plan)) and sha(delivery['delivery_sha256']),
                'RENEWAL_DELIVERY')
        marker = dict(schema=1, contract=CONTRACT, operation_id=record['operation_id'],
            plan_sha256=digest(canonical(plan)), ready=True, crl_sha256=digest(plan['candidate']['crl'].encode()),
            gateways=identities, issued_at=issued)
        require(delivery['delivery_sha256'] == digest(canonical(marker)), 'RENEWAL_DELIVERY_HASH')
    if record['state'] == 'COMMITTED':
        require(set(record['published']) == {'NL', 'NL2'} and 'delivery' in record and 'reconciliation' in record,
                'RENEWAL_TERMINAL_INCOMPLETE')


def node_check(files, record, slot, captured_at):
    operation = record['operation_id']
    prefix = 'archive/' + operation + '/'
    archive = {name.removeprefix(prefix): raw for name, raw in files.items() if name.startswith(prefix)}
    active = {name: raw for name, raw in files.items() if name in NODE_FILES}
    require(not (set(active) & set(archive)), 'RENEWAL_ARCHIVE_COLLISION')
    retained = dict(active, **{name: raw for name, raw in archive.items() if name != 'archive-manifest.json'})
    ledger = parse(files['completed.json']) if 'completed.json' in files else None
    owner = parse(files['owner.json']) if 'owner.json' in files else None
    require(not files or 'operation.lock' in files, 'RENEWAL_LOCK_MISSING')
    if archive:
        require(record['decision'] in ('COMMIT', 'ABORT'), 'RENEWAL_ARCHIVE_DECISION')
        require('archive-manifest.json' in archive, 'RENEWAL_ARCHIVE_MANIFEST_MISSING')
        manifest = parse(archive['archive-manifest.json'])
        require(type(manifest) is dict and set(manifest) == set(retained) and all(
                sha(expected) and digest(retained[name]) == expected for name, expected in manifest.items()),
                'RENEWAL_ARCHIVE_HASH')
        if ledger is not None:
            require(type(ledger) is dict and set(ledger) == {operation}, 'RENEWAL_HISTORY_VARIANT')
            entry = ledger[operation]
            require(type(entry) is dict and set(entry) == {'result', 'manifest_sha256', 'timestamp'} and
                    entry['result'] == 'CLEANED' and entry['manifest_sha256'] == digest(canonical(manifest)) and
                    integer(entry['timestamp']) and entry['timestamp'] <= captured_at and not active,
                    'RENEWAL_COMPLETED_LEDGER')
    else:
        require(ledger is None, 'RENEWAL_ARCHIVE_MISSING')
    if owner is not None:
        require(type(owner) is dict and set(owner) - {'prepared'} == {'schema', 'operation_id', 'expected_state',
                'state', 'first_cause', 'mode', 'fence', 'online', 'commit_decided'} and
                type(owner['schema']) is int and owner['schema'] == 1 and owner['operation_id'] == operation and
                owner['mode'] == 'online' and owner['online'] == record['online'] and
                owner['expected_state'] == record['before'][slot] and integer(owner['fence'], 1) and
                owner['fence'] <= record['fence'] and owner['state'] in NODE_STATES and
                type(owner['commit_decided']) is bool and
                (not owner['commit_decided'] or record['commit_decided']), 'RENEWAL_NODE_OWNER')
        if owner['commit_decided']:
            require(owner.get('prepared') == record['prepared'] and set(record['prepared']) == SLOTS,
                    'RENEWAL_NODE_DECISION')
        else:
            require('prepared' not in owner, 'RENEWAL_NODE_DECISION')
        if owner['state'] in ('RESUMED', 'ONLINE_PUBLISHED'):
            require(owner['commit_decided'], 'RENEWAL_NODE_DECISION')
        if owner['state'] == 'ABORTED':
            require(record['decision'] == 'ABORT' and not owner['commit_decided'], 'RENEWAL_NODE_DECISION')
        if archive:
            require(owner['state'] in ('RESUMED', 'ABORTED', 'CLEANING'), 'RENEWAL_ARCHIVE_DECISION')
        require('operation.lock' in files, 'RENEWAL_LOCK_MISSING')
    elif ledger is None:
        require(not retained and not archive, 'RENEWAL_OWNER_MISSING')
    if record['state'] == 'COMMITTED' or slot in record['cleaned'] and record['commit_decided']:
        require(owner is None and ledger is not None, 'RENEWAL_TERMINAL_NODE')
    require(not archive or owner is not None or ledger is not None, 'RENEWAL_ARCHIVE_UNOWNED')
    if 'online-published.json' in retained:
        require(record['commit_decided'] and (owner is None or owner['commit_decided']), 'RENEWAL_NODE_DECISION')
    return retained, owner, ledger


@dataclass(frozen=True, repr=False)
class RenewalEvidence:
    parts: dict = field(repr=False)
    checkpoint: str
    state: str
    operation: str
    committed: bool
    node_states: dict

    def summary(self):
        return dict(result='ISOLATED_RENEWAL_EVIDENCE_PASS', adapter=ADAPTER, state=self.state,
                    commit_decided=self.committed, nodes=self.node_states, parts=len(self.parts),
                    activation='FORBIDDEN', import_status='NOT_INTEGRATED_WITH_CANONICAL_CAPSULE',
                    host_resume='NOT_AUTHORIZED', full_dr='NOT_QUALIFIED')


def inspect_renewal(parts, expected_checkpoint, anchor, now):
    try:
        require(sha(expected_checkpoint) and hmac.compare_digest(evidence_digest(parts), expected_checkpoint),
                'RENEWAL_CHECKPOINT_MISMATCH')
        capture = parse(parts['capture.json'])
        require(type(capture) is dict and set(capture) == {'schema', 'purpose', 'operation_id', 'captured_at',
                'anchor_sha256', 'nodes'} and type(capture['schema']) is int and capture['schema'] == 1 and
                capture['purpose'] == PURPOSE and capture['nodes'] == sorted(SLOTS) and
                integer(capture['captured_at'], 1) and integer(now, capture['captured_at']) and
                type(anchor) is bytes and len(anchor) == 32 and capture['anchor_sha256'] == digest(anchor) and
                type(capture['operation_id']) is str and re.fullmatch('[a-z0-9-]{16,96}', capture['operation_id']),
                'RENEWAL_CAPTURE')
        at, operation = capture['captured_at'], capture['operation_id']
        documents = {slot: decode_document(parts[slot + '.json'], slot, operation)
                     for slot in SLOTS | {'coordinator'}}
        paths = [PurePosixPath(document['host']['path']) for document, _ in documents.values()]
        require(all(not left.is_relative_to(right) for index, left in enumerate(paths)
                    for other, right in enumerate(paths) if index != other), 'RENEWAL_HOST_OVERLAP')
        coordinator = documents['coordinator'][1]
        record, identities = transaction(coordinator, operation)
        validator = Validator(anchor, delegation, all_activated=True)
        primary = validator.validate(canonical(record['previous']), at)
        secondary = validator.validate(canonical(record['gateway']['secondary_snapshot']), at)
        shared(primary, secondary, identities)
        bound_profile(primary, {key: value for key, value in record['gateway'].items()
                                if key not in ('secondary', 'secondary_snapshot')}, identities['NL'])
        bound_profile(secondary, record['gateway']['secondary'], identities['NL2'])
        require(record['gateway']['profile_sha256'] == record['before']['NL']['files']['gateway.json'] and
                record['gateway']['secondary']['profile_sha256'] == record['before']['NL2']['files']['gateway.json'],
                'RENEWAL_GATEWAY_BINDING')
        if 'last-receipt.json' in coordinator:
            require(parse(coordinator['last-receipt.json'])['timestamp'] <= at, 'RENEWAL_RECEIPT_TIME')
        retained = {}
        states = {}
        for slot in sorted(SLOTS):
            node_files, owner, ledger = node_check(documents[slot][1], record, slot, at)
            retained[slot] = node_files
            states[slot] = owner['state'] if owner else 'CLEANED' if ledger else 'ABSENCE_UNPROVEN'
        plans = [parse(raw) for files in [coordinator, *retained.values()] for name, raw in files.items()
                 if name in ('plan.json', 'prepared-plan.json')]
        if plans:
            plan = plans[0]
            require(all(canonical(value) == canonical(plan) for value in plans), 'RENEWAL_PLAN_CONFLICT')
            plan_check(plan, record, validator, at, identities)
            require('plan_sha256' not in record or record['plan_sha256'] == digest(canonical(plan)),
                    'RENEWAL_PLAN_HASH')
            for slot, files in retained.items():
                node_receipts(files, record, plan, slot, at, validator)
        else:
            require(not record['prepared'] and not record['published'] and not record['commit_decided'] and
                    'plan_sha256' not in record and not any(retained.values()), 'RENEWAL_PLAN_MISSING')
        return RenewalEvidence(dict(parts), expected_checkpoint, record['state'], operation,
                               record['commit_decided'], states)
    except ImportRejected:
        raise
    except (Rejected, ValueError, KeyError, TypeError, AttributeError, OverflowError, InvalidSignature,
            UnsupportedAlgorithm):
        raise ImportRejected('RENEWAL_EVIDENCE_INVALID') from None


def node_receipts(files, record, plan, slot, at, validator):
    operation = record['operation_id']
    for name, expected in [('online-prepared.json', record['prepared'].get(slot)),
                           ('online-published.json', record.get('delivery') if slot == 'RU'
                            else record['published'].get(slot))]:
        if name in files:
            receipt = parse(files[name])
            if name == 'online-prepared.json':
                prepared_receipt(receipt, slot, operation, plan)
            elif slot != 'RU':
                publication_receipt(slot, operation, plan, receipt, at)
            require(expected is None or receipt == expected, 'RENEWAL_RECEIPT_CONFLICT')
        if expected is not None:
            require(name in files, 'RENEWAL_RECEIPT_MISSING')
        if record['state'] == 'COMMITTED':
            require(expected is not None, 'RENEWAL_RECEIPT_MISSING')
    if 'reconciliation.json' in files:
        require(parse(files['reconciliation.json']) == record.get('reconciliation'), 'RENEWAL_RECONCILIATION')
    if record['state'] == 'COMMITTED':
        require({'files.json', 'plan.json', 'reconciliation.json'} <= set(files), 'RENEWAL_TERMINAL_FILES')
    if 'files.json' in files:
        metadata = parse(files['files.json'])
        target = 'revocations.pem' if slot == 'RU' else 'gateway.json'
        require(type(metadata) is dict and set(metadata) == {target}, 'RENEWAL_MATERIAL_VARIANT')
        entry = metadata[target]
        require(set(entry) == {'before', 'after', 'uid', 'gid', 'mode'} and
                all(integer(entry[key]) for key in ('uid', 'gid', 'mode')) and entry['mode'] in (0o600, 0o640),
                'RENEWAL_MATERIAL_METADATA')
        for suffix, key in (('.before', 'before'), ('.staged', 'after')):
            require(target + suffix in files and digest(files[target + suffix]) == entry[key], 'RENEWAL_MATERIAL_HASH')
        require(entry['before'] == record['before'][slot]['files'][target], 'RENEWAL_PREVIOUS_BINDING')
        if slot == 'RU':
            require(files[target + '.staged'] == plan['candidate']['crl'].encode() and
                    files[target + '.before'] == plan['previous']['crl'].encode(), 'RENEWAL_CRL_BINDING')
        else:
            before, after = parse(files[target + '.before']), parse(files[target + '.staged'])
            chosen = selected(plan, slot)
            require(set(before) == set(after) and all(before[key] == after[key] for key in before
                    if key not in ('certificate', 'revocations', 'minimum_crl')) and
                    before['certificate'] == chosen['previous']['certificate'] and
                    before['revocations'] == chosen['previous']['crl'] and
                    after['certificate'] == chosen['candidate']['certificate'] and
                    after['revocations'] == chosen['candidate']['crl'], 'RENEWAL_PROFILE_TARGET')
            from control.friends.profile_store import renewal_target
            require(renewal_target(files[target + '.before'], files[target + '.staged'], plan['grant_plan']['issued_at'])
                    == files[target + '.staged'], 'RENEWAL_PROFILE_TARGET')
            for profile, phase, expected_hash in ((before, 'previous', entry['before']), (after, 'candidate', entry['after'])):
                public = {key: value for key, value in profile.items() if key != 'private_key'}
                public['profile_sha256'] = expected_hash
                bound_profile(validator.validate(canonical(chosen[phase]), plan['grant_plan']['issued_at']),
                              public, plan['gateway_ids'][slot])
            private = load_pem_private_key(after['private_key'].encode(), password=None)
            leaf = x509.load_pem_x509_certificate(after['certificate'].encode())
            require(isinstance(private, Ed25519PrivateKey) and
                    private.public_key().public_bytes_raw() == leaf.public_key().public_bytes_raw() and
                    after['gateway'] == plan['gateway_ids'][slot], 'RENEWAL_PRIVATE_KEY_BINDING')
            if slot in record['prepared']:
                require(entry['after'] == record['prepared'][slot]['target_sha256'], 'RENEWAL_TARGET_RECEIPT')


def compare_same_host(previous, current, expected_checkpoint, anchor, now):
    evidence = inspect_renewal(previous, expected_checkpoint, anchor, now)
    require(evidence_digest(current) == evidence.checkpoint, 'RENEWAL_HOST_OR_EVIDENCE_CHANGED')
    return dict(result='UNCHANGED_EVIDENCE_ONLY', host_resume='NOT_AUTHORIZED', operation_id=evidence.operation,
                decision='COMMIT' if evidence.committed else 'UNDECIDED_OR_ABORT', automatic_retry=False)
