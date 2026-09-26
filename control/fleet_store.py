"""Single-host fleet leases. Local POSIX storage; no production DB migration.

Trusted callers synchronize public access grants and authenticated observations.
SQLite serializes capacity/IP decisions with revocation. Network provisioning and
signing are deliberately outside this module; worker receipts require a remote
fencing/quiescence contract before they may release an address for reuse.
"""
from contextlib import closing, contextmanager
from dataclasses import dataclass
import hashlib
import ipaddress
import json
import os
import re
import sqlite3
import time
import uuid

from control.fleet import Gateway, load_registry, rank_gateways, validate_update
from device_identity.device import _decode
from provisioning.cache import ProvisioningCache
from provisioning.envelope import public_identity


class LeaseRejected(ValueError):
    """Fixed code only; do not include device credentials or raw database rows."""


@dataclass(frozen=True)
class Lease:
    lease_id: str
    device: str
    gateway_id: str
    country: str
    transport: str
    version: str
    address: str
    registry_revision: int
    access_revision: int
    created_at: int
    expires_at: int
    state: str
    generation: int


@dataclass(frozen=True)
class LeaseWork:
    lease: Lease
    gateway: Gateway
    public: str
    wg: str


PUBLICATION_SCHEMA = '''
CREATE TABLE publication_authority (id INTEGER PRIMARY KEY CHECK(id=1), public TEXT NOT NULL);
CREATE TABLE publication_counters (device TEXT PRIMARY KEY REFERENCES access(device), revision INTEGER NOT NULL);
CREATE TABLE publications (lease_id TEXT NOT NULL REFERENCES leases(lease_id), access_revision INTEGER NOT NULL,
    revision INTEGER NOT NULL, signer TEXT NOT NULL, policy_digest TEXT NOT NULL, previous_hash TEXT, envelope BLOB NOT NULL,
    PRIMARY KEY(lease_id,access_revision));
'''

SERVICE_SCHEMA = '''
CREATE TABLE challenges (nonce TEXT PRIMARY KEY, device TEXT NOT NULL REFERENCES access(device),
    revision INTEGER NOT NULL, request TEXT NOT NULL, expires_at INTEGER NOT NULL);
CREATE INDEX challenge_device ON challenges(device);
CREATE TABLE jobs (lease_id TEXT NOT NULL REFERENCES leases(lease_id), generation INTEGER NOT NULL,
    token TEXT NOT NULL, claim_until INTEGER NOT NULL, attempts INTEGER NOT NULL,
    next_at INTEGER NOT NULL, result TEXT NOT NULL, PRIMARY KEY(lease_id,generation));
'''

SCHEMA = '''
CREATE TABLE metadata (id INTEGER PRIMARY KEY CHECK(id=1), schema_version INTEGER NOT NULL,
    last_now INTEGER NOT NULL);
CREATE TABLE registries (revision INTEGER PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE access (device TEXT PRIMARY KEY, public TEXT UNIQUE NOT NULL, wg TEXT UNIQUE NOT NULL,
    revision INTEGER NOT NULL, expires_at INTEGER NOT NULL, max_leases INTEGER NOT NULL,
    revoked INTEGER NOT NULL CHECK(revoked IN (0,1)));
CREATE TABLE leases (lease_id TEXT PRIMARY KEY, device TEXT NOT NULL REFERENCES access(device),
    gateway_id TEXT NOT NULL, country TEXT NOT NULL, transport TEXT NOT NULL, version TEXT NOT NULL,
    address TEXT NOT NULL, registry_revision INTEGER NOT NULL REFERENCES registries(revision),
    access_revision INTEGER NOT NULL, created_at INTEGER NOT NULL, expires_at INTEGER NOT NULL,
    state TEXT NOT NULL CHECK(state IN ('reserved','ready','retiring','released')),
    generation INTEGER NOT NULL CHECK(generation>0));
CREATE UNIQUE INDEX live_address ON leases(gateway_id,address) WHERE state!='released';
CREATE UNIQUE INDEX live_device_gateway ON leases(device,gateway_id) WHERE state!='released';
CREATE UNIQUE INDEX live_scope ON leases(device,country,transport,version) WHERE state!='released';
CREATE TABLE requests (device TEXT NOT NULL REFERENCES access(device), request_id TEXT NOT NULL,
    fingerprint TEXT NOT NULL, lease_id TEXT NOT NULL REFERENCES leases(lease_id),
    PRIMARY KEY(device,request_id));
CREATE TABLE events (id INTEGER PRIMARY KEY, observed_at INTEGER NOT NULL,
    kind TEXT NOT NULL, subject TEXT NOT NULL);
'''


def positive(value, maximum=2**63-1):
    if type(value) is not int or not 1 <= value <= maximum:
        raise LeaseRejected('invalid-integer')
    return value


class FleetStore:
    def __init__(self, path, *, clock=lambda: int(time.time())):
        self.files = ProvisioningCache(path, None)
        self.clock = clock

    def initialize(self, registry):
        # An existing/partial directory is never silently reinitialized.
        registry = load_registry(registry.model_dump_json().encode())
        self.files.path.mkdir(mode=0o700)
        fd = os.open(self.files.path / 'fleet.db', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.close(fd)
        with self._transaction(initializing=True) as (db, now):
            for statement in (SCHEMA + SERVICE_SCHEMA + PUBLICATION_SCHEMA).split(';'):
                if statement.strip():
                    db.execute(statement)
            db.execute('INSERT INTO metadata VALUES(1,3,?)', (now,))
            db.execute('INSERT INTO registries VALUES(?,?)', (registry.revision, registry.model_dump_json()))
            self._event(db, now, 'registry', str(registry.revision))
        with self.files._locked() as directory:
            os.fsync(directory)

    @contextmanager
    def _transaction(self, *, initializing=False, migrating=False):
        with self.files._locked() as directory:
            fd = os.open('fleet.db', os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
            try:
                self.files._safe(fd)
            finally:
                os.close(fd)
            uri = (self.files.path / 'fleet.db').absolute().as_uri() + '?mode=rw'
            with closing(sqlite3.connect(uri, uri=True, timeout=15)) as db, db:
                db.row_factory = sqlite3.Row
                db.execute('PRAGMA foreign_keys=ON')
                db.execute('PRAGMA synchronous=FULL')
                db.execute('BEGIN IMMEDIATE')
                now = self.clock()
                if type(now) is not int or not 0 <= now < 2**63:
                    raise LeaseRejected('invalid-clock')
                if not initializing:
                    row = db.execute('SELECT schema_version,last_now FROM metadata WHERE id=1').fetchone()
                    if row is None or row['schema_version'] not in ((1, 2, 3) if migrating else (3,)) or now < row['last_now']:
                        raise LeaseRejected('state-or-clock')
                    db.execute('UPDATE metadata SET last_now=? WHERE id=1', (now,))
                yield db, now

    @staticmethod
    def _event(db, now, kind, subject):
        db.execute('INSERT INTO events(observed_at,kind,subject) VALUES(?,?,?)', (now, kind, subject))

    @staticmethod
    def _registry(db):
        row = db.execute('SELECT value FROM registries ORDER BY revision DESC LIMIT 1').fetchone()
        if row is None:
            raise LeaseRejected('registry-missing')
        return load_registry(row['value'].encode())

    @staticmethod
    def _lease(db, lease_id):
        row = db.execute('SELECT * FROM leases WHERE lease_id=?', (lease_id,)).fetchone()
        if row is None:
            raise LeaseRejected('lease-missing')
        return Lease(**dict(row))

    @staticmethod
    def _authorized(db, device, now):
        row = db.execute('SELECT * FROM access WHERE device=?', (device,)).fetchone()
        if row is None or row['revoked'] or row['expires_at'] <= now:
            raise LeaseRejected('access-denied')
        return row

    def install_registry(self, candidate):
        candidate = load_registry(candidate.model_dump_json().encode())
        with self._transaction() as (db, now):
            previous = self._registry(db)
            if candidate == previous:
                return  # Lost response retry, not a rollback or replacement.
            validate_update(previous, candidate)
            before = {g.gateway_id: g for g in previous.gateways}
            for node in candidate.gateways:
                old = before.get(node.gateway_id)
                if old and node.endpoints != old.endpoints:
                    if db.execute("SELECT 1 FROM leases WHERE gateway_id=? AND state!='released' LIMIT 1",
                                  (node.gateway_id,)).fetchone():
                        raise LeaseRejected('endpoint-migration-required')
                if old and node.state in ('disabled', 'provisioning'):
                    for row in db.execute("SELECT lease_id FROM leases WHERE gateway_id=? AND state IN ('reserved','ready')",
                                          (node.gateway_id,)).fetchall():
                        self._retire(db, row['lease_id'], now)
            db.execute('INSERT INTO registries VALUES(?,?)', (candidate.revision, candidate.model_dump_json()))
            self._event(db, now, 'registry', str(candidate.revision))

    def set_access(self, *, device, public, wg, revision, expires_at, max_leases, revoked=False):
        """Trusted access synchronizer, not an enrollment endpoint or proof verifier.

        Versions are monotonic; public identity/WG binding cannot be replaced.
        Revocation and all retiring intents are committed in one transaction.
        """
        positive(revision); positive(expires_at); positive(max_leases, 8)
        if type(revoked) is not bool:
            raise LeaseRejected('invalid-revoke')
        raw = _decode(public, 64)
        wg_bytes = _decode(wg, 32)
        if public_identity(raw).hash.hex() != device or wg_bytes == bytes(32):
            raise LeaseRejected('binding-mismatch')
        values = (public, wg, revision, expires_at, max_leases, int(revoked))
        with self._transaction() as (db, now):
            old = db.execute('SELECT public,wg,revision,expires_at,max_leases,revoked FROM access WHERE device=?',
                             (device,)).fetchone()
            if old is not None:
                if tuple(old) == values:
                    return
                if old['public'] != public or old['wg'] != wg or revision <= old['revision']:
                    raise LeaseRejected('access-revision-or-binding')
            if expires_at <= now and not revoked:
                raise LeaseRejected('expired-access')
            db.execute('INSERT INTO access VALUES(?,?,?,?,?,?,?) ON CONFLICT(device) DO UPDATE SET '
                       'revision=excluded.revision,expires_at=excluded.expires_at,max_leases=excluded.max_leases,'
                       'revoked=excluded.revoked', (device, *values))
            for row in db.execute("SELECT lease_id,expires_at FROM leases WHERE device=? AND state IN ('reserved','ready')",
                                  (device,)).fetchall():
                if revoked or row['expires_at'] > expires_at:
                    self._retire(db, row['lease_id'], now)
            self._event(db, now, 'access-revoked' if revoked else 'access', device)

    def reserve(self, *, device, request_id, registry_revision, country, transport, version,
                lifetime, observations, address_families=(4,)):
        """Trusted internal API. Public callers must use FleetAccess.complete()."""
        with self._transaction() as (db, now):
            return self._reserve(db, now, device=device, request_id=request_id,
                registry_revision=registry_revision, country=country, transport=transport,
                version=version, lifetime=lifetime, observations=observations,
                address_families=address_families)

    def _reserve(self, db, now, *, device, request_id, registry_revision, country, transport, version,
                lifetime, observations, address_families=(4,)):
        positive(registry_revision); positive(lifetime, 86400)
        if (type(request_id) is not str or re.fullmatch(r'[A-Za-z0-9_-]{1,64}', request_id) is None
                or type(country) is not str or re.fullmatch(r'[a-z]{2}', country) is None
                or transport not in ('wireguard', 'amneziawg', 'vless-reality')
                or version not in ({'2.0', '3.1'} if transport == 'amneziawg' else {'1'})
                or type(address_families) is not tuple or not address_families
                or any(type(v) is not int or v not in (4, 6) for v in address_families)):
            raise LeaseRejected('invalid-request')
        fingerprint = hashlib.sha256(json.dumps([country, transport, version, lifetime,
            sorted(set(address_families))], separators=(',', ':')).encode()).hexdigest()
        access = self._authorized(db, device, now)
        prior = db.execute('SELECT fingerprint,lease_id FROM requests WHERE device=? AND request_id=?',
                           (device, request_id)).fetchone()
        if prior:
            if prior['fingerprint'] != fingerprint:
                raise LeaseRejected('request-conflict')
            # Historical result never renews or resurrects a retired lease.
            return self._lease(db, prior['lease_id'])
        registry = self._registry(db)
        if registry.revision != registry_revision:
            raise LeaseRejected('registry-stale')
        existing = db.execute("SELECT * FROM leases WHERE device=? AND state!='released'", (device,)).fetchall()
        if any((r['country'], r['transport'], r['version']) == (country, transport, version) for r in existing):
            raise LeaseRejected('assignment-exists')
        if len(existing) >= access['max_leases']:
            raise LeaseRejected('device-limit')
        counts = dict(db.execute("SELECT gateway_id,COUNT(*) FROM leases WHERE state!='released' GROUP BY gateway_id"))
        # The store must be the sole allocator after importing ALL existing
        # assignments. Counts from two snapshots of that same population use
        # max(), not sum(); unmanaged peers require reconciliation first.
        # Stale low collector counts cannot override durable reservations.
        samples = [sample.model_copy(update={'allocated_devices': max(sample.allocated_devices,
                    counts.get(sample.gateway_id, 0))}) for sample in observations]
        candidates = rank_gateways(registry, samples, device=device, country=country, transport=transport,
                                   version=version, now=now, address_families=address_families)
        nodes = {g.gateway_id: g for g in registry.gateways}
        used_gateways = {r['gateway_id'] for r in existing}
        for gateway_id in candidates:
            node = nodes[gateway_id]
            if gateway_id in used_gateways or counts.get(gateway_id, 0) >= node.max_devices:
                continue
            pool = ipaddress.ip_network(node.tunnel_pool)
            used = {r[0] for r in db.execute("SELECT address FROM leases WHERE gateway_id=? AND state!='released'",
                                            (gateway_id,))}
            address = next((str(ipaddress.IPv4Address(n)) + '/32' for n in
                range(int(pool.network_address) + 2, int(pool.broadcast_address))
                if str(ipaddress.IPv4Address(n)) + '/32' not in used), None)
            if address is None:
                continue
            lease_id = uuid.uuid4().hex
            db.execute('INSERT INTO leases VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',
                (lease_id, device, gateway_id, country, transport, version, address, registry.revision,
                 access['revision'], now, min(now + lifetime, access['expires_at']), 'reserved', 1))
            db.execute('INSERT INTO requests VALUES(?,?,?,?)', (device, request_id, fingerprint, lease_id))
            self._event(db, now, 'reserved', lease_id)
            return self._lease(db, lease_id)
        raise LeaseRejected('no-capacity')

    def get(self, lease_id):
        with self._transaction() as (db, _):
            return self._lease(db, lease_id)

    def pending(self, *, limit=100):
        """Durable work discovery after restart. This is not a worker claim."""
        positive(limit, 1000)
        with self._transaction() as (db, _):
            return [Lease(**dict(row)) for row in db.execute(
                "SELECT * FROM leases WHERE state IN ('reserved','retiring') "
                "ORDER BY CASE state WHEN 'retiring' THEN 0 ELSE 1 END,created_at,lease_id LIMIT ?", (limit,))]

    def work_item(self, lease_id, *, generation):
        """Original gateway snapshot/public binding for a trusted fenced worker.

        Authorization is checked again before preparing an install. A removal
        remains possible after revoke/expiry. Neither this read nor pending()
        serializes remote effects or authorizes an arbitrary endpoint from a client.
        """
        positive(generation)
        with self._transaction() as (db, now):
            lease = self._lease(db, lease_id)
            if lease.generation != generation or lease.state not in ('reserved', 'retiring'):
                raise LeaseRejected('stale-work')
            binding = db.execute('SELECT public,wg FROM access WHERE device=?', (lease.device,)).fetchone()
            if lease.state == 'reserved':
                self._authorized(db, lease.device, now)
                if lease.expires_at <= now:
                    raise LeaseRejected('expired-work')
            row = db.execute('SELECT value FROM registries WHERE revision=?', (lease.registry_revision,)).fetchone()
            registry = load_registry(row['value'].encode())
            gateway = next(g for g in registry.gateways if g.gateway_id == lease.gateway_id)
            return LeaseWork(lease, gateway, binding['public'], binding['wg'])

    def mark_ready(self, lease_id, *, generation):
        """Trusted reconciler receipt; never accept this from a client ACK."""
        positive(generation)
        with self._transaction() as (db, now):
            lease = self._lease(db, lease_id)
            self._authorized(db, lease.device, now)
            if lease.generation != generation or lease.state not in ('reserved', 'ready') or lease.expires_at <= now:
                raise LeaseRejected('stale-ready')
            if lease.state != 'ready':
                db.execute("UPDATE leases SET state='ready' WHERE lease_id=?", (lease_id,))
                self._event(db, now, 'ready', lease_id)
            return self._lease(db, lease_id)

    def publishable(self, lease_id):
        """Point-in-time eligibility, not an atomic publication or signing permit."""
        with self._transaction() as (db, now):
            lease = self._lease(db, lease_id)
            self._authorized(db, lease.device, now)
            if lease.state != 'ready' or lease.expires_at <= now:
                raise LeaseRejected('not-ready')
            return lease

    def _retire(self, db, lease_id, now):
        lease = self._lease(db, lease_id)
        if lease.state in ('reserved', 'ready'):
            db.execute("UPDATE leases SET state='retiring',generation=generation+1 WHERE lease_id=?", (lease_id,))
            self._event(db, now, 'retiring', lease_id)
        return self._lease(db, lease_id)

    def retire(self, lease_id):
        with self._transaction() as (db, now):
            return self._retire(db, lease_id, now)

    def expire(self, *, limit=1000):
        """Expiry schedules removal. It never frees addresses or capacity."""
        positive(limit, 1000)
        with self._transaction() as (db, now):
            rows = db.execute("SELECT l.lease_id FROM leases l JOIN access a ON a.device=l.device "
                "WHERE l.state IN ('reserved','ready') AND (l.expires_at<=? OR a.expires_at<=? OR a.revoked=1) ORDER BY l.expires_at,l.lease_id LIMIT ?",
                (now, now, limit)).fetchall()
            return [self._retire(db, row['lease_id'], now) for row in rows]

    def confirm_removed(self, lease_id, *, generation):
        """Worker guarantees no older remote apply can reappear after this receipt.

        Local generation checks reject delayed receipts, but cannot fence remote
        commands. A future adapter must implement that guarantee before use live.
        """
        positive(generation)
        with self._transaction() as (db, now):
            lease = self._lease(db, lease_id)
            if lease.generation != generation or lease.state not in ('retiring', 'released'):
                raise LeaseRejected('stale-removal')
            if lease.state == 'retiring':
                db.execute("UPDATE leases SET state='released' WHERE lease_id=?", (lease_id,))
                self._event(db, now, 'released', lease_id)
            return self._lease(db, lease_id)

    def upgrade_services(self):
        """Explicit v1/v2 -> v3 migration with writers stopped; no auto-upgrade."""
        with self._transaction(migrating=True) as (db, now):
            version = db.execute('SELECT schema_version FROM metadata WHERE id=1').fetchone()[0]
            if version == 3:
                return
            schema = (SERVICE_SCHEMA if version == 1 else '') + PUBLICATION_SCHEMA
            for statement in schema.split(';'):
                if statement.strip():
                    db.execute(statement)
            db.execute('UPDATE metadata SET schema_version=3 WHERE id=1')
            self._event(db, now, 'schema', '3')

    def pin_publication_authority(self, public):
        """Explicit trusted operator action. Rotation needs a separate migration."""
        _decode(public, 32)
        with self._transaction() as (db, now):
            old = db.execute('SELECT public FROM publication_authority WHERE id=1').fetchone()
            if old:
                if old['public'] != public:
                    raise LeaseRejected('authority-migration-required')
                return
            db.execute('INSERT INTO publication_authority VALUES(1,?)', (public,))
            self._event(db, now, 'publication-authority', '1')

    def claim_work(self, *, hold=60):
        """One durable claim. Remote fencing remains necessary after claim expiry."""
        positive(hold, 300)
        with self._transaction() as (db, now):
            row = db.execute("SELECT l.* FROM leases l LEFT JOIN jobs j ON "
                "j.lease_id=l.lease_id AND j.generation=l.generation "
                "WHERE l.state IN ('reserved','retiring') AND "
                "(j.lease_id IS NULL OR (j.claim_until<=? AND j.next_at<=?)) "
                "ORDER BY CASE l.state WHEN 'retiring' THEN 0 ELSE 1 END,"
                "COALESCE(j.next_at,0),l.created_at,l.lease_id LIMIT 1", (now, now)).fetchone()
            if row is None:
                return None
            lease = Lease(**dict(row))
            token = uuid.uuid4().hex
            db.execute("INSERT INTO jobs VALUES(?,?,?,?,?,?,?) ON CONFLICT(lease_id,generation) "
                "DO UPDATE SET token=excluded.token,claim_until=excluded.claim_until,"
                "attempts=MIN(jobs.attempts+1,16),result='running'",
                (lease.lease_id, lease.generation, token, now+hold, 1, now, 'running'))
            return lease, token

    def finish_work(self, lease, token, result):
        if result not in ('ready', 'released', 'retry', 'state-changed'):
            raise LeaseRejected('invalid-job-result')
        with self._transaction() as (db, now):
            row = db.execute('SELECT attempts FROM jobs WHERE lease_id=? AND generation=? AND token=?',
                             (lease.lease_id, lease.generation, token)).fetchone()
            if row is None:
                return False
            delay = min(300, 5 * 2**(row['attempts']-1))
            db.execute('UPDATE jobs SET claim_until=0,next_at=?,result=? WHERE lease_id=? AND generation=? AND token=?',
                       (now+delay, result, lease.lease_id, lease.generation, token))
            return True

    def published(self, lease_id, *, device):
        """Authorized ciphertext retrieval without any signing key; no HTTP API."""
        with self._transaction() as (db, now):
            access = self._authorized(db, device, now)
            lease = self._lease(db, lease_id)
            if lease.device != device or lease.state != 'ready' or lease.expires_at <= now:
                raise LeaseRejected('not-publishable')
            row = db.execute('SELECT p.envelope FROM publications p JOIN publication_authority a '
                'ON a.id=1 AND a.public=p.signer WHERE p.lease_id=? AND p.access_revision=?',
                (lease_id, access['revision'])).fetchone()
            if row is None:
                raise LeaseRejected('not-published')
            return bytes(row['envelope'])
