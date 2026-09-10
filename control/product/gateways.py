"""Single-host durable peer work queue. Operator-configured adapters only.

External operations run under the product write transaction. This deliberately
serializes installs with revoke and prevents stale workers reinstalling peers.
Use a single worker and bounded subprocess timeouts; this is not a distributed
lease/fencing protocol. Gateways must be reachable through local Docker adapters.
"""
import ipaddress
import json

from provisioning.envelope import ProvisioningRejected
from provisioning.models import NetworkProvisioningState


class GatewayReconciler:
    def __init__(self, store, adapters):
        self.store, self.adapters = store, adapters

    def stage(self, identity, network, *, lease_seconds=3600):
        from .provisioning import ProvisioningService
        if (type(network) is not dict or set(network) != {'addresses','dns','gateways'} or
                type(lease_seconds) is not int or not 1 <= lease_seconds <= 86400):
            raise ValueError('invalid deployment')
        with self.store._transaction() as db:
            now = int(self.store.clock())
            row, ent = ProvisioningService(self.store)._authorized(db, identity, now)
            expiry = min(now+lease_seconds, ent['expires_at'])
            state = NetworkProvisioningState.model_validate_json(json.dumps(dict(**network,
                schema_version=1, revision=1, recipient=identity, issued_at=now, expires_at=expiry,
                entitlement_id=ent['id'], entitlement_revision=ent['revision'], wireguard_public_key=row['public_key'])))
            normalized = {key:state.model_dump(mode='json')[key] for key in ('addresses','dns','gateways')}
            canonical = json.dumps(normalized, sort_keys=True, separators=(',',':'))
            # Pilot uses dedicated host routes. Subnets would authorize other devices.
            for address in state.addresses:
                if address.network.prefixlen != address.max_prefixlen:
                    raise ValueError('device addresses must be host routes')
            previous = db.execute('SELECT * FROM peer_deployments WHERE device_identity=?',(identity,)).fetchone()
            if previous is not None and previous['network'] != canonical:
                raise ValueError('topology changes require a separate migration')
            for address in state.addresses:
                owner = db.execute('SELECT device_identity FROM peer_allocations WHERE address=?',
                                   (str(address.ip),)).fetchone()
                if owner and owner[0] != identity:
                    raise ValueError('address already allocated')
                db.execute('INSERT OR IGNORE INTO peer_allocations VALUES (?,?)',(str(address.ip),identity))
            if previous and expiry < previous['expires_at']:
                raise ValueError('cannot shorten an existing deployment lease')
            db.execute('INSERT INTO peer_deployments VALUES (?,?,?) ON CONFLICT(device_identity) '
                       'DO UPDATE SET expires_at=excluded.expires_at',(identity,canonical,expiry))
            for gateway in state.gateways:
                db.execute('INSERT INTO peer_outbox(device_identity,gateway_id,public_key,desired) '
                           'VALUES (?,?,?,?) ON CONFLICT(device_identity,gateway_id) DO UPDATE SET '
                           'desired=excluded.desired, applied=NULL, retry_at=0, attempts=0, error=NULL',
                           (identity,gateway.gateway_id,row['public_key'],'present'))
            return dict(device_identity=identity, expires_at=expiry, status='pending')

    @staticmethod
    def require_ready(db, identity, network, now):
        deployment = db.execute('SELECT * FROM peer_deployments WHERE device_identity=?',(identity,)).fetchone()
        jobs = db.execute('SELECT * FROM peer_outbox WHERE device_identity=?',(identity,)).fetchall()
        if (deployment is None or deployment['expires_at'] <= now or
                json.loads(deployment['network']) != network or not jobs or
                {job['gateway_id'] for job in jobs} != {g['gateway_id'] for g in network['gateways']} or
                any(job['desired'] != 'present' or job['applied'] != 'present' or job['error'] is not None for job in jobs)):
            raise ProvisioningRejected('gateway deployment not ready')
        return deployment['expires_at']

    @staticmethod
    def revoke(db, identity):
        db.execute("UPDATE peer_outbox SET desired='absent',retry_at=0,attempts=0,error=NULL "
                   "WHERE device_identity=? AND desired!='absent'", (identity,))

    def run_once(self):
        from .provisioning import ProvisioningService
        results = []
        # Snapshot only identifiers. Every operation re-reads authorization under lock.
        with self.store._transaction() as db:
            subjects = [(r[0],r[1]) for r in db.execute('SELECT device_identity,gateway_id FROM peer_outbox '
                                                       'ORDER BY device_identity,gateway_id')]
        for identity, gateway in subjects:
            with self.store._transaction() as db:
                now = int(self.store.clock())
                deployment = db.execute('SELECT * FROM peer_deployments WHERE device_identity=?',(identity,)).fetchone()
                try:
                    ProvisioningService(self.store)._authorized(db, identity, now)
                    active = deployment['expires_at'] > now
                except ProvisioningRejected:
                    active = False
                if not active:
                    self.revoke(db, identity)
                job = db.execute('SELECT * FROM peer_outbox WHERE device_identity=? AND gateway_id=?',
                                 (identity,gateway)).fetchone()
                if job['retry_at'] > now:
                    continue
                network = json.loads(deployment['network'])
                candidate = next(g for g in network['gateways'] if g['gateway_id']==gateway)
                try:
                    self.adapters[gateway].apply(identity, job['public_key'], network['addresses'],
                        present=job['desired']=='present', gateway=candidate)
                except Exception:
                    # Never persist subprocess output, exceptions, or credentials.
                    attempts = min(job['attempts']+1, 10)
                    db.execute('UPDATE peer_outbox SET applied=NULL,attempts=?,retry_at=?,error=? '
                               'WHERE device_identity=? AND gateway_id=?',
                               (attempts,now+min(300,2**attempts),'GATEWAY_UNAVAILABLE',identity,gateway))
                    results.append(dict(device_identity=identity,gateway_id=gateway,status='retry'))
                else:
                    db.execute('UPDATE peer_outbox SET applied=desired,attempts=0,retry_at=0,checked_at=?,error=NULL '
                               'WHERE device_identity=? AND gateway_id=?',(now,identity,gateway))
                    results.append(dict(device_identity=identity,gateway_id=gateway,status=job['desired']))
        return results

    def status(self):
        with self.store._transaction() as db:
            return [dict(row) for row in db.execute('SELECT * FROM peer_outbox ORDER BY device_identity,gateway_id')]
