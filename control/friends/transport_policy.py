"""Read-only canonical decisions; delivery uses the existing pinned SSH channel."""
import base64
import json
import os
from pathlib import Path
import re
import time
import uuid

PROFILE = 'paid-transports-v2'
LEASE_SECONDS = 120
RECONCILE_SECONDS = 30
TICK_SECONDS = 2
CLOCK_SKEW_SECONDS = 5
NODES = ('gateway-ru', 'nl-amsterdam-1', 'nl-amsterdam-2')


def enabled(root):
    path = Path(root) / 'transport-enforcement.json'
    if not path.exists() and not path.is_symlink():
        return False
    if path.is_symlink() or path.stat().st_uid != os.geteuid() or path.stat().st_mode & 0o022:
        raise ValueError('UNSAFE_TRANSPORT_CONFIGURATION')
    value = json.loads(path.read_text())
    if (set(value) != {'schema', 'profile', 'enabled', 'hosts'} or type(value['schema']) is not int or value['schema'] != 1
            or value['profile'] != PROFILE or value['enabled'] is not True
            or type(value['hosts']) is not dict or set(value['hosts'].values()) != set(NODES)):
        raise ValueError('INVALID_TRANSPORT_CONFIGURATION')
    return True


def node_for_host(root, host):
    if not enabled(root):
        return None
    return json.loads((Path(root) / 'transport-enforcement.json').read_text())['hosts'][host]


def snapshot(registry, node, *, device=None, clock=time.time):
    from . import paid_beta
    if node not in NODES:
        raise ValueError('INVALID_NODE')
    with paid_beta.connection(registry) as database:
        paid_beta.require(paid_beta.schema_present(database), 'PAID_SCHEMA_REQUIRED')
        return read_snapshot(database, node, int(clock()), device=device)


def read_snapshot(database, node, now, *, device=None):
    from . import paid_beta
    query = 'SELECT device,wg,tcp,revoked FROM devices'
    records = database.execute(query + (' WHERE device=?' if device else '') + ' ORDER BY device',
                               (device,) if device else ()).fetchall()
    if device and len(records) != 1:
        raise ValueError('UNKNOWN_DEVICE')
    decisions = []
    for record in records:
        identity = not record['revoked'] and database.execute(
            'SELECT 1 FROM invites WHERE device=? AND revoked=0', (record['device'],)).fetchone() is not None
        effective = paid_beta.effective_subscription_state(database, record['device'], now)
        row = database.execute('SELECT state,version,paid_until,grace_until FROM paid_beta_subscriptions WHERE device=?',
                               (record['device'],)).fetchone()
        allowed = bool(identity and (effective is None or effective.allowed))
        deadline = min(now + LEASE_SECONDS, effective.expires_at) if allowed and effective else now + LEASE_SECONDS
        decisions.append(dict(device=record['device'], public_key=record['wg'], tcp_id=record['tcp'],
            cohort=effective is not None, revision=row['version'] if row else 0,
            state=effective.state if effective else 'noncohort', identity_allowed=bool(identity),
            allowed=allowed, paid_until=row['paid_until'] if row else None,
            grace_until=row['grace_until'] if row else None, observed_at=now, valid_until=deadline))
    return dict(schema=1, profile=PROFILE, node=node, observed_at=now, decisions=decisions)


def validate(envelope, node, now):
    if (type(envelope) is not dict or set(envelope) != {'schema', 'profile', 'node', 'observed_at', 'decisions'}
            or type(envelope['schema']) is not int or envelope['schema'] != 1 or envelope['profile'] != PROFILE or envelope['node'] != node
            or node not in NODES or type(envelope['observed_at']) is not int
            or not now - LEASE_SECONDS < envelope['observed_at'] <= now + CLOCK_SKEW_SECONDS
            or type(envelope['decisions']) is not list or len(envelope['decisions']) > 10000):
        raise ValueError('INVALID_TRANSPORT_ENVELOPE')
    devices, keys, users = set(), set(), set()
    for record in envelope['decisions']:
        if (type(record) is not dict or set(record) != {'device', 'public_key', 'tcp_id', 'cohort', 'revision',
                'state', 'identity_allowed', 'allowed', 'paid_until', 'grace_until', 'observed_at', 'valid_until'}
                or not re.fullmatch('[a-f0-9]{32}', record['device'])
                or str(uuid.UUID(record['tcp_id'])) != record['tcp_id']
                or len(base64.b64decode(record['public_key'], validate=True)) != 32
                or any(type(record[name]) is not bool for name in ('cohort', 'allowed', 'identity_allowed'))
                or type(record['revision']) is not int or record['revision'] < int(record['cohort'])
                or record['observed_at'] != envelope['observed_at']
                or type(record['valid_until']) is not int
                or not record['observed_at'] < record['valid_until'] <= record['observed_at'] + LEASE_SECONDS
                or record['state'] not in ('noncohort', 'trial', 'active', 'grace', 'expired', 'revoked')
                or record['cohort'] != (record['state'] != 'noncohort')
                or record['allowed'] and (not record['identity_allowed'] or record['state'] in ('expired', 'revoked'))
                or record['cohort'] and type(record['paid_until']) is not int
                or record['allowed'] and record['cohort'] and record['valid_until'] > (record['grace_until'] if record['state'] == 'grace' else record['paid_until'])
                or record['device'] in devices or record['public_key'] in keys or record['tcp_id'] in users):
            raise ValueError('INVALID_TRANSPORT_DECISION')
        devices.add(record['device'])
        keys.add(record['public_key'])
        users.add(record['tcp_id'])
    return envelope


def successor(previous, record):
    if previous is None:
        return
    if any(previous[name] != record[name] for name in ('device', 'public_key', 'tcp_id')):
        raise ValueError('BINDING_CONFLICT')
    if (previous['cohort'] and not record['cohort'] or previous['state'] == 'revoked' and record['state'] != 'revoked'
            or not previous['identity_allowed'] and record['identity_allowed']):
        raise ValueError('TERMINAL_DECISION')
    if (record['revision'] < previous['revision'] or record['observed_at'] < previous['observed_at']
            or record['revision'] == previous['revision'] and any(record[name] != previous[name]
                for name in ('paid_until', 'grace_until', 'cohort'))):
        raise ValueError('STALE_OR_CONFLICTING_DECISION')
    if record['observed_at'] == previous['observed_at'] and record != previous:
        if record['revision'] <= previous['revision'] and record['allowed']:
            raise ValueError('SAME_CLOCK_ALLOW_CONFLICT')
    if record['revision'] == previous['revision'] and record['state'] != previous['state']:
        boundary = previous['grace_until'] if previous['state'] == 'grace' else previous['paid_until']
        if record['state'] != 'expired' or boundary is None or record['observed_at'] < boundary:
            raise ValueError('SAME_REVISION_STATE_CONFLICT')


def configuration_decision(access, root, node, record):
    if not enabled(root):
        return record
    envelope = snapshot(access.path, node, device=record['device'], clock=access.clock)
    decision = envelope['decisions'][0]
    if not decision['allowed']:
        from .access import Rejected
        raise Rejected()
    if decision['public_key'] != record['public_key'] or decision['tcp_id'] != record['tcp_id']:
        raise ValueError('BINDING_CONFLICT')
    return dict(record, paid=envelope)
