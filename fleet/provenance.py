"""Fail-closed role admission; observed hashes are not deployment authority."""

from pathlib import Path
import re

from .contracts import canonical, digest, exact, fail, typed
from .bundle import safe_path, source_bytes

FIELDS = ('id', 'path', 'sha256', 'size', 'source_commit', 'source_inventory_sha256',
          'receipt', 'license', 'source_reference', 'architecture', 'runtime', 'roles',
          'argv', 'unit', 'user', 'group', 'capabilities', 'listeners', 'state', 'secret_slots', 'health')


def validate(inventory):
    exact(inventory, ('schema', 'scope', 'artifacts', 'disabled_roles'))
    if type(inventory['schema']) is not int or (inventory['schema'],inventory['scope']) not in (
            (1,'BOUND_REHEARSAL_INPUTS'),(2,'DEPLOYABLE_REHEARSAL')):
        fail('UNBOUND_ROLE_ARTIFACT')
    if type(inventory['artifacts']) is not list or not inventory['artifacts']:
        fail('UNBOUND_ROLE_ARTIFACT')
    identifiers = set()
    paths = set()
    for artifact in inventory['artifacts']:
        exact(artifact, FIELDS)
        if (not typed(artifact['id'], 'id') or artifact['id'] in identifiers
                or not typed(artifact['sha256'], 'hash') or not typed(artifact['source_commit'], 'commit')
                or not typed(artifact['source_inventory_sha256'], 'hash')
                or type(artifact['size']) is not int or not 0 < artifact['size'] <= 64*1024*1024
                or artifact['architecture'] != 'x86_64' or not typed(artifact['roles'], 'roles')
                or not artifact['roles'] or not typed(artifact['secret_slots'], 'ids')
                or artifact['path'] in paths):
            fail('UNBOUND_ROLE_ARTIFACT')
        safe_path(artifact['path'])
        safe_path(artifact['receipt'])
        for field in ('license', 'source_reference', 'runtime', 'unit', 'user', 'group', 'health'):
            if type(artifact[field]) is not str or not 1 <= len(artifact[field]) <= 512 or '\n' in artifact[field]:
                fail('UNBOUND_ROLE_ARTIFACT')
        for field in ('argv', 'capabilities', 'listeners', 'state'):
            if (type(artifact[field]) is not list or len(artifact[field]) > 32
                    or any(type(value) is not str or not 1 <= len(value) <= 256 or '\n' in value for value in artifact[field])):
                fail('UNBOUND_ROLE_ARTIFACT')
        if not artifact['argv']:
            fail('UNBOUND_ROLE_ARTIFACT')
        if (not re.fullmatch(r'fc-rehearsal-[a-z-]+\.service', artifact['unit'])
                or not all(typed(artifact[name], 'id') for name in ('user','group'))
                or any(not re.fullmatch(r'[A-Za-z0-9_./:=+-]+', argument) for argument in artifact['argv'])
                or any(not value.startswith('STATE/') for value in artifact['state'])
                or not artifact['health'].startswith('REHEARSAL_HEALTH/')):
            fail('UNBOUND_ROLE_ARTIFACT')
        identifiers.add(artifact['id'])
        paths.add(artifact['path'])
    if type(inventory['disabled_roles']) is not dict or any(not typed(name, 'id') or type(reason) is not str
                                                         for name, reason in inventory['disabled_roles'].items()):
        fail('UNBOUND_ROLE_ARTIFACT')
    if inventory['schema']==2:
        from .role_config import DISABLED, ROLES
        admitted={role for artifact in inventory['artifacts'] for role in artifact['roles']}
        if (admitted!=set(ROLES) or set(inventory['disabled_roles'])!=set(DISABLED)
                or not {'awg-engine','awg-tools','tcp-xray','mesh-gateway','rehearsal-monitoring'}<=identifiers):
            fail('deployable_role_contract')
    return inventory


def check_inputs(inventory, root, source_inventories):
    validate(inventory)
    results = {}
    for artifact in inventory['artifacts']:
        content = source_bytes(Path(root).resolve(), artifact['path'], 64*1024*1024)
        if len(content) != artifact['size'] or digest(content) != artifact['sha256']:
            fail('UNBOUND_ROLE_ARTIFACT')
        source = source_inventories.get(artifact['id'])
        if source is None or digest(canonical(source)) != artifact['source_inventory_sha256']:
            fail('UNBOUND_ROLE_ARTIFACT')
        results[artifact['id']] = artifact['sha256']
    return results
