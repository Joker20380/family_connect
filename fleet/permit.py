"""Offline, bounded authority for one unpublished disposable rehearsal."""

import base64
import ipaddress
import re
import time

from cryptography.exceptions import InvalidSignature

from .contracts import canonical, digest, exact, fail, typed

SCOPE = 'DISPOSABLE_FLEET_REHEARSAL'
ACTIONS = ('preflight', 'enroll', 'deliver-materials', 'stage', 'start-verification',
           'complete-verification', 'run-acceptance', 'activate-local', 'status', 'upgrade', 'rollback',
           'reboot-verify', 'drain', 'retire')
EXCLUDED = frozenset(('185.251.89.19', '185.10.158.212', '186.246.45.246', '186.246.51.201'))
FIELDS = ('schema', 'scope', 'permit_id', 'instance_id', 'logical_gateway', 'ipv4',
          'ssh_fingerprint', 'provider', 'region', 'bundle_a', 'bundle_b', 'allowed_actions',
          'issued_at', 'expires_at', 'catalog_publication', 'production_identity_import',
          'user_operations', 'paid_operations', 'agent_sha256', 'bundle_signer_sha256')


def target_check(instance_id, logical_gateway, ipv4):
    if (not typed(instance_id, 'id') or not re.fullmatch(r'fleet-rehearsal-[a-z0-9-]+', instance_id)
            or logical_gateway != 'fleet-rehearsal'):
        fail('rehearsal_instance_required')
    try:
        address = ipaddress.IPv4Address(ipv4)
    except (ValueError, TypeError):
        fail('rehearsal_ipv4')
    if not address.is_global or str(address) in EXCLUDED:
        fail('production_or_nonpublic_target')


def validate(body, now=None):
    exact(body, FIELDS)
    target_check(body['instance_id'], body['logical_gateway'], body['ipv4'])
    if (type(body['schema']) is not int or body['schema'] != 1 or body['scope'] != SCOPE
            or not all(typed(body[name], 'id') for name in ('permit_id', 'provider', 'region'))
            or not all(typed(body[name], 'hash') for name in ('agent_sha256', 'bundle_signer_sha256'))
            or not re.fullmatch(r'SHA256:[A-Za-z0-9+/]{43}', str(body['ssh_fingerprint']))
            or not re.fullmatch(r'gw-[0-9a-f]{32}', str(body['bundle_a']))
            or body['bundle_b'] is not None and not re.fullmatch(r'gw-[0-9a-f]{32}', str(body['bundle_b']))
            or body['bundle_a'] == body['bundle_b']):
        fail('rehearsal_permit_contract')
    actions = body['allowed_actions']
    if (type(actions) is not list or not actions or any(action not in ACTIONS for action in actions)
            or len(set(actions)) != len(actions)):
        fail('rehearsal_action')
    if any(body[name] is not False for name in
           ('catalog_publication', 'production_identity_import', 'user_operations', 'paid_operations')):
        fail('rehearsal_prohibited_capability')
    current = time.time() if now is None else now
    if (type(body['issued_at']) is not int or type(body['expires_at']) is not int
            or not 0 < body['expires_at'] - body['issued_at'] <= 14400
            or not body['issued_at'] <= current < body['expires_at']):
        fail('rehearsal_permit_expired_or_not_yet_valid')
    return body


def sign(body, key, now=None):
    validate(body, now)
    return dict(body=body, signature=base64.b64encode(key.sign(canonical(body))).decode())


def verify(permit, public_key, *, host, fingerprint, bundle_id, action, agent_sha256,
           bundle_signer_sha256, now=None):
    exact(permit, ('body', 'signature'))
    body = validate(permit['body'], now)
    try:
        public_key.verify(base64.b64decode(permit['signature'], validate=True), canonical(body))
    except (ValueError, TypeError, InvalidSignature):
        fail('rehearsal_permit_signature')
    if (host != body['ipv4'] or fingerprint != body['ssh_fingerprint']
            or bundle_id not in (body['bundle_a'], body['bundle_b']) or bundle_id is None
            or agent_sha256 != body['agent_sha256'] or bundle_signer_sha256 != body['bundle_signer_sha256']):
        fail('rehearsal_permit_binding')
    if action not in body['allowed_actions']:
        fail('rehearsal_action')
    return digest(canonical(body))


def replay_binding(previous, permit, request):
    exact(request, ('operation_id', 'action', 'bundle_id', 'parameters'))
    if not typed(request['operation_id'], 'id') or request['action'] not in ACTIONS:
        fail('rehearsal_operation')
    binding = dict(permit_sha256=digest(canonical(permit)), request_sha256=digest(canonical(request)))
    if previous is not None and previous != binding:
        fail('rehearsal_replay_changed_parameters')
    return binding
