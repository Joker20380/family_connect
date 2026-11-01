"""Sticky physical NL assignment using unchanged, offline-signed schema2 catalogs."""

import base64
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import stat

from .access import Rejected
from provisioning.friends_catalog import parse, verify_catalog


def require(condition):
    if not condition:
        raise ValueError('Gateway routing rejected')


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def private_read(root, name, limit):
    require(Path(name).name == name and name not in ('.', '..'))
    for parent in (root, *root.parents):
        info = parent.lstat()
        require(stat.S_ISDIR(info.st_mode))
    info = root.stat()
    require(info.st_uid == os.geteuid() and stat.S_IMODE(info.st_mode) == 0o700)
    descriptor = os.open(root / name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as source:
        info = os.fstat(source.fileno())
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and
                info.st_uid == os.geteuid() and stat.S_IMODE(info.st_mode) == 0o600)
        raw = source.read(limit + 1)
    require(0 < len(raw) <= limit)
    return raw


def address(value):
    require(type(value) is str)
    result = ipaddress.IPv4Address(value)
    require(str(result) == value and not result.is_loopback and not result.is_unspecified
            and not result.is_multicast and 0 < result.packed[0] < 224)
    return value


class Policy:
    def __init__(self, raw, anchor, catalogs):
        self.value = parse(raw.decode())
        require(set(self.value) == {'schema', 'generation', 'legacy', 'admit', 'catalogs'})
        require(type(self.value['schema']) is int and self.value['schema'] == 1)
        require(type(self.value['generation']) is int and 0 < self.value['generation'] < 2**53)
        records = self.value['catalogs']
        require(type(records) is list and 1 <= len(records) <= 32)
        self.catalogs, self.routes = {}, {}
        sequences, hosts, countries = {}, {}, None
        for record in records:
            require(type(record) is dict and set(record) == {'node', 'sha256'})
            node, sha256 = record['node'], record['sha256']
            require(type(node) is str and re.fullmatch(r'nl-[a-z0-9][a-z0-9-]{0,47}', node))
            require(type(sha256) is str and re.fullmatch('[0-9a-f]{64}', sha256))
            require(sha256 not in self.catalogs and sha256 in catalogs)
            envelope_raw = catalogs[sha256]
            require(type(envelope_raw) is bytes and digest(envelope_raw) == sha256)
            envelope = parse(envelope_raw.decode())
            verified = verify_catalog(envelope, anchor)
            require(verified.sequence not in sequences)
            payload = parse(base64.b64decode(envelope['payload'], validate=True).decode())
            gateways = {item['country']: item for item in payload['gateways']}
            ru = canonical(gateways['ru'])
            require(countries is None or countries == ru)
            countries = ru
            host = address(gateways['nl']['tcp']['server'])
            require(re.findall(r'(?m)^Endpoint\s*=\s*([0-9.]+):[0-9]+\s*$', gateways['nl']['awg']) == [host])
            require(node not in hosts or hosts[node] == host)
            require(all(other == node or previous != host for other, previous in hosts.items()))
            hosts[node] = host
            sequences[verified.sequence] = sha256
            self.catalogs[sha256] = envelope
            self.routes[sha256] = dict(node=node, host=host, sequence=verified.sequence)
        require(type(self.value['legacy']) is str and self.value['legacy'] in self.catalogs)
        require(type(self.value['admit']) is str and self.value['admit'] in self.catalogs)
        require(self.routes[self.value['admit']]['sequence'] >= self.routes[self.value['legacy']]['sequence'])
        self.sha256 = digest(raw)

    @classmethod
    def load(cls, root, sha256):
        require(type(sha256) is str and re.fullmatch('[0-9a-f]{64}', sha256))
        root = Path(root)
        raw = private_read(root, sha256 + '.policy.json', 16384)
        require(digest(raw) == sha256)
        value = parse(raw.decode())
        anchor = base64.b64decode(private_read(root, 'anchor.pub', 128).strip(), validate=True)
        require(type(value.get('catalogs')) is list and len(value['catalogs']) <= 32)
        catalogs = {}
        for record in value['catalogs']:
            require(type(record) is dict and type(record.get('sha256')) is str
                    and re.fullmatch('[0-9a-f]{64}', record['sha256']))
            key = record['sha256']
            catalogs[key] = private_read(root, key + '.catalog.json', 16384)
        return cls(raw, anchor, catalogs)


def state(database):
    exists = database.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='gateway_routing_state'").fetchone()
    if exists is None:
        return None
    rows = database.execute('SELECT * FROM gateway_routing_state').fetchall()
    require(len(rows) == 1 and rows[0]['singleton'] == 1)
    return rows[0]


def operation(value):
    require(type(value) is str and re.fullmatch('[a-zA-Z0-9][a-zA-Z0-9_-]{7,95}', value))
    return value


def replayed(database, operation_id, request_hash):
    record = database.execute('SELECT request_sha256 FROM gateway_assignment_events WHERE operation_id=?',
                              (operation_id,)).fetchone()
    if record is not None:
        require(record['request_sha256'] == request_hash)
    return record is not None


def install(access, policy, legacy_raw, *, operation_id=None):
    """Offline operator transaction; seeds existing devices without moving any of them."""
    require(digest(legacy_raw) == policy.value['legacy'])
    operation_id = operation(operation_id or 'install-'+policy.sha256)
    request_hash = digest(canonical(dict(action='install', policy=policy.sha256)))
    with access.db() as database:
        current = state(database)
        if current is not None:
            require(current['policy_sha256'] == policy.sha256 and current['generation'] == policy.value['generation'])
            require(replayed(database, operation_id, request_hash))
            return dict(result='UNCHANGED', policy_sha256=policy.sha256)
        statements = (
            'CREATE TABLE gateway_routing_state (singleton INTEGER PRIMARY KEY CHECK(singleton=1), '
            'policy_sha256 TEXT NOT NULL, generation INTEGER NOT NULL)',
            'CREATE TABLE gateway_assignments (device TEXT PRIMARY KEY REFERENCES devices(device), '
            'catalog_sha256 TEXT NOT NULL, node TEXT NOT NULL, sequence INTEGER NOT NULL)',
            'CREATE TABLE gateway_assignment_events (operation_id TEXT PRIMARY KEY, request_sha256 TEXT NOT NULL, '
            'device TEXT NOT NULL, previous_sha256 TEXT NOT NULL, catalog_sha256 TEXT NOT NULL)',
            "CREATE TRIGGER gateway_events_no_update BEFORE UPDATE ON gateway_assignment_events "
            "BEGIN SELECT RAISE(ABORT, 'append-only routing evidence'); END",
            "CREATE TRIGGER gateway_events_no_delete BEFORE DELETE ON gateway_assignment_events "
            "BEGIN SELECT RAISE(ABORT, 'append-only routing evidence'); END",
        )
        for statement in statements:
            database.execute(statement)
        route = policy.routes[policy.value['legacy']]
        database.execute('INSERT INTO gateway_assignments SELECT device, ?, ?, ? FROM devices',
                         (policy.value['legacy'], route['node'], route['sequence']))
        database.execute('INSERT INTO gateway_routing_state VALUES (1, ?, ?)',
                         (policy.sha256, policy.value['generation']))
        database.execute('INSERT INTO gateway_assignment_events VALUES (?, ?, ?, ?, ?)',
                         (operation_id, request_hash, '', policy.value['legacy'], policy.sha256))
        count = database.execute('SELECT COUNT(*) FROM gateway_assignments').fetchone()[0]
    return dict(result='INSTALLED', policy_sha256=policy.sha256, preserved_devices=count)


def replace_policy(access, previous, replacement, *, operation_id=None):
    """Retain every served catalog; a policy change never implicitly moves devices."""
    require(replacement.value['generation'] > previous.value['generation'])
    require(previous.value['legacy'] == replacement.value['legacy'])
    require(set(previous.catalogs) <= set(replacement.catalogs))
    require(all(previous.routes[key] == replacement.routes[key] for key in previous.routes))
    operation_id = operation(operation_id or 'policy-'+replacement.sha256)
    request_hash = digest(canonical(dict(action='replace-policy', previous=previous.sha256, policy=replacement.sha256)))
    with access.db() as database:
        current = state(database)
        require(current is not None and current['policy_sha256'] in (previous.sha256, replacement.sha256))
        expected = previous if current['policy_sha256'] == previous.sha256 else replacement
        require(current['generation'] == expected.value['generation'])
        if replayed(database, operation_id, request_hash):
            return dict(result='UNCHANGED', policy_sha256=replacement.sha256)
        require(current['policy_sha256'] == previous.sha256)
        database.execute('UPDATE gateway_routing_state SET policy_sha256=?, generation=? WHERE singleton=1',
                         (replacement.sha256, replacement.value['generation']))
        database.execute('INSERT INTO gateway_assignment_events VALUES (?, ?, ?, ?, ?)',
                         (operation_id, request_hash, '', previous.sha256, replacement.sha256))
    return dict(result='POLICY_INSTALLED', policy_sha256=replacement.sha256)


def assign(database, policy, device):
    require(type(device) is str and re.fullmatch('[0-9a-f]{32}', device))
    record = database.execute('SELECT d.revoked, i.revoked AS invite_revoked FROM devices d '
                              'JOIN invites i ON i.device=d.device WHERE d.device=?', (device,)).fetchone()
    if record is None or record['revoked'] or record['invite_revoked']:
        raise Rejected()
    assigned = database.execute('SELECT * FROM gateway_assignments WHERE device=?', (device,)).fetchone()
    if assigned is None:
        sha256 = policy.value['admit']
        route = policy.routes[sha256]
        database.execute('INSERT INTO gateway_assignments VALUES (?, ?, ?, ?)',
                         (device, sha256, route['node'], route['sequence']))
    else:
        sha256 = assigned['catalog_sha256']
        require(sha256 in policy.routes)
        route = policy.routes[sha256]
        require(assigned['node'] == route['node'] and assigned['sequence'] == route['sequence'])
    return sha256


def configuration(access, root, country, device):
    require(country in ('ru', 'nl'))
    with access.db() as database:
        current = state(database)
        if current is None:
            return None
        policy = Policy.load(Path(root) / 'gateway-routing', current['policy_sha256'])
        require(current['generation'] == policy.value['generation'])
        sha256 = assign(database, policy, device)
        envelope = policy.catalogs[sha256]
        payload = parse(base64.b64decode(envelope['payload'], validate=True).decode())
        gateway = next(item for item in payload['gateways'] if item['country'] == country)
        return envelope, address(gateway['tcp']['server'])


def move(access, policy, *, device, expected, destination, operation_id):
    """Explicit forward-only reassignment, including rollback via a newer signed catalog."""
    operation(operation_id)
    require(expected in policy.routes and destination in policy.routes)
    require(policy.routes[destination]['sequence'] > policy.routes[expected]['sequence'])
    request_hash = digest(canonical(dict(action='assign', device=device, expected=expected, destination=destination,
                                        policy=policy.sha256, operation_id=operation_id)))
    with access.db() as database:
        current = state(database)
        require(current is not None and current['policy_sha256'] == policy.sha256
                and current['generation'] == policy.value['generation'])
        if replayed(database, operation_id, request_hash):
            return dict(result='UNCHANGED', operation_id=operation_id)
        require(assign(database, policy, device) == expected)
        route = policy.routes[destination]
        database.execute('UPDATE gateway_assignments SET catalog_sha256=?, node=?, sequence=? WHERE device=?',
                         (destination, route['node'], route['sequence'], device))
        database.execute('INSERT INTO gateway_assignment_events VALUES (?, ?, ?, ?, ?)',
                         (operation_id, request_hash, device, expected, destination))
    return dict(result='ASSIGNED', operation_id=operation_id)


def administer(access, root, request):
    """Local operator entry; HTTP has no route to this function and receives no request file."""
    require(type(request) is dict and type(request.get('schema')) is int and request['schema'] == 1)
    action = request.get('action')
    common = {'schema', 'action', 'operation_id', 'policy_sha256'}
    fields = {'install': common | {'legacy_sha256'},
              'replace-policy': common | {'previous_policy_sha256'},
              'assign': common | {'device', 'expected', 'destination'},
              'status': {'schema', 'action'}}
    require(type(action) is str and action in fields and set(request) == fields[action])
    root = Path(root)
    if action == 'status':
        with access.db() as database:
            current = state(database)
            if current is None:
                return dict(result='LEGACY_SINGLE_NL', mutations=0)
            policy = Policy.load(root / 'gateway-routing', current['policy_sha256'])
            require(current['generation'] == policy.value['generation'])
            counts = {row['node']: row['total'] for row in database.execute(
                'SELECT node, COUNT(*) AS total FROM gateway_assignments GROUP BY node')}
            require(set(counts) <= {route['node'] for route in policy.routes.values()})
            return dict(result='ROUTING_CONFIGURED', policy_sha256=policy.sha256, assigned_counts=counts,
                        mutations=0, dataplane_acceptance='NOT_CHECKED', restricted_routing='UNCHANGED')
    operation_id = operation(request['operation_id'])
    policy = Policy.load(root / 'gateway-routing', request['policy_sha256'])
    if action == 'install':
        legacy = private_read(root, 'catalog.json', 16384)
        require(digest(legacy) == request['legacy_sha256'])
        result = install(access, policy, legacy, operation_id=operation_id)
    elif action == 'replace-policy':
        previous = Policy.load(root / 'gateway-routing', request['previous_policy_sha256'])
        result = replace_policy(access, previous, policy, operation_id=operation_id)
    else:
        result = move(access, policy, device=request['device'], expected=request['expected'],
                      destination=request['destination'], operation_id=operation_id)
    return dict(result, operation_id=operation_id, dataplane_acceptance='NOT_CHECKED', restricted_routing='UNCHANGED')
