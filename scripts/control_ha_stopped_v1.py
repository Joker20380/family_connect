"""Validate completed native stopped/offline/emergency evidence without host I/O."""
import base64
from pathlib import PurePosixPath
import re

from cryptography import x509
from cryptography.exceptions import InvalidSignature, UnsupportedAlgorithm
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from scripts.control_ha_import import ImportRejected, digest, encoded, require
from scripts.control_ha_recovery_bundle import parse
from scripts.control_ha_renewal_history import projection, crl_number
from scripts.control_ha_renewal_v1 import (BASE_RECORD, OPTIONAL_RECORD, NODE_FILES, PURPOSE, SLOTS,
    decode_document, evidence_digest, inspect_renewal, integer, sha)
from credential_renewal import Rejected, Validator, canonical
from control.friends.restricted import delegation, directory
from control.friends.profile_store import renewal_target
from gateway_set import bound_profile, membership, selected, validate as validate_gateways
from grant_cutover import validate_grant_plan

STOPPED_PURPOSE = 'synthetic-stopped-renewal/v1/not-live-attestation'
MATERIAL = {'revocations.pem', 'issuer.json', 'issuer-NL2.json', 'gateway.json'}
ARCHIVE = {'files.json', 'plan.json', 'prepared-plan.json', 'reconciliation.json', 'directory-before.json',
           'directory-accepted.json', 'authority-request.json', 'online-origin.json'} | {
               name + suffix for name in MATERIAL for suffix in ('.before', '.staged')}
STANDARD_RECORD = set(('schema operation_id state first_cause before_sha256 before previous previous_secondary '
                       'acquired quiesced commit_decided gate reconciliation').split())
EMERGENCY_RECORD = set(('online_parent handoffs cursor continuation_id emergency_commit_decided terminal_result '
                        'emergency_request gate emergency_plan_sha256').split())


def manifest_check(files, name, excluded):
    manifest = parse(files[name])
    require(type(manifest) is dict and set(manifest) == set(files) - excluded and all(
        sha(checksum) and digest(files[item]) == checksum for item, checksum in manifest.items()),
        'STOPPED_ARCHIVE_HASH')
    return manifest


def cohort(before, identities):
    require(type(before) is dict and set(before) == SLOTS, 'STOPPED_COHORT')
    for slot, value in before.items():
        require(value['gateway_ids'] == identities and value['gateway_slot'] == slot and
                value['role'] == ('RU' if slot == 'RU' else 'NL') and value['admission_mode'] == 'all_activated',
                'STOPPED_COHORT_BINDING')


def material_check(files, slot, record, plan, validator, at, emergency):
    metadata = parse(files['files.json'])
    chosen = selected(plan, slot)
    if slot == 'RU':
        targets = {'revocations.pem': plan['candidate']['crl'].encode(),
                   'issuer.json': canonical(plan['candidate']['authority']),
                   'issuer-NL2.json': canonical(plan['secondary']['candidate']['authority'])}
    else:
        targets = {'gateway.json': files['gateway.json.staged']}
    changed = {name for name, raw in targets.items() if digest(raw) != record['before'][slot]['files'][name]}
    require(type(metadata) is dict and set(metadata) == changed, 'STOPPED_MATERIAL_SCOPE')
    require({name for name in files if name.endswith(('.before', '.staged'))} ==
            {name + suffix for name in changed for suffix in ('.before', '.staged')}, 'STOPPED_MATERIAL_COVERAGE')
    for name, item in metadata.items():
        require(set(item) == {'before', 'after', 'uid', 'gid', 'mode'} and
                all(integer(item[key]) for key in ('uid', 'gid', 'mode')) and item['mode'] in (0o600, 0o640),
                'STOPPED_MATERIAL_METADATA')
        require(item['before'] == record['before'][slot]['files'][name] == digest(files[name + '.before']) and
                item['after'] == digest(files[name + '.staged']) and files[name + '.staged'] == targets[name],
                'STOPPED_MATERIAL_HASH')
    if slot == 'RU':
        for name in changed:
            if name == 'revocations.pem':
                candidates = ([plan['online_emergency']['plan'][phase]['crl'].encode() for phase in ('previous', 'candidate')]
                              if emergency else [plan['previous']['crl'].encode()])
            else:
                candidates = [canonical(selected(plan, 'NL2' if name == 'issuer-NL2.json' else 'NL')['previous']['authority'])]
            require(files[name + '.before'] in candidates, 'STOPPED_PREVIOUS_MATERIAL')
        return
    before, after = parse(files['gateway.json.before']), parse(files['gateway.json.staged'])
    require(set(before) == set(after) and all(before[key] == after[key] for key in before if key not in
            ('authority', 'certificate', 'revocations', 'minimum_crl')), 'STOPPED_PROFILE_CHANGED')
    issued = plan['grant_plan']['issued_at']
    require(renewal_target(files['gateway.json.before'], files['gateway.json.staged'], issued,
                           expired_predecessor=True) == files['gateway.json.staged'], 'STOPPED_PROFILE_TARGET')
    phases = [selected(plan['online_emergency']['plan'], slot)[phase] for phase in ('previous', 'candidate')] if emergency else [chosen['previous']]
    require(any(before['certificate'] == value['certificate'] and before['revocations'] == value['crl'] for value in phases),
            'STOPPED_PROFILE_PREDECESSOR')
    predecessor = next(value for value in phases if before['certificate'] == value['certificate'] and
                       before['revocations'] == value['crl'])
    before_public = {key: value for key, value in before.items() if key != 'private_key'}
    before_public['profile_sha256'] = digest(files['gateway.json.before'])
    bound_profile(validator.validate(canonical(predecessor), issued, expired_leaf_predecessor=True),
                  before_public, plan['gateway_ids'][slot])
    public = {key: value for key, value in after.items() if key != 'private_key'}
    public['profile_sha256'] = digest(files['gateway.json.staged'])
    bound_profile(validator.validate(canonical(chosen['candidate']), at), public, plan['gateway_ids'][slot])
    private = load_pem_private_key(after['private_key'].encode(), password=None)
    leaf = x509.load_pem_x509_certificate(after['certificate'].encode())
    require(isinstance(private, Ed25519PrivateKey) and
            private.public_key().public_bytes_raw() == leaf.public_key().public_bytes_raw(), 'STOPPED_PRIVATE_KEY_BINDING')
    require(chosen['nl_profile_sha256'] == digest(files['gateway.json.before']), 'STOPPED_PROFILE_BINDING')


def parent_check(parts, documents, parent_archives, record, plan, anchor, now):
    origin = record['online_parent']
    require(plan['online_emergency'] == origin and origin['decision'] == 'COMMIT' and
            record['continuation_id'] == 'emergency-' + digest(canonical(origin)), 'STOPPED_EMERGENCY_ORIGIN')
    old = {key: value for key, value in record.items() if key in BASE_RECORD | OPTIONAL_RECORD}
    old.update(mode='online', state='ONLINE_EMERGENCY_REQUIRED', before={
        slot: parse(files['owner.json'])['expected_state'] for slot, files in parent_archives.items()})
    old.pop('reconciliation', None)
    require(digest(canonical(old['before'])) == record['before_sha256'] and origin == dict(
        operation_id=record['operation_id'], decision='COMMIT', plan=origin['plan'],
        prepared=record['prepared'], fence=record['fence']) and
        record['plan_sha256'] == digest(canonical(origin['plan'])), 'STOPPED_EMERGENCY_PARENT')
    capture = dict(parse(parts['capture.json']), purpose=PURPOSE)
    coordinator = documents['coordinator'][0]
    projected = {'capture.json': encoded(capture), 'coordinator.json': projection(coordinator,
        {'operation.lock': b'', 'transaction.json': canonical(old), 'plan.json': canonical(origin['plan'])},
        {name: coordinator['metadata'][name] for name in ('operation.lock', 'transaction.json', 'plan.json')})}
    for slot, files in parent_archives.items():
        require(parse(files['origin.json']) == origin, 'STOPPED_EMERGENCY_ORIGIN')
        manifest_check(files, 'manifest.json', {'manifest.json', 'owner.json', 'origin.json'})
        document = documents[slot][0]
        prefix = 'archive/online-' + digest(record['operation_id'].encode()) + '/'
        retained = {name: raw for name, raw in files.items() if name not in ('origin.json', 'manifest.json')}
        metadata = {name: document['metadata'][prefix + name] for name in retained}
        retained['operation.lock'] = b''
        metadata['operation.lock'] = document['metadata']['operation.lock']
        projected[slot + '.json'] = projection(document, retained, metadata)
    inspect_renewal(projected, evidence_digest(projected), anchor, now)
    require(set(record['handoffs']) == SLOTS and set(record['emergency_request']) == {
        'operation_id', 'continuation_id', 'origin_sha256', 'expected', 'expected_state_sha256', 'purpose'},
        'STOPPED_EMERGENCY_REQUEST')
    request = record['emergency_request']
    require(request == dict(operation_id=record['operation_id'], continuation_id=record['continuation_id'],
        origin_sha256=digest(canonical(origin)), expected=record['before'],
        expected_state_sha256=digest(canonical(record['before'])), purpose='OPERATOR_APPROVED_OUTAGE'),
        'STOPPED_EMERGENCY_REQUEST')
    for slot in SLOTS:
        require(record['handoffs'][slot] == dict(operation_id=record['operation_id'], slot=slot,
            origin_sha256=digest(canonical(origin)), state=record['before'][slot], stopped=True), 'STOPPED_EMERGENCY_HANDOFF')
    for slot in ('NL', 'NL2'):
        current, previous = selected(plan, slot), selected(origin['plan'], slot)
        require(current['previous'] == dict(previous['candidate'], grants=plan['grant_plan']['before']['restricted_grants']) and
                current['nl_profile_sha256'] in (previous['nl_profile_sha256'], origin['prepared'][slot]['target_sha256']),
                'STOPPED_EMERGENCY_SUCCESSOR')
    floor = crl_number(origin['plan']['candidate'])
    require(crl_number(plan['candidate']) == floor + 1 and
            plan['grant_plan']['before']['restricted_crl_sequence'] in
            ([dict(singleton=1, sequence=floor - 1)], [dict(singleton=1, sequence=floor)]),
            'STOPPED_EMERGENCY_FLOOR')


def inspect_stopped(parts, publication, anchor, now):
    try:
        evidence_digest(parts)
        capture = parse(parts['capture.json'])
        require(set(capture) == {'schema', 'purpose', 'operation_id', 'captured_at', 'anchor_sha256', 'nodes'} and
            type(capture['schema']) is int and capture['schema'] == 1 and capture['purpose'] == STOPPED_PURPOSE and
            capture['nodes'] == sorted(SLOTS) and integer(capture['captured_at'], 1) and integer(now, capture['captured_at']) and
            type(anchor) is bytes and len(anchor) == 32 and capture['anchor_sha256'] == digest(anchor) and
            type(capture['operation_id']) is str and re.fullmatch('[a-z0-9-]{16,96}', capture['operation_id']), 'STOPPED_CAPTURE')
        operation, at = capture['operation_id'], capture['captured_at']
        coordinator, coordinator_files = decode_document(parts['coordinator.json'], 'coordinator', operation)
        require(set(coordinator_files) == {'operation.lock', 'plan.json', 'transaction.json', 'last-receipt.json'}, 'STOPPED_COORDINATOR')
        record, plan = parse(coordinator_files['transaction.json']), parse(coordinator_files['plan.json'])
        emergency = record.get('mode') == 'online-emergency'
        required = (BASE_RECORD | EMERGENCY_RECORD) if emergency else STANDARD_RECORD
        allowed = required | OPTIONAL_RECORD | {'emergency_cause'} if emergency else required
        require(required <= set(record) <= allowed and type(record['schema']) is int and record['schema'] == 1 and
                record['operation_id'] == operation and record['state'] == 'COMMITTED' and record['commit_decided'] is True,
                'STOPPED_TERMINAL_RECORD')
        require(type(record['acquired']) is list and len(record['acquired']) == 3 and set(record['acquired']) == SLOTS,
                'STOPPED_ACQUIRED')
        if emergency:
            require(record['emergency_commit_decided'] is True and record['decision'] == 'COMMIT' and
                    type(record['cursor']) is int and record['cursor'] == 6 and record['terminal_result'] == 'EMERGENCY_RECOVERED' and
                    record['emergency_plan_sha256'] == digest(canonical(plan)), 'STOPPED_EMERGENCY_DECISION')
        else:
            require(type(record['quiesced']) is list and len(record['quiesced']) == 3 and set(record['quiesced']) == SLOTS and
                    record['before_sha256'] == digest(canonical(record['before'])) and record['previous'] == plan['previous'] and
                    record['previous_secondary'] == plan['secondary']['previous'], 'STOPPED_PREVIOUS_BINDING')
        gate = record['gate']
        require(set(gate) == {'result', 'authorization', 'pre_stop_sessions', 'zero_downtime'} and
                gate['result'] == 'RENEWAL_READY' and gate['zero_downtime'] is False and
                gate['authorization'] == 'OPERATOR_APPROVED_OUTAGE' and
                (gate['pre_stop_sessions'] == 'UNKNOWN' or integer(gate['pre_stop_sessions'])), 'STOPPED_GATE')
        receipt = parse(coordinator_files['last-receipt.json'])
        receipt_keys = {'schema', 'operation_id', 'state', 'first_cause', 'before_sha256', 'timestamp',
                        'remote_alert_delivery', 'grant_successor_model'} | ({'terminal_result'} if emergency else set())
        require(set(receipt) == receipt_keys and all(canonical(receipt[key]) == canonical(record[key]) for key in
                receipt_keys - {'timestamp', 'remote_alert_delivery', 'grant_successor_model'}) and
                integer(receipt['timestamp'], 1) and receipt['timestamp'] <= at, 'STOPPED_RECEIPT')
        identities = membership(plan['gateway_ids'])
        cohort(record['before'], identities)
        validator = Validator(anchor, delegation, all_activated=True)
        require(set(plan) == {'schema', 'operation_id', 'previous', 'candidate', 'grant_plan', 'ru_expected',
                'nl_profile_sha256', 'gateway_ids', 'secondary'} | ({'online_emergency'} if emergency else set()) and
                type(plan['schema']) is int and plan['schema'] == 2 and plan['operation_id'] == operation and
                plan['ru_expected'] == record['before']['RU'], 'STOPPED_PLAN')
        grant = plan['grant_plan']
        issued = grant['issued_at']
        require(integer(issued, 1) and issued <= receipt['timestamp'] and plan['candidate']['grants'] == grant['after_grants'] and
                plan['previous']['grants'] == grant['before']['restricted_grants'], 'STOPPED_GRANTS')
        validate_grant_plan(grant, issued)
        validator.transition(canonical(plan['previous']), canonical(plan['candidate']), issued, revoke=True, expired_leaf_predecessor=True)
        validate_gateways(plan, validator, at, identities, recovery=True)
        old_crl, new_crl = (x509.load_pem_x509_crl(plan[phase]['crl'].encode()) for phase in ('previous', 'candidate'))
        require({item.serial_number for item in new_crl} == {item.serial_number for item in old_crl} | set(grant['predecessors']),
                'STOPPED_REVOCATIONS')
        expected = dict(plan_sha256=digest(canonical(plan)), crl_sha256=digest(plan['candidate']['crl'].encode()), state='PROMOTED')
        require(record['reconciliation'] == {slot: expected for slot in SLOTS}, 'STOPPED_RECONCILIATION')
        authority_changed = any(selected(plan, slot)['previous']['authority'] != selected(plan, slot)['candidate']['authority']
                                for slot in ('NL', 'NL2'))
        documents, archives, parents = {'coordinator': (coordinator, coordinator_files)}, {}, {}
        for slot in sorted(SLOTS):
            prefix = 'archive/' + operation + '/'
            parent_prefix = 'archive/online-' + digest(operation.encode()) + '/'
            allowed = {'operation.lock', 'completed.json'} | {prefix + name for name in ARCHIVE | {'archive-manifest.json'}}
            if emergency:
                allowed |= {parent_prefix + name for name in NODE_FILES | {'manifest.json', 'owner.json', 'origin.json'}}
            document, files = decode_document(parts[slot + '.json'], slot, operation, allowed_files=allowed)
            documents[slot] = document, files
            require(files['operation.lock'] == b'', 'STOPPED_LOCK')
            archived = {name.removeprefix(prefix): raw for name, raw in files.items() if name.startswith(prefix)}
            archives[slot] = archived
            manifest = manifest_check(archived, 'archive-manifest.json', {'archive-manifest.json'})
            ledger = parse(files['completed.json'])
            require(type(ledger) is dict and set(ledger) == {operation}, 'STOPPED_HISTORY_UNSUPPORTED')
            entry = ledger[operation]
            require(set(entry) == {'result', 'manifest_sha256', 'timestamp'} and entry['result'] == 'CLEANED' and
                    entry['manifest_sha256'] == digest(canonical(manifest)) and integer(entry['timestamp'], issued) and
                    entry['timestamp'] <= receipt['timestamp'], 'STOPPED_LEDGER')
            required_files = {'files.json', 'plan.json', 'reconciliation.json', 'archive-manifest.json'} | (
                {'prepared-plan.json', 'directory-accepted.json'} if slot == 'RU' else {'directory-before.json'})
            if emergency:
                required_files.add('online-origin.json')
                require(parse(archived['online-origin.json']) == record['online_parent'], 'STOPPED_EMERGENCY_ORIGIN')
                parents[slot] = {name.removeprefix(parent_prefix): raw for name, raw in files.items() if name.startswith(parent_prefix)}
            if slot == 'RU' and authority_changed:
                required_files.add('authority-request.json')
            required_files |= {name + suffix for name in parse(archived['files.json']) for suffix in ('.before', '.staged')}
            require(required_files == set(archived) and all(archived[name] == canonical(plan) for name in
                    ('plan.json', 'prepared-plan.json') if name in archived) and
                    archived['reconciliation.json'] == canonical(record['reconciliation']), 'STOPPED_ARCHIVE_BINDING')
            material_check(archived, slot, record, plan, validator, at, emergency)
        paths = [PurePosixPath(document['host']['path']) for document, _ in documents.values()]
        require(all(not left.is_relative_to(right) for index, left in enumerate(paths)
                    for other, right in enumerate(paths) if index != other), 'STOPPED_HOST_OVERLAP')
        if emergency:
            parent_check(parts, documents, parents, record, plan, anchor, now)
        else:
            require(('authority-request.json' in archives['RU']) == authority_changed, 'STOPPED_AUTHORITY_REQUEST')
            if authority_changed:
                request = parse(archives['RU']['authority-request.json'])
                require(set(request) == {'schema', 'operation_id', 'gateway_ids', 'requests'} and type(request['schema']) is int and
                        request['schema'] == 2 and request['operation_id'] == operation and request['gateway_ids'] == identities and
                        set(request['requests']) == {'NL', 'NL2'}, 'STOPPED_AUTHORITY_REQUEST')
                for slot, item in request['requests'].items():
                    chosen = selected(plan, slot)
                    require(set(item) == {'schema', 'operation_id', 'previous_authority', 'successor_payload', 'request_expires_at'} and
                            type(item['schema']) is int and item['schema'] == 1 and item['operation_id'] == operation and
                            item['previous_authority'] == chosen['previous']['authority'] and
                            item['successor_payload'] == parse(base64.b64decode(chosen['candidate']['authority']['payload'], validate=True)) and
                            integer(item['request_expires_at'], issued + 1), 'STOPPED_AUTHORITY_REQUEST')
        published = parse(publication)
        require(type(publication) is bytes and len(publication) <= 1024 * 1024 and set(published) == {'schema', 'directories'} and
                type(published['schema']) is int and published['schema'] == 1 and set(published['directories']) == {'NL', 'NL2'},
                'STOPPED_PUBLICATION')
        directories = {slot: base64.b64decode(raw, validate=True) for slot, raw in published['directories'].items()}
        require(parse(archives['RU']['directory-accepted.json']) == dict(operation_id=operation,
                directories={slot: digest(raw) for slot, raw in directories.items()}), 'STOPPED_DIRECTORY_RECEIPT')
        for slot, raw in directories.items():
            candidate = selected(plan, slot)['candidate']
            validator.validate(canonical(candidate), now)
            trust, _ = delegation(candidate['authority'], anchor, now)
            directory(raw, trust['family'], identities[slot], now_ns=now * 10**9)
            before = parse(archives[slot]['directory-before.json'])
            require(set(before) == {'sha256'} and sha(before['sha256']) and before['sha256'] != digest(raw), 'STOPPED_DIRECTORY_UNCHANGED')
        return plan, directories, 'emergency' if emergency else 'offline' if authority_changed else 'stopped'
    except ImportRejected:
        raise
    except (Rejected, ValueError, KeyError, TypeError, AttributeError, OverflowError, RecursionError,
            InvalidSignature, UnsupportedAlgorithm):
        raise ImportRejected('STOPPED_EVIDENCE_INVALID') from None
