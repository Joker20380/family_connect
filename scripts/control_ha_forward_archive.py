"""Portable encrypted forward-checkpoint inputs, never a trust registry or restore permit."""
import base64
import hmac
import secrets

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from scripts import control_ha_forward_checkpoint as forward
from scripts import control_ha_forward_sources as sources
from scripts import control_ha_legacy_custody as custody
from scripts import control_ha_recovery_bundle as recovery
from scripts.control_ha_import import ImportRejected, digest, encoded, require

PURPOSE = 'family-connect/forward-checkpoint-archive/v1/offline-inputs-only'
MAGIC = b'FC-HA-FORWARD\x00\x01'
MAX_SIDECARS = 32 * 1024 * 1024
FRAMES = (('request', forward.MAX_REQUEST), ('signature', 64),
          ('recovery_bundle', recovery.MAX_PLAINTEXT + len(recovery.MAGIC) + 28),
          ('history_bundle', custody.MAX_PLAINTEXT + len(custody.MAGIC) + 28),
          ('sidecars', MAX_SIDECARS))
MAX_PLAINTEXT = sum(limit + 8 for _, limit in FRAMES)


def encode_map(values):
    return {name: base64.b64encode(raw).decode() for name, raw in values.items()}


def decode_map(value, keys, limit):
    require(type(value) is dict and set(value) == set(keys), 'FORWARD_ARCHIVE_SIDECAR_FIELDS')
    return {name: recovery.decode(raw, limit) for name, raw in value.items()}


def encode_sidecars(document, publications, authorities, source_materials):
    identities, material = sources.inspect(source_materials)
    require(identities == document['sources'], 'FORWARD_SOURCE_BYTES_MISMATCH')
    require(forward.publication_hashes(publications) == document['publications'], 'FORWARD_PUBLICATION_MISMATCH')
    gateway_ids = {node: binding['identity'] for node, binding in document['gateways'].items()}
    require(forward.gateway_bindings(gateway_ids, authorities) == document['gateways'], 'FORWARD_GATEWAY_MISMATCH')
    return encoded(dict(version=1, purpose=PURPOSE, publications=encode_map(publications),
        authorities=encode_map(authorities), source_materials={node: dict(
            configuration=base64.b64encode(parts['configuration']).decode(), files=encode_map(parts['files']))
            for node, parts in material.items()}))


def decode_sidecars(raw):
    document = recovery.parse(raw)
    require(type(document) is dict and set(document) ==
            {'version', 'purpose', 'publications', 'authorities', 'source_materials'}, 'FORWARD_ARCHIVE_SIDECAR_FIELDS')
    require(type(document['version']) is int and document['version'] == 1 and document['purpose'] == PURPOSE,
            'FORWARD_ARCHIVE_PURPOSE')
    publications = decode_map(document['publications'], forward.GATEWAYS, 1024 * 1024)
    authorities = decode_map(document['authorities'], forward.GATEWAYS, 16384)
    require(type(document['source_materials']) is dict and set(document['source_materials']) == forward.NODES,
            'FORWARD_SOURCE_MATERIAL_COVERAGE')
    materials = {}
    for node, material in document['source_materials'].items():
        require(type(material) is dict and set(material) == {'configuration', 'files'}, 'FORWARD_SOURCE_MATERIAL_FIELDS')
        configuration = recovery.decode(material['configuration'], sources.MAX_FILE)
        declared = sources.configuration(configuration)['source_files']
        materials[node] = dict(configuration=configuration, files=decode_map(material['files'], declared, sources.MAX_FILE))
    return publications, authorities, materials


def frame(parts):
    require(type(parts) is dict and set(parts) == {name for name, _ in FRAMES}, 'FORWARD_ARCHIVE_FRAMES')
    chunks = []
    for name, limit in FRAMES:
        raw = parts[name]
        require(type(raw) is bytes and 0 < len(raw) <= limit, 'FORWARD_ARCHIVE_FRAME_BOUNDS')
        chunks.extend((len(raw).to_bytes(8, 'big'), raw))
    return b''.join(chunks)


def unframe(plaintext):
    require(type(plaintext) is bytes and 0 < len(plaintext) <= MAX_PLAINTEXT, 'FORWARD_ARCHIVE_PLAINTEXT_BOUNDS')
    parts, offset = {}, 0
    for name, limit in FRAMES:
        require(offset + 8 <= len(plaintext), 'FORWARD_ARCHIVE_FRAME_BOUNDS')
        length = int.from_bytes(plaintext[offset:offset + 8], 'big')
        offset += 8
        require(0 < length <= limit and offset + length <= len(plaintext), 'FORWARD_ARCHIVE_FRAME_BOUNDS')
        parts[name] = plaintext[offset:offset + length]
        offset += length
    require(offset == len(plaintext), 'FORWARD_ARCHIVE_TRAILING_BYTES')
    return parts


def seal(request, signature, key, *, recovery_bundle, history_bundle, publications, authorities, source_materials):
    require(type(key) is bytes and len(key) == 32, 'FORWARD_ARCHIVE_KEY')
    document = forward.checked_request(request)
    require(type(signature) is bytes and len(signature) == 64, 'FORWARD_SIGNATURE_FORMAT')
    for name, raw in (('recovery', recovery_bundle), ('history', history_bundle)):
        limit = dict(FRAMES)[name + '_bundle']
        require(type(raw) is bytes and 0 < len(raw) <= limit, 'FORWARD_ARCHIVE_FRAME_BOUNDS')
        require(digest(raw) == document[name]['bundle_sha256'], 'FORWARD_ARCHIVE_INNER_BINDING')
    require(type(publications) is dict and type(authorities) is dict, 'FORWARD_MATERIAL_MAPS')
    sidecars = encode_sidecars(document, dict(publications), dict(authorities), source_materials)
    plaintext = frame(dict(request=request, signature=signature, recovery_bundle=recovery_bundle,
                           history_bundle=history_bundle, sidecars=sidecars))
    nonce = secrets.token_bytes(12)
    bundle = MAGIC + nonce + AESGCM(key).encrypt(nonce, plaintext, MAGIC + PURPOSE.encode() + bytes.fromhex(digest(request)))
    return bundle, digest(bundle)


def verify(bundle, key, expected_bundle_sha256, *, expected_request_sha256, trusted_key,
           minimum_sequence, minimum_crl, minimum_authority_sequences, now, recovery_key, history_key, anchor):
    require(type(key) is bytes and len(key) == 32, 'FORWARD_ARCHIVE_KEY')
    require(forward.hexadecimal(expected_bundle_sha256) and forward.hexadecimal(expected_request_sha256),
            'FORWARD_ARCHIVE_EXTERNAL_PINS')
    require(type(bundle) is bytes and len(MAGIC) + 28 < len(bundle) <= MAX_PLAINTEXT + len(MAGIC) + 28 and
            bundle.startswith(MAGIC), 'FORWARD_ARCHIVE_FORMAT')
    require(hmac.compare_digest(digest(bundle), expected_bundle_sha256), 'FORWARD_ARCHIVE_DIGEST')
    try:
        offset = len(MAGIC)
        plaintext = AESGCM(key).decrypt(bundle[offset:offset + 12], bundle[offset + 12:],
            MAGIC + PURPOSE.encode() + bytes.fromhex(expected_request_sha256))
        parts = unframe(plaintext)
        document = forward.checked_request(parts['request'])
        require(digest(parts['request']) == expected_request_sha256, 'FORWARD_REQUEST_PIN')
        publications, authorities, materials = decode_sidecars(parts['sidecars'])
        return forward.verify(parts['request'], parts['signature'], trusted_key, expected_request_sha256,
            minimum_sequence=minimum_sequence, minimum_crl=minimum_crl, now=now,
            recovery_bundle=parts['recovery_bundle'], recovery_key=recovery_key,
            history_bundle=parts['history_bundle'], history_key=history_key, anchor=anchor,
            sources=document['sources'], publications=publications, authorities=authorities,
            gateway_ids={node: binding['identity'] for node, binding in document['gateways'].items()},
            minimum_authority_sequences=minimum_authority_sequences, source_materials=materials)
    except ImportRejected:
        raise
    except InvalidTag:
        raise ImportRejected('FORWARD_ARCHIVE_AUTHENTICATION') from None
    except (ValueError, TypeError, KeyError, OverflowError, RecursionError):
        raise ImportRejected('FORWARD_ARCHIVE_INVALID') from None
