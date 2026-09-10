"""Operator publication and transactional, authenticated delivery of immutable versions."""
import base64
import secrets

import RNS

from provisioning.auth import AUDIENCE, verify
from provisioning.envelope import ProvisioningRejected, issue
from provisioning.models import NetworkProvisioningState
from .store import EnrollmentRejected
from .gateways import GatewayReconciler


class ProvisioningService:
    def __init__(self, store):
        self.store = store

    def _authorized(self, db, identity, now):
        row = db.execute('SELECT d.public_identity, d.revoked_at, m.entitlement_id, '
                         'k.public_key, k.revoked_at AS key_revoked FROM devices d '
                         'JOIN device_entitlements m ON d.identity=m.device_identity '
                         'JOIN transport_keys k ON d.identity=k.device_identity '
                         'WHERE d.identity=? AND k.transport=?', (identity, 'wireguard')).fetchone()
        if row is None or row['revoked_at'] is not None or row['key_revoked'] is not None:
            raise ProvisioningRejected('provisioning rejected')
        try:
            entitlement = self.store._entitlement(db, row['entitlement_id'], now)
        except EnrollmentRejected:
            raise ProvisioningRejected('provisioning rejected') from None
        return row, entitlement

    def publish(self, identity, network, *, signing_identity, lease_seconds=3600):
        """Publish only after reconciliation confirmed peers on every candidate.

        Only addresses/dns/gateways are supplied. Authorization, version and lease
        always come from the database. Publication is serialized with revocation.
        """
        if (type(network) is not dict or set(network) != {'addresses', 'dns', 'gateways'} or
                type(lease_seconds) is not int or not 1 <= lease_seconds <= 86400):
            raise ValueError('invalid publication parameters')
        import json
        with self.store._transaction() as db:
            now = int(self.store.clock())
            row, entitlement = self._authorized(db, identity, now)
            previous = db.execute('SELECT MAX(revision), MAX(issued_at) FROM provisioning_versions '
                                  'WHERE device_identity=?', (identity,)).fetchone()
            if previous[1] is not None and now < previous[1]:
                raise ProvisioningRejected('server clock moved backwards')
            state = NetworkProvisioningState.model_validate_json(json.dumps(dict(
                **network, schema_version=1, revision=(previous[0] or 0) + 1, recipient=identity,
                issued_at=now, expires_at=min(now + lease_seconds, entitlement['expires_at']),
                entitlement_id=entitlement['id'], entitlement_revision=entitlement['revision'],
                wireguard_public_key=row['public_key'])))
            normalized = {key:state.model_dump(mode='json')[key] for key in ('addresses','dns','gateways')}
            deployment_expiry = GatewayReconciler.require_ready(db, identity, normalized, now)
            state = state.model_copy(update={'expires_at': min(state.expires_at, deployment_expiry)})
            envelope = issue(state, recipient_public=base64.b64decode(row['public_identity']),
                             signing_identity=signing_identity)
            db.execute('INSERT INTO provisioning_versions VALUES (?,?,?,?,?,?,?,?)',
                       (identity, state.revision, state.entitlement_id, state.entitlement_revision,
                        state.wireguard_public_key, now, state.expires_at, envelope))
            return dict(device_identity=identity, revision=state.revision, expires_at=state.expires_at)

    def challenge(self, *, public_identity, wireguard_public_key):
        try:
            self.store._public(public_identity, 64)
            self.store._public(wireguard_public_key, 32)
            public = RNS.Identity(create_keys=False)
            public.load_public_key(base64.b64decode(public_identity))
        except (ValueError, TypeError):
            raise ProvisioningRejected('provisioning rejected') from None
        with self.store._transaction() as db:
            now = int(self.store.clock())
            row, entitlement = self._authorized(db, public.hash.hex(), now)
            if row['public_identity'] != public_identity or row['public_key'] != wireguard_public_key:
                raise ProvisioningRejected('provisioning rejected')
            count = db.execute('SELECT count(*) FROM provisioning_challenges WHERE device_identity=? '
                               'AND expires_at>? AND consumed_at IS NULL',
                               (public.hash.hex(), now)).fetchone()[0]
            if count >= 16:
                raise ProvisioningRejected('provisioning rejected')
            nonce = base64.b64encode(secrets.token_bytes(32)).decode()
            expiry = min(now + 120, entitlement['expires_at'])
            db.execute('INSERT INTO provisioning_challenges VALUES (?,?,?,?,?,NULL)',
                       (self.store._hash(nonce), public.hash.hex(), public_identity,
                        wireguard_public_key, expiry))
            return dict(challenge=nonce, expires_at=expiry, audience=AUDIENCE)

    def fetch(self, proof):
        try:
            identity = verify(proof)
        except (ValueError, TypeError, KeyError):
            raise ProvisioningRejected('provisioning rejected') from None
        with self.store._transaction() as db:
            now = int(self.store.clock())
            row, entitlement = self._authorized(db, identity, now)
            nonce_hash = self.store._hash(proof['challenge'])
            challenge = db.execute('SELECT * FROM provisioning_challenges WHERE nonce_hash=?',
                                   (nonce_hash,)).fetchone()
            if (challenge is None or challenge['consumed_at'] is not None or
                    challenge['expires_at'] <= now or challenge['device_identity'] != identity or
                    challenge['public_identity'] != proof['public_identity'] or
                    challenge['wireguard_public_key'] != proof['wireguard_public_key'] or
                    row['public_identity'] != proof['public_identity'] or
                    row['public_key'] != proof['wireguard_public_key']):
                raise ProvisioningRejected('provisioning rejected')
            latest = db.execute('SELECT * FROM provisioning_versions WHERE device_identity=? '
                                'ORDER BY revision DESC LIMIT 1', (identity,)).fetchone()
            if (latest is None or not latest['issued_at'] <= now < latest['expires_at'] or
                    latest['expires_at'] > entitlement['expires_at'] or
                    latest['entitlement_id'] != entitlement['id'] or
                    latest['entitlement_revision'] != entitlement['revision'] or
                    latest['wireguard_public_key'] != row['public_key']):
                raise ProvisioningRejected('provisioning rejected')
            import json
            deployment = db.execute('SELECT network FROM peer_deployments WHERE device_identity=?', (identity,)).fetchone()
            if deployment is None:
                raise ProvisioningRejected('gateway deployment not ready')
            expiry = GatewayReconciler.require_ready(db, identity, json.loads(deployment['network']), now)
            if latest['expires_at'] > expiry:
                raise ProvisioningRejected('gateway lease too short')
            db.execute('UPDATE provisioning_challenges SET consumed_at=? WHERE nonce_hash=?',
                       (now, nonce_hash))
            return bytes(latest['envelope'])

    def versions(self, identity):
        with self.store._transaction() as db:
            return [dict(row) for row in db.execute(
                'SELECT revision, issued_at, expires_at, entitlement_revision FROM provisioning_versions '
                'WHERE device_identity=? ORDER BY revision', (identity,))]
