"""Pinned receiver safety inputs; no live capture, lease refresh or activation."""
from contextlib import closing
from dataclasses import replace
import math
import re
import sqlite3
import uuid

import RNS

from control.friends import transport_policy as policy
from control.friends.chat import chat_transaction
from messenger.membership import validate as validate_membership
from scripts.control_ha_external_v1 import RoleRecoveryInputs, allocation_check, records, routing_check, preflight_external
from scripts.control_ha_import import ImportRejected, digest, require
from scripts.control_ha_recovery_bundle import parse

ADAPTER = 'family-connect/receiver-safety/v1/not-for-activation'
CAPTURE_PURPOSE = 'synthetic-receiver-capture/v1/not-live-attestation'
PARTS = frozenset({node + suffix for node in policy.NODES for suffix in ('.state.json', '.config.json')} |
                 {'capture.json', 'members.json', 'settings.json', 'bootstrap.json', 'chat-node.json',
                  'node.identity', 'volume-id'})


class ReceiverRecoveryInputs(RoleRecoveryInputs):
    def summary(self):
        value = super().summary()
        value.update(result='ISOLATED_RECEIVER_PREFLIGHT_PASS', receiver_adapter=ADAPTER,
                     exact_bytes_only=['maintenance_state'], receiver_nodes=len(policy.NODES),
                     receiver_activation='FORBIDDEN_REQUIRES_RECONCILIATION')
        value['semantic_checks'].append('receiver_state')
        return value


def integer(value, minimum=0):
    return type(value) is int and minimum <= value < 2**53


def monotonic(value):
    return type(value) in (int, float) and math.isfinite(value) and 0 <= value < 2**53


def boot(value):
    return type(value) is str and str(uuid.UUID(value)) == value


def applied_check(value, cached, observed, registered):
    if value is None:
        return
    decision = cached['decision']
    require(type(value) is dict and set(value) == {'expected_revision', 'applied_revision', 'observed_at',
            'registered', 'allowed', 'result', 'reason'}, 'RECEIVER_APPLIED_FORMAT')
    require(all(integer(value[name]) for name in ('expected_revision', 'applied_revision', 'observed_at')) and
            value['expected_revision'] == value['applied_revision'] == decision['revision'] and
            decision['observed_at'] <= value['observed_at'] <= observed and
            type(value['registered']) is bool and value['registered'] == registered and
            type(value['allowed']) is bool and value['result'] == 'applied' and
            value['reason'] in ('membership-pending', 'canonical', 'noncohort', 'lease-expired', 'lease-valid'),
            'RECEIVER_APPLIED_BINDING')
    require(not value['allowed'] or registered and decision['allowed'] and
            (decision['cohort'] or cached['prepared'] is None), 'RECEIVER_APPLIED_UNSAFE')


def transport_check(parts, database, allocations, capture, now):
    for node in policy.NODES:
        config = parse(parts[node + '.config.json'])
        require(config == dict(schema=1, profile=policy.PROFILE, node=node, enabled=True) and
                type(config['schema']) is int and config['enabled'] is True, 'RECEIVER_CONFIG')
        point = capture['nodes'][node]
        require(type(point) is dict and set(point) == {'boot', 'monotonic'} and boot(point['boot']) and
                monotonic(point['monotonic']), 'RECEIVER_CAPTURE_CLOCK')
        state = parse(parts[node + '.state.json'])
        require(type(state) is dict and set(state) == {'schema', 'node', 'records', 'observed_at'} and
                type(state['schema']) is int and state['schema'] == 1 and state['node'] == node and
                integer(state['observed_at']) and state['observed_at'] <= capture['captured_at'] + policy.CLOCK_SKEW_SECONDS and
                type(state['records']) is dict and len(state['records']) <= 10000, 'RECEIVER_STATE')
        current = {row['device']: row for row in policy.read_snapshot(database, node, now)['decisions']}
        require(set(state['records']) == set(current), 'RECEIVER_DEVICE_COVERAGE')
        peers = {public for index, public in allocations[node]['peers']}
        for device, cached in state['records'].items():
            require(type(cached) is dict and set(cached) == {'decision', 'boot', 'deadline', 'applied', 'prepared'} and
                    boot(cached['boot']) and monotonic(cached['deadline']) and
                    (cached['prepared'] is None or type(cached['prepared']) is str and
                     re.fullmatch('[a-f0-9]{64}', cached['prepared'])), 'RECEIVER_CACHE')
            decision = cached['decision']
            require(type(decision) is dict and integer(decision.get('observed_at')) and
                    decision['observed_at'] <= state['observed_at'], 'RECEIVER_DECISION_TIME')
            policy.validate(dict(schema=1, profile=policy.PROFILE, node=node,
                observed_at=decision['observed_at'], decisions=[decision]), node, decision['observed_at'])
            expected = policy.read_snapshot(database, node, decision['observed_at'], device=device)['decisions'][0]
            require(decision == expected, 'RECEIVER_CANONICAL_BINDING')
            policy.successor(decision, current[device])
            require(not decision['allowed'] or current[device]['allowed'], 'RECEIVER_ALLOW_CONFLICT')
            require(cached['boot'] != point['boot'] or
                    cached['deadline'] <= point['monotonic'] + policy.LEASE_SECONDS, 'RECEIVER_LEASE_EXTENSION')
            applied_check(cached['applied'], cached, state['observed_at'], decision['public_key'] in peers)


def mailbox_check(parts, database, hosts, captured_at):
    members = parse(parts['members.json'])
    require(type(members) is dict and integer(members.get('expires_at'), 1) and
            members['expires_at'] <= captured_at + policy.LEASE_SECONDS, 'RECEIVER_MAILBOX_EXPIRY')
    validate_membership(members, members['expires_at'] - 1)
    chat = chat_transaction(database)
    require(members['sequence'] == chat.sequence() and members['public_keys'] == chat.members(),
            'RECEIVER_MAILBOX_FLOOR_OR_MEMBERS')
    settings, bootstrap, controller = (parse(parts[name]) for name in
                                      ('settings.json', 'bootstrap.json', 'chat-node.json'))
    require(type(settings) is dict and set(settings) == {'volume_id', 'public_key', 'allowed_public'} and
            type(settings['volume_id']) is str and re.fullmatch('[0-9a-f]{32}', settings['volume_id']) and
            parts['volume-id'] == settings['volume_id'].encode() + b'\n', 'RECEIVER_MAILBOX_VOLUME')
    require(type(settings['allowed_public']) is list and 1 <= len(settings['allowed_public']) <= 100 and
            all(type(public) is str and public in chat.members() for public in settings['allowed_public']) and
            len(set(settings['allowed_public'])) == len(settings['allowed_public']), 'RECEIVER_STATIC_MEMBERS')
    require(len(parts['node.identity']) == 64, 'RECEIVER_MAILBOX_KEY')
    identity = RNS.Identity.from_bytes(parts['node.identity'])
    require(identity is not None and settings['public_key'] == identity.get_public_key().hex(), 'RECEIVER_MAILBOX_KEY')
    require(type(bootstrap) is dict and set(bootstrap) == {'server', 'port', 'public_key', 'destination'} and
            bootstrap['server'] in hosts.values() and integer(bootstrap['port'], 1) and bootstrap['port'] <= 65535 and
            bootstrap['public_key'] == settings['public_key'] and
            bootstrap['destination'] == RNS.Destination.hash(identity, 'lxmf', 'propagation').hex(), 'RECEIVER_MAILBOX_BOOTSTRAP')
    require(type(controller) is dict and set(controller) == {'host', 'port', 'public_key'} and
            type(controller['port']) is int and controller == dict(host=bootstrap['server'],
                port=bootstrap['port'], public_key=bootstrap['public_key']), 'RECEIVER_MAILBOX_CONTROLLER')


def receiver_check(recovered, now):
    parts = recovered.artifacts['receiver_state']
    require(set(parts) == PARTS, 'RECEIVER_PARTS')
    require(all(len(raw) <= (1024 * 1024 if name.endswith('.state.json') else 131072)
                for name, raw in parts.items()), 'RECEIVER_BOUNDS')
    capture = parse(parts['capture.json'])
    require(type(capture) is dict and set(capture) == {'schema', 'purpose', 'captured_at', 'nodes'} and
            type(capture['schema']) is int and capture['schema'] == 1 and capture['purpose'] == CAPTURE_PURPOSE and
            integer(capture['captured_at']) and capture['captured_at'] <= now + policy.CLOCK_SKEW_SECONDS and
            type(capture['nodes']) is dict and set(capture['nodes']) == set(policy.NODES), 'RECEIVER_CAPTURE')
    rows = records(recovered.snapshot)
    hosts = routing_check(recovered.artifacts['routing_files'], rows)
    allocations = allocation_check(recovered.artifacts['node_allocations'], rows, hosts)
    with closing(sqlite3.connect(':memory:')) as database:
        database.deserialize(recovered.stores['registry'])
        database.row_factory = sqlite3.Row
        database.execute('PRAGMA trusted_schema=OFF')
        database.execute('PRAGMA query_only=ON')
        database.set_progress_handler(lambda: 1, 2000000)
        transport_check(parts, database, allocations, capture, now)
        mailbox_check(parts, database, hosts, capture['captured_at'])


def preflight_receivers(bundle, key, expected, anchor, *, now):
    recovered = preflight_external(bundle, key, expected, anchor, now=now)
    try:
        receiver_check(recovered, now)
    except ImportRejected:
        raise
    except (ValueError, TypeError, KeyError, IndexError, sqlite3.Error, OverflowError, RecursionError):
        raise ImportRejected('RECEIVER_INVALID') from None
    snapshot = replace(recovered.snapshot, external_digests=recovered.snapshot.external_digests +
                       (('receiver-adapter', digest(ADAPTER.encode())),))
    return ReceiverRecoveryInputs(snapshot, recovered.stores, recovered.references, recovered.artifacts, recovered.bootstrap)
