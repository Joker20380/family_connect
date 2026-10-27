from contextlib import contextmanager
import fcntl
import hashlib
import json
from pathlib import Path
import sqlite3
import time
import uuid

from django.conf import settings

from control.friends import paid_beta, support_ids
from control.friends.access import Access
from device_identity.device import DeviceIdentity

ROOT = settings.BASE_DIR / '.local' / 'synthetic'
FIXTURE_VERSION = 'CONTROL-PLANE-1-SYNTHETIC-v2'


class BackendError(Exception):
    pass


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def checked_path():
    path = ROOT / 'registry.sqlite3'
    if any(parent.is_symlink() for parent in (path, *path.parents)) or not path.is_file():
        raise BackendError('SYNTHETIC_FIXTURE_REQUIRED')
    return path


def guard(database, *, legacy=False):
    try:
        marker = database.execute('SELECT version FROM control_plane_fixture WHERE singleton=1').fetchone()
        count = database.execute('SELECT count(*) FROM devices').fetchone()[0]
        known = database.execute('SELECT count(*) FROM control_plane_devices').fetchone()[0]
        unexpected = database.execute('SELECT device FROM devices EXCEPT SELECT device FROM control_plane_devices').fetchone()
        version = 'CONTROL-PLANE-0-SYNTHETIC-v1' if legacy else FIXTURE_VERSION
        if marker is None or marker[0] != version or count != (12 if legacy else 50) or known != count or unexpected:
            raise BackendError('SYNTHETIC_FIXTURE_REQUIRED')
    except sqlite3.Error:
        raise BackendError('SYNTHETIC_FIXTURE_REQUIRED') from None


@contextmanager
def registry(*, write=False):
    try:
        with paid_beta.connection(checked_path(), write=write) as database:
            guard(database)
            yield database
    except paid_beta.PaidBetaError as error:
        raise BackendError(str(error)) from None
    except (sqlite3.Error, OSError):
        raise BackendError('SYNTHETIC_BACKEND_UNAVAILABLE') from None


def seed_fixture():
    if any(parent.is_symlink() for parent in (ROOT, *ROOT.parents)):
        raise BackendError('SYNTHETIC_FIXTURE_REQUIRED')
    ROOT.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (ROOT / 'seed.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if (ROOT / 'registry.sqlite3').exists():
            with paid_beta.connection(checked_path(), write=True) as database:
                marker = database.execute('SELECT version FROM control_plane_fixture WHERE singleton=1').fetchone()
                if marker and marker[0] == 'CONTROL-PLANE-0-SYNTHETIC-v1':
                    guard(database, legacy=True)
                    for number in range(13, 51):
                        identity = DeviceIdentity.generate()
                        database.execute('INSERT INTO devices(device,public,wg,tcp,revoked) VALUES (?,?,?,?,0)',
                            (identity.reference, identity.public_identity, identity.wireguard_public_key, str(uuid.uuid4())))
                        database.execute('INSERT INTO invites(hash,device,revoked) VALUES (?,?,0)',
                            (Access.code_hash(uuid.uuid4().hex), identity.reference))
                        add_member(database, identity.reference, number)
                    database.execute('UPDATE control_plane_fixture SET version=?', (FIXTURE_VERSION,))
                    database.execute("UPDATE control_plane_devices SET label=replace(label,'Synthetic ','Демо ')")
                guard(database)
            return
        temporary = ROOT / 'initializing.sqlite3'
        if temporary.exists():
            raise BackendError('INCOMPLETE_FIXTURE_REQUIRES_REVIEW')
        access = Access(temporary)
        access.initialize()
        with access.db() as database:
            paid_beta.migrate(database)
            database.execute('CREATE TABLE control_plane_fixture(singleton INTEGER PRIMARY KEY, version TEXT NOT NULL)')
            database.execute('INSERT INTO control_plane_fixture VALUES (1,?)', (FIXTURE_VERSION,))
            database.execute('CREATE TABLE control_plane_devices(device TEXT PRIMARY KEY REFERENCES devices(device), label TEXT NOT NULL)')
        for number in range(1, 51):
            identity = DeviceIdentity.generate()
            challenge = access.challenge(identity.public_identity, identity.wireguard_public_key, 'activate', access.invite())
            access.complete(identity.prove_transport_key(challenge['challenge']), 'activate')
            with access.db() as database:
                add_member(database, identity.reference, number)
        temporary.rename(ROOT / 'registry.sqlite3')


def add_member(database, device, number):
    support_ids.registered(database, device)
    database.execute('INSERT INTO control_plane_devices VALUES (?,?)', (device, f'Демо {number:02d}'))
    database.execute('UPDATE device_support SET platform=?,app_version=?,version_code=?,last_seen=? WHERE device=?',
        ('android', paid_beta.VERSION if number != 12 else '0.1.18-beta84',
         106 if number != 12 else 84, int(time.time()), device))


def members():
    with registry() as database:
        return [dict(row) for row in database.execute('SELECT device,label FROM control_plane_devices ORDER BY label')]


def selector(database, device):
    row = database.execute('SELECT s.support_id FROM device_support s JOIN control_plane_devices d ON s.device=d.device WHERE d.device=?', (device,)).fetchone()
    if row is None:
        raise BackendError('UNKNOWN_SYNTHETIC_DEVICE')
    return row[0]


def lookup(value):
    with registry() as database:
        if len(value) == 32 and all(character in '0123456789abcdef' for character in value):
            selector(database, value)
            return value
        return paid_beta.resolve_device(database, value)['device']


def snapshot(database, device, now):
    alias = selector(database, device)
    state = paid_beta.status(database, alias, now)
    observation = dict(database.execute('SELECT platform,app_version,version_code,last_seen FROM device_support WHERE device=?', (device,)).fetchone())
    cohort_size = database.execute('SELECT count(*) FROM paid_beta_subscriptions').fetchone()[0]
    binding = tuple(database.execute('SELECT * FROM devices WHERE device=?', (device,)).fetchone())
    value = dict(status=state, version_observation=observation, cohort_size=cohort_size)
    return dict(value, fingerprint=digest(dict(value, binding=binding)))


def readback(device):
    with registry() as database:
        return snapshot(database, device, int(time.time()))


def apply(database, intent, now):
    values = {name: intent[name] for name in ('period_start', 'paid_until', 'grace_until') if intent[name] is not None}
    if intent['action'] == 'activate':
        values['apk_sha256'] = paid_beta.APK_SHA256
    return paid_beta.apply_event(database, selector(database, intent['device']),
        'payment' if intent['action'] == 'activate' else intent['action'], intent['event_id'], intent['reference'], now=now, **values)


def preview(intent):
    with registry() as source:
        now = int(time.time())
        before = snapshot(source, intent['device'], now)
        memory = sqlite3.connect(':memory:', isolation_level=None)
        try:
            source.backup(memory)
            memory.row_factory = sqlite3.Row
            memory.execute('PRAGMA foreign_keys=ON')
            memory.execute('BEGIN IMMEDIATE')
            receipt = apply(memory, intent, now)
            after = snapshot(memory, intent['device'], now)
        except paid_beta.PaidBetaError as error:
            raise BackendError(str(error)) from None
        finally:
            memory.close()
    return dict(before=before, after=after, receipt=receipt, intent_hash=digest(intent),
                created_at=now, expires_at=now + 300, synthetic=True)


def execute(intent, prepared):
    with registry(write=True) as database:
        now = int(time.time())
        existing = database.execute('SELECT * FROM paid_beta_events WHERE event_id=?', (intent['event_id'],)).fetchone()
        if digest(intent) != prepared['intent_hash']:
            raise BackendError('INTENT_CHANGED')
        if existing is not None:
            if existing['payload_hash'] != prepared['receipt']['event']['payload_hash']:
                raise BackendError('EVENT_ID_CONFLICT')
            return dict(schema=1, duplicate=True, event=dict(existing))
        if now >= prepared['expires_at'] or snapshot(database, intent['device'], now)['fingerprint'] != prepared['before']['fingerprint']:
            raise BackendError('PREVIEW_STALE')
        receipt = apply(database, intent, now)
    return receipt


def reconcile(event_id, expected_hash):
    with registry() as database:
        row = database.execute('SELECT * FROM paid_beta_events WHERE event_id=?', (event_id,)).fetchone()
        if row is None:
            return None
        if row['payload_hash'] != expected_hash:
            raise BackendError('EVENT_ID_CONFLICT')
        return dict(schema=1, duplicate=True, event=dict(row))
