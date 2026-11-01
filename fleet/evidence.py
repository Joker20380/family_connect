"""Strict signed, sanitized import contract; no remote execution dependencies."""

import base64

from cryptography.exceptions import InvalidSignature

from .contracts import canonical, digest, exact, fail, typed
from .materials import public_hex

SCOPE='DISPOSABLE_FLEET_REHEARSAL_EVIDENCE'
KINDS=('artifact','permit','enrollment','intent','completion','local-health','external-acceptance','reboot','retirement')
STATES=('PREFLIGHTED','STAGED','AWAITING_EXTERNAL_ACCEPTANCE','VERIFIED','ACTIVE','DRAINING','FAILED','QUARANTINED','RETIRED')
RESULTS=('NOT_RUN','PASS','FAIL','RUNNING','AWAITING_EXTERNAL_ACCEPTANCE')
FIELDS=('schema','scope','kind','instance_id','operation_id','bundle_id','previous_bundle','actual_bundle',
        'state','result','provider','region','target_sha256','source_receipt_sha256','source_commit',
        'archive_sha256','manifest_sha256','signature_sha256','local_health','external','duration_ms',
        'rollback','reboot','retirement','issued_at','signer')


def validate(body):
    exact(body,FIELDS)
    if (type(body['schema']) is not int or body['schema']!=1 or body['scope']!=SCOPE or body['kind'] not in KINDS
            or body['state'] not in STATES or body['result'] not in RESULTS
            or any(not typed(body[name],'id') for name in ('instance_id','operation_id','provider','region'))
            or not body['instance_id'].startswith('fleet-rehearsal-')
            or any(not typed(body[name],'hash') for name in ('target_sha256','source_receipt_sha256','signer'))
            or any(not typed(body[name],'hash?') for name in ('archive_sha256','manifest_sha256','signature_sha256'))
            or not typed(body['source_commit'],'commit?')
            or type(body['issued_at']) is not int or body['issued_at']<0
            or type(body['duration_ms']) is not int or not 0<=body['duration_ms']<=14400000
            or any(body[name] not in RESULTS for name in ('local_health','rollback','reboot','retirement'))):
        fail('rehearsal_evidence_contract')
    import re
    for name in ('bundle_id','previous_bundle','actual_bundle'):
        if body[name] is not None and not re.fullmatch(r'gw-[0-9a-f]{32}',str(body[name])):
            fail('rehearsal_evidence_bundle')
    exact(body['external'],('awg','tcp','mesh'))
    if any(value not in RESULTS for value in body['external'].values()):
        fail('rehearsal_evidence_external')
    return body


def sign(body, authority):
    validate(body)
    if body['signer']!=digest(bytes.fromhex(public_hex(authority.public_key()))):
        fail('evidence_signer_binding')
    return dict(body=body,signature=base64.b64encode(authority.sign(canonical(body))).decode())


def verify(receipt, authority):
    exact(receipt,('body','signature'))
    body=validate(receipt['body'])
    try:
        authority.verify(base64.b64decode(receipt['signature'],validate=True),canonical(body))
    except (ValueError,TypeError,InvalidSignature):
        fail('rehearsal_evidence_signature')
    if body['signer']!=digest(bytes.fromhex(public_hex(authority))):
        fail('rehearsal_evidence_signer')
    return body
