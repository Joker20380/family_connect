from concurrent.futures import ThreadPoolExecutor
import json
import os
import sqlite3
import subprocess
import sys

import pytest

from control.fleet import Observation
from control.fleet_store import FleetStore, LeaseRejected
from device_identity.device import DeviceIdentity
from test_fleet import inventory, load, observations


@pytest.fixture
def state(tmp_path, inventory):
    clock = [1000]
    store = FleetStore(tmp_path / 'fleet', clock=lambda: clock[0])
    store.initialize(load(inventory))
    device = DeviceIdentity.generate()
    grant(store, device)
    return store, device, clock


def grant(store, device, **changes):
    args = dict(device=device.reference, public=device.public_identity, wg=device.wireguard_public_key,
                revision=1, expires_at=2000, max_leases=2)
    args.update(changes)
    store.set_access(**args)


def reserve(store, device, **changes):
    args = dict(device=device.reference, request_id='request-1', registry_revision=7,
                country='nl', transport='amneziawg', version='3.1', lifetime=100,
                observations=observations())
    args.update(changes)
    return store.reserve(**args)


def test_ready_is_required_and_same_request_survives_restart(state):
    store, device, clock = state
    lease = reserve(store, device)
    assert lease.state == 'reserved' and lease.generation == 1 and lease.expires_at == 1100
    assert lease.address.endswith('.2/32')
    with pytest.raises(LeaseRejected, match='not-ready'):
        store.publishable(lease.lease_id)
    store = FleetStore(store.files.path, clock=lambda: clock[0])
    assert reserve(store, device) == lease
    ready = store.mark_ready(lease.lease_id, generation=1)
    assert ready.state == 'ready'
    assert store.mark_ready(lease.lease_id, generation=1) == ready
    assert store.publishable(lease.lease_id) == ready


def test_idempotency_does_not_extend_or_reallocate(state):
    store, device, clock = state
    lease = reserve(store, device)
    clock[0] += 20
    assert reserve(store, device, observations=[]) == lease
    with pytest.raises(LeaseRejected, match='request-conflict'):
        reserve(store, device, lifetime=101)
    with pytest.raises(LeaseRejected, match='assignment-exists'):
        reserve(store, device, request_id='request-2')
    retired = store.retire(lease.lease_id)
    released = store.confirm_removed(lease.lease_id, generation=retired.generation)
    assert reserve(store, device).state == 'released'
    assert store.confirm_removed(lease.lease_id, generation=retired.generation) == released
    assert reserve(store, device, request_id='request-2').lease_id != lease.lease_id


def test_expiry_keeps_address_until_cleanup(state):
    store, device, clock = state
    lease = reserve(store, device)
    clock[0] = lease.expires_at
    assert store.get(lease.lease_id).state == 'reserved'
    with pytest.raises(LeaseRejected, match='stale-ready'):
        store.mark_ready(lease.lease_id, generation=1)
    retired, = store.expire()
    assert retired.state == 'retiring' and retired.generation == 2
    assert store.expire() == []
    with pytest.raises(LeaseRejected, match='assignment-exists'):
        reserve(store, device, request_id='request-2')
    with pytest.raises(LeaseRejected, match='stale-removal'):
        store.confirm_removed(lease.lease_id, generation=1)
    store.confirm_removed(lease.lease_id, generation=2)
    fresh = [s.model_copy(update={'observed_at': clock[0]}) for s in observations()]
    new = reserve(store, device, request_id='request-2', observations=fresh)
    assert new.address == lease.address and new.lease_id != lease.lease_id
    # Delayed cleanup for the historical lease cannot affect the new owner.
    store.confirm_removed(lease.lease_id, generation=2)
    assert store.get(new.lease_id).state == 'reserved'


def test_revoke_is_atomic_and_old_ready_ack_cannot_resurrect(state):
    store, device, _ = state
    lease = reserve(store, device)
    store.mark_ready(lease.lease_id, generation=1)
    grant(store, device, revision=2, revoked=True)
    assert store.get(lease.lease_id).state == 'retiring'
    for call in (lambda: reserve(store, device), lambda: store.publishable(lease.lease_id),
                 lambda: store.mark_ready(lease.lease_id, generation=1)):
        with pytest.raises(LeaseRejected, match='access-denied'):
            call()
    with pytest.raises(LeaseRejected, match='access-revision-or-binding'):
        grant(store, device)
    grant(store, device, revision=3)
    with pytest.raises(LeaseRejected, match='stale-ready'):
        store.mark_ready(lease.lease_id, generation=1)
    assert reserve(store, device).state == 'retiring'


def test_access_grant_cannot_replace_keys_or_change_same_revision(state):
    store, device, _ = state
    grant(store, device)  # Exact lost-response retry.
    with pytest.raises(LeaseRejected, match='access-revision-or-binding'):
        grant(store, device, expires_at=3000)
    other = DeviceIdentity.generate()
    with pytest.raises(LeaseRejected, match='binding-mismatch'):
        grant(store, device, public=other.public_identity, revision=2)
    with pytest.raises(LeaseRejected, match='access-revision-or-binding'):
        grant(store, device, wg=other.wireguard_public_key, revision=2)


def test_lease_clamped_to_access_and_shortening_retires(state):
    store, device, _ = state
    lease = reserve(store, device, lifetime=86400)
    assert lease.expires_at == 2000
    grant(store, device, revision=2, expires_at=1500)
    assert store.get(lease.lease_id).state == 'retiring'


def test_registry_update_is_durable_and_rejects_rollback(state, inventory):
    store, device, _ = state
    lease = reserve(store, device)
    inventory['revision'] = 8
    inventory['gateways'][0]['weight'] = 2.0
    store.install_registry(load(inventory))
    assert reserve(store, device) == lease  # Exact request result survives registry change.
    store.install_registry(load(inventory))
    with pytest.raises(ValueError):
        inventory['revision'] = 7
        store.install_registry(load(inventory))
    other = DeviceIdentity.generate(); grant(store, other)
    with pytest.raises(LeaseRejected, match='registry-stale'):
        reserve(store, other)


@pytest.mark.parametrize('change', ['disabled', 'provisioning'])
def test_registry_invalidation_retires_and_blocks_stale_receipts(state, inventory, change):
    store, device, _ = state
    lease = reserve(store, device)
    store.mark_ready(lease.lease_id, generation=1)
    node = next(g for g in inventory['gateways'] if g['gateway_id'] == lease.gateway_id)
    inventory['revision'] += 1
    node['state'] = change
    store.install_registry(load(inventory))
    assert store.get(lease.lease_id).state == 'retiring'
    with pytest.raises(LeaseRejected, match='stale-ready'):
        store.mark_ready(lease.lease_id, generation=1)


def test_endpoint_edit_cannot_abandon_an_unremoved_peer(state, inventory):
    store, device, _ = state
    lease = reserve(store, device)
    node = next(g for g in inventory['gateways'] if g['gateway_id'] == lease.gateway_id)
    inventory['revision'] += 1
    node['endpoints'][0]['address'] = '1.1.1.1'
    with pytest.raises(LeaseRejected, match='endpoint-migration-required'):
        store.install_registry(load(inventory))
    retired = store.retire(lease.lease_id)
    with pytest.raises(LeaseRejected, match='endpoint-migration-required'):
        store.install_registry(load(inventory))
    store.confirm_removed(lease.lease_id, generation=retired.generation)
    store.install_registry(load(inventory))


def test_work_discovery_and_original_binding_survive_restart_and_revoke(state, inventory):
    store, device, _ = state
    lease = reserve(store, device)
    work = store.work_item(lease.lease_id, generation=1)
    assert work.public == device.public_identity and work.wg == device.wireguard_public_key
    assert work.gateway.gateway_id == lease.gateway_id
    inventory['revision'] += 1
    for g in inventory['gateways']:
        g['state'] = 'draining'
    store.install_registry(load(inventory))
    assert store.work_item(lease.lease_id, generation=1).gateway == work.gateway
    grant(store, device, revision=2, revoked=True)
    reopened = FleetStore(store.files.path, clock=lambda: 1000)
    pending, = reopened.pending()
    assert pending.state == 'retiring'
    assert reopened.work_item(pending.lease_id, generation=2).wg == work.wg
    with pytest.raises(LeaseRejected, match='stale-work'):
        reopened.work_item(pending.lease_id, generation=1)
    reopened.confirm_removed(pending.lease_id, generation=2)
    assert reopened.pending() == []


def test_expired_work_never_becomes_installable(state):
    store, device, clock = state
    lease = reserve(store, device)
    clock[0] = lease.expires_at
    with pytest.raises(LeaseRejected, match='expired-work'):
        store.work_item(lease.lease_id, generation=1)
    store.expire()
    assert store.work_item(lease.lease_id, generation=2).lease.state == 'retiring'


def test_removal_receipt_cannot_skip_retiring(state):
    store, device, _ = state
    lease = reserve(store, device)
    with pytest.raises(LeaseRejected, match='stale-removal'):
        store.confirm_removed(lease.lease_id, generation=1)
    assert store.get(lease.lease_id) == lease


def test_revoke_write_failure_preserves_access_and_ready_state(state, monkeypatch):
    store, device, _ = state
    lease = reserve(store, device); store.mark_ready(lease.lease_id, generation=1)
    original = store._event
    def failed(db, now, kind, subject):
        original(db, now, kind, subject)
        if kind == 'access-revoked':
            raise OSError('test disk failure')
    with monkeypatch.context() as m:
        m.setattr(store, '_event', failed)
        with pytest.raises(OSError):
            grant(store, device, revision=2, revoked=True)
    assert store.publishable(lease.lease_id).state == 'ready'


def test_draining_keeps_existing_ready_but_rejects_new(state, inventory):
    store, device, _ = state
    lease = reserve(store, device)
    store.mark_ready(lease.lease_id, generation=1)
    inventory['revision'] = 8
    for g in inventory['gateways']:
        g['state'] = 'draining'
    store.install_registry(load(inventory))
    assert store.publishable(lease.lease_id).state == 'ready'
    other = DeviceIdentity.generate(); grant(store, other)
    samples = [s.model_copy(update={'registry_revision': 8}) for s in observations()]
    with pytest.raises(LeaseRejected, match='no-capacity'):
        reserve(store, other, registry_revision=8, observations=samples)


def test_retiring_holds_capacity_until_matching_removal(tmp_path, inventory):
    inventory['gateways'][0]['max_devices'] = 1
    inventory['gateways'][1]['state'] = 'disabled'
    store = FleetStore(tmp_path / 'fleet', clock=lambda: 1000); store.initialize(load(inventory))
    first, second = DeviceIdentity.generate(), DeviceIdentity.generate()
    grant(store, first); grant(store, second)
    samples = [s.model_copy(update={'allocated_devices': 0}) for s in observations()]
    lease = reserve(store, first, observations=samples)
    retired = store.retire(lease.lease_id)
    assert store.retire(lease.lease_id) == retired
    with pytest.raises(LeaseRejected, match='no-capacity'):
        reserve(store, second, observations=samples)
    store.confirm_removed(lease.lease_id, generation=retired.generation)
    new = reserve(store, second, observations=samples)
    assert new.address == lease.address


def test_device_limit_is_shared_across_countries(tmp_path, inventory):
    inventory['gateways'][1]['country'] = 'ru'
    store = FleetStore(tmp_path / 'fleet', clock=lambda: 1000); store.initialize(load(inventory))
    device = DeviceIdentity.generate(); grant(store, device, max_leases=1)
    lease = reserve(store, device)
    with pytest.raises(LeaseRejected, match='device-limit'):
        reserve(store, device, request_id='request-ru', country='ru')
    grant(store, device, revision=2, max_leases=2)
    second = reserve(store, device, request_id='request-ru', country='ru')
    assert second.gateway_id != lease.gateway_id and second.address != lease.address


def test_full_pool_excludes_network_gateway_and_broadcast(tmp_path, inventory):
    inventory['gateways'][0].update(tunnel_pool='10.83.0.0/29', max_devices=5)
    inventory['gateways'][1]['state'] = 'disabled'
    store = FleetStore(tmp_path / 'fleet', clock=lambda: 1000); store.initialize(load(inventory))
    samples = [s.model_copy(update={'allocated_devices': 0}) for s in observations()]
    addresses = []
    for _ in range(5):
        device = DeviceIdentity.generate(); grant(store, device)
        addresses.append(reserve(store, device, observations=samples).address)
    assert addresses == [f'10.83.0.{n}/32' for n in range(2, 7)]
    device = DeviceIdentity.generate(); grant(store, device)
    with pytest.raises(LeaseRejected, match='no-capacity'):
        reserve(store, device, observations=samples)


def test_store_does_not_admit_with_stale_telemetry(state):
    store, device, clock = state
    clock[0] = 1046
    with pytest.raises(LeaseRejected, match='no-capacity'):
        reserve(store, device)


def test_private_storage_missing_database_and_partial_init_fail_closed(state, inventory):
    store, device, _ = state
    assert store.files.path.stat().st_mode & 0o777 == 0o700
    path = store.files.path / 'fleet.db'
    assert path.stat().st_mode & 0o777 == 0o600
    with pytest.raises(FileExistsError):
        store.initialize(load(inventory))
    path.unlink()
    with pytest.raises(FileNotFoundError):
        reserve(store, device)
    assert not path.exists()


@pytest.mark.parametrize('mode', ['permissions', 'symlink', 'hardlink', 'corrupt'])
def test_unsafe_store_is_not_repaired(state, mode):
    store, device, _ = state
    path = store.files.path / 'fleet.db'
    if mode == 'permissions':
        path.chmod(0o644)
    elif mode == 'symlink':
        target = path.with_name('target.db'); path.rename(target); path.symlink_to(target)
    elif mode == 'hardlink':
        os.link(path, path.with_name('another.db'))
    else:
        path.write_bytes(b'not a database')
    with pytest.raises((ValueError, OSError, sqlite3.DatabaseError)):
        reserve(store, device)


def test_clock_rollback_and_expired_access_fail_closed(state):
    store, device, clock = state
    lease = reserve(store, device)
    clock[0] = 999
    with pytest.raises(LeaseRejected, match='state-or-clock'):
        store.get(lease.lease_id)
    clock[0] = 2000
    with pytest.raises(LeaseRejected, match='access-denied'):
        reserve(store, device)
    assert store.expire()[0].state == 'retiring'


@pytest.mark.parametrize('change', [dict(lifetime=True), dict(lifetime=0), dict(lifetime=86401),
    dict(request_id=''), dict(country='NL'), dict(version='4'), dict(address_families=(True,))])
def test_invalid_request_never_allocates(state, change):
    store, device, _ = state
    with pytest.raises(LeaseRejected):
        reserve(store, device, **change)
    assert reserve(store, device).address.endswith('.2/32')


def test_transaction_failure_rolls_back_address_request_and_event(state, monkeypatch):
    store, device, _ = state
    original = store._event
    def failure(db, now, kind, subject):
        original(db, now, kind, subject)
        if kind == 'reserved':
            raise OSError('test disk error')
    with monkeypatch.context() as m:
        m.setattr(store, '_event', failure)
        with pytest.raises(OSError):
            reserve(store, device)
    assert reserve(store, device).address.endswith('.2/32')


def test_concurrent_duplicate_requests_have_one_durable_result(state):
    store, device, _ = state
    def work(_):
        other = FleetStore(store.files.path, clock=lambda: 1000)
        return reserve(other, device)
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(work, range(24)))
    assert len({r.lease_id for r in results}) == 1


# Separate OS processes test flock/SQLite arbitration, and real process death
# tests SQLite hot-journal recovery instead of only mocked exception handling.
CHILD = '''
import json,os,sys,time
from dataclasses import asdict
from control.fleet import Observation
from control.fleet_store import FleetStore,LeaseRejected
value=json.load(sys.stdin)
store=FleetStore(value['path'],clock=lambda:1000)
original=store._event
def event(db,now,kind,subject):
    original(db,now,kind,subject)
    if kind=='reserved' and value.get('crash')=='before-commit':os._exit(23)
store._event=event
while value.get('gate') and not os.path.exists(value['gate']):time.sleep(.01)
try:
    lease=store.reserve(device=value['device'],request_id='request-1',registry_revision=7,
        country='nl',transport='amneziawg',version='3.1',lifetime=100,
        observations=[Observation.model_validate_json(json.dumps(s)) for s in value['observations']])
    if value.get('crash')=='after-commit':os._exit(23)
    print(json.dumps(asdict(lease)))
except LeaseRejected as e:print(json.dumps({'error':str(e)}))
'''


def child(store, device, **options):
    process = subprocess.Popen([sys.executable, '-c', CHILD], stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    data = dict(path=str(store.files.path), device=device.reference,
        observations=[s.model_dump(mode='json') for s in observations()])
    data.update(options)
    process.stdin.write(json.dumps(data))
    process.stdin.close(); process.stdin = None
    return process


@pytest.mark.parametrize('phase', ['before-commit', 'after-commit'])
def test_process_death_does_not_lose_or_duplicate_assignment(state, phase):
    store, device, _ = state
    process = child(store, device, crash=phase)
    _, error = process.communicate(timeout=15)
    assert process.returncode == 23 and not error
    lease = reserve(store, device)
    assert lease.address.endswith('.2/32')
    with sqlite3.connect(store.files.path / 'fleet.db') as db:
        assert db.execute('SELECT COUNT(*) FROM leases').fetchone()[0] == 1
        assert db.execute('SELECT COUNT(*) FROM requests').fetchone()[0] == 1
        assert db.execute("SELECT COUNT(*) FROM events WHERE kind='reserved'").fetchone()[0] == 1


def test_multiprocess_capacity_and_ip_uniqueness(tmp_path, inventory):
    inventory['gateways'][0].update(tunnel_pool='10.83.0.0/29', max_devices=3)
    inventory['gateways'][1]['state'] = 'disabled'
    store = FleetStore(tmp_path / 'fleet', clock=lambda: 1000); store.initialize(load(inventory))
    devices = [DeviceIdentity.generate() for _ in range(10)]
    for device in devices:
        grant(store, device)
    gate = tmp_path / 'go'
    samples = [s.model_copy(update={'allocated_devices': 0}).model_dump(mode='json') for s in observations()]
    processes = [child(store, device, gate=str(gate), observations=samples) for device in devices]
    try:
        gate.touch()
        results = []
        for process in processes:
            out, err = process.communicate(timeout=30)
            assert process.returncode == 0 and not err
            results.append(json.loads(out))
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill(); process.wait()
    successful = [r for r in results if 'lease_id' in r]
    assert len(successful) == 3
    assert {r['address'] for r in successful} == {'10.83.0.2/32', '10.83.0.3/32', '10.83.0.4/32'}
    assert [r['error'] for r in results if 'error' in r] == ['no-capacity'] * 7
