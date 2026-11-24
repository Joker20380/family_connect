"""Encrypted, bounded laboratory recovery inputs; no live capture or activation."""
import base64
from dataclasses import dataclass, field, replace
import hmac
import json
import re
import secrets

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from control.friends import restricted
from control.friends.access import Access
from control.friends.referrals import Referrals
from scripts.control_ha_import import EXTERNAL_ROLES, STORES, TABLES, MAX_BYTES
from scripts.control_ha_import import ImportRejected, digest, encoded, require, unique
from scripts.control_ha_sqlite_import import preflight_installed_sqlite, preflight_sqlite

PURPOSE = 'family-connect/ha-recovery-bundle/v1/not-for-activation'
MAGIC = b'FC-HA-RECOVERY\x00\x01'
HANDOFF_PURPOSE = 'family-connect/ha-recovery-bundle/v2/closed-handoff/not-for-activation'
HANDOFF_MAGIC = b'FC-HA-RECOVERY\x00\x02'
MAX_PLAINTEXT = 96 * 1024 * 1024
MAX_ARTIFACT = 1024 * 1024
MAX_ARTIFACTS = 64
ISSUER_PARTS = frozenset(('runtime-key', 'referral-secret', 'directory', 'crl', 'delegation'))


@dataclass(frozen=True, repr=False)
class Checkpoint:
    checkpoint: str
    bundle_sha256: str
    anchor_sha256: str
    snapshot_sha256: str


@dataclass(frozen=True, repr=False)
class RecoveryInputs:
    snapshot: object = field(repr=False)
    stores: dict = field(repr=False)
    references: dict = field(repr=False)
    artifacts: dict = field(repr=False)
    bootstrap: bytes = field(repr=False)

    def summary(self):
        return dict(result='ISOLATED_RECOVERY_BUNDLE_PREFLIGHT_PASS', activation='FORBIDDEN',
                    stores=len(self.stores), roles=len(self.artifacts),
                    artifacts=sum(len(parts) for parts in self.artifacts.values()),
                    semantic_checks=['application-sqlite', 'signed-crl', 'issuer-key', 'directory', 'referral-secret'],
                    exact_bytes_only=sorted(EXTERNAL_ROLES - {'issuer_material'}),
                    live_barrier='NOT_IMPLEMENTED', full_external_recovery='NOT_QUALIFIED')


def binary(raw, limit):
    require(type(raw) is bytes and 0 < len(raw) <= limit, 'BUNDLE_BYTES_BOUNDS')
    return raw


def decode(value, limit):
    require(type(value) is str and 0 < len(value) <= 4 * ((limit + 2) // 3), 'BUNDLE_ENCODING_BOUNDS')
    try:
        raw = base64.b64decode(value, validate=True)
    except (ValueError, UnicodeError):
        raise ImportRejected('BUNDLE_ENCODING_INVALID') from None
    binary(raw, limit)
    require(base64.b64encode(raw).decode() == value, 'BUNDLE_ENCODING_NONCANONICAL')
    return raw


def reject_constant(value):
    raise ValueError()


def parse(raw):
    try:
        return json.loads(raw, object_pairs_hook=unique, parse_constant=reject_constant)
    except (ValueError, TypeError, UnicodeError, RecursionError):
        raise ImportRejected('BUNDLE_DOCUMENT_INVALID') from None


def artifact_inventory(artifacts):
    require(type(artifacts) is dict and set(artifacts) == EXTERNAL_ROLES, 'BUNDLE_ROLE_COVERAGE')
    count = 0
    for parts in artifacts.values():
        require(type(parts) is dict and 0 < len(parts) <= MAX_ARTIFACTS, 'BUNDLE_EMPTY_ROLE')
        count += len(parts)
        require(count <= MAX_ARTIFACTS, 'BUNDLE_ARTIFACT_COUNT')
        for name, raw in parts.items():
            require(type(name) is str and re.fullmatch('[a-z0-9][a-z0-9_.-]{0,95}', name) and
                    '..' not in name, 'BUNDLE_ARTIFACT_NAME')
            binary(raw, MAX_ARTIFACT)
    require(set(artifacts['issuer_material']) == ISSUER_PARTS, 'BUNDLE_ISSUER_COVERAGE')


def authority_check(snapshot, artifacts, bootstrap, anchor, now):
    issuer = artifacts['issuer_material']
    envelope = parse(bootstrap)
    require(parse(issuer['delegation']) == envelope['manifest'] and
            issuer['crl'] == envelope['crl'].encode(), 'BUNDLE_ISSUER_BOOTSTRAP_MISMATCH')
    try:
        trust, certificate = restricted.delegation(envelope['manifest'], anchor, now)
        require(len(issuer['runtime-key']) == 32, 'BUNDLE_ISSUER_KEY_SIZE')
        signer = Ed25519PrivateKey.from_private_bytes(issuer['runtime-key'])
        require(hmac.compare_digest(signer.public_key().public_bytes_raw(),
                                    certificate.public_key().public_bytes_raw()), 'BUNDLE_ISSUER_KEY_MISMATCH')
        restricted.directory(issuer['directory'], trust['family'], trust['gateway'], now)
        referrals = Referrals(None, issuer['referral-secret'])
        records = dict(zip((table.name for table in TABLES), snapshot.rows, strict=True))
        for token_hash, sponsor in records['referral_links']:
            require(digest(referrals.digest('referral-v1:' + sponsor).encode()) == token_hash,
                    'BUNDLE_REFERRAL_LINK_MISMATCH')
        for request, sponsor, invitation_hash, created in records['referral_claims']:
            raw = referrals.digest('invite-v1:' + request)[:32].upper()
            invitation = 'FC-' + '-'.join(raw[index:index + 4] for index in range(0, 32, 4))
            require(Access.code_hash(invitation) == invitation_hash, 'BUNDLE_REFERRAL_CLAIM_MISMATCH')
    except ImportRejected:
        raise
    except (ValueError, TypeError, KeyError, UnicodeError):
        raise ImportRejected('BUNDLE_AUTHORITY_INVALID') from None


def bundle_format(version):
    require(type(version) is int and version in (1, 2), 'BUNDLE_VERSION')
    return (MAGIC, PURPOSE, preflight_sqlite) if version == 1 else (
        HANDOFF_MAGIC, HANDOFF_PURPOSE, preflight_installed_sqlite)


def validated(stores, references, artifacts, checkpoint, bootstrap, anchor, now, *, version=1):
    _, purpose, preflight = bundle_format(version)
    artifact_inventory(artifacts)
    require(type(references) is dict and set(references) == EXTERNAL_ROLES, 'BUNDLE_REFERENCE_COVERAGE')
    for raw in references.values():
        binary(raw, MAX_ARTIFACT)
    snapshot = preflight(stores, references, {role: digest(raw) for role, raw in references.items()},
                         checkpoint, bootstrap, anchor, now=now)
    require(version == 1 or bool(snapshot.handoff), 'BUNDLE_HANDOFF_REQUIRED')
    authority_check(snapshot, artifacts, bootstrap, anchor, now)
    provenance = [('bundle-format', digest(purpose.encode()))]
    provenance.extend(('artifact:' + role + '/' + name, digest(raw)) for role, parts in sorted(artifacts.items())
                      for name, raw in sorted(parts.items()))
    snapshot = replace(snapshot, external_digests=snapshot.external_digests + tuple(provenance))
    return RecoveryInputs(snapshot, stores, references, artifacts, bootstrap)


def seal(stores, references, artifacts, checkpoint, bootstrap, anchor, key, *, now):
    return _seal(stores, references, artifacts, checkpoint, bootstrap, anchor, key, now=now, version=1)


def seal_handoff(stores, references, artifacts, checkpoint, bootstrap, anchor, key, *, now):
    return _seal(stores, references, artifacts, checkpoint, bootstrap, anchor, key, now=now, version=2)


def _seal(stores, references, artifacts, checkpoint, bootstrap, anchor, key, *, now, version):
    magic, purpose, _ = bundle_format(version)
    require(type(key) is bytes and len(key) == 32, 'BUNDLE_KEY_REQUIRED')
    recovered = validated(stores, references, artifacts, checkpoint, bootstrap, anchor, now, version=version)
    wrap = lambda raw: base64.b64encode(raw).decode()
    document = dict(version=version, purpose=purpose, checkpoint=checkpoint,
        stores={name: wrap(raw) for name, raw in stores.items()},
        references={role: wrap(raw) for role, raw in references.items()},
        artifacts={role: {name: wrap(raw) for name, raw in parts.items()} for role, parts in artifacts.items()},
        bootstrap=wrap(bootstrap))
    plaintext = binary(encoded(document), MAX_PLAINTEXT)
    nonce = secrets.token_bytes(12)
    bundle = magic + nonce + AESGCM(key).encrypt(nonce, plaintext, magic + purpose.encode())
    return bundle, Checkpoint(checkpoint, digest(bundle), digest(anchor), recovered.snapshot.fingerprint)


def preflight_bundle(bundle, key, expected, anchor, *, now):
    require(type(expected) is Checkpoint and type(expected.checkpoint) is str and
            re.fullmatch('[0-9a-f]{32}', expected.checkpoint), 'BUNDLE_CHECKPOINT_REQUIRED')
    require(all(type(value) is str and re.fullmatch('[0-9a-f]{64}', value) for value in
                (expected.bundle_sha256, expected.anchor_sha256, expected.snapshot_sha256)), 'BUNDLE_CHECKPOINT_INVALID')
    require(type(key) is bytes and len(key) == 32, 'BUNDLE_KEY_REQUIRED')
    require(type(anchor) is bytes and len(anchor) == 32 and digest(anchor) == expected.anchor_sha256,
            'BUNDLE_ANCHOR_MISMATCH')
    binary(bundle, MAX_PLAINTEXT + len(MAGIC) + 28)
    require(len(bundle) > len(MAGIC) + 28 and bundle.startswith((MAGIC, HANDOFF_MAGIC)), 'BUNDLE_FORMAT')
    require(hmac.compare_digest(digest(bundle), expected.bundle_sha256), 'BUNDLE_CHECKPOINT_MISMATCH')
    version = 1 if bundle.startswith(MAGIC) else 2
    magic, purpose, _ = bundle_format(version)
    nonce = bundle[len(magic):len(magic) + 12]
    try:
        plaintext = AESGCM(key).decrypt(nonce, bundle[len(magic) + 12:], magic + purpose.encode())
    except InvalidTag:
        raise ImportRejected('BUNDLE_AUTHENTICATION_FAILED') from None
    document = parse(binary(plaintext, MAX_PLAINTEXT))
    require(type(document) is dict and set(document) ==
            {'version', 'purpose', 'checkpoint', 'stores', 'references', 'artifacts', 'bootstrap'}, 'BUNDLE_FIELDS')
    require(type(document['version']) is int and document['version'] == version and document['purpose'] == purpose,
            'BUNDLE_VERSION')
    require(document['checkpoint'] == expected.checkpoint, 'BUNDLE_CHECKPOINT_MISMATCH')
    require(type(document['stores']) is dict and set(document['stores']) == STORES, 'BUNDLE_STORE_COVERAGE')
    require(type(document['references']) is dict and set(document['references']) == EXTERNAL_ROLES,
            'BUNDLE_REFERENCE_COVERAGE')
    require(type(document['artifacts']) is dict and set(document['artifacts']) == EXTERNAL_ROLES,
            'BUNDLE_ROLE_COVERAGE')
    artifacts = {}
    count = 0
    for role, parts in document['artifacts'].items():
        require(type(parts) is dict and 0 < len(parts) <= MAX_ARTIFACTS, 'BUNDLE_EMPTY_ROLE')
        count += len(parts)
        require(count <= MAX_ARTIFACTS, 'BUNDLE_ARTIFACT_COUNT')
        artifacts[role] = {name: decode(raw, MAX_ARTIFACT) for name, raw in parts.items()}
    recovered = validated({name: decode(raw, MAX_BYTES) for name, raw in document['stores'].items()},
        {role: decode(raw, MAX_ARTIFACT) for role, raw in document['references'].items()}, artifacts,
        document['checkpoint'], decode(document['bootstrap'], 65536), anchor, now, version=version)
    require(recovered.snapshot.fingerprint == expected.snapshot_sha256, 'BUNDLE_SNAPSHOT_MISMATCH')
    return recovered
