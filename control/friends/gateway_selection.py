"""Explicit ordinary-node selection, independent of legacy sticky assignments."""
import base64
from pathlib import Path

from provisioning.friends_catalog import GATEWAY_CHOICES, verify_catalog
from .access import Rejected
from .gateway_routing import Policy, canonical, digest, operation, parse, private_read, require, state


def current(database):
    if database.execute("SELECT 1 FROM sqlite_master WHERE name='gateway_selection_events'").fetchone() is None:
        return None
    return database.execute('SELECT * FROM gateway_selection_events ORDER BY sequence DESC LIMIT 1').fetchone()


def load(root, policy, sha256):
    require(isinstance(sha256, str) and len(sha256) == 64 and all(character in '0123456789abcdef' for character in sha256))
    raw = private_read(Path(root) / 'gateway-routing', sha256 + '.selection.json', 16384)
    require(digest(raw) == sha256)
    anchor = base64.b64decode(private_read(Path(root) / 'gateway-routing', 'anchor.pub', 128).strip(), validate=True)
    envelope = parse(raw.decode())
    verified = verify_catalog(envelope, anchor, schema=3)
    payload = parse(base64.b64decode(envelope['payload'], validate=True).decode())
    for gateway in payload['gateways']:
        candidates = [sha for sha, route in policy.routes.items() if route['node'] == gateway['gateway_id']]
        require(bool(candidates))
        newest = max(candidates, key=lambda sha: policy.routes[sha]['sequence'])
        bound = parse(base64.b64decode(policy.catalogs[newest]['payload'], validate=True).decode())
        template = next(item for item in bound['gateways'] if item['country'] == 'nl')
        require({key: value for key, value in gateway.items() if key != 'gateway_id'} == template)
    return envelope, payload, verified


def install(access, root, request):
    require(set(request) == {'schema', 'action', 'operation_id', 'policy_sha256', 'catalog_sha256', 'previous_sha256'})
    operation_id = operation(request['operation_id'])
    policy = Policy.load(Path(root) / 'gateway-routing', request['policy_sha256'])
    _envelope, _payload, verified = load(root, policy, request['catalog_sha256'])
    request_hash = digest(canonical(request))
    with access.db() as database:
        active = state(database)
        require(active is not None and active['policy_sha256'] == policy.sha256)
        previous = current(database)
        if previous is None:
            require(request['previous_sha256'] is None)
            database.execute('CREATE TABLE IF NOT EXISTS gateway_selection_events ('
                             'operation_id TEXT PRIMARY KEY, request_sha256 TEXT NOT NULL, '
                             'catalog_sha256 TEXT NOT NULL, policy_sha256 TEXT NOT NULL, sequence INTEGER NOT NULL UNIQUE)')
            for action in ('UPDATE', 'DELETE'):
                database.execute(f'CREATE TRIGGER IF NOT EXISTS gateway_selection_no_{action.lower()} '
                                 f'BEFORE {action} ON gateway_selection_events BEGIN '
                                 "SELECT RAISE(ABORT, 'append-only'); END")
        replay = database.execute('SELECT request_sha256 FROM gateway_selection_events WHERE operation_id=?', (operation_id,)).fetchone()
        if replay is not None:
            require(replay['request_sha256'] == request_hash)
            return dict(result='UNCHANGED', operation_id=operation_id)
        if previous is not None:
            require(previous['catalog_sha256'] == request['previous_sha256'] and verified.sequence > previous['sequence'])
        database.execute('INSERT INTO gateway_selection_events VALUES (?, ?, ?, ?, ?)',
                         (operation_id, request_hash, request['catalog_sha256'], policy.sha256, verified.sequence))
    return dict(result='SELECTION_CATALOG_INSTALLED', operation_id=operation_id, sequence=verified.sequence,
                catalog_sha256=request['catalog_sha256'], legacy_assignments='UNCHANGED')


def configuration(access, root, gateway_id, device):
    require(gateway_id in GATEWAY_CHOICES)
    with access.db() as database:
        record = database.execute('SELECT d.revoked, i.revoked AS invite_revoked FROM devices d '
                                  'JOIN invites i ON i.device=d.device WHERE d.device=?', (device,)).fetchone()
        if record is None or record['revoked'] or record['invite_revoked']:
            raise Rejected()
        selected, active = current(database), state(database)
        require(selected is not None and active is not None and selected['policy_sha256'] == active['policy_sha256'])
        policy = Policy.load(Path(root) / 'gateway-routing', active['policy_sha256'])
        envelope, payload, verified = load(root, policy, selected['catalog_sha256'])
        require(verified.sequence == selected['sequence'])
        gateway = next(item for item in payload['gateways'] if item['gateway_id'] == gateway_id)
        return envelope, gateway['tcp']['server']
