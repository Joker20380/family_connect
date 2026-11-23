"""Read-only canonical bounded-maintenance archive checks, never a resume API."""
import base64
from dataclasses import replace
import hashlib
import hmac
from pathlib import PurePosixPath
import re

from cryptography import x509
from cryptography.exceptions import InvalidSignature, UnsupportedAlgorithm
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, load_pem_private_key

from control.friends import profile_store, restricted, restricted_maintenance as maintenance
from control.friends.transport_policy import NODES
from scripts.control_ha_import import ImportRejected, digest, encoded, require
from scripts.control_ha_receiver_v1 import ReceiverRecoveryInputs, preflight_receivers
from scripts.control_ha_recovery_bundle import parse

ADAPTER = 'family-connect/canonical-maintenance/v1/not-for-activation'
PURPOSE = 'synthetic-canonical-maintenance/v1/not-live-attestation'
PARTS = frozenset({'capture.json'} | {node + '.json' for node in NODES})
FILES = {'profile': 49152, 'directory': 8192, 'lock': 4096, 'journal-key': 32, 'publisher': 131072}
OP_FILES = {'permit.json': 8192, 'request.json': 20000, 'journal.json': 16384,
            'before-profile.json': 49152, 'before-directory.json': 8192, 'target-profile.json': 49152}
JOURNAL_FIELDS = frozenset(('schema state permit_sha256 request_sha256 before_profile_sha256 '
    'before_directory_sha256 target_profile_sha256 expected_crl_number target_crl_number '
    'expected_minimum_crl target_minimum_crl target_payload_sha256 attempt_count replace_started '
    'committed_write applied_at material_metadata directory_checkpoint configuration_sha256').split())


class MaintenanceRecoveryInputs(ReceiverRecoveryInputs):
    def summary(self):
        value = super().summary()
        value.update(result='ISOLATED_MAINTENANCE_PREFLIGHT_PASS', maintenance_adapter=ADAPTER,
                     exact_bytes_only=[], maintenance_nodes=len(NODES),
                     maintenance_resume='FORBIDDEN_REQUIRES_HOST_RECONCILIATION',
                     maintenance_scope='ONE_CANONICAL_BOUNDED_JOURNAL_PER_NODE_NO_RENEWAL_LEDGERS')
        value['semantic_checks'].append('maintenance_state')
        return value


def integer(value, minimum=0):
    return type(value) is int and minimum <= value < 2**63


def path(value):
    require(type(value) is str and 1 < len(value) <= 512 and not value.startswith('//') and
            re.fullmatch('/[A-Za-z0-9_./-]+', value) and
            str(PurePosixPath(value)) == value and '..' not in PurePosixPath(value).parts,
            'MAINTENANCE_PATH')
    return PurePosixPath(value)


def binaries(value, limits, *, optional_response=False):
    require(type(value) is dict and (set(value) == set(limits) or
            optional_response and set(value) == set(limits) | {'response.json'}), 'MAINTENANCE_FILES')
    result = {}
    for name, text in value.items():
        limit = limits.get(name, 16384)
        require(type(text) is str and len(text) <= 4 * ((limit + 2) // 3), 'MAINTENANCE_FILE_BOUNDS')
        raw = base64.b64decode(text, validate=True)
        require((bool(raw) or name == 'lock') and len(raw) <= limit and
                base64.b64encode(raw).decode() == text, 'MAINTENANCE_FILE_BOUNDS')
        result[name] = raw
    return result


def metadata(value, *, owner=None, modes=None):
    require(type(value) is dict and set(value) == {'uid', 'gid', 'mode'} and
            all(integer(number) for number in value.values()) and
            value['uid'] < 2**32 - 1 and value['gid'] < 2**32 - 1 and value['mode'] <= 0o7777 and
            (owner is None or value['uid'] == owner) and (modes is None or value['mode'] in modes),
            'MAINTENANCE_METADATA')


def configuration(value, files):
    locator, contract, snapshot = value['locator'], value['contract'], value['metadata']
    require(type(locator) is dict and set(locator) == {'schema', 'lock_version', 'profile', 'lock',
            'operations', 'reader_gid', 'directory'} and type(locator['schema']) is int and
            locator['schema'] == 1 and type(locator['lock_version']) is int and locator['lock_version'] == 1 and
            integer(locator['reader_gid'], 1) and locator['reader_gid'] < 2**32 - 1, 'MAINTENANCE_LOCATOR')
    port = locator['directory']
    require(type(port) is dict and set(port) == {'path', 'metadata', 'publisher_parent', 'publisher_contract'},
            'MAINTENANCE_LOCATOR')
    paths = [path(locator[name]) for name in ('profile', 'lock', 'operations')] + [path(port['path'])]
    require(len(set(paths)) == 4 and all(not left.is_relative_to(right) for left in paths for right in paths
            if left != right), 'MAINTENANCE_PATH_CONFLICT')
    parent = port['publisher_parent']
    require(type(parent) is dict and set(parent) == {'path', 'uid', 'gid', 'mode', 'device', 'inode'} and
            integer(parent['device']) and integer(parent['inode'], 1), 'MAINTENANCE_PUBLISHER')
    metadata({name: parent[name] for name in ('uid', 'gid', 'mode')}, owner=0, modes=(0o1770,))
    publisher = path(parent['path'])
    require(paths[3].parent == publisher and all(not item.is_relative_to(publisher) for item in paths[:3]),
            'MAINTENANCE_PATH_CONFLICT')
    metadata(port['metadata'], modes=(0o600, 0o640))
    require(port['metadata']['uid'] > 0 and port['metadata']['gid'] == parent['gid'], 'MAINTENANCE_PUBLISHER')
    contracts = port['publisher_contract']
    require(type(contracts) is list and len(contracts) == 1 and type(contracts[0]) is list and
            len(contracts[0]) == 3, 'MAINTENANCE_PUBLISHER_VARIANT')
    spelling, expected_hash, expected_metadata = contracts[0]
    require(path(spelling) not in paths and not path(spelling).is_relative_to(publisher) and
            expected_hash == digest(files['publisher']), 'MAINTENANCE_PUBLISHER')
    metadata(expected_metadata, owner=0, modes=(0o600, 0o644, 0o700, 0o755))
    expected_profile = dict(uid=0, gid=locator['reader_gid'], mode=0o640)
    expected_contract = dict(schema=2, profile=locator['profile'], directory=port['path'], lock=locator['lock'],
        operations=locator['operations'], profile_metadata=expected_profile, directory_metadata=port['metadata'],
        publisher_parent=parent, publisher_contract=contracts, max_attempts=1)
    require(encoded(contract) == encoded(expected_contract), 'MAINTENANCE_CONFIGURATION')
    require(type(snapshot) is dict and set(snapshot) == {'profile_metadata', 'lock_sha256', 'lock_inode',
            'operations_inode', 'parents'} and encoded(snapshot['profile_metadata']) == encoded(expected_profile) and
            snapshot['lock_sha256'] == digest(files['lock']) and integer(snapshot['lock_inode'], 1) and
            integer(snapshot['operations_inode'], 1), 'MAINTENANCE_SNAPSHOT')
    parents = snapshot['parents']
    expected_paths = [paths[0], paths[1], paths[2] / 'placeholder']
    require(type(parents) is dict and set(parents) == {str(item) for item in expected_paths}, 'MAINTENANCE_PARENTS')
    seen = {}
    for item in expected_paths:
        chain = parents[str(item)]
        require(type(chain) is dict and set(chain) == {str(parent_path) for parent_path in item.parents},
                'MAINTENANCE_PARENTS')
        for spelling, identity in chain.items():
            require(type(identity) is list and len(identity) == 5 and all(integer(number) for number in identity) and
                    identity[1] > 0 and identity[2] == 0 and identity[4] <= 0o7777 and not identity[4] & 0o022,
                    'MAINTENANCE_PARENTS')
            require(spelling not in seen or seen[spelling] == identity, 'MAINTENANCE_PARENT_CONFLICT')
            seen[spelling] = identity
    require(seen[str(paths[0].parent)][2:] == [0, locator['reader_gid'], 0o750] and
            seen[str(paths[1].parent)][2:] == [0, 0, 0o700] and
            seen[str(paths[2])][1:] == [snapshot['operations_inode'], 0, 0, 0o700], 'MAINTENANCE_PARENTS')


def profile(raw, trust, at):
    value, authority, crl, number = profile_store.profile_material(raw, at)
    require(all(encoded(value[name]) == encoded(trust[name]) for name in ('authority', 'family', 'gateway', 'minimum_revision')),
            'MAINTENANCE_PROFILE_BINDING')
    leaf = x509.load_pem_x509_certificate(value['certificate'].encode())
    leaf.verify_directly_issued_by(authority)
    private = load_pem_private_key(value['private_key'].encode(), password=None)
    require(isinstance(private, Ed25519PrivateKey) and
            private.public_key().public_bytes_raw() == leaf.public_key().public_bytes_raw() and
            leaf.public_bytes(Encoding.PEM).decode() == value['certificate'] and
            leaf.not_valid_before_utc <= restricted.utc(at) < leaf.not_valid_after_utc <= authority.not_valid_after_utc and
            not leaf.extensions.get_extension_for_class(x509.BasicConstraints).value.ca and
            crl.get_revoked_certificate_by_serial_number(leaf.serial_number) is None, 'MAINTENANCE_CREDENTIAL')
    return value, number


def directory_checkpoint(raw, value, contract, at):
    restricted.directory(raw, value['family'], value['gateway'], now=at)
    document = parse(raw)
    return dict(sha256=digest(raw), family=value['family'], gateway=value['gateway'],
        issued=restricted.timestamp_ns(document['issued_at']), expires=restricted.timestamp_ns(document['expires_at']),
        contract_sha256=digest(encoded(contract['publisher_contract'])))


def operation_check(operation_id, encoded_files, node, files, trust, captured_at):
    raw = binaries(encoded_files, OP_FILES, optional_response=True)
    permit = maintenance.validate_permit(parse(raw['permit.json']))
    require(permit['operation_id'] == operation_id and raw['permit.json'] == encoded(permit), 'MAINTENANCE_PERMIT')
    envelope = parse(raw['journal.json'])
    require(type(envelope) is dict and set(envelope) == {'journal', 'mac'} and type(envelope['mac']) is str and
            re.fullmatch('[a-f0-9]{64}', envelope['mac']) and
            hmac.compare_digest(envelope['mac'], hmac.new(files['journal-key'], encoded(envelope['journal']),
                                                       hashlib.sha256).hexdigest()), 'MAINTENANCE_MAC')
    journal = envelope['journal']
    require(type(journal) is dict and set(journal) == JOURNAL_FIELDS and type(journal['schema']) is int and
            journal['schema'] == 1 and journal['state'] in maintenance.STATES, 'MAINTENANCE_JOURNAL')
    expected = dict(permit_sha256=digest(raw['permit.json']), request_sha256=digest(raw['request.json']),
        before_profile_sha256=digest(raw['before-profile.json']), before_directory_sha256=digest(raw['before-directory.json']),
        target_profile_sha256=digest(raw['target-profile.json']), configuration_sha256=digest(encoded(node['contract'])))
    require(all(journal[name] == value for name, value in expected.items()) and
            encoded(journal['material_metadata']) == encoded(node['metadata']), 'MAINTENANCE_JOURNAL_BINDING')
    at = permit['not_before']
    require(at <= captured_at, 'MAINTENANCE_TIME')
    before, old_number = profile(raw['before-profile.json'], trust, at)
    target, target_number = profile(raw['target-profile.json'], trust, at)
    checkpoint = directory_checkpoint(raw['before-directory.json'], before, node['contract'], at)
    require(encoded(journal['directory_checkpoint']) == encoded(checkpoint), 'MAINTENANCE_DIRECTORY_CHECKPOINT')
    current_directory = directory_checkpoint(files['directory'], target, node['contract'], captured_at)
    require(current_directory['issued'] >= checkpoint['issued'] and current_directory['expires'] >= checkpoint['expires'] and
            (current_directory['sha256'] == checkpoint['sha256'] or current_directory['issued'] > checkpoint['issued']),
            'MAINTENANCE_DIRECTORY_ROLLBACK')
    payload = maintenance.request_payload(raw['request.json'])
    expected_permit = dict(expected_profile_sha256=expected['before_profile_sha256'],
        expected_directory_sha256=expected['before_directory_sha256'],
        expected_embedded_crl_sha256=digest(before['revocations'].encode()), expected_embedded_crl_number=old_number,
        expected_minimum_crl=before['minimum_crl'], request_sha256=expected['request_sha256'],
        target_crl_sha256=digest(payload), target_crl_number=target_number, target_minimum_crl=target['minimum_crl'])
    require(all(permit[name] == item for name, item in expected_permit.items()), 'MAINTENANCE_PERMIT_BINDING')
    built = (profile_store.floor_target(raw['before-profile.json'], at) if permit['action'] == 'reconcile_current_floor'
             else profile_store.exact_crl_target(raw['before-profile.json'], payload, at))
    require(built == raw['target-profile.json'] and payload == target['revocations'].encode() and
            built != raw['before-profile.json'], 'MAINTENANCE_TARGET')
    expected_fields = dict(expected_crl_number=old_number, target_crl_number=target_number,
        expected_minimum_crl=before['minimum_crl'], target_minimum_crl=target['minimum_crl'], target_payload_sha256=digest(payload))
    require(all(encoded(journal[name]) == encoded(item) for name, item in expected_fields.items()), 'MAINTENANCE_FLOORS')
    state = journal['state']
    settled = state in ('COMMITTED', 'IDEMPOTENT')
    require(type(journal['attempt_count']) is int and journal['attempt_count'] in (0, 1) and
            type(journal['replace_started']) is bool and type(journal['committed_write']) is bool and
            journal['committed_write'] == settled and
            journal['replace_started'] == (state not in ('PREPARED', 'CONFLICT')) and
            (journal['attempt_count'] == 1 or state == 'PREPARED'), 'MAINTENANCE_STATE')
    allowed = (raw['target-profile.json'],) if settled else ((raw['before-profile.json'], raw['target-profile.json'])
              if state in ('APPLYING', 'UNKNOWN') else (raw['before-profile.json'],))
    require(files['profile'] in allowed, 'MAINTENANCE_CURRENT_PROFILE')
    if not settled:
        require(journal['applied_at'] is None and 'response.json' not in raw, 'MAINTENANCE_UNSETTLED_RECEIPT')
        return state
    require(integer(journal['applied_at']) and at <= journal['applied_at'] <= captured_at and
            'response.json' in raw, 'MAINTENANCE_RESPONSE')
    response = parse(raw['response.json'])
    expected_response = dict(schema=1, result='PASS' if state == 'COMMITTED' else 'IDEMPOTENT',
        operation_safe_label='maintenance_' + digest(operation_id.encode())[:12], crl_number=target_number,
        payload_sha256=digest(payload), minimum_crl=target['minimum_crl'], profile_sha256=digest(built),
        directory_sha256=digest(files['directory']), directory_base64=base64.b64encode(files['directory']).decode(),
        applied_at=journal['applied_at'])
    require(encoded(response) == encoded(expected_response), 'MAINTENANCE_RESPONSE')
    return state


def inspect_maintenance(parts, issuer, *, now):
    """Authenticate archived evidence; unresolved evidence is retained, not executable."""
    try:
        require(set(parts) == PARTS, 'MAINTENANCE_PARTS')
        require(all(type(raw) is bytes and 0 < len(raw) <= (8192 if name == 'capture.json' else 1024 * 1024)
                    for name, raw in parts.items()), 'MAINTENANCE_BOUNDS')
        capture = parse(parts['capture.json'])
        require(type(capture) is dict and set(capture) == {'schema', 'purpose', 'captured_at', 'nodes'} and
                type(capture['schema']) is int and capture['schema'] == 1 and capture['purpose'] == PURPOSE and
                integer(capture['captured_at']) and integer(now) and capture['captured_at'] <= now and
                capture['nodes'] == sorted(NODES), 'MAINTENANCE_CAPTURE')
        trust = parse(base64.b64decode(parse(issuer['delegation'])['payload'], validate=True))
        states, identities = [], set()
        for node in NODES:
            value = parse(parts[node + '.json'])
            require(type(value) is dict and set(value) == {'schema', 'node', 'locator', 'contract', 'metadata',
                    'files', 'operations', 'renewal'} and type(value['schema']) is int and value['schema'] == 1 and
                    value['node'] == node, 'MAINTENANCE_NODE')
            require(value['renewal'] == dict(format='none-declared/v1', coordinator=[], node=[]),
                    'MAINTENANCE_RENEWAL_UNSUPPORTED')
            files = binaries(value['files'], FILES)
            require(len(files['journal-key']) == 32, 'MAINTENANCE_KEY')
            configuration(value, files)
            identity = (value['locator']['profile'], value['locator']['lock'], value['locator']['operations'],
                        value['locator']['directory']['path'])
            require(not identities.intersection(identity), 'MAINTENANCE_NODE_PATH_CONFLICT')
            identities.update(identity)
            require(type(value['operations']) is dict and len(value['operations']) == 1,
                    'MAINTENANCE_OPERATION_COVERAGE')
            for operation_id, operation in value['operations'].items():
                state = operation_check(operation_id, operation, value, files, trust, capture['captured_at'])
                current, number = profile(files['profile'], trust, capture['captured_at'])
                target = parse(base64.b64decode(operation['target-profile.json'], validate=True))
                require(target['revocations'].encode() == issuer['crl'] and
                        (state not in ('COMMITTED', 'IDEMPOTENT') or current['minimum_crl'] == number),
                        'MAINTENANCE_CANONICAL_CRL')
                states.append(state)
        return dict(nodes=len(NODES), states={state: states.count(state) for state in sorted(set(states))},
                    settled=all(state in ('COMMITTED', 'IDEMPOTENT') for state in states))
    except ImportRejected:
        raise
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, OverflowError, RecursionError,
            InvalidSignature, UnsupportedAlgorithm):
        raise ImportRejected('MAINTENANCE_INVALID') from None


def preflight_maintenance(bundle, key, expected, anchor, *, now):
    recovered = preflight_receivers(bundle, key, expected, anchor, now=now)
    result = inspect_maintenance(recovered.artifacts['maintenance_state'], recovered.artifacts['issuer_material'], now=now)
    require(result['settled'], 'MAINTENANCE_UNSETTLED_REQUIRES_RECONCILIATION')
    snapshot = replace(recovered.snapshot, external_digests=recovered.snapshot.external_digests +
                       (('maintenance-adapter', digest(ADAPTER.encode())),))
    return MaintenanceRecoveryInputs(snapshot, recovered.stores, recovered.references, recovered.artifacts, recovered.bootstrap)
