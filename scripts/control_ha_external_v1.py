"""Pinned read-only external-role checks; maintenance/receiver authority still pending."""
import base64
from contextlib import closing
from dataclasses import replace
import ipaddress
import re
import sqlite3

from control.friends import gateway_routing, pseudonyms, restricted, transport_policy
from provisioning.friends_catalog import verify_catalog
from scripts.control_ha_import import TABLES, ImportRejected, digest, require
from scripts.control_ha_recovery_bundle import RecoveryInputs, parse, preflight_bundle

ADAPTER = 'family-connect/external-roles/v1/not-for-activation'
QUALIFIED_ROLES = frozenset(('aliases', 'admission', 'sender_policy', 'routing_files', 'node_allocations'))
REMAINING_ROLES = frozenset(('maintenance_state', 'receiver_state'))
PEER_SCHEMA = [
    ('index', 'sqlite_autoindex_peers_1', 'peers', None),
    ('table', 'peers', 'peers', 'CREATE TABLE peers (id INTEGER PRIMARY KEY AUTOINCREMENT, public TEXT UNIQUE NOT NULL)'),
    ('table', 'sqlite_sequence', 'sqlite_sequence', 'CREATE TABLE sqlite_sequence(name,seq)'),
]


class RoleRecoveryInputs(RecoveryInputs):
    def summary(self):
        value = super().summary()
        value.update(result='ISOLATED_EXTERNAL_ROLE_PREFLIGHT_PASS', external_adapter=ADAPTER,
                     exact_bytes_only=sorted(REMAINING_ROLES), allocator_nodes=len(transport_policy.NODES))
        value['semantic_checks'] += sorted(QUALIFIED_ROLES)
        return value


def records(snapshot):
    return {table.name: [dict(zip(table.columns, row, strict=True)) for row in rows]
            for table, rows in zip(TABLES, snapshot.rows, strict=True)}


def alias_check(parts, rows):
    require(set(parts) == {'manifest', 'current-hmac'}, 'EXTERNAL_ALIAS_PARTS')
    aliases = pseudonyms.Aliases(parse(parts['manifest']))
    aliases.check_key(parts['current-hmac'])
    canonical = dict(device=[row['device'] for row in rows['devices']],
                     panel_event=[row['event_id'] for row in rows['paid_beta_events']])
    for domain, values in canonical.items():
        for value in values:
            aliases.resolve(domain, pseudonyms.pseudonym(parts['current-hmac'], domain, value), current=True)


def admission_check(parts, rows, trust, now):
    require(set(parts) == {'field.json'}, 'EXTERNAL_ADMISSION_PARTS')
    value = parse(parts['field.json'])
    require(type(value) is dict and set(value) == {'devices'} and type(value['devices']) is list and
            len(value['devices']) <= 3, 'EXTERNAL_ADMISSION_FORMAT')
    require(all(type(device) is str and re.fullmatch('[0-9a-f]{32}', device) for device in value['devices']) and
            len(set(value['devices'])) == len(value['devices']), 'EXTERNAL_ADMISSION_FORMAT')
    active = {row['device'] for row in rows['devices'] if not row['revoked']}
    invited = {row['device'] for row in rows['invites'] if row['device'] and not row['revoked']}
    grants = {row['device']: row for row in rows['restricted_grants']}
    for device in value['devices']:
        require(device in active & invited and device in grants, 'EXTERNAL_ADMISSION_IDENTITY')
        grant = grants[device]
        require(not grant['revoked'] and grant['family'] == trust['family'] and
                grant['revision'] >= trust['minimum_revision'] and
                (grant['expires'] is None or grant['expires'] > now), 'EXTERNAL_ADMISSION_GRANT')


def sender_check(parts, rows):
    require(set(parts) == {'support.json'}, 'EXTERNAL_SENDER_PARTS')
    value = parse(parts['support.json'])
    require(type(value) is dict and set(value) == {'schema', 'sender_public', 'revision', 'enabled'} and
            type(value['schema']) is int and value['schema'] == 2 and type(value['enabled']) is bool and
            type(value['revision']) is int and 1 <= value['revision'] < 2**53 and
            type(value['sender_public']) is str and re.fullmatch('[0-9a-f]{128}', value['sender_public']),
            'EXTERNAL_SENDER_FORMAT')
    require(any(row['public'] == value['sender_public'] and row['enabled'] == 1 for row in rows['chat_service_senders']),
            'EXTERNAL_SENDER_UNREGISTERED')
    require(all(row['support_sender'] in (None, value['sender_public']) for row in rows['chat_bindings']),
            'EXTERNAL_SENDER_BINDING')


def selection_check(raw, anchor, policy):
    envelope = parse(raw)
    verified = verify_catalog(envelope, anchor, schema=3)
    payload = parse(base64.b64decode(envelope['payload'], validate=True))
    for gateway in payload['gateways']:
        choices = [sha for sha, route in policy.routes.items() if route['node'] == gateway['gateway_id']]
        require(bool(choices), 'EXTERNAL_SELECTION_NODE')
        newest = max(choices, key=lambda sha: policy.routes[sha]['sequence'])
        template = parse(base64.b64decode(policy.catalogs[newest]['payload'], validate=True))
        expected = next(item for item in template['gateways'] if item['country'] == 'nl')
        require({name: value for name, value in gateway.items() if name != 'gateway_id'} == expected,
                'EXTERNAL_SELECTION_TEMPLATE')
    return verified


def routing_check(parts, rows):
    require('anchor.pub' in parts, 'EXTERNAL_ROUTING_ANCHOR')
    anchor = base64.b64decode(parts['anchor.pub'].strip(), validate=True)
    require(len(anchor) == 32, 'EXTERNAL_ROUTING_ANCHOR')
    files = {kind: {} for kind in ('policy', 'catalog', 'selection')}
    for name, raw in parts.items():
        if name == 'anchor.pub':
            continue
        match = re.fullmatch(r'([0-9a-f]{64})\.(policy|catalog|selection)\.json', name)
        require(match is not None and digest(raw) == match[1] and len(raw) <= 16384, 'EXTERNAL_ROUTING_FILE')
        files[match[2]][match[1]] = raw
    for raw in files['catalog'].values():
        verify_catalog(parse(raw), anchor)
    for raw in files['selection'].values():
        verify_catalog(parse(raw), anchor, schema=3)
    policies = {sha: gateway_routing.Policy(raw, anchor, files['catalog']) for sha, raw in files['policy'].items()}
    require(len(rows['gateway_routing_state']) == 1, 'EXTERNAL_ROUTING_STATE')
    state = rows['gateway_routing_state'][0]
    current = policies[state['policy_sha256']]
    require(current.value['generation'] == state['generation'], 'EXTERNAL_ROUTING_GENERATION')
    for row in rows['gateway_assignments']:
        route = current.routes[row['catalog_sha256']]
        require(row['node'] == route['node'] and row['sequence'] == route['sequence'], 'EXTERNAL_ROUTING_ASSIGNMENT')
    for row in rows['gateway_assignment_events']:
        if row['device'] == '':
            target = policies[row['catalog_sha256']]
            require(row['previous_sha256'] == target.value['legacy'] or row['previous_sha256'] in policies,
                    'EXTERNAL_ROUTING_POLICY_HISTORY')
        else:
            require(row['catalog_sha256'] in files['catalog'] and row['previous_sha256'] in files['catalog'],
                    'EXTERNAL_ROUTING_HISTORY')
    for row in rows['gateway_selection_events']:
        selected = selection_check(files['selection'][row['catalog_sha256']], anchor, policies[row['policy_sha256']])
        require(selected.sequence == row['sequence'], 'EXTERNAL_SELECTION_SEQUENCE')
    require(bool(rows['gateway_selection_events']), 'EXTERNAL_SELECTION_REQUIRED')
    latest = max(rows['gateway_selection_events'], key=lambda row: row['sequence'])
    require(latest['policy_sha256'] == state['policy_sha256'], 'EXTERNAL_SELECTION_POLICY')
    hosts = {route['node']: route['host'] for route in current.routes.values()}
    payload = parse(base64.b64decode(current.catalogs[current.value['legacy']]['payload'], validate=True))
    hosts['gateway-ru'] = next(item['tcp']['server'] for item in payload['gateways'] if item['country'] == 'ru')
    return hosts


def allocation_image(raw, network, known):
    require(type(raw) is bytes and 0 < len(raw) <= 1024 * 1024, 'EXTERNAL_ALLOCATOR_BOUNDS')
    with closing(sqlite3.connect(':memory:')) as database:
        database.deserialize(raw)
        database.execute('PRAGMA trusted_schema=OFF')
        database.execute('PRAGMA query_only=ON')
        database.set_progress_handler(lambda: 1, 2000000)
        require(database.execute('PRAGMA quick_check').fetchall() == [('ok',)] and
                database.execute('SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name').fetchall()
                == PEER_SCHEMA, 'EXTERNAL_ALLOCATOR_SCHEMA')
        require(database.execute('PRAGMA user_version').fetchone() == (0,) and
                database.execute('PRAGMA application_id').fetchone() == (0,) and
                database.execute('PRAGMA encoding').fetchone() == ('UTF-8',), 'EXTERNAL_ALLOCATOR_VERSION')
        peers = database.execute('SELECT id,public FROM peers ORDER BY id LIMIT 20001').fetchall()
        require(0 < len(peers) <= 20000 and all(type(index) is int and 1 <= index < network.num_addresses - 2 and
                type(public) is str and public in known for index, public in peers), 'EXTERNAL_ALLOCATOR_BINDING')
        sequences = database.execute('SELECT name,seq FROM sqlite_sequence').fetchall()
        require(len(sequences) == 1 and sequences[0][0] == 'peers' and type(sequences[0][1]) is int and
                max(index for index, public in peers) <= sequences[0][1] < network.num_addresses - 2,
                'EXTERNAL_ALLOCATOR_FLOOR')
        return dict(peers=tuple(peers), floor=sequences[0][1])


def allocation_check(parts, rows, hosts):
    require(set(parts) == {node + suffix for node in transport_policy.NODES for suffix in ('.sqlite', '.json')},
            'EXTERNAL_ALLOCATOR_NODE_COVERAGE')
    result = {}
    for node in transport_policy.NODES:
        settings = parse(parts[node + '.json'])
        require(type(settings) is dict and set(settings) == {'network', 'address', 'external'} and
                all(type(value) is str for value in settings.values()), 'EXTERNAL_ALLOCATOR_SETTINGS')
        network = ipaddress.IPv4Network(settings['network'])
        expected = '10.84.0.0/16' if node == 'gateway-ru' else '10.83.0.0/16'
        require(str(network) == expected and settings['address'] == str(network[1]) + '/16' and
                settings['external'] == hosts[node], 'EXTERNAL_ALLOCATOR_NODE_BINDING')
        result[node] = allocation_image(parts[node + '.sqlite'], network, {row['wg'] for row in rows['devices']})
    return result


def preflight_external(bundle, key, expected, anchor, *, now):
    recovered = preflight_bundle(bundle, key, expected, anchor, now=now)
    rows, artifacts = records(recovered.snapshot), recovered.artifacts
    try:
        trust, authority = restricted.delegation(parse(recovered.bootstrap)['manifest'], anchor, now)
        alias_check(artifacts['aliases'], rows)
        admission_check(artifacts['admission'], rows, trust, now)
        sender_check(artifacts['sender_policy'], rows)
        hosts = routing_check(artifacts['routing_files'], rows)
        allocation_check(artifacts['node_allocations'], rows, hosts)
    except ImportRejected:
        raise
    except (ValueError, TypeError, KeyError, IndexError, StopIteration, sqlite3.Error, OverflowError, RecursionError):
        raise ImportRejected('EXTERNAL_ROLE_INVALID') from None
    snapshot = replace(recovered.snapshot, external_digests=recovered.snapshot.external_digests +
                       (('external-adapter', digest(ADAPTER.encode())),))
    return RoleRecoveryInputs(snapshot, recovered.stores, recovered.references, artifacts, recovered.bootstrap)
