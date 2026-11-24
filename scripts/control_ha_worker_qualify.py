"""Native queue recovery on private copies using in-memory adapters, never Docker."""
from contextlib import closing
import json
from pathlib import Path
import sqlite3

from control.product.gateways import GatewayReconciler
from control.product.provisioning import ProvisioningService
from control.product.store import ProductStore
from provisioning.envelope import ProvisioningRejected
from scripts import control_ha_worker_custody as custody
from scripts.control_ha_live_sqlite import require


class OfflineAdapter:
    def __init__(self):
        self.calls = []
        self.fail = False

    def apply(self, identity, public, addresses, *, present, gateway):
        self.calls.append((identity, present))
        if self.fail:
            raise RuntimeError('OFFLINE_INJECTED_FAILURE')


def qualify(value, destination):
    root = Path(__file__).resolve().parents[1]
    require(all(custody.digest((root / name).read_bytes()) == pin for name, pin in custody.PINS.items()),
            'LOCAL_NATIVE_SOURCE_CHANGED')
    custody.restore(value, destination)
    files = custody.unpack(value)
    destination = Path(destination)
    database_path = destination / 'product.sqlite'
    now = [value['captured_at_ns'] // 1000000000]
    store = ProductStore(database_path, clock=lambda: now[0])
    store.check_ready()
    adapters = {name: OfflineAdapter() for name in custody.bindings(files)}
    worker = GatewayReconciler(store, adapters)
    preserved_tables = tuple(name for name in custody.validate(value)['tables'] if name != 'peer_outbox')

    def preserved():
        with store._transaction() as database:
            return {name: [tuple(row) for row in database.execute('SELECT * FROM ' + name)]
                    for name in preserved_tables}

    original = preserved()
    with store._transaction() as database:
        deployments = database.execute('SELECT * FROM peer_deployments').fetchall()
        allowed = set()
        for deployment in deployments:
            try:
                ProvisioningService(store)._authorized(database, deployment['device_identity'], now[0])
            except ProvisioningRejected:
                continue
            if deployment['expires_at'] > now[0]:
                allowed.add(deployment['device_identity'])
        future = database.execute('SELECT coalesce(max(retry_at),0) FROM peer_outbox').fetchone()[0]
    original_jobs = worker.status()
    worker.run_once()
    require(all(not present or identity in allowed for adapter in adapters.values()
                for identity, present in adapter.calls), 'UNAUTHORIZED_INSTALL')
    for before, after in zip(original_jobs, worker.status()):
        if before['retry_at'] > now[0] and before['device_identity'] in allowed:
            require(after == before, 'RETRY_FLOOR_RESET')
    worker = GatewayReconciler(ProductStore(database_path, clock=lambda: now[0]), adapters)
    worker.run_once()
    require(preserved() == original, 'DUPLICATE_RESET_AUTHORITY')
    with store._transaction() as database:
        for deployment in deployments:
            if deployment['expires_at'] <= now[0]:
                try:
                    worker.require_ready(database, deployment['device_identity'],
                                         json.loads(deployment['network']), now[0])
                except ProvisioningRejected:
                    continue
                raise ValueError('EXPIRED_DEPLOYMENT_READY')
    now[0] = max(now[0], future) + 1
    for adapter in adapters.values():
        adapter.fail = True
    failed = worker.run_once()
    require(all(row['status'] == 'retry' for row in failed), 'FAILURE_ACKNOWLEDGED')
    pending = worker.status()
    require(all(row['applied'] is None and row['error'] == 'GATEWAY_UNAVAILABLE' and
                row['retry_at'] > now[0] for row in pending), 'FAILURE_NOT_DURABLE')
    call_count = sum(len(adapter.calls) for adapter in adapters.values())
    worker = GatewayReconciler(ProductStore(database_path, clock=lambda: now[0]), adapters)
    worker.run_once()
    require(worker.status() == pending and call_count == sum(len(adapter.calls) for adapter in adapters.values()),
            'RESTART_IGNORED_RETRY_FLOOR')
    now[0] = max([now[0]] + [row['expires_at'] for row in deployments] + [row['retry_at'] for row in pending]) + 1
    for adapter in adapters.values():
        adapter.fail = False
        adapter.calls.clear()
    expired = worker.run_once()
    require(all(row['status'] == 'absent' for row in expired) and
            all(not present for adapter in adapters.values() for identity, present in adapter.calls), 'EXPIRED_INSTALL')
    require(preserved() == original, 'RECOVERY_RESET_AUTHORITY')
    with closing(sqlite3.connect(database_path)) as database:
        require(database.execute('PRAGMA integrity_check').fetchall() == [('ok',)], 'QUALIFICATION_INTEGRITY')
    return dict(result='NATIVE_WORKER_OFFLINE_PASS', jobs=len(original_jobs), allowed_at_capture=len(allowed),
                expired_at_capture=sum(row['expires_at'] <= value['captured_at_ns'] // 1000000000 for row in deployments),
                duplicate_no_authority_reset=True, durable_retry_restart=True, expiry_denies_install=True,
                real_gateway_commands=0, activation=False, external_command_fence=False)
