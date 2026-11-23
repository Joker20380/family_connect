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
    with access.enrollment() as enrollment:
        database = enrollment.chat()
        if database.public_binding(public):
            raise ValueError('Device identity cannot become a service identity')
        prior = database.service(public)
        if prior is not None and not prior['enabled']:
            raise ValueError('Revoked service identity cannot be reactivated by replay')
        database.add_service(public)


def revoke(access, public):
    message(public)
    with access.enrollment() as enrollment:
        enrollment.chat().revoke_service(public)
