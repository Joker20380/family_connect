"""Explicitly authorized current-state qualification, never an import or resume permit."""
from dataclasses import asdict, dataclass, field
import re

from cryptography import x509
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from scripts import control_ha_legacy_custody as custody
from scripts.control_ha_import import ImportRejected, digest, encoded, require
from scripts.control_ha_maintenance_v1 import integer, preflight_maintenance
from scripts.control_ha_recovery_bundle import Checkpoint, parse

PURPOSE = 'family-connect/current-state-checkpoint/v1/isolated-qualification-only'
DOMAIN = (PURPOSE + '\x00authorization\x00').encode()
ACTION = 'QUALIFY_CURRENT_STATE_OFFLINE'
NODES = frozenset(('RU', 'NL1', 'NL2'))
MAX_REQUEST = 16384
MAX_LIFETIME = 3600
FIELDS = frozenset(('version', 'purpose', 'action', 'checkpoint_id', 'sequence', 'captured_at',
    'expires_at', 'recovery', 'history', 'sources', 'publications', 'issuer_public_sha256'))


@dataclass(frozen=True, repr=False)
class QualifiedCheckpoint:
    current: object = field(repr=False)
    history: object = field(repr=False)
    request_sha256: str
    sequence: int

    def summary(self):
        return dict(result='FORWARD_CHECKPOINT_OFFLINE_QUALIFIED', request_sha256=self.request_sha256,
            sequence=self.sequence, stores=len(self.current.stores), history='OPAQUE_NOT_EXECUTABLE',
            original_approval='NOT_ESTABLISHED_NOT_REQUIRED_FOR_THIS_CONTRACT',
            authorization_scope=ACTION, source_identity='CALLER_BOUND_NOT_ATTESTED',
            capture_consistency='NOT_QUALIFIED', publication_semantics='SECOND_NODE_NOT_QUALIFIED',
            durable_replay_floor='EXTERNAL_REQUIRED', full_recovery='NOT_QUALIFIED',
            database_import='NOT_AUTHORIZED', host_resume='NOT_AUTHORIZED', activation='FORBIDDEN')


def hexadecimal(value, length=64):
    return type(value) is str and re.fullmatch('[0-9a-f]{' + str(length) + '}', value) is not None


def checkpoint_fields(value, kind, identifier):
    require(type(value) is dict and set(value) == set(kind.__dataclass_fields__), 'FORWARD_CHECKPOINT_FIELDS')
    require(all(hexadecimal(item, 32 if name == identifier else 64) for name, item in value.items()),
            'FORWARD_CHECKPOINT_VALUE')


def source_fields(value):
    require(type(value) is dict and set(value) == NODES, 'FORWARD_SOURCE_COVERAGE')
    for identity in value.values():
        require(type(identity) is dict and set(identity) == {'runtime_sha256', 'configuration_sha256'}
                and all(hexadecimal(item) for item in identity.values()), 'FORWARD_SOURCE_IDENTITY')


def publication_hashes(publications):
    require(type(publications) is dict and set(publications) == {'NL', 'NL2'} and
            all(type(raw) is bytes and 0 < len(raw) <= 1024 * 1024 for raw in publications.values()),
            'FORWARD_PUBLICATIONS')
    return {node: digest(raw) for node, raw in publications.items()}


def checked_request(raw):
    require(type(raw) is bytes and 0 < len(raw) <= MAX_REQUEST, 'FORWARD_REQUEST_BOUNDS')
    document = parse(raw)
    require(type(document) is dict and set(document) == FIELDS, 'FORWARD_REQUEST_FIELDS')
    require(type(document['version']) is int and document['version'] == 1 and
            document['purpose'] == PURPOSE and document['action'] == ACTION, 'FORWARD_SCOPE')
    require(hexadecimal(document['checkpoint_id'], 32) and integer(document['sequence'], 1),
            'FORWARD_IDENTITY')
    captured, expires = document['captured_at'], document['expires_at']
    require(integer(captured, 1) and integer(expires, captured + 1) and
            expires - captured <= MAX_LIFETIME, 'FORWARD_VALIDITY')
    checkpoint_fields(document['recovery'], Checkpoint, 'checkpoint')
    checkpoint_fields(document['history'], custody.CustodyCheckpoint, 'identifier')
    require(document['checkpoint_id'] == document['recovery']['checkpoint'], 'FORWARD_CAPTURE_ID')
    source_fields(document['sources'])
    require(type(document['publications']) is dict and set(document['publications']) == {'NL', 'NL2'} and
            all(hexadecimal(value) for value in document['publications'].values()), 'FORWARD_PUBLICATION_HASHES')
    require(hexadecimal(document['issuer_public_sha256']), 'FORWARD_ISSUER_IDENTITY')
    require(encoded(document) == raw, 'FORWARD_NONCANONICAL')
    return document


def request_for(recovery, history, *, sequence, captured_at, expires_at, sources, publications,
                issuer_public_sha256):
    require(type(recovery) is Checkpoint and type(history) is custody.CustodyCheckpoint,
            'FORWARD_CHECKPOINT_TYPES')
    raw = encoded(dict(version=1, purpose=PURPOSE, action=ACTION, checkpoint_id=recovery.checkpoint,
        sequence=sequence, captured_at=captured_at, expires_at=expires_at, recovery=asdict(recovery),
        history=asdict(history), sources=sources, publications=publication_hashes(publications),
        issuer_public_sha256=issuer_public_sha256))
    checked_request(raw)
    return raw


def pending_markers(preserved):
    coordinator = preserved.trees['coordinator']
    require('owner.json' not in coordinator['entries'], 'FORWARD_PENDING_OWNER')
    record = custody.json_file(coordinator, 'transaction.json')
    require(record.get('state') == 'COMMITTED', 'FORWARD_UNSETTLED_COORDINATOR')
    operation = record.get('operation_id')
    require(type(operation) is str and 0 < len(operation) <= 256, 'FORWARD_CURRENT_OPERATION')
    for node in NODES:
        tree = preserved.trees[node]
        require(set(custody.children(tree)) == {'operation.lock', 'completed.json', 'archive'},
                'FORWARD_PENDING_OR_UNKNOWN_NODE')
        ledger = custody.json_file(tree, 'completed.json')
        require(type(ledger.get(operation)) is dict and ledger[operation].get('result') == 'CLEANED',
                'FORWARD_UNSETTLED_NODE')


def verify(request, signature, trusted_key, expected_request_sha256, *, minimum_sequence, minimum_crl, now,
           recovery_bundle, recovery_key, history_bundle, history_key, anchor, sources, publications):
    try:
        document = checked_request(request)
        require(hexadecimal(expected_request_sha256) and digest(request) == expected_request_sha256,
                'FORWARD_REQUEST_PIN')
        require(integer(minimum_sequence) and document['sequence'] > minimum_sequence, 'FORWARD_STALE_SEQUENCE')
        require(integer(now, document['captured_at']) and now < document['expires_at'], 'FORWARD_EXPIRED_OR_FUTURE')
        require(type(trusted_key) is bytes and len(trusted_key) == 32 and
                type(signature) is bytes and len(signature) == 64, 'FORWARD_SIGNATURE_FORMAT')
        Ed25519PublicKey.from_public_bytes(trusted_key).verify(signature, DOMAIN + request)
        source_fields(sources)
        require(document['sources'] == sources, 'FORWARD_SOURCE_MISMATCH')
        require(document['publications'] == publication_hashes(publications), 'FORWARD_PUBLICATION_MISMATCH')
        recovered = preflight_maintenance(recovery_bundle, recovery_key, Checkpoint(**document['recovery']),
                                         anchor, now=now)
        issuer = recovered.artifacts['issuer_material']
        public = Ed25519PrivateKey.from_private_bytes(issuer['runtime-key']).public_key().public_bytes_raw()
        require(digest(public) == document['issuer_public_sha256'], 'FORWARD_ISSUER_MISMATCH')
        number = x509.load_pem_x509_crl(issuer['crl']).extensions.get_extension_for_class(x509.CRLNumber).value.crl_number
        require(integer(minimum_crl, 1) and number >= minimum_crl, 'FORWARD_CRL_ROLLBACK')
        require(publications['NL'] == issuer['directory'], 'FORWARD_PRIMARY_PUBLICATION')
        preserved = custody.inspect(history_bundle, history_key, custody.CustodyCheckpoint(**document['history']))
        pending_markers(preserved)
        return QualifiedCheckpoint(recovered, preserved, expected_request_sha256, document['sequence'])
    except ImportRejected:
        raise
    except InvalidSignature:
        raise ImportRejected('FORWARD_SIGNATURE_INVALID') from None
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError, RecursionError):
        raise ImportRejected('FORWARD_INVALID') from None
