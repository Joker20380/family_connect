"""Real application file formats in an owned fixture; never a live capture tool."""
from contextlib import closing, redirect_stdout
import importlib.util
import io
import ipaddress
from pathlib import Path
import secrets
from types import SimpleNamespace

from control.friends import pseudonyms, support, support_admin, transport_policy
from device_identity.device import DeviceIdentity
from scripts.control_ha_bundle_fixture import artifacts_for
from scripts.control_ha_external_v1 import records, routing_check, allocation_check
from scripts.control_ha_import import encoded
from scripts.control_ha_import_fixture import CHECKPOINT
from scripts.control_ha_recovery_bundle import parse
from scripts.control_ha_rehearsal import private_file, require
from scripts.control_ha_sqlite_fixture import image
from scripts.control_ha_sqlite_import import preflight_sqlite
from scripts.referral_postgres_rehearsal import NOW


def offline_gateway(root):
    path = Path(__file__).resolve().parents[1] / 'deploy/friends/awg-gateway.py'
    spec = importlib.util.spec_from_file_location('ha_external_fixture_gateway', path)
    gateway = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gateway)
    gateway.ROOT = root
    gateway.paid_engine = lambda: None
    gateway.add_peer = lambda *args: None
    gateway.tcp_user = lambda *args: None
    def forbidden(*args, **kwargs):
        raise RuntimeError('EXTERNAL_FIXTURE_MUST_NOT_EXECUTE_GATEWAY_COMMANDS')
    gateway.command = forbidden
    gateway.subprocess = SimpleNamespace(run=forbidden, Popen=forbidden)
    return gateway


def register(gateway, record):
    request = dict(public_key=record['wg'], device=record['device'], tcp_id=record['tcp'])
    gateway.sys = SimpleNamespace(stdin=SimpleNamespace(buffer=io.BytesIO(encoded(request))), modules={})
    output = io.StringIO()
    with redirect_stdout(output):
        gateway.register()
    return parse(output.getvalue())['address']


def newcomer():
    device = DeviceIdentity.generate()
    return dict(device=device.reference, wg=device.wireguard_public_key, tcp='00000000-0000-4000-8000-000000000001')


def artifacts_for_external(fixture):
    artifacts = artifacts_for(fixture)
    frozen = preflight_sqlite(fixture.stores, fixture.external, fixture.expected, CHECKPOINT,
                             fixture.bootstrap, fixture.service.anchor, now=NOW)
    rows = records(frozen)
    current_key = secrets.token_bytes(32)
    aliases = pseudonyms.prepare(dict(device=[row['device'] for row in rows['devices']],
        panel_event=[row['event_id'] for row in rows['paid_beta_events']]), current_key, legacy_key=secrets.token_bytes(32))
    root = fixture.paths['registry'].parent
    pseudonyms.save(root / 'aliases.json', aliases)
    artifacts['aliases'] = {'manifest': (root / 'aliases.json').read_bytes(), 'current-hmac': current_key}
    private_file(root / 'field.json', encoded(dict(devices=[])))
    support_admin.write_admission(root / 'field.json', [], [fixture.device.reference])
    artifacts['admission'] = {'field.json': (root / 'field.json').read_bytes()}
    artifacts['node_allocations'] = {}
    hosts = routing_check(artifacts['routing_files'], rows)
    for offset, node in enumerate(transport_policy.NODES):
        node_root = root / node
        node_root.mkdir(mode=0o700)
        network = ipaddress.IPv4Network('10.84.0.0/16' if node == 'gateway-ru' else '10.83.0.0/16')
        settings = encoded(dict(network=str(network), address=str(network[1]) + '/16', external=hosts[node]))
        private_file(node_root / 'settings.json', settings)
        gateway = offline_gateway(node_root)
        devices = rows['devices'][offset:] + rows['devices'][:offset]
        for record in devices:
            register(gateway, record)
        removed = newcomer()
        register(gateway, removed)
        with closing(gateway.database()) as database:
            with database:
                database.execute('DELETE FROM peers WHERE public=?', (removed['wg'],))
        artifacts['node_allocations'][node + '.sqlite'] = image(node_root / 'peers.db')
        artifacts['node_allocations'][node + '.json'] = settings
    return artifacts


def exercise_external_files(fixture, recovered, root):
    rows = records(recovered.snapshot)
    artifacts = recovered.artifacts
    private_file(root / 'aliases.json', artifacts['aliases']['manifest'])
    aliases = pseudonyms.load(root / 'aliases.json')
    current_key = artifacts['aliases']['current-hmac']
    aliases.check_key(current_key)
    extended = pseudonyms.prepare(dict(device=[DeviceIdentity.generate().reference], panel_event=[]),
                                 current_key, existing=aliases, generation=aliases.generation)
    for domain in pseudonyms.DOMAINS:
        require(extended.document['entities'][domain][:len(aliases.document['entities'][domain])] ==
                aliases.document['entities'][domain], 'EXTERNAL_ALIAS_HISTORY_CHANGED')
    private_file(root / 'field.json', artifacts['admission']['field.json'])
    require(support_admin.admission(root / 'field.json') == [fixture.device.reference], 'EXTERNAL_ADMISSION_CHANGED')
    policy = support.load(root / 'support.json')
    with fixture.access.read_enrollment() as enrollment:
        support.sender(enrollment.chat(), policy)
    hosts = routing_check(artifacts['routing_files'], rows)
    allocations = allocation_check(artifacts['node_allocations'], rows, hosts)
    devices = {row['wg']: row for row in rows['devices']}
    for node, state in allocations.items():
        node_root = root / node
        node_root.mkdir(mode=0o700)
        private_file(node_root / 'peers.db', artifacts['node_allocations'][node + '.sqlite'])
        private_file(node_root / 'settings.json', artifacts['node_allocations'][node + '.json'])
        gateway = offline_gateway(node_root)
        network = ipaddress.IPv4Network(parse(artifacts['node_allocations'][node + '.json'])['network'])
        for index, public in reversed(state['peers']):
            require(register(gateway, devices[public]) == str(network[index + 1]) + '/32', 'EXTERNAL_ALLOCATOR_REPLAY')
        require(register(gateway, newcomer()) == str(network[state['floor'] + 2]) + '/32', 'EXTERNAL_ALLOCATOR_REUSED_ID')
    return dict(alias_history=True, admission=True, registered_sender=True, allocator_nodes=len(allocations),
                reverse_registration_replay=True, deleted_highest_id_not_reused=True)
