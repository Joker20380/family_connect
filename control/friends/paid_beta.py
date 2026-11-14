"""Explicit, bounded paid cohort layered over existing Friends admission."""
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3

from . import support_ids

PAID_ANDROID_APK_SHA256 = '144b158fe4c07dd19a67683887558cf88a0202b937d135a9924698ffc11b4fdf'
PAID_ANDROID_VERSION = '0.1.18-beta108'
PAID_ANDROID_VERSION_CODE = 108
COHORT_LIMIT = 10
MAX_TIME = 253402300799
TABLES = {'paid_beta_subscriptions', 'paid_beta_events'}
PAID_ANDROID_POLICY = 'android-paid-108-119-123-125-v1'


@dataclass(frozen=True)
class AndroidRelease:
    platform: str
    version_name: str
    version_code: int
    apk_sha256: str


LEGACY_ANDROID_RELEASE = AndroidRelease('android', PAID_ANDROID_VERSION,
                                       PAID_ANDROID_VERSION_CODE, PAID_ANDROID_APK_SHA256)
PAID_ANDROID_RELEASES = (
    LEGACY_ANDROID_RELEASE,
    AndroidRelease('android', '0.1.18-beta119', 119,
                   '52a9847b74181c48808c86a0c5bf5925b53ef498eec628aef2d78d26f1c92d2d'),
    AndroidRelease('android', '0.1.18-beta123', 123,
                   'ae011307b4afc58ea211ea6c5cd27c28bc472bda6af9b19892de400a3d3de15d'),
    AndroidRelease('android', '0.1.18-beta125', 125,
                   'f1c5bf578a5ca1e8e864a60fa9ab33249807e22c4552b5da984d126720e5740c'),
)


def policy():
    return dict(schema=1, policy=PAID_ANDROID_POLICY, cohort_limit=COHORT_LIMIT,
                releases=[asdict(release) for release in PAID_ANDROID_RELEASES])


class PaidBetaError(ValueError):
    pass


def require(condition, reason):
    if not condition:
        raise PaidBetaError(reason)


def instant(value):
    require(type(value) is int and 0 <= value <= MAX_TIME, 'INVALID_TIME')
    return value


def parse_utc(value):
    require(type(value) is str and re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z', value), 'UTC_REQUIRED')
    try:
        return instant(int(datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc).timestamp()))
    except (ValueError, OverflowError):
        raise PaidBetaError('INVALID_TIME') from None


@contextmanager
def connection(path, *, write=False):
    path = Path(path)
    require(path.is_file() and not path.is_symlink(), 'EXISTING_REGISTRY_REQUIRED')
    database = sqlite3.connect(path.resolve().as_uri() + ('?mode=rw' if write else '?mode=ro'),
                               uri=True, timeout=15, isolation_level=None)
    database.row_factory = sqlite3.Row
    try:
        database.execute('PRAGMA foreign_keys=ON')
        if write:
            database.execute('PRAGMA synchronous=FULL')
        else:
            database.execute('PRAGMA query_only=ON')
        database.execute('BEGIN IMMEDIATE' if write else 'BEGIN')
        yield database
        database.commit()
    except BaseException:
        database.rollback()
        raise
    finally:
        database.close()


def schema_present(database):
    found = {row[0] for row in database.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN (?,?)", tuple(sorted(TABLES)))}
    require(not found or found == TABLES, 'INCOMPLETE_PAID_SCHEMA')
    return bool(found)


def migrate(database):
    require(database.in_transaction, 'TRANSACTION_REQUIRED')
    require(database.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='devices'").fetchone(), 'EXISTING_REGISTRY_REQUIRED')
    database.execute('CREATE TABLE IF NOT EXISTS paid_beta_subscriptions ('
        'device TEXT PRIMARY KEY NOT NULL REFERENCES devices(device), '
        "state TEXT NOT NULL CHECK(state IN ('trial','active','grace','expired','revoked')), "
        'period_start INTEGER NOT NULL CHECK(period_start>=0), '
        'paid_until INTEGER NOT NULL CHECK(paid_until>period_start), '
        'grace_until INTEGER CHECK(grace_until IS NULL OR grace_until>=paid_until), '
        'created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL, '
        'version INTEGER NOT NULL CHECK(version>0), last_event_id TEXT NOT NULL, revoked_at INTEGER, '
        "CHECK(state!='grace' OR grace_until IS NOT NULL), "
        "CHECK((state='revoked')=(revoked_at IS NOT NULL)))")
    database.execute('CREATE TABLE IF NOT EXISTS paid_beta_events ('
        'event_id TEXT PRIMARY KEY NOT NULL, device TEXT NOT NULL REFERENCES devices(device), '
        "event_type TEXT NOT NULL CHECK(event_type IN ('payment','grace','expire','revoke')), "
        'occurred_at INTEGER NOT NULL, previous_state TEXT, new_state TEXT NOT NULL, '
        'period_start INTEGER NOT NULL, paid_until INTEGER NOT NULL, grace_until INTEGER, '
        'reference_hash TEXT NOT NULL, payload_hash TEXT NOT NULL, applied_at INTEGER NOT NULL, '
        "result TEXT NOT NULL CHECK(result='APPLIED'))")
    database.execute('CREATE TRIGGER IF NOT EXISTS paid_beta_cohort_limit BEFORE INSERT ON paid_beta_subscriptions '
        f'WHEN (SELECT count(*) FROM paid_beta_subscriptions)>={COHORT_LIMIT} '
        'AND NOT EXISTS (SELECT 1 FROM paid_beta_subscriptions WHERE device=NEW.device) '
        "BEGIN SELECT RAISE(ABORT,'PAID_COHORT_LIMIT'); END")
    database.execute('CREATE TRIGGER IF NOT EXISTS paid_beta_no_unenroll BEFORE DELETE ON paid_beta_subscriptions '
        "BEGIN SELECT RAISE(ABORT,'PAID_COHORT_RETAINED'); END")
    database.execute('CREATE TRIGGER IF NOT EXISTS paid_beta_binding BEFORE UPDATE OF device ON paid_beta_subscriptions '
        "WHEN NEW.device!=OLD.device BEGIN SELECT RAISE(ABORT,'PAID_DEVICE_IMMUTABLE'); END")
    database.execute('CREATE TRIGGER IF NOT EXISTS paid_beta_revocation_terminal BEFORE UPDATE ON paid_beta_subscriptions '
        "WHEN OLD.state='revoked' BEGIN SELECT RAISE(ABORT,'PAID_REVOKED'); END")
    for operation in ('UPDATE', 'DELETE'):
        database.execute(f'CREATE TRIGGER IF NOT EXISTS paid_beta_event_no_{operation.lower()} '
            f'BEFORE {operation} ON paid_beta_events '
            "BEGIN SELECT RAISE(ABORT,'PAID_EVENT_IMMUTABLE'); END")


@dataclass(frozen=True)
class SubscriptionState:
    state: str
    allowed: bool
    expires_at: int | None


def effective_subscription_state(database, device, now):
    instant(now)
    require(type(device) is str and re.fullmatch('[0-9a-f]{32}', device), 'INVALID_DEVICE')
    if not schema_present(database):
        return None
    row = database.execute('SELECT state,paid_until,grace_until,revoked_at FROM paid_beta_subscriptions WHERE device=?', (device,)).fetchone()
    if row is None:
        return None
    if row['state'] == 'revoked' or row['revoked_at'] is not None:
        return SubscriptionState('revoked', False, None)
    require(row['state'] in ('trial', 'active', 'grace', 'expired'), 'INVALID_SUBSCRIPTION')
    boundary = row['grace_until'] if row['state'] == 'grace' else row['paid_until']
    instant(boundary)
    if row['state'] in ('active', 'trial', 'grace') and now < boundary:
        return SubscriptionState(row['state'], True, boundary)
    return SubscriptionState('expired', False, None)


def resolve_device(database, support):
    try:
        support = support_ids.normalize(support)
    except ValueError:
        raise PaidBetaError('INVALID_SUPPORT_SELECTOR') from None
    rows = database.execute('SELECT s.device,d.revoked,i.revoked AS invite_revoked FROM device_support s '
        'JOIN devices d ON s.device=d.device LEFT JOIN invites i ON i.device=d.device WHERE s.support_id=?', (support,)).fetchall()
    require(len(rows) == 1, 'UNIQUE_EXISTING_DEVICE_REQUIRED')
    return rows[0]


def confirmed_android_release(database, device):
    support = database.execute('SELECT platform,app_version,version_code,last_seen FROM device_support WHERE device=?', (device,)).fetchone()
    require(support is not None and support['platform'] == 'android', 'ANDROID_BASELINE_REQUIRED')
    observations = []
    if support['last_seen'] is not None:
        observations.append((support['last_seen'], support['app_version'], support['version_code']))
    if database.execute("SELECT 1 FROM sqlite_master WHERE name='restricted_readiness_results'").fetchone():
        records = database.execute('SELECT ack,ack_at FROM restricted_readiness_results WHERE device=? AND ack IS NOT NULL '
            'AND ack_at=(SELECT MAX(ack_at) FROM restricted_readiness_results WHERE device=? AND ack IS NOT NULL)',
            (device, device)).fetchall()
        for record in records:
            if support['last_seen'] is not None and record['ack_at'] < support['last_seen']:
                continue
            try:
                ack = json.loads(record['ack'])
                require(type(ack) is dict, 'INVALID_VERSION_OBSERVATION')
                observations.append((record['ack_at'], ack.get('app_version'), ack.get('version_code')))
            except (ValueError, TypeError, KeyError):
                raise PaidBetaError('INVALID_VERSION_OBSERVATION') from None
    require(observations, 'ANDROID_BASELINE_REQUIRED')
    latest = max(item[0] for item in observations)
    selected = None
    for seen, version, code in observations:
        if seen != latest:
            continue
        matches = [release for release in PAID_ANDROID_RELEASES
                   if type(version) is str and type(code) is int
                   and version == release.version_name and code == release.version_code]
        require(len(matches) == 1, 'ANDROID_BASELINE_REQUIRED')
        require(selected is None or selected == matches[0], 'ANDROID_VERSION_CONFLICT')
        selected = matches[0]
    return selected


def confirm_android_baseline(database, device):
    require(confirmed_android_release(database, device) == LEGACY_ANDROID_RELEASE,
            'ANDROID_BASELINE_REQUIRED')


def status(database, support, now):
    device = resolve_device(database, support)
    effective = effective_subscription_state(database, device['device'], now)
    result = dict(schema=1, device=device['device'], activation_active=not device['revoked'] and device['invite_revoked'] == 0,
                  cohort=effective is not None, legacy_admission_unchanged=effective is None)
    if effective is not None:
        row = database.execute('SELECT * FROM paid_beta_subscriptions WHERE device=?', (device['device'],)).fetchone()
        result.update(subscription=dict(row), effective_state=effective.state,
                      paid_allow=effective.allowed, entitlement_until=effective.expires_at)
    return result


def apply_event(database, support, event_type, event_id, reference, *, now, period_start=None,
                paid_until=None, grace_until=None, apk_sha256=None):
    require(database.in_transaction, 'TRANSACTION_REQUIRED')
    require(schema_present(database), 'PAID_MIGRATION_REQUIRED')
    instant(now)
    require(event_type in ('payment', 'grace', 'expire', 'revoke'), 'INVALID_EVENT_TYPE')
    require(type(event_id) is str and re.fullmatch('[A-Za-z0-9_-]{8,128}', event_id)
            and not re.search(support_ids.PATTERN, event_id.upper()), 'OPAQUE_EVENT_ID_REQUIRED')
    require(type(reference) is str and 1 <= len(reference.encode()) <= 1024 and reference.strip(), 'REFERENCE_REQUIRED')
    if event_type == 'payment':
        instant(period_start)
        instant(paid_until)
        require(period_start < paid_until and grace_until is None
                and type(apk_sha256) is str and re.fullmatch('[0-9a-f]{64}', apk_sha256),
                'PAYMENT_BOUNDS_OR_APK_INVALID')
    elif event_type == 'grace':
        instant(grace_until)
        require(period_start is paid_until is apk_sha256 is None, 'GRACE_BOUNDS_INVALID')
    else:
        require(period_start is paid_until is grace_until is apk_sha256 is None, 'UNEXPECTED_EVENT_FIELDS')
    device = resolve_device(database, support)
    reference_hash = hashlib.sha256(reference.encode()).hexdigest()
    payload = dict(device=device['device'], event_type=event_type, event_id=event_id,
                   period_start=period_start, paid_until=paid_until, grace_until=grace_until,
                   reference_hash=reference_hash, apk_sha256=apk_sha256)
    payload_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    previous_event = database.execute('SELECT * FROM paid_beta_events WHERE event_id=?', (event_id,)).fetchone()
    if previous_event is not None:
        require(previous_event['payload_hash'] == payload_hash, 'EVENT_ID_CONFLICT')
        return dict(schema=1, duplicate=True, event=dict(previous_event))
    if event_type == 'payment':
        require(period_start <= now < paid_until, 'PAYMENT_BOUNDS_INVALID')
    if event_type == 'grace':
        require(grace_until > now, 'GRACE_BOUNDS_INVALID')
    previous = database.execute('SELECT * FROM paid_beta_subscriptions WHERE device=?', (device['device'],)).fetchone()
    effective = effective_subscription_state(database, device['device'], now)
    require(effective is None or effective.state != 'revoked', 'REVOCATION_TERMINAL')
    if event_type in ('payment', 'grace'):
        require(not device['revoked'] and device['invite_revoked'] == 0, 'ACTIVE_IDENTITY_REQUIRED')
        release = confirmed_android_release(database, device['device'])
        if event_type == 'payment':
            require(apk_sha256 == release.apk_sha256, 'PAYMENT_BOUNDS_OR_APK_INVALID')
        if database.execute("SELECT 1 FROM sqlite_master WHERE name='restricted_grants'").fetchone():
            grant = database.execute('SELECT revoked FROM restricted_grants WHERE device=?', (device['device'],)).fetchone()
            require(grant is None or not grant['revoked'], 'EXISTING_MESH_REVOCATION')
    require(previous is not None or event_type == 'payment', 'COHORT_ENROLLMENT_REQUIRES_PAYMENT')
    if previous is None:
        require(database.execute('SELECT count(*) FROM paid_beta_subscriptions').fetchone()[0] < COHORT_LIMIT, 'COHORT_LIMIT')
    if event_type == 'payment':
        if previous is not None:
            require(period_start >= previous['period_start'] and paid_until >= max(previous['paid_until'], previous['grace_until'] or 0), 'PAYMENT_MUST_NOT_SHORTEN')
        new_state = 'active'
    else:
        period_start, paid_until = previous['period_start'], previous['paid_until']
        if event_type == 'grace':
            require(grace_until >= max(paid_until, previous['grace_until'] or 0), 'GRACE_MUST_NOT_SHORTEN')
            new_state = 'grace'
        else:
            grace_until = previous['grace_until']
            new_state = 'revoked' if event_type == 'revoke' else 'expired'
    record = dict(event_id=event_id, device=device['device'], event_type=event_type, occurred_at=now,
                  previous_state=effective.state if effective is not None else None, new_state=new_state,
                  period_start=period_start, paid_until=paid_until, grace_until=grace_until,
                  reference_hash=reference_hash, payload_hash=payload_hash, applied_at=now, result='APPLIED')
    if previous is None:
        registry_path = next(row[2] for row in database.execute('PRAGMA database_list') if row[1] == 'main')
        transport_config = Path(registry_path).parent/'transport-enforcement.json'
        if transport_config.exists() or transport_config.is_symlink():
            from .transport_membership import prepare
            prepare(database, device['device'], payload_hash, now)
    database.execute('INSERT INTO paid_beta_events VALUES (:event_id,:device,:event_type,:occurred_at,:previous_state,'
        ':new_state,:period_start,:paid_until,:grace_until,:reference_hash,:payload_hash,:applied_at,:result)', record)
    database.execute('INSERT INTO paid_beta_subscriptions VALUES (?,?,?,?,?,?,?,?,?,?) '
        'ON CONFLICT(device) DO UPDATE SET state=excluded.state,period_start=excluded.period_start,'
        'paid_until=excluded.paid_until,grace_until=excluded.grace_until,updated_at=excluded.updated_at,'
        'version=paid_beta_subscriptions.version+1,last_event_id=excluded.last_event_id,revoked_at=excluded.revoked_at',
        (device['device'], new_state, period_start, paid_until, grace_until,
         now, now, 1, event_id, now if new_state == 'revoked' else None))
    return dict(schema=1, duplicate=False, event=record)
