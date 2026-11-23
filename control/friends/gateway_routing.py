"""Sticky physical NL assignment using unchanged, offline-signed schema2 catalogs."""

import base64
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import stat

from .access import Rejected, SQLiteEnrollment
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


class RoutingTransaction:
    def __init__(self, enrollment):
        self.enrollment = enrollment
        self.database = enrollment.database
        self.placeholder = enrollment.placeholder

    def exists(self, table):
        return self.database.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                                     (table,)).fetchone() is not None

    def state(self):
        if not self.exists('gateway_routing_state'):
            return None
        rows = self.database.execute('SELECT * FROM gateway_routing_state').fetchall()
        require(len(rows) == 1 and rows[0]['singleton'] == 1)
        return rows[0]

    def initialize_routing(self):
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
            self.database.execute(statement)

    def initialize_selection(self):
        self.database.execute('CREATE TABLE gateway_selection_events ('
            'operation_id TEXT PRIMARY KEY, request_sha256 TEXT NOT NULL, '
            'catalog_sha256 TEXT NOT NULL, policy_sha256 TEXT NOT NULL, sequence INTEGER NOT NULL UNIQUE)')
        for action in ('UPDATE', 'DELETE'):
            self.database.execute(f'CREATE TRIGGER gateway_selection_no_{action.lower()} '
                f'BEFORE {action} ON gateway_selection_events BEGIN '
                "SELECT RAISE(ABORT, 'append-only'); END")

    def replayed(self, operation_id, request_hash, *, selection=False):
        table = 'gateway_selection_events' if selection else 'gateway_assignment_events'
        record = self.database.execute('SELECT request_sha256 FROM ' + table + ' WHERE operation_id=' +
            self.placeholder, (operation_id,)).fetchone()
        if record is not None:
            require(record['request_sha256'] == request_hash)
        return record is not None

    def seed(self, sha256, route):
        self.database.execute('INSERT INTO gateway_assignments SELECT device,' +
            ','.join([self.placeholder] * 3) + ' FROM devices', (sha256, route['node'], route['sequence']))
        return self.database.execute('SELECT COUNT(*) AS total FROM gateway_assignments').fetchone()['total']

    def set_state(self, policy, *, initial=False):
        query = ('INSERT INTO gateway_routing_state VALUES (1,' + ','.join([self.placeholder] * 2) + ')'
                 if initial else 'UPDATE gateway_routing_state SET policy_sha256=' + self.placeholder +
                 ', generation=' + self.placeholder + ' WHERE singleton=1')
        self.database.execute(query, (policy.sha256, policy.value['generation']))

    def event(self, operation_id, request_hash, device, previous, destination):
        self.database.execute('INSERT INTO gateway_assignment_events VALUES (' +
            ','.join([self.placeholder] * 5) + ')', (operation_id, request_hash, device, previous, destination))

    def active(self, device):
        record = self.database.execute('SELECT d.revoked, i.revoked AS invite_revoked FROM devices d '
            'JOIN invites i ON i.device=d.device WHERE d.device=' + self.placeholder, (device,)).fetchone()
        if record is None or record['revoked'] or record['invite_revoked']:
            raise Rejected()

    def assignment(self, device):
        return self.database.execute('SELECT * FROM gateway_assignments WHERE device=' +
            self.placeholder, (device,)).fetchone()

    def set_assignment(self, device, sha256, route, *, initial=False):
        if initial:
            self.database.execute('INSERT INTO gateway_assignments VALUES (' +
                ','.join([self.placeholder] * 4) + ')', (device, sha256, route['node'], route['sequence']))
        else:
            self.database.execute('UPDATE gateway_assignments SET catalog_sha256=' + self.placeholder +
                ', node=' + self.placeholder + ', sequence=' + self.placeholder + ' WHERE device=' + self.placeholder,
                (sha256, route['node'], route['sequence'], device))

    def counts(self):
        return {row['node']: row['total'] for row in self.database.execute(
            'SELECT node, COUNT(*) AS total FROM gateway_assignments GROUP BY node')}

    def selection(self):
        if not self.exists('gateway_selection_events'):
            return None
        return self.database.execute('SELECT * FROM gateway_selection_events ORDER BY sequence DESC LIMIT 1').fetchone()

    def selection_event(self, operation_id, request_hash, catalog, policy, sequence):
        self.database.execute('INSERT INTO gateway_selection_events VALUES (' +
            ','.join([self.placeholder] * 5) + ')', (operation_id, request_hash, catalog, policy, sequence))


def routing_transaction(database):
    return database if isinstance(database, RoutingTransaction) else SQLiteEnrollment(database).routing()


def state(database):
    return routing_transaction(database).state()


def operation(value):
    require(type(value) is str and re.fullmatch('[a-zA-Z0-9][a-zA-Z0-9_-]{7,95}', value))
    return value


def replayed(database, operation_id, request_hash):
    return routing_transaction(database).replayed(operation_id, request_hash)


def install(access, policy, legacy_raw, *, operation_id=None):
    """Offline operator transaction; seeds existing devices without moving any of them."""
    require(digest(legacy_raw) == policy.value['legacy'])
    operation_id = operation(operation_id or 'install-'+policy.sha256)
    request_hash = digest(canonical(dict(action='install', policy=policy.sha256)))
    with access.enrollment() as enrollment:
        database = enrollment.routing()
        current = state(database)
        if current is not None:
            require(current['policy_sha256'] == policy.sha256 and current['generation'] == policy.value['generation'])
            require(replayed(database, operation_id, request_hash))
            return dict(result='UNCHANGED', policy_sha256=policy.sha256)
        database.initialize_routing()
        route = policy.routes[policy.value['legacy']]
        count = database.seed(policy.value['legacy'], route)
        database.set_state(policy, initial=True)
        database.event(operation_id, request_hash, '', policy.value['legacy'], policy.sha256)
    return dict(result='INSTALLED', policy_sha256=policy.sha256, preserved_devices=count)


def replace_policy(access, previous, replacement, *, operation_id=None):
    """Retain every served catalog; a policy change never implicitly moves devices."""
    require(replacement.value['generation'] > previous.value['generation'])
    require(previous.value['legacy'] == replacement.value['legacy'])
    require(set(previous.catalogs) <= set(replacement.catalogs))
    require(all(previous.routes[key] == replacement.routes[key] for key in previous.routes))
    operation_id = operation(operation_id or 'policy-'+replacement.sha256)
    request_hash = digest(canonical(dict(action='replace-policy', previous=previous.sha256, policy=replacement.sha256)))
    with access.enrollment() as enrollment:
        database = enrollment.routing()
        current = state(database)
        require(current is not None and current['policy_sha256'] in (previous.sha256, replacement.sha256))
        expected = previous if current['policy_sha256'] == previous.sha256 else replacement
        require(current['generation'] == expected.value['generation'])
        if replayed(database, operation_id, request_hash):
            return dict(result='UNCHANGED', policy_sha256=replacement.sha256)
        require(current['policy_sha256'] == previous.sha256)
        database.set_state(replacement)
        database.event(operation_id, request_hash, '', previous.sha256, replacement.sha256)
    return dict(result='POLICY_INSTALLED', policy_sha256=replacement.sha256)


def assign(database, policy, device):
    database = routing_transaction(database)
    require(type(device) is str and re.fullmatch('[0-9a-f]{32}', device))
    database.active(device)
    assigned = database.assignment(device)
    if assigned is None:
        sha256 = policy.value['admit']
        route = policy.routes[sha256]
        database.set_assignment(device, sha256, route, initial=True)
    else:
        sha256 = assigned['catalog_sha256']
        require(sha256 in policy.routes)
        route = policy.routes[sha256]
        require(assigned['node'] == route['node'] and assigned['sequence'] == route['sequence'])
    return sha256


def configuration(access, root, country, device):
    require(country in ('ru', 'nl'))
    with access.enrollment() as enrollment:
        database = enrollment.routing()
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
    with access.enrollment() as enrollment:
        database = enrollment.routing()
        current = state(database)
        require(current is not None and current['policy_sha256'] == policy.sha256
                and current['generation'] == policy.value['generation'])
        if replayed(database, operation_id, request_hash):
            return dict(result='UNCHANGED', operation_id=operation_id)
        require(assign(database, policy, device) == expected)
        route = policy.routes[destination]
        database.set_assignment(device, destination, route)
        database.event(operation_id, request_hash, device, expected, destination)
    return dict(result='ASSIGNED', operation_id=operation_id)


def administer(access, root, request):
    """Local operator entry; HTTP has no route to this function and receives no request file."""
    require(type(request) is dict and type(request.get('schema')) is int and request['schema'] == 1)
    action = request.get('action')
    if action == 'install-selection':
        from .gateway_selection import install as install_selection
        return install_selection(access, root, request)
    common = {'schema', 'action', 'operation_id', 'policy_sha256'}
    fields = {'install': common | {'legacy_sha256'},
              'replace-policy': common | {'previous_policy_sha256'},
              'assign': common | {'device', 'expected', 'destination'},
              'status': {'schema', 'action'}}
    require(type(action) is str and action in fields and set(request) == fields[action])
    root = Path(root)
    if action == 'status':
        with access.read_enrollment() as enrollment:
            database = enrollment.routing()
            current = state(database)
            if current is None:
                return dict(result='LEGACY_SINGLE_NL', mutations=0)
            policy = Policy.load(root / 'gateway-routing', current['policy_sha256'])
            require(current['generation'] == policy.value['generation'])
            counts = database.counts()
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
