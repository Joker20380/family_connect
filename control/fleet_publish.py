"""Offline-only, local atomic issuer. No network I/O or private device keys.

Uses the existing offline Ed25519 authority. Never import/call this from the
online worker/relay. Public delivery and independent offline transfer are separate.
"""
import base64
import hashlib
import json
import time

from control.fleet import load_registry
from control.fleet_store import LeaseRejected, positive
from provisioning.fleet import ProfileBinding
from provisioning.configuration import ControlConfiguration, ControlGateway, TransportProfile, LOCAL_KEY, AUDIENCE, issue_config


class FleetPublisher:
    def __init__(self, store, *, signer, bindings, monotonic=time.monotonic):
        self.store, self.signer, self.monotonic = store, signer, monotonic
        self.public = base64.b64encode(signer.public_key().public_bytes_raw()).decode()
        # Clone/revalidate mutable nested parameters; caller cannot mutate pins.
        self.bindings = {key: ProfileBinding.model_validate_json(value.model_dump_json())
                         for key, value in bindings.items()}

    def publish(self, lease_id, *, device, previous_config_hash, min_client_version):
        started = self.monotonic()
        with self.store._transaction() as (db, now):
            lease = self.store._lease(db, lease_id)
            access = self.store._authorized(db, device, now)
            if lease.device != device or lease.state != 'ready' or lease.expires_at <= now:
                raise LeaseRejected('not-publishable')
            authority = db.execute('SELECT public FROM publication_authority WHERE id=1').fetchone()
            if authority is None or authority['public'] != self.public:
                raise LeaseRejected('publication-authority')
            profile = self.bindings[lease.gateway_id, lease.transport, lease.version]
            if (profile.transport, profile.version) != (lease.transport, lease.version):
                raise LeaseRejected('profile-binding')
            digest = hashlib.sha256(json.dumps(dict(profile=profile.model_dump(mode='json'), minimum=min_client_version), sort_keys=True,
                                               separators=(',', ':')).encode()).hexdigest()
            old = db.execute('SELECT * FROM publications WHERE lease_id=? ORDER BY revision DESC LIMIT 1', (lease_id,)).fetchone()
            if old and (old['policy_digest'] != digest or old['signer'] != self.public):
                raise LeaseRejected('profile-migration-required')
            if old and old['access_revision'] == access['revision']:
                if old['previous_hash'] != previous_config_hash:
                    raise LeaseRejected('publication-context')
                return bytes(old['envelope'])
            registry = load_registry(db.execute('SELECT value FROM registries WHERE revision=?',
                                               (lease.registry_revision,)).fetchone()[0].encode())
            gateway = next(g for g in registry.gateways if g.gateway_id == lease.gateway_id)
            endpoints = [e for e in gateway.endpoints if (e.transport,e.version)==(lease.transport,lease.version)]
            if len(endpoints) != 1:
                raise LeaseRejected('ambiguous-endpoint')
            endpoint = endpoints[0]
            counter = db.execute('SELECT revision FROM publication_counters WHERE device=?', (device,)).fetchone()
            revision = positive((counter[0] if counter else 0)+1)
            host = '['+endpoint.address+']' if ':' in endpoint.address else endpoint.address
            config = ('[Interface]\nPrivateKey = '+LOCAL_KEY+'\nAddress = '+lease.address+
                '\nDNS = '+', '.join(profile.dns)+'\nMTU = '+str(profile.mtu)+'\n'+
                ''.join(k+' = '+v+'\n' for k,v in sorted(profile.parameters.items()))+
                '[Peer]\nPublicKey = '+profile.server_public+'\nEndpoint = '+host+':'+str(endpoint.port)+
                '\nAllowedIPs = 0.0.0.0/0, ::/0\nPersistentKeepalive = 25\n')
            state = ControlConfiguration(schema_version=2, config_id=lease_id, revision=revision,
                recipient=device, audience=AUDIENCE, wireguard_public_key=access['wg'],
                min_client_version=min_client_version, previous_config_hash=previous_config_hash,
                signer_key_id=hashlib.sha256(self.signer.public_key().public_bytes_raw()).hexdigest(),
                issued_at=now, expires_at=min(lease.expires_at,access['expires_at']),
                gateways=(ControlGateway(gateway_id=lease.gateway_id, endpoint=endpoint.address,port=endpoint.port),),
                transport_profiles=(TransportProfile(profile_id=lease_id,gateway_id=lease.gateway_id,
                    transport=lease.transport,transport_version=lease.version,config=config),))
            envelope = issue_config(state, recipient_public=base64.b64decode(access['public']), signing_key=self.signer)
            # A slow signer must never commit an artifact already expired. Only
            # offline local signing is supported; blocking remote HSMs are not.
            after = self.store.clock()
            if type(after) is not int or not now <= after < state.expires_at or self.monotonic()-started > 5:
                raise LeaseRejected('publication-timeout')
            db.execute('UPDATE metadata SET last_now=? WHERE id=1', (after,))
            db.execute('INSERT INTO publication_counters VALUES(?,?) ON CONFLICT(device) DO UPDATE SET revision=excluded.revision',
                       (device,revision))
            db.execute('INSERT INTO publications VALUES(?,?,?,?,?,?,?)',
                       (lease_id, access['revision'],revision,self.public,digest,previous_config_hash,envelope))
            self.store._event(db,after,'published',lease_id)
        return envelope
