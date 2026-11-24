"""Operator-only, proof-bearing mailbox identities with no device or VPN grant."""
import re

import RNS


def message(public):
    if type(public) is not str or re.fullmatch('[0-9a-f]{128}', public) is None:
        raise ValueError('Invalid service public key')
    return b'family-connect/chat-service/v1\n' + public.encode('ascii')


def register(access, public, signature):
    payload = message(public)
    if type(signature) is not str or re.fullmatch('[0-9a-f]{128}', signature) is None:
        raise ValueError('Invalid service proof')
    identity = RNS.Identity(create_keys=False)
    if not identity.load_public_key(bytes.fromhex(public)) or not identity.validate(bytes.fromhex(signature), payload):
        raise ValueError('Invalid service proof')
    with access.db() as database:
        if database.execute('SELECT 1 FROM chat_bindings WHERE public=?', (public,)).fetchone():
            raise ValueError('Device identity cannot become a service identity')
        prior = database.execute('SELECT enabled FROM chat_service_senders WHERE public=?', (public,)).fetchone()
        if prior is not None and not prior['enabled']:
            raise ValueError('Revoked service identity cannot be reactivated by replay')
        database.execute('INSERT OR IGNORE INTO chat_service_senders VALUES (?,1)', (public,))


def revoke(access, public):
    message(public)
    with access.db() as database:
        database.execute('UPDATE chat_service_senders SET enabled=0 WHERE public=?', (public,))
