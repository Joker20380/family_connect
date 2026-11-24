"""Real receiver file consumers over disposable bytes and simulated engine readback."""
from copy import deepcopy
import importlib.util
import io
import os
from pathlib import Path
import secrets
from types import SimpleNamespace
import uuid

import RNS

from control.friends import transport_policy as policy
from control.friends.chat import ChatAccess
from messenger.membership import Membership, validate as validate_membership
from scripts.control_ha_external_fixture import artifacts_for_external
from scripts.control_ha_external_v1 import records, routing_check
from scripts.control_ha_import import encoded
from scripts.control_ha_import_fixture import CHECKPOINT
from scripts.control_ha_receiver_v1 import CAPTURE_PURPOSE
from scripts.control_ha_recovery_bundle import parse
from scripts.control_ha_rehearsal import private_file, require
from scripts.control_ha_sqlite_fixture import image
from scripts.control_ha_sqlite_import import preflight_sqlite
from scripts.referral_postgres_rehearsal import NOW


def forbidden(*args, **kwargs):
    raise RuntimeError('RECEIVER_FIXTURE_RUNTIME_COMMAND_FORBIDDEN')


def native_gateway(root, point, *, now=NOW):
    path = Path(__file__).resolve().parents[1] / 'control/friends/transport_gateway.py'
    spec = importlib.util.spec_from_file_location('control.friends._ha_receiver_gateway', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.boot_id = lambda: point['boot']
    module.emit = lambda value: None
    engine = module.Gateway(SimpleNamespace(ROOT=root, add_peer=forbidden), clock=lambda: now,
                            monotonic=lambda: point['monotonic'], run=forbidden)
    return engine, module


def artifacts_for_receivers(fixture, *, sqlite_preflight=preflight_sqlite):
    chat = ChatAccess(fixture.access)
    chat.snapshot()
    members = chat.snapshot()
    fixture.stores['registry'] = image(fixture.paths['registry'])
    artifacts = artifacts_for_external(fixture, sqlite_preflight=sqlite_preflight)
    frozen = sqlite_preflight(fixture.stores, fixture.external, fixture.expected, CHECKPOINT,
                              fixture.bootstrap, fixture.service.anchor, now=NOW)
    hosts = routing_check(artifacts['routing_files'], records(frozen))
    parts, points = {}, {}
    for node in policy.NODES:
        root = fixture.paths['registry'].parent / ('receiver-' + node)
        root.mkdir(mode=0o700)
        config = encoded(dict(schema=1, profile=policy.PROFILE, node=node, enabled=True))
        private_file(root / 'transport-enforcement.json', config)
        private_file(root / 'transport-state.json', encoded(dict(schema=1, node=node, records={}, observed_at=0)))
        point = dict(boot=str(uuid.uuid4()), monotonic=1000.0)
        points[node] = point
        engine, module = native_gateway(root, point)
        envelope = policy.snapshot(fixture.paths['registry'], node, clock=lambda: NOW)
        with engine.operation():
            engine.accept(envelope)
            if node != 'nl-amsterdam-2':
                engine.prepare(dict(envelope, decisions=[row for row in envelope['decisions']
                               if row['device'] == fixture.child.reference]), 'a' * 64)
            state = engine.load()
            peers = {cached['decision']['public_key']: '10.83.0.' + str(index + 2) + '/32'
                     for index, cached in enumerate(state['records'].values())}
            allowed = {device: engine.allowed(cached) for device, cached in state['records'].items()}
            engine.awg_snapshot = lambda: {cached['decision']['public_key']: peers[cached['decision']['public_key']]
                for device, cached in state['records'].items() if allowed[device]}
            clients = {device + '@family.test': dict(account=dict(id=cached['decision']['tcp_id'],
                       flow='xtls-rprx-vision')) for device, cached in state['records'].items() if allowed[device]}
            engine.tcp_snapshot = lambda: (clients, {user['account']['id']: user for user in clients.values()})
            observations = {device: dict(expected_revision=cached['decision']['revision'], applied_revision=None,
                observed_at=NOW, registered=True, allowed=allowed[device], result='pending',
                reason='membership-pending' if cached['prepared'] else 'canonical')
                for device, cached in state['records'].items()}
            require(engine.readback(state, peers, observations), 'RECEIVER_FIXTURE_READBACK')
        parts[node + '.state.json'] = (root / 'transport-state.json').read_bytes()
        parts[node + '.config.json'] = config
    identity = RNS.Identity()
    public, marker = identity.get_public_key().hex(), secrets.token_hex(16)
    parts.update({'capture.json': encoded(dict(schema=1, purpose=CAPTURE_PURPOSE, captured_at=NOW, nodes=points)),
        'members.json': encoded(members), 'node.identity': identity.get_private_key(), 'volume-id': marker.encode() + b'\n',
        'settings.json': encoded(dict(volume_id=marker, public_key=public, allowed_public=members['public_keys'][:1])),
        'bootstrap.json': encoded(dict(server=hosts['nl-amsterdam-1'], port=4243, public_key=public,
            destination=RNS.Destination.hash(identity, 'lxmf', 'propagation').hex())),
        'chat-node.json': encoded(dict(host=hosts['nl-amsterdam-1'], port=4243, public_key=public))})
    artifacts['receiver_state'] = parts
    return artifacts


def refuse_mailbox_replay(root, members):
    path = Path(__file__).resolve().parents[1] / 'pilot/messenger/accept_membership.py'
    spec = importlib.util.spec_from_file_location('ha_receiver_membership', path)
    module = importlib.util.module_from_spec(spec)
    import sys
    previous_path = list(sys.path)
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path[:] = previous_path
    module.ROOT = root
    module.subprocess = SimpleNamespace(run=forbidden)
    module.validate = lambda value: validate_membership(value, NOW)
    descriptors = []
    def owned_open(*args, **kwargs):
        descriptor = os.open(*args, **kwargs)
        descriptors.append(descriptor)
        return descriptor
    module.os = SimpleNamespace(**{**vars(os), 'getuid': lambda: 0, 'environ': {'SSH_ORIGINAL_COMMAND': 'chat-sync'},
                                  'open': owned_open})
    for sequence in (members['sequence'] - 1, members['sequence']):
        try:
            incoming = dict(members, sequence=sequence, expires_at=NOW + 100)
            module.sys = SimpleNamespace(stdin=SimpleNamespace(buffer=io.BytesIO(encoded(incoming))))
            try:
                module.main()
            except ValueError as error:
                require(str(error) == 'Stale snapshot', 'RECEIVER_UNEXPECTED_MAILBOX_REFUSAL')
            else:
                raise ValueError('RECEIVER_REPLAY_ACCEPTED')
        finally:
            for descriptor in descriptors:
                os.close(descriptor)
            descriptors.clear()


def exercise_receiver_files(recovered, root):
    root.mkdir(mode=0o700)
    parts = recovered.artifacts['receiver_state']
    capture = parse(parts['capture.json'])
    pending_nodes = 0
    for node in policy.NODES:
        target = root / node
        target.mkdir(mode=0o700)
        private_file(target / 'transport-enforcement.json', parts[node + '.config.json'])
        private_file(target / 'transport-state.json', parts[node + '.state.json'])
        point = deepcopy(capture['nodes'][node])
        engine, module = native_gateway(target, point)
        original = parse(parts[node + '.state.json'])
        require(engine.load() == original, 'RECEIVER_RESTORE_CHANGED')
        with engine.operation():
            for cached in original['records'].values():
                decision = cached['decision']
                engine.accept(dict(schema=1, profile=policy.PROFILE, node=node,
                    observed_at=decision['observed_at'], decisions=[decision]))
        require(engine.load() == original, 'RECEIVER_REPLAY_RENEWED_LEASE')
        for cached in original['records'].values():
            if cached['prepared'] and not cached['decision']['cohort']:
                pending_nodes += 1
                require(not engine.allowed(cached), 'RECEIVER_PREPARE_LOST')
            if not cached['decision']['identity_allowed']:
                attack = dict(cached['decision'], identity_allowed=True, allowed=True)
                with engine.operation():
                    try:
                        engine.accept(dict(schema=1, profile=policy.PROFILE, node=node,
                            observed_at=attack['observed_at'], decisions=[attack]))
                    except ValueError as error:
                        require(str(error) == 'TERMINAL_DECISION', 'RECEIVER_UNEXPECTED_DENIAL')
                    else:
                        raise ValueError('RECEIVER_TERMINAL_DENIAL_LOST')
            if cached['decision']['cohort']:
                point['boot'] = str(uuid.uuid4())
                require(not engine.allowed(cached), 'RECEIVER_REBOOT_RENEWED_LEASE')
                point['boot'] = cached['boot']
                point['monotonic'] = cached['deadline']
                require(not engine.allowed(cached), 'RECEIVER_MONOTONIC_LEASE_EXTENDED')
                point['monotonic'] = capture['nodes'][node]['monotonic']
                expired, unused = native_gateway(target, point, now=NOW + policy.LEASE_SECONDS)
                require(not expired.allowed(cached), 'RECEIVER_WALLCLOCK_LEASE_EXTENDED')
        require(engine.load() == original, 'RECEIVER_SAFETY_STATE_CHANGED')
    mailbox = root / 'mailbox'
    mailbox.mkdir(mode=0o700)
    for name in ('members.json', 'settings.json', 'bootstrap.json', 'chat-node.json', 'node.identity', 'volume-id'):
        private_file(mailbox / name, parts[name])
    members = parse(parts['members.json'])
    refuse_mailbox_replay(mailbox, members)
    reader = Membership(mailbox / 'members.json', lambda path, limit: path.read_bytes(), clock=lambda: NOW + 121)
    require(reader.keys() == [] and (mailbox / 'members.json').read_bytes() == parts['members.json'],
            'RECEIVER_EXPIRED_MEMBERSHIP_OR_FLOOR_LOST')
    require(pending_nodes == 2, 'RECEIVER_PARTIAL_PREPARATION_LOST')
    return dict(nodes=3, partial_preparation_nodes=pending_nodes, terminal_denial=True,
                duplicate_does_not_renew=True, reboot_denies_paid=True, both_lease_clocks=True,
                mailbox_stale_replay_refused=True, expired_membership_keeps_floor=True)
