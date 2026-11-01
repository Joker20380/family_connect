"""Strict, deterministic fleet contracts. No runtime policy or transport issuance."""

import datetime
import hashlib
import ipaddress
import json
import re


class FleetError(ValueError):
    pass


STATES = ('DISCOVERED', 'PREFLIGHTED', 'STAGED', 'VERIFIED', 'ACTIVE', 'DRAINING',
          'QUARANTINED', 'FAILED', 'RETIRED')
ROLES = ('awg', 'tcp', 'mesh', 'profile-reader', 'publisher', 'renewal', 'snapshot',
         'restricted-sync', 'mailbox', 'load-monitor', 'monitoring')
TRANSITIONS = {
    'DISCOVERED': ('PREFLIGHTED', 'FAILED', 'QUARANTINED'),
    'PREFLIGHTED': ('STAGED', 'FAILED', 'QUARANTINED'),
    'STAGED': ('VERIFIED', 'FAILED', 'QUARANTINED'),
    'VERIFIED': ('ACTIVE', 'STAGED', 'FAILED', 'QUARANTINED'),
    'ACTIVE': ('DRAINING', 'QUARANTINED', 'FAILED'),
    'DRAINING': ('RETIRED', 'QUARANTINED', 'VERIFIED', 'PREFLIGHTED'),
    'QUARANTINED': ('PREFLIGHTED', 'RETIRED'),
    'FAILED': ('PREFLIGHTED', 'QUARANTINED', 'RETIRED'),
    'RETIRED': (),
}
FIELDS = {
    'logical': dict(id='id', country='country', transports='transports', desired_state='state',
                    active_instance='id?', fallback_instances='ids', catalog_generation='int'),
    'instance': dict(instance_id='id', logical_gateway='id', provider='id', region='id', ipv4='ipv4',
                     ipv6='ipv6?', os_family='id', os_version='version', architecture='id', state='state',
                     desired_bundle='id', actual_bundle='id?', enrollment_state='enrollment',
                     health_state='health', deployment_identity='hash?', roles='roles', created_at='time',
                     activated_at='time?', drained_at='time?', quarantined_at='time?'),
    'artifact': dict(bundle_id='id', source_commit='commit', manifest_sha256='hash', archive_sha256='hash',
                     signature='signature', supported_os='ids', architectures='ids', roles='roles', created_at='time'),
    'operation': dict(operation_id='id', instance='id', action='action', previous_bundle='id?', target_bundle='id',
                      state='operation_state', first_failure='id?', started_at='time', completed_at='time?',
                      safe_receipt='receipt'),
}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load(data):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise FleetError('duplicate_json_key')
            result[key] = value
        return result
    try:
        return json.loads(data, object_pairs_hook=pairs, parse_constant=lambda value: fail('nonfinite_json'))
    except (ValueError, UnicodeError) as error:
        raise FleetError('invalid_json') from error


def fail(code):
    raise FleetError(code)


def exact(value, fields):
    if type(value) is not dict or set(value) != set(fields):
        fail('unknown_or_missing_fields')


def typed(value, kind):
    if kind.endswith('?'):
        return value is None or typed(value, kind[:-1])
    if kind in ('ids', 'roles', 'transports'):
        domain = ROLES if kind == 'roles' else ('awg', 'tcp', 'mesh') if kind == 'transports' else None
        return (type(value) is list and len(value) <= 64 and all(typed(item, 'id') for item in value)
                and len(set(value)) == len(value) and (domain is None or set(value) <= set(domain)))
    if kind == 'int':
        return type(value) is int and 0 <= value < 2**53
    if kind == 'receipt':
        return (type(value) is dict and set(value) <= {'result', 'evidence_sha256', 'scope'}
                and all(typed(item, 'hash' if key == 'evidence_sha256' else 'id') for key, item in value.items()))
    domains = {'state': STATES, 'health': ('UNKNOWN', 'PASS', 'FAIL'),
               'enrollment': ('NEW', 'ENROLLED', 'CANCELLED'),
               'action': ('plan', 'preflight', 'stage', 'verify', 'activate', 'drain', 'quarantine', 'rollback', 'status'),
               'operation_state': ('INTENT', 'RUNNING', 'SUCCEEDED', 'FAILED')}
    if kind in domains:
        return type(value) is str and value in domains[kind]
    if type(value) is not str:
        return False
    patterns = {'id': r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}', 'hash': r'[0-9a-f]{64}',
                'commit': r'[0-9a-f]{40}', 'country': r'[A-Z]{2}', 'version': r'[0-9]{2}\.[0-9]{2}',
                'signature': r'[A-Za-z0-9+/]{86}=='}
    if kind in patterns:
        return re.fullmatch(patterns[kind], value) is not None
    if kind in ('ipv4', 'ipv6'):
        try:
            address = ipaddress.ip_address(value)
            return address.version == int(kind[-1]) and not address.is_multicast and not address.is_unspecified and '%' not in value
        except ValueError:
            return False
    if kind == 'time':
        try:
            return value.endswith('Z') and datetime.datetime.fromisoformat(value.replace('Z', '+00:00')).tzinfo is not None
        except ValueError:
            return False
    return False


def validate(kind, value):
    exact(value, FIELDS[kind])
    if not all(typed(value[key], spec) for key, spec in FIELDS[kind].items()):
        fail('invalid_' + kind)
    return value


def inventory(value):
    exact(value, ('schema', 'logical_gateways', 'instances', 'artifacts'))
    if type(value['schema']) is not int or value['schema'] != 1:
        fail('inventory_schema')
    indexes = {}
    for collection, kind, identifier in [('logical_gateways', 'logical', 'id'),
            ('instances', 'instance', 'instance_id'), ('artifacts', 'artifact', 'bundle_id')]:
        items = value[collection]
        if type(items) is not list or len(items) > 10000:
            fail('inventory_bound')
        indexes[collection] = {}
        for item in items:
            validate(kind, item)
            if item[identifier] in indexes[collection]:
                fail('duplicate_' + kind)
            indexes[collection][item[identifier]] = item
    identities = set()
    active_gateways = set()
    for item in value['instances']:
        if item['logical_gateway'] not in indexes['logical_gateways']:
            fail('missing_logical_gateway')
        for bundle in (item['desired_bundle'], item['actual_bundle']):
            if bundle is not None and bundle not in indexes['artifacts']:
                fail('missing_artifact_binding')
        if item['state'] == 'ACTIVE':
            identity = item['deployment_identity']
            if not identity or identity in identities or item['logical_gateway'] in active_gateways:
                fail('conflicting_active_identity')
            if item['health_state'] != 'PASS' or item['enrollment_state'] != 'ENROLLED' or not item['actual_bundle']:
                fail('active_not_accepted')
            identities.add(identity)
            active_gateways.add(item['logical_gateway'])
    for gateway in value['logical_gateways']:
        for identifier in [gateway['active_instance']] + gateway['fallback_instances']:
            if identifier is not None and (identifier not in indexes['instances'] or
                    indexes['instances'][identifier]['logical_gateway'] != gateway['id']):
                fail('instance_gateway_binding')
        active = gateway['active_instance']
        if active is not None and indexes['instances'][active]['state'] != 'ACTIVE':
            fail('active_pointer')
        if gateway['id'] in active_gateways and active is None:
            fail('missing_active_pointer')
    return value


def transition(previous, target, *, health_pass=False):
    if target not in TRANSITIONS.get(previous, ()):
        fail('invalid_state_transition')
    if target in ('VERIFIED', 'ACTIVE') and health_pass is not True:
        fail('health_acceptance_required')
    return target
