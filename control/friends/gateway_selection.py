"""Explicit ordinary-node selection, independent of legacy sticky assignments."""
import base64
from pathlib import Path

from provisioning.friends_catalog import GATEWAY_CHOICES, verify_catalog
from .gateway_routing import Policy, canonical, digest, operation, parse, private_read, require, state, routing_transaction


def current(database):
    return routing_transaction(database).selection()


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
    with access.enrollment() as enrollment:
        database = enrollment.routing()
        active = state(database)
        require(active is not None and active['policy_sha256'] == policy.sha256
                and active['generation'] == policy.value['generation'])
        previous = current(database)
        if previous is None:
            require(request['previous_sha256'] is None)
            if not database.exists('gateway_selection_events'):
                database.initialize_selection()
        if database.replayed(operation_id, request_hash, selection=True):
            return dict(result='UNCHANGED', operation_id=operation_id)
        if previous is not None:
            require(previous['catalog_sha256'] == request['previous_sha256'] and verified.sequence > previous['sequence'])
        database.selection_event(operation_id, request_hash, request['catalog_sha256'], policy.sha256, verified.sequence)
    return dict(result='SELECTION_CATALOG_INSTALLED', operation_id=operation_id, sequence=verified.sequence,
                catalog_sha256=request['catalog_sha256'], legacy_assignments='UNCHANGED')


def configuration(access, root, gateway_id, device):
    require(gateway_id in GATEWAY_CHOICES)
    with access.read_enrollment() as enrollment:
        database = enrollment.routing()
        database.active(device)
        selected, active = current(database), state(database)
        require(selected is not None and active is not None and selected['policy_sha256'] == active['policy_sha256'])
        policy = Policy.load(Path(root) / 'gateway-routing', active['policy_sha256'])
        require(active['generation'] == policy.value['generation'])
        envelope, payload, verified = load(root, policy, selected['catalog_sha256'])
        require(verified.sequence == selected['sequence'])
        gateway = next(item for item in payload['gateways'] if item['gateway_id'] == gateway_id)
        return envelope, gateway['tcp']['server']
