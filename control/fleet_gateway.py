"""Gateway-side durable fencing prototype for WG/AWG lease operations.

Management callers and backend are trusted. No listening server or SSH endpoint
is exposed. All managed peer effects MUST use this journal; backend children must
inherit the supplied lock FD until every side effect has finished. Restoring an
old journal or bypassing it invalidates the fence guarantee.
"""
from contextlib import closing, contextmanager
import fcntl
import hashlib
import ipaddress
import json
import os
import sqlite3
import time
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator

from control.fleet import Gateway
from provisioning.cache import ProvisioningCache
from provisioning.models import FrozenModel, GatewayCandidate, Identifier, Positive


class FenceRejected(ValueError):
    pass


class PeerCommand(FrozenModel):
    lease_id: Annotated[str, Field(pattern=r'^[0-9a-f]{32}$')]
    gateway_id: Identifier
    device: Annotated[str, Field(pattern=r'^[0-9a-f]{32}$')]
    wg: str
    address: str
    transport: Literal['wireguard', 'amneziawg']
    version: Literal['1', '2.0', '3.1']
    expires_at: Positive
    generation: Positive
    operation: Literal['present', 'absent']

    @field_validator('wg')
    @classmethod
    def valid_key(cls, value):
        return GatewayCandidate.valid_key(value)

    @field_validator('address')
    @classmethod
    def host_route(cls, value):
        ip = ipaddress.IPv4Interface(value)
        if str(ip) != value or ip.network.prefixlen != 32:
            raise ValueError('canonical IPv4 host route required')
        return value

    @model_validator(mode='after')
    def lifecycle(self):
        if self.generation != (1 if self.operation == 'present' else 2):
            raise ValueError('immutable lease lifecycle required')
        if self.version not in ({'2.0', '3.1'} if self.transport == 'amneziawg' else {'1'}):
            raise ValueError('invalid transport version')
        return self

    def canonical(self):
        return json.dumps(self.model_dump(), sort_keys=True, separators=(',', ':'))

    def binding(self):
        return json.dumps(self.model_dump(exclude={'generation', 'operation'}), sort_keys=True, separators=(',', ':'))


def receipt(command):
    return dict(lease_id=command.lease_id, gateway_id=command.gateway_id,
                generation=command.generation, operation=command.operation,
                digest=hashlib.sha256(command.canonical().encode()).hexdigest())


class FencedGateway:
    def __init__(self, path, gateway, backend, *, clock=lambda: int(time.time())):
        self.files = ProvisioningCache(path, None)
        self.gateway = Gateway.model_validate_json(gateway.model_dump_json())
        self.backend, self.clock = backend, clock

    def initialize(self):
        self.files.path.mkdir(mode=0o700)
        fd = os.open(self.files.path / 'gateway.db', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.close(fd)
        with self._gate(initializing=True) as (db, lock):
            with db:
                db.execute('CREATE TABLE metadata(id INTEGER PRIMARY KEY CHECK(id=1), schema_version INTEGER NOT NULL, '
                           'gateway TEXT NOT NULL,last_now INTEGER NOT NULL)')
                db.execute('CREATE TABLE commands(lease_id TEXT PRIMARY KEY,binding TEXT NOT NULL,command TEXT NOT NULL,'
                           'generation INTEGER NOT NULL,address TEXT NOT NULL,wg TEXT NOT NULL,'
                           'held INTEGER NOT NULL CHECK(held IN(0,1)),done INTEGER NOT NULL CHECK(done IN(0,1)))')
                db.execute('CREATE UNIQUE INDEX held_ip ON commands(address) WHERE held=1')
                db.execute('CREATE UNIQUE INDEX held_key ON commands(wg) WHERE held=1')
                db.execute('INSERT INTO metadata VALUES(1,1,?,?)', (self.gateway.model_dump_json(), self._now()))
        with self.files._locked() as directory:
            os.fsync(directory)

    def _now(self):
        value = self.clock()
        if type(value) is not int or not 0 <= value < 2**63:
            raise FenceRejected('clock')
        return value

    @contextmanager
    def _gate(self, *, initializing=False):
        with self.files._locked() as directory:
            # A separate inherited lock survives death of the parent worker.
            lock = os.open('.effects.lock', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK,
                           0o600, dir_fd=directory)
            try:
                self.files._safe(lock)
                fcntl.flock(lock, fcntl.LOCK_EX)
                fd = os.open('gateway.db', os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
                try:
                    self.files._safe(fd)
                finally:
                    os.close(fd)
                uri = (self.files.path / 'gateway.db').absolute().as_uri() + '?mode=rw'
                with closing(sqlite3.connect(uri, uri=True, timeout=15)) as db:
                    db.row_factory = sqlite3.Row
                    db.execute('PRAGMA synchronous=FULL')
                    if not initializing:
                        row = db.execute('SELECT * FROM metadata WHERE id=1').fetchone()
                        if (row is None or row['schema_version'] != 1 or self._now() < row['last_now']
                                or row['gateway'] != self.gateway.model_dump_json()):
                            raise FenceRejected('gateway-state')
                    yield db, lock
            finally:
                # Do NOT explicitly LOCK_UN: children share this open description.
                os.close(lock)

    def execute(self, command, *, _restore=False):
        # Revalidate actual field types; typed JSON serialization can normalize
        # a malformed model_copy value (e.g. bool in an integer field).
        command = PeerCommand.model_validate({name: getattr(command, name) for name in PeerCommand.model_fields})
        pool = ipaddress.IPv4Network(self.gateway.tunnel_pool)
        ip = ipaddress.IPv4Interface(command.address).ip
        if (command.gateway_id != self.gateway.gateway_id or ip not in pool
                or ip in (pool.network_address, pool.network_address + 1, pool.broadcast_address)
                or not any((e.transport, e.version) == (command.transport, command.version)
                           for e in self.gateway.endpoints)):
            raise FenceRejected('gateway-binding')
        with self._gate() as (db, lock):
            old = db.execute('SELECT * FROM commands WHERE lease_id=?', (command.lease_id,)).fetchone()
            if old and (old['binding'] != command.binding() or old['generation'] > command.generation):
                raise FenceRejected('stale-or-conflicting-command')
            if command.operation == 'present' and command.expires_at <= self._now():
                raise FenceRejected('expired-command')
            if old and old['generation'] == command.generation:
                if old['command'] != command.canonical():
                    raise FenceRejected('command-conflict')
                if old['done'] and not (_restore and command.operation == 'present'):
                    # Crucially, an old completed removal NEVER deletes a reused key.
                    return receipt(command)
            # Absent-before-present can be fenced without touching another lease's peer.
            never_installed = old is None and command.operation == 'absent'
            if old is None and command.operation == 'present':
                preflight = getattr(self.backend, 'preflight', None)
                if preflight is not None:
                    preflight(command, lock_fd=lock)
            held = int(command.operation == 'present' or (old is not None and old['held']))
            try:
                with db:
                    db.execute('BEGIN IMMEDIATE')
                    db.execute('UPDATE metadata SET last_now=? WHERE id=1', (self._now(),))
                    db.execute('INSERT INTO commands VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(lease_id) DO UPDATE SET '
                               'command=excluded.command,generation=excluded.generation,held=excluded.held,done=excluded.done',
                               (command.lease_id, command.binding(), command.canonical(), command.generation,
                                command.address, command.wg, held, int(never_installed)))
            except sqlite3.IntegrityError:
                raise FenceRejected('resource-owned') from None
            # Fence/intent is COMMITTED before an external effect can begin.
            if never_installed:
                return receipt(command)
            self.backend.ensure(command, lock_fd=lock)
            with db:
                db.execute('UPDATE commands SET done=1,held=? WHERE lease_id=?',
                           (int(command.operation == 'present'), command.lease_id))
            return receipt(command)

    def recover(self):
        """Restore desired live peers/pending removals before declaring node healthy.

        Expired installs fail closed and need a controller removal command. This
        method does not invent a lease revocation or silently erase its fence.
        """
        with self._gate() as (db, _):
            commands = [PeerCommand.model_validate_json(row[0]) for row in
                        db.execute('SELECT command FROM commands WHERE held=1 OR done=0 ORDER BY generation DESC,lease_id')]
        return [self.execute(command, _restore=True) for command in commands]
