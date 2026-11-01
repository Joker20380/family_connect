"""Node-local material custody and authority-signed encryption-key enrollment."""

import base64
from contextlib import contextmanager
import fcntl
import os
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .contracts import canonical, exact, fail
from .enrollment import verify_receipt
from .installer import fsync_directory
from .materials import SCOPE, SLOTS, binding_check, open_envelope
from .private_files import checked, remove_private, write_private


def possession_payload(binding, challenge):
    binding_check(binding)
    if type(challenge) is not str or len(challenge) != 64:
        fail('material_enrollment_challenge')
    return canonical(dict(scope=SCOPE, binding=binding, challenge=challenge))


def bind_enrollment(binding, challenge, proof, authority, node_receipt):
    node_binding = node_receipt['body']['binding']
    verify_receipt(node_receipt, authority.public_key(), node_binding, scope='rehearsal')
    if (node_receipt['body']['public_key'] != binding['enrollment_public_key']
            or any(node_binding[name] != binding[name] for name in ('instance_id', 'logical_gateway', 'ipv4'))
            or node_binding['bundle_id'] not in (binding['bundle_a'], binding['bundle_b'])):
        fail('material_node_enrollment_binding')
    try:
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(binding['enrollment_public_key'])).verify(
            proof, possession_payload(binding, challenge))
    except (ValueError, InvalidSignature):
        fail('material_enrollment_possession')
    body = dict(schema=1, scope=SCOPE, binding=binding, challenge=challenge)
    return dict(body=body, signature=base64.b64encode(authority.sign(canonical(body))).decode())


def verify_enrollment(receipt, binding, authority):
    binding_check(binding)
    exact(receipt, ('body', 'signature'))
    body = receipt['body']
    exact(body, ('schema', 'scope', 'binding', 'challenge'))
    possession_payload(binding, body['challenge'])
    if type(body['schema']) is not int or body['schema'] != 1 or body['scope'] != SCOPE or body['binding'] != binding:
        fail('material_enrollment_binding')
    try:
        authority.verify(base64.b64decode(receipt['signature'], validate=True), canonical(body))
    except (ValueError, TypeError, InvalidSignature):
        fail('material_enrollment_signature')


class MaterialStore:
    def __init__(self, directory, binding, authority, private_key, enrollment, *, service_gid, uid=0, custody_gid=0):
        self.directory = checked(Path(directory).absolute(), directory=True, owner=uid)
        if self.directory.stat().st_mode & 0o077:
            fail('material_store_permissions')
        verify_enrollment(enrollment, binding, authority)
        self.binding = binding
        self.authority = authority
        self.private_key = private_key
        self.uid = uid
        self.service_gid = service_gid
        self.custody_gid = custody_gid

    @contextmanager
    def lock(self):
        path = self.directory/'material.lock'
        if not path.exists():
            try:
                write_private(path, b'', uid=self.uid, gid=self.custody_gid)
            except FileExistsError:
                pass
        checked(path, owner=self.uid)
        descriptor = os.open(path, os.O_WRONLY | os.O_NOFOLLOW)
        with os.fdopen(descriptor, 'wb') as output:
            fcntl.flock(output.fileno(), fcntl.LOCK_EX)
            yield

    def deliver(self, envelope, *, permit_expires_at, now=None):
        slots, receipt = open_envelope(envelope, self.binding, self.private_key, self.authority,
                                       permit_expires_at=permit_expires_at, now=now)
        with self.lock():
            marker = self.directory/('nonce-'+receipt['nonce']+'.json')
            if marker.exists():
                fail('material_replay')
            if (self.directory/'slots').exists() or (self.directory/'slots.pending').exists():
                fail('material_delivery_already_present_or_interrupted')
            write_private(marker, canonical(dict(state='RESERVED', **receipt)), uid=self.uid, gid=self.custody_gid)
            pending = self.directory/'slots.pending'
            pending.mkdir(mode=0o750)
            os.chown(pending, self.uid, self.service_gid)
            fsync_directory(self.directory)
            for name in SLOTS:
                privileged = name in ('awg-material', 'publisher-material')
                write_private(pending/name, slots[name], mode=0o600 if privileged else 0o640,
                              uid=self.uid, gid=self.custody_gid if privileged else self.service_gid)
            write_private(pending/'receipt.json', canonical(receipt), uid=self.uid, gid=self.custody_gid)
            os.rename(pending, self.directory/'slots')
            fsync_directory(self.directory)
            write_private(marker, canonical(dict(state='DELIVERED', **receipt)), uid=self.uid, gid=self.custody_gid, replace=True)
            return receipt

    def retire(self):
        with self.lock():
            removed = []
            for name in ('slots', 'slots.pending'):
                directory = self.directory/name
                if not directory.exists():
                    continue
                checked(directory, directory=True, owner=self.uid)
                if set(path.name for path in directory.iterdir()) - {*SLOTS, 'receipt.json'}:
                    fail('material_retire_unowned_file')
                for slot in directory.iterdir():
                    remove_private(slot, owner=self.uid)
                    removed.append(slot.name)
                directory.rmdir()
                fsync_directory(self.directory)
            return dict(scope=SCOPE, instance_id=self.binding['instance_id'], removed=sorted(set(removed)))
