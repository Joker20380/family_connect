"""Operator-signed physical acceptance, bound to a post-start node challenge."""

import base64
import time

from cryptography.exceptions import InvalidSignature

from .contracts import canonical, digest, exact, fail, typed
from .materials import public_hex
from .permit import target_check

SCOPE = 'DISPOSABLE_FLEET_REHEARSAL_ACCEPTANCE'
STEPS = dict(awg=('handshake','dns','https','egress'), tcp=('authentication','https','egress'),
             mesh=('room','join','ready','registration','family_tls','dns','four_https_streams','egress'))
FIELDS = ('schema','scope','instance_id','bundle_id','operation_id','verification_nonce','ipv4','roles',
          'issued_at','expires_at','local_health_sha256','external_evidence_sha256','cleanup','signer')


def validate(body, now):
    exact(body,FIELDS)
    target_check(body['instance_id'],'fleet-rehearsal',body['ipv4'])
    import re
    if (type(body['schema']) is not int or body['schema']!=1 or body['scope']!=SCOPE
            or not re.fullmatch(r'gw-[0-9a-f]{32}', str(body['bundle_id']))
            or not typed(body['operation_id'],'id')
            or any(not typed(body[name],'hash') for name in ('verification_nonce','local_health_sha256',
                    'external_evidence_sha256','signer'))
            or type(body['issued_at']) is not int or type(body['expires_at']) is not int
            or not 0 < body['expires_at']-body['issued_at'] <= 300
            or not body['issued_at'] <= now < body['expires_at']):
        fail('acceptance_contract_or_expired')
    exact(body['roles'],STEPS)
    for role, steps in STEPS.items():
        exact(body['roles'][role],steps)
        if any(value not in ('PASS','FAIL') for value in body['roles'][role].values()):
            fail('acceptance_safe_result')
    if body['cleanup'] not in ('PASS','FAIL'):
        fail('acceptance_cleanup')


def sign(body, authority, *, now=None):
    validate(body, time.time() if now is None else now)
    if body['signer'] != digest(bytes.fromhex(public_hex(authority.public_key()))):
        fail('acceptance_signer_binding')
    return dict(body=body, signature=base64.b64encode(authority.sign(canonical(body))).decode())


def verify(receipt, authority, challenge, *, now=None):
    current = time.time() if now is None else now
    exact(receipt,('body','signature'))
    body = receipt['body']
    validate(body,current)
    try:
        authority.verify(base64.b64decode(receipt['signature'],validate=True),canonical(body))
    except (ValueError,TypeError,InvalidSignature):
        fail('acceptance_signature')
    for field in ('instance_id','bundle_id','operation_id','verification_nonce','ipv4','local_health_sha256'):
        if body[field] != challenge[field]:
            fail('acceptance_challenge_binding')
    if (body['issued_at'] < challenge['started_at'] or body['expires_at'] > challenge['expires_at']
            or body['signer'] != digest(bytes.fromhex(public_hex(authority)))):
        fail('acceptance_window_or_signer')
    if body['cleanup']!='PASS' or any(value!='PASS' for role in body['roles'].values() for value in role.values()):
        fail('acceptance_not_passed')
    return digest(canonical(receipt))
