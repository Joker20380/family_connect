import json
import base64
import ipaddress
import os
from pathlib import Path
import subprocess
import sys
import uuid

import pytest

from control.fleet_gateway import FenceRejected, FencedGateway, PeerCommand, receipt
from control.fleet_worker import FleetWorker
from test_fleet import inventory, load
from test_fleet_store import state, reserve


class Backend:
    def __init__(self):
        self.peers = {}
        self.calls = []
        self.fail_after_effect = False

    def ensure(self, command, *, lock_fd):
        os.fstat(lock_fd)
        self.calls.append(command.operation)
        if command.operation == 'present':
            self.peers[command.wg] = command.address
        else:
            self.peers.pop(command.wg, None)
        if self.fail_after_effect:
            raise OSError('test lost backend reply')


@pytest.fixture
def system(state, inventory, tmp_path):
    store, device, clock = state
    lease = reserve(store, device)
    gateway = next(g for g in load(inventory).gateways if g.gateway_id == lease.gateway_id)
    backend = Backend()
    agent = FencedGateway(tmp_path / 'gateway', gateway, backend, clock=lambda: clock[0])
    agent.initialize()
    command = PeerCommand(lease_id=lease.lease_id, gateway_id=lease.gateway_id, device=device.reference,
        wg=device.wireguard_public_key, address=lease.address, transport=lease.transport,
        version=lease.version, expires_at=lease.expires_at, generation=1, operation='present')
    return store, agent, backend, command, clock


def removal(command):
    return command.model_copy(update={'generation': 2, 'operation': 'absent'})


def test_fence_survives_restart_and_rejects_delayed_create(system):
    _, agent, backend, command, clock = system
    assert agent.execute(command) == receipt(command)
    agent.execute(removal(command))
    restarted = FencedGateway(agent.files.path, agent.gateway, backend, clock=lambda: clock[0])
    with pytest.raises(FenceRejected, match='stale-or-conflicting'):
        restarted.execute(command)
    assert backend.peers == {} and backend.calls == ['present', 'absent']


def test_absent_before_present_never_touches_another_peer(system):
    _, agent, backend, command, _ = system
    backend.peers[command.wg] = '10.99.0.2/32'  # Unmanaged, must not be removed.
    agent.execute(removal(command))
    with pytest.raises(FenceRejected):
        agent.execute(command)
    assert backend.calls == [] and backend.peers[command.wg] == '10.99.0.2/32'


def test_old_delete_receipt_does_not_delete_reused_key_or_address(system):
    _, agent, backend, command, _ = system
    agent.execute(command); agent.execute(removal(command))
    new = command.model_copy(update={'lease_id': uuid.uuid4().hex})
    agent.execute(new)
    calls = list(backend.calls)
    assert agent.execute(removal(command)) == receipt(removal(command))
    assert backend.calls == calls and backend.peers == {new.wg: new.address}


def test_pending_delete_keeps_key_and_ip_reserved(system):
    _, agent, backend, command, _ = system
    agent.execute(command)
    backend.fail_after_effect = True
    with pytest.raises(OSError):
        agent.execute(removal(command))
    backend.fail_after_effect = False
    other = command.model_copy(update={'lease_id': uuid.uuid4().hex})
    with pytest.raises(FenceRejected, match='resource-owned'):
        agent.execute(other)
    with pytest.raises(FenceRejected, match='stale-or-conflicting'):
        agent.execute(command)
    agent.execute(removal(command))
    agent.execute(other)


@pytest.mark.parametrize('field,value', [('address','10.83.0.30/32'), ('expires_at',1200), ('device','a'*32)])
def test_same_lease_binding_cannot_change(system, field, value):
    _, agent, _, command, _ = system
    agent.execute(command)
    with pytest.raises(FenceRejected):
        agent.execute(command.model_copy(update={field: value}))


@pytest.mark.parametrize('change', [dict(gateway_id='other'), dict(address='10.99.0.2/32'),
    dict(address='127.0.0.1/32'), dict(generation=True), dict(generation=3),
    dict(transport='vless-reality',version='1')])
def test_untrusted_or_unsupported_commands_fail_before_effect(system, change):
    _, agent, backend, command, _ = system
    with pytest.raises(ValueError):
        agent.execute(command.model_copy(update=change))
    assert not backend.calls


def test_gateway_recovery_reapplies_live_peers_but_not_historical_deletes(system):
    _, agent, backend, command, _ = system
    agent.execute(command)
    backend.peers.clear()  # Engine restart lost volatile runtime configuration.
    assert agent.recover() == [receipt(command)]
    assert backend.peers == {command.wg: command.address}
    agent.execute(removal(command))
    calls = list(backend.calls)
    assert agent.recover() == [] and backend.calls == calls


def test_expired_command_and_clock_rollback_do_not_install(system):
    _, agent, backend, command, clock = system
    clock[0] = 999
    with pytest.raises(FenceRejected, match='gateway-state'):
        agent.execute(command)
    clock[0] = command.expires_at
    with pytest.raises(FenceRejected, match='expired-command'):
        agent.execute(command)
    assert not backend.calls


@pytest.mark.parametrize('resource', ['key', 'address'])
def test_ownership_checks_both_key_and_address(system, resource):
    _, agent, _, command, _ = system
    agent.execute(command)
    changes = dict(lease_id=uuid.uuid4().hex)
    if resource == 'key':
        changes['address'] = str(ipaddress.IPv4Interface(command.address).ip + 1) + '/32'
    else:
        changes['wg'] = base64.b64encode(bytes([2])*32).decode()
    with pytest.raises(FenceRejected, match='resource-owned'):
        agent.execute(command.model_copy(update=changes))


def test_lost_gateway_database_never_reinitializes(system):
    _, agent, _, command, _ = system
    agent.execute(command)
    path = agent.files.path / 'gateway.db'
    path.unlink()
    with pytest.raises(FileNotFoundError):
        agent.execute(command)
    with pytest.raises(FileExistsError):
        agent.initialize()
    assert not path.exists()


def test_changed_gateway_pin_cannot_reuse_old_journal(system):
    _, agent, backend, command, _ = system
    other = agent.gateway.model_copy(update={'gateway_id': 'other'})
    wrong = FencedGateway(agent.files.path, other, backend, clock=lambda:1000)
    with pytest.raises(FenceRejected, match='gateway-state'):
        wrong.execute(command.model_copy(update={'gateway_id': 'other'}))


def test_worker_complete_lifecycle(system):
    store, agent, backend, command, _ = system
    worker = FleetWorker(store, {command.gateway_id: agent})
    assert worker.once() == [(command.lease_id, 'ready')]
    assert worker.once() == []
    assert store.publishable(command.lease_id).state == 'ready'
    store.retire(command.lease_id)
    assert worker.once() == [(command.lease_id, 'released')]
    assert backend.peers == {} and store.pending() == []


def test_lost_receipt_is_retried_without_reapplying(system):
    store, agent, backend, command, _ = system
    class Lost:
        def execute(self, cmd):
            agent.execute(cmd)
            raise OSError('test network reply lost')
    assert FleetWorker(store, {command.gateway_id: Lost()}).once() == [(command.lease_id, 'retry')]
    assert store.get(command.lease_id).state == 'reserved'
    FleetWorker(store, {command.gateway_id: agent}).once()
    assert backend.calls == ['present']
    store.retire(command.lease_id)
    FleetWorker(store, {command.gateway_id: Lost()}).once()
    assert store.get(command.lease_id).state == 'retiring'
    FleetWorker(store, {command.gateway_id: agent}).once()
    assert backend.calls == ['present', 'absent']


def test_revocation_racing_with_apply_never_commits_ready(system):
    store, agent, backend, command, _ = system
    class Race:
        def execute(self, cmd):
            answer = agent.execute(cmd)
            store.retire(cmd.lease_id)
            return answer
    assert FleetWorker(store, {command.gateway_id: Race()}).once() == [(command.lease_id, 'state-changed')]
    assert store.get(command.lease_id).state == 'retiring'
    FleetWorker(store, {command.gateway_id: agent}).once()
    assert not backend.peers


@pytest.mark.parametrize('change', [dict(digest='0'*64), dict(generation=True), dict(operation='absent')])
def test_bad_receipt_keeps_work_pending(system, change):
    store, _, _, command, _ = system
    class Bad:
        def execute(self, cmd):
            return {**receipt(cmd), **change}
    assert FleetWorker(store, {command.gateway_id: Bad()}).once() == [(command.lease_id, 'retry')]
    assert store.get(command.lease_id).state == 'reserved'


def test_missing_adapter_does_not_release_or_mark_ready(system):
    store, _, _, command, _ = system
    assert FleetWorker(store, {}).once() == [(command.lease_id, 'retry')]


# Real process death: a child still holds the effects FD after its parent exits.
# A competing removal must wait until the child's late install finishes.
CRASH_PARENT = '''
import json,os,subprocess,sys
from pathlib import Path
from control.fleet import Gateway
from control.fleet_gateway import FencedGateway,PeerCommand
v=json.load(sys.stdin)
class Backend:
    def ensure(self,cmd,*,lock_fd):
        child="import os,sys,time;from pathlib import Path; gate=Path(sys.argv[1]); end=time.monotonic()+10;\\nwhile not gate.exists() and time.monotonic()<end: time.sleep(.01)\\nPath(sys.argv[2]).write_text('present');os.close(int(sys.argv[3]))"
        subprocess.Popen([sys.executable,'-c',child,v['gate'],v['peer'],str(lock_fd)],
            pass_fds=(lock_fd,),stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        os._exit(23)
agent=FencedGateway(v['path'],Gateway.model_validate_json(json.dumps(v['gateway'])),Backend(),clock=lambda:1000)
agent.execute(PeerCommand.model_validate_json(json.dumps(v['command'])))
'''


def test_child_effect_lock_survives_parent_death(system, tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    import threading
    _, agent, _, command, _ = system
    gate, peer = tmp_path/'release-child', tmp_path/'peer'
    data = dict(path=str(agent.files.path), gateway=agent.gateway.model_dump(mode='json'),
                command=command.model_dump(), gate=str(gate), peer=str(peer))
    process = subprocess.run([sys.executable, '-c', CRASH_PARENT], input=json.dumps(data),
                             text=True, capture_output=True, timeout=15)
    assert process.returncode == 23 and not process.stderr
    entered = threading.Event()
    class Remove:
        def ensure(self, cmd, *, lock_fd):
            entered.set()
            assert peer.read_text() == 'present'
            peer.write_text('absent')
    restarted = FencedGateway(agent.files.path, agent.gateway, Remove(), clock=lambda:1000)
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(restarted.execute, removal(command))
        try:
            assert not entered.wait(.2)
        finally:
            gate.touch()
        assert future.result(timeout=15) == receipt(removal(command))
    assert peer.read_text() == 'absent'
    with pytest.raises(FenceRejected):
        restarted.execute(command)
