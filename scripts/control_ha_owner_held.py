"""Held synthetic SQLite/PG pair; native and launch domains must be held by the caller."""
from contextlib import ExitStack, closing
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import stat
import time

from control.capture_native import fingerprint, require
from control.friends.pseudonyms import Aliases
from scripts.control_ha_installed_inventory import Reader
from scripts import control_ha_owner_capture as legacy


class HeldSynthetic:
    def __init__(self, root, aliases, collector_aliases, key, projections, operation, *, store_uid=None):
        self.root, self.aliases = Path(root), Path(aliases)
        self.collector_aliases, self.key = Path(collector_aliases), Path(key)
        self.projections = {name: Path(value) for name, value in projections.items()}
        require(set(self.projections) == {'support-bindings', 'subscriptions'}, 'OWNER_PROJECTION_COVERAGE')
        self.operation = operation
        self.store_uid = os.getuid() if store_uid is None else store_uid
        require(type(self.store_uid) is int and self.store_uid >= 0, 'OWNER_STORE_UID')
        self.attempted = self.active = False
        self.stack = ExitStack()

    def __enter__(self):
        require(not self.attempted, 'OWNER_NO_REACQUIRE')
        self.attempted = True
        try:
            self.reader = Reader()
            path = self.root / 'registry.sqlite3'
            require(set(item.name for item in self.root.iterdir()) == {'registry.sqlite3', 'seed.lock'},
                    'OWNER_SIDECAR_OR_INCOMPLETE_SEED')
            for target, mode in ((self.root, 0o700), (path, 0o600)):
                info = target.stat()
                require(info.st_uid == self.store_uid and stat.S_IMODE(info.st_mode) == mode,
                        'OWNER_PRIVATE_STORE')
            require(512 <= path.stat().st_size <= legacy.LIMIT, 'OWNER_STORE_BOUNDS')
            raw = self.reader.raw(path)
            require(raw[:16] == b'SQLite format 3\x00' and raw[18:20] == b'\x01\x01', 'OWNER_ROLLBACK_JOURNAL')
            self.seed = self.stack.enter_context(self.reader.opened(self.root / 'seed.lock'))
            info = os.fstat(self.seed)
            require(stat.S_ISREG(info.st_mode) and info.st_size == 0 and info.st_uid == self.store_uid and
                    not stat.S_IMODE(info.st_mode) & 0o022, 'OWNER_SEED_LOCK')
            fcntl.flock(self.seed, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.connection = self.stack.enter_context(closing(sqlite3.connect(
                path.as_uri() + '?mode=rw', uri=True, timeout=0, isolation_level=None)))
            self.connection.setconfig(sqlite3.SQLITE_DBCONFIG_NO_CKPT_ON_CLOSE, True)
            self.connection.execute('PRAGMA trusted_schema=OFF')
            self.connection.execute('BEGIN IMMEDIATE')
            self.stack.callback(self.connection.rollback)
            require(self.connection.execute('PRAGMA journal_mode').fetchone() == ('delete',), 'OWNER_JOURNAL_CHANGED')
            require(legacy.digest(legacy.encoded(self.connection.execute(legacy.SCHEMA_QUERY).fetchall())) ==
                    legacy.SCHEMA, 'OWNER_SCHEMA')
            self.alias_raw = self.reader.raw(self.aliases)
            self.collector_raw = self.reader.raw(self.collector_aliases)
            self.key_raw = self.reader.raw(self.key)
            alias = Aliases(json.loads(self.alias_raw))
            require(alias.document == json.loads(self.collector_raw), 'OWNER_ALIASES_DISAGREE')
            alias.check_key(self.key_raw)
            self.generation = alias.generation
            self.projection_raw = {name: self.reader.raw(path) for name, path in self.projections.items()}
            for raw in self.projection_raw.values():
                value = json.loads(raw)
                require(type(value) is dict and type(value.get('expires_at')) is int,
                        'OWNER_PROJECTION_EXPIRY')
            self.active = True
            self.connection.set_authorizer(self.authorize)
            self.sqlite_hash = hashlib.sha256(self.connection.serialize()).hexdigest()
            self.lease = fingerprint(dict(operation=self.operation, generation=self.generation,
                sqlite=self.sqlite_hash, seed=[info.st_dev, info.st_ino], aliases=legacy.digest(self.alias_raw)))
            self.check()
            return self
        except BaseException as error:
            self.active = False
            try:
                self.stack.close()
            except Exception as cleanup:
                error.add_note('OWNER_STORE_CLEANUP_' + type(cleanup).__name__)
            raise

    def authorize(self, action, first, second, database, trigger):
        if action in (sqlite3.SQLITE_TRANSACTION, sqlite3.SQLITE_SAVEPOINT):
            self.active = False
        return sqlite3.SQLITE_OK

    def check(self):
        try:
            require(self.active and self.connection.in_transaction, 'OWNER_SQLITE_LEASE_LOST')
            require(' FLOCK ' in Path(f'/proc/self/fdinfo/{self.seed}').read_text(), 'OWNER_SEED_LEASE_LOST')
            self.reader.verify()
            require(set(item.name for item in self.root.iterdir()) == {'registry.sqlite3', 'seed.lock'} and
                    hashlib.sha256(self.connection.serialize()).hexdigest() == self.sqlite_hash,
                    'OWNER_STORE_CHANGED')
            return self.lease
        except BaseException:
            self.active = False
            raise

    def snapshot(self, postgres, native, *, support_snapshot_sha256):
        from control_plane.fc_control_plane.capture_pg_boundary import PostgresBoundary
        from control.capture_native import ReadOnlyTrees
        require(isinstance(postgres, PostgresBoundary) and isinstance(native, ReadOnlyTrees), 'OWNER_PHYSICAL_PAIR')
        require(len(support_snapshot_sha256) == 64 and all(value in '0123456789abcdef'
                for value in support_snapshot_sha256), 'OWNER_STOPPED_SUPPORT_BINDING')
        require(all(any(path == root or root in path.parents for root in native.roots)
                    for path in (self.root, self.aliases.parent, self.collector_aliases.parent,
                                 self.key.parent, *(path.parent for path in self.projections.values()))),
                'OWNER_NATIVE_COVERAGE')
        pair = dict(sqlite=self.check(), postgres=postgres.check(), native=native.check())
        operation_rows = postgres.connection.execute('SELECT COALESCE(jsonb_agg(to_jsonb(record) ORDER BY id), '
            "'[]'::jsonb)::text FROM public.console_operationrequest AS record").fetchone()[0].encode()
        files = {'synthetic.sqlite': self.connection.serialize(), 'panel-aliases.json': self.alias_raw,
                 'collector-aliases.json': self.collector_raw, 'inventory-hmac.key': self.key_raw,
                 'pg-operation-history.json': operation_rows,
                 **{name + '.json': raw for name, raw in self.projection_raw.items()}}
        require(pair == dict(sqlite=self.check(), postgres=postgres.check(), native=native.check()),
                'OWNER_PAIR_LOST')
        receipt = dict(purpose='family-connect/owner-held-pair/v1', operation=self.operation, leases=pair,
            stopped_support_sha256=support_snapshot_sha256, alias_generation=self.generation,
            store_uid=self.store_uid,
            stopped_support_reader_verified=False,
            files={name: hashlib.sha256(raw).hexdigest() for name, raw in files.items()},
            pg_pair_fence=True, captured_at_ns=time.time_ns(),
            projections='EVIDENCE_ONLY_KEEP_ORIGINAL_EXPIRY_REFRESH_FROM_CURRENT_AUTHORITY',
            operation_history='PRESERVE_UNKNOWN_RECONCILE_EVENT_ID_AND_PAYLOAD_BEFORE_DISPATCH',
            fleet_capture=False)
        return files, receipt

    def __exit__(self, error_type, error, traceback):
        self.active = False
        self.key_raw = None
        try:
            self.stack.close()
        except Exception as cleanup:
            if error is None:
                raise
            error.add_note('OWNER_STORE_CLEANUP_' + type(cleanup).__name__)
