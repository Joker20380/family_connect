"""Signed X25519/HKDF/AEAD envelopes; no identity-key conversion or plaintext receipts."""

import base64
import secrets
import time

from cryptography.exceptions import InvalidSignature, InvalidTag
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from .contracts import canonical, digest, exact, fail, load, typed
from .permit import target_check
from .private_files import write_private

SCOPE = 'DISPOSABLE_FLEET_REHEARSAL_MATERIAL'
SLOTS = ('awg-material', 'tcp-material', 'mesh-material', 'publisher-material')
BINDING_FIELDS = ('instance_id', 'logical_gateway', 'ipv4', 'bundle_a', 'bundle_b',
                  'enrollment_public_key', 'material_public_key')
HEADER_FIELDS = ('schema', 'scope', *BINDING_FIELDS, 'slots', 'issued_at', 'expires_at',
                 'nonce', 'ephemeral_public_key')


def public_hex(key):
    return key.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex()


def generate_key(path):
    key = X25519PrivateKey.generate()
    write_private(path, key.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw,
                                         serialization.NoEncryption()))
    return public_hex(key.public_key())


def binding_check(binding):
    exact(binding, BINDING_FIELDS)
    target_check(binding['instance_id'], binding['logical_gateway'], binding['ipv4'])
    import re
    if (any(not re.fullmatch(r'gw-[0-9a-f]{32}', str(binding[name])) for name in ('bundle_a', 'bundle_b'))
            or binding['bundle_a'] == binding['bundle_b']
            or any(not typed(binding[name], 'hash') for name in ('enrollment_public_key', 'material_public_key'))):
        fail('material_binding')


def header_check(header, now):
    exact(header, HEADER_FIELDS)
    binding_check({name: header[name] for name in BINDING_FIELDS})
    if (type(header['schema']) is not int or header['schema'] != 1 or header['scope'] != SCOPE
            or header['slots'] != list(SLOTS) or not typed(header['nonce'], 'hash')
            or not typed(header['ephemeral_public_key'], 'hash')
            or type(header['issued_at']) is not int or type(header['expires_at']) is not int
            or not 0 < header['expires_at'] - header['issued_at'] <= 14400
            or not header['issued_at'] <= now < header['expires_at']):
        fail('material_header_or_expiry')


def cipher(private_key, peer_hex, header):
    try:
        shared = private_key.exchange(X25519PublicKey.from_public_bytes(bytes.fromhex(peer_hex)))
    except ValueError:
        fail('material_key')
    key = HKDF(algorithm=hashes.SHA256(), length=32, salt=bytes.fromhex(header['nonce']),
               info=SCOPE.encode() + canonical(header)).derive(shared)
    return ChaCha20Poly1305(key)


def seal(binding, slots, authority, *, issued_at, expires_at):
    binding_check(binding)
    exact(slots, SLOTS)
    if any(type(value) is not bytes or not 0 < len(value) <= 64*1024 for value in slots.values()):
        fail('material_slot')
    ephemeral = X25519PrivateKey.generate()
    header = dict(schema=1, scope=SCOPE, **binding, slots=list(SLOTS), issued_at=issued_at,
                  expires_at=expires_at, nonce=secrets.token_hex(32),
                  ephemeral_public_key=public_hex(ephemeral.public_key()))
    header_check(header, issued_at)
    payload = canonical({name: base64.b64encode(value).decode() for name, value in slots.items()})
    ciphertext = cipher(ephemeral, binding['material_public_key'], header).encrypt(
        bytes.fromhex(header['nonce'])[:12], payload, canonical(header))
    body = dict(header=header, ciphertext=base64.b64encode(ciphertext).decode())
    return dict(body=body, signature=base64.b64encode(authority.sign(canonical(body))).decode())


def open_envelope(envelope, binding, private_key, authority, *, permit_expires_at, now=None):
    current = time.time() if now is None else now
    binding_check(binding)
    exact(envelope, ('body', 'signature'))
    exact(envelope['body'], ('header', 'ciphertext'))
    body = envelope['body']
    if len(canonical(envelope)) > 400*1024:
        fail('material_bound')
    try:
        authority.verify(base64.b64decode(envelope['signature'], validate=True), canonical(body))
    except (ValueError, TypeError, InvalidSignature):
        fail('material_signature')
    header = body['header']
    header_check(header, current)
    if ({name: header[name] for name in BINDING_FIELDS} != binding
            or header['expires_at'] > permit_expires_at
            or public_hex(private_key.public_key()) != binding['material_public_key']):
        fail('material_binding')
    try:
        plaintext = cipher(private_key, header['ephemeral_public_key'], header).decrypt(
            bytes.fromhex(header['nonce'])[:12], base64.b64decode(body['ciphertext'], validate=True), canonical(header))
        decoded = load(plaintext)
        exact(decoded, SLOTS)
        slots = {name: base64.b64decode(value, validate=True) for name, value in decoded.items()}
    except (ValueError, TypeError, InvalidTag):
        fail('material_decryption')
    if any(not 0 < len(value) <= 64*1024 for value in slots.values()):
        fail('material_slot')
    receipt = dict(scope=SCOPE, instance_id=binding['instance_id'], nonce=header['nonce'],
                   envelope_sha256=digest(canonical(envelope)), expires_at=header['expires_at'],
                   slots={name: digest(value) for name, value in slots.items()})
    return slots, receipt
