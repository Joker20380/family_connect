"""Explicitly authorized current-state qualification, never an import or resume permit."""
from dataclasses import asdict, dataclass, field
import re

from cryptography import x509
from cryptography.exceptions import InvalidSignature, UnsupportedAlgorithm
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from control.friends import restricted
from scripts import control_ha_legacy_custody as custody
from scripts import control_ha_forward_sources as source_custody
from scripts.control_ha_import import ImportRejected, digest, encoded, require
from scripts.control_ha_maintenance_v1 import integer, preflight_maintenance
from scripts.control_ha_recovery_bundle import Checkpoint, parse

PURPOSE = 'family-connect/current-state-checkpoint/v1/isolated-qualification-only'
DOMAIN = (PURPOSE + '\x00authorization\x00').encode()
ACTION = 'QUALIFY_CURRENT_STATE_OFFLINE'
NODES = frozenset(('RU', 'NL1', 'NL2'))
GATEWAYS = frozenset(('NL', 'NL2'))
MAX_REQUEST = 16384
MAX_LIFETIME = 3600
FIELDS = frozenset(('version', 'purpose', 'action', 'checkpoint_id', 'sequence', 'captured_at',
    'expires_at', 'recovery', 'history', 'sources', 'publications', 'issuer_public_sha256', 'gateways'))


@dataclass(frozen=True, repr=False)
class QualifiedCheckpoint:
    current: object = field(repr=False)
    history: object = field(repr=False)
    publications: dict = field(repr=False)
    authorities: dict = field(repr=False)
    source_materials: dict = field(repr=False)
    request_sha256: str
    sequence: int

    def summary(self):
        return dict(result='FORWARD_CHECKPOINT_OFFLINE_QUALIFIED', request_sha256=self.request_sha256,
            sequence=self.sequence, stores=len(self.current.stores), history='OPAQUE_NOT_EXECUTABLE',
            original_approval='NOT_ESTABLISHED_NOT_REQUIRED_FOR_THIS_CONTRACT',
            authorization_scope=ACTION, source_identity='RENEWAL_BYTES_VERIFIED_OFFLINE',
            installed_source='NOT_ATTESTED', source_scope='RENEWAL_MODULES_AND_NODE_CONFIGURATION_ONLY',
            capture_consistency='NOT_QUALIFIED', publication_semantics='BOTH_GATEWAYS_CHECKED_OFFLINE',
            live_publication='NOT_ATTESTED', gateway_leaf_keys='NOT_QUALIFIED',
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


def gateway_fields(value):
    require(type(value) is dict and set(value) == GATEWAYS, 'FORWARD_GATEWAY_COVERAGE')
    for binding in value.values():
        require(type(binding) is dict and set(binding) == {'identity', 'authority_sha256'} and
                hexadecimal(binding['identity'], 32) and hexadecimal(binding['authority_sha256']),
                'FORWARD_GATEWAY_BINDING')
    require(len({binding['identity'] for binding in value.values()}) == 2, 'FORWARD_GATEWAY_ALIASED')


def gateway_bindings(gateway_ids, authorities):
    require(type(gateway_ids) is dict and set(gateway_ids) == GATEWAYS, 'FORWARD_GATEWAY_COVERAGE')
    require(type(authorities) is dict and set(authorities) == GATEWAYS and
            all(type(raw) is bytes and 0 < len(raw) <= 16384 for raw in authorities.values()),
            'FORWARD_AUTHORITY_BOUNDS')
    bindings = {node: dict(identity=gateway_ids[node], authority_sha256=digest(raw))
                for node, raw in authorities.items()}
    gateway_fields(bindings)
    return bindings


def check_publications(authorities, publications, gateway_ids, minimum_authority_sequences, issuer,
                       anchor, *, captured_at, now):
    try:
        gateway_bindings(gateway_ids, authorities)
        publication_hashes(publications)
        require(type(minimum_authority_sequences) is dict and set(minimum_authority_sequences) == GATEWAYS and
                all(type(value) is int and 0 < value < 2**53 for value in minimum_authority_sequences.values()),
                'FORWARD_AUTHORITY_FLOORS')
        require(integer(captured_at, 1) and integer(now, captured_at), 'FORWARD_PUBLICATION_TIME')
        require(parse(authorities['NL']) == parse(issuer['delegation']) and
                publications['NL'] == issuer['directory'], 'FORWARD_PRIMARY_PUBLICATION')
        trusts = {}
        for node in sorted(GATEWAYS):
            envelope = parse(authorities[node])
            trust, _ = restricted.delegation(envelope, anchor, now)
            restricted.delegation(envelope, anchor, captured_at)
            require(trust['gateway'] == gateway_ids[node], 'FORWARD_GATEWAY_IDENTITY')
            require(trust['sequence'] >= minimum_authority_sequences[node], 'FORWARD_AUTHORITY_ROLLBACK')
            for instant in {captured_at, now}:
                restricted.directory(publications[node], trust['family'], gateway_ids[node], now=instant)
            trusts[node] = trust
        require(all(trusts['NL'][name] == trusts['NL2'][name]
                    for name in ('family', 'authority', 'minimum_revision')), 'FORWARD_SHARED_AUTHORITY')
    except ImportRejected:
        raise
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError, RecursionError,
            InvalidSignature, UnsupportedAlgorithm, x509.ExtensionNotFound, x509.DuplicateExtension):
        raise ImportRejected('FORWARD_PUBLICATION_INVALID') from None


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
    gateway_fields(document['gateways'])
    require(type(document['publications']) is dict and set(document['publications']) == {'NL', 'NL2'} and
            all(hexadecimal(value) for value in document['publications'].values()), 'FORWARD_PUBLICATION_HASHES')
    require(hexadecimal(document['issuer_public_sha256']), 'FORWARD_ISSUER_IDENTITY')
    require(encoded(document) == raw, 'FORWARD_NONCANONICAL')
    return document


def request_for(recovery, history, *, sequence, captured_at, expires_at, sources, publications,
                issuer_public_sha256, gateway_ids, authorities):
    require(type(recovery) is Checkpoint and type(history) is custody.CustodyCheckpoint,
            'FORWARD_CHECKPOINT_TYPES')
    raw = encoded(dict(version=1, purpose=PURPOSE, action=ACTION, checkpoint_id=recovery.checkpoint,
        sequence=sequence, captured_at=captured_at, expires_at=expires_at, recovery=asdict(recovery),
        history=asdict(history), sources=sources, publications=publication_hashes(publications),
        issuer_public_sha256=issuer_public_sha256, gateways=gateway_bindings(gateway_ids, authorities)))
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
           recovery_bundle, recovery_key, history_bundle, history_key, anchor, sources, publications,
           gateway_ids, authorities, minimum_authority_sequences, source_materials):
    try:
        document = checked_request(request)
        require(hexadecimal(expected_request_sha256) and digest(request) == expected_request_sha256,
                'FORWARD_REQUEST_PIN')
        require(integer(minimum_sequence) and document['sequence'] > minimum_sequence, 'FORWARD_STALE_SEQUENCE')
        require(integer(now, document['captured_at']) and now < document['expires_at'], 'FORWARD_EXPIRED_OR_FUTURE')
        require(type(trusted_key) is bytes and len(trusted_key) == 32 and
                type(signature) is bytes and len(signature) == 64, 'FORWARD_SIGNATURE_FORMAT')
        Ed25519PublicKey.from_public_bytes(trusted_key).verify(signature, DOMAIN + request)
        require(all(type(value) is dict for value in
                    (authorities, publications, gateway_ids, minimum_authority_sequences)), 'FORWARD_MATERIAL_MAPS')
        authorities, publications = dict(authorities), dict(publications)
        gateway_ids, minimum_authority_sequences = dict(gateway_ids), dict(minimum_authority_sequences)
        source_fields(sources)
        require(document['sources'] == sources, 'FORWARD_SOURCE_MISMATCH')
        require(document['publications'] == publication_hashes(publications), 'FORWARD_PUBLICATION_MISMATCH')
        require(document['gateways'] == gateway_bindings(gateway_ids, authorities), 'FORWARD_GATEWAY_MISMATCH')
        source_materials = source_custody.verify(source_materials, document['sources'], anchor=anchor, gateway_ids=gateway_ids)
        recovered = preflight_maintenance(recovery_bundle, recovery_key, Checkpoint(**document['recovery']),
                                         anchor, now=now)
        issuer = recovered.artifacts['issuer_material']
        public = Ed25519PrivateKey.from_private_bytes(issuer['runtime-key']).public_key().public_bytes_raw()
        require(digest(public) == document['issuer_public_sha256'], 'FORWARD_ISSUER_MISMATCH')
        number = x509.load_pem_x509_crl(issuer['crl']).extensions.get_extension_for_class(x509.CRLNumber).value.crl_number
        require(integer(minimum_crl, 1) and number >= minimum_crl, 'FORWARD_CRL_ROLLBACK')
        check_publications(authorities, publications, gateway_ids, minimum_authority_sequences, issuer, anchor,
                           captured_at=document['captured_at'], now=now)
        preserved = custody.inspect(history_bundle, history_key, custody.CustodyCheckpoint(**document['history']))
        pending_markers(preserved)
        return QualifiedCheckpoint(recovered, preserved, dict(publications), dict(authorities), source_materials,
                                   expected_request_sha256, document['sequence'])
    except ImportRejected:
        raise
    except InvalidSignature:
        raise ImportRejected('FORWARD_SIGNATURE_INVALID') from None
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError, RecursionError):
        raise ImportRejected('FORWARD_INVALID') from None
