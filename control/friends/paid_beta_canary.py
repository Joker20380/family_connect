"""Private single-device, single-permit orchestration over paid_beta; no HTTP API."""
import argparse
import hashlib
import hmac
import json
from pathlib import Path
import re
import sqlite3
import sys
import time

from . import paid_beta

ALIAS = 'OWNER_CANARY_1'
PURPOSE = 'internal_canary'
MAX_INPUT = 4096
require = paid_beta.require


def strict_json(raw):
    require(len(raw) <= MAX_INPUT, 'INPUT_TOO_LARGE')
    def pairs(items):
        result = {}
        for name, value in items:
            require(name not in result, 'DUPLICATE_FIELD')
            result[name] = value
        return result
    try:
        return json.loads(raw, object_pairs_hook=pairs,
                          parse_constant=lambda value: require(False, 'NONFINITE_JSON'))
    except (ValueError, UnicodeError):
        raise paid_beta.PaidBetaError('INVALID_JSON') from None


def fields(value, names):
    require(type(value) is dict and set(value) == set(names.split()), 'INVALID_FIELDS')


def token_for(key, device):
    require(type(key) is bytes and len(key) == 32, 'INVALID_HMAC_KEY')
    return hmac.new(key, device.encode(), hashlib.sha256).hexdigest()


def validate_envelope(envelope):
    fields(envelope, 'schema alias device_token safe_ref permit')
    require(type(envelope['schema']) is int and envelope['schema'] == 1 and envelope['alias'] == ALIAS,
            'INVALID_BINDING')
    token = envelope['device_token']
    require(type(token) is str and re.fullmatch('[0-9a-f]{64}', token), 'INVALID_BINDING')
    require(envelope['safe_ref'] == 'dev_' + token[:12], 'INVALID_BINDING')
    permit = envelope['permit']
    if permit is None:
        return
    fields(permit, 'action event_id expected_version period_start paid_until not_before not_after')
    version = permit['expected_version']
    require(type(version) is int and 0 <= version <= 3, 'INVALID_CANARY_STAGE')
    require(permit['action'] == ('expire' if version == 2 else 'activate'), 'INVALID_CANARY_STAGE')
    require(type(permit['event_id']) is str and re.fullmatch('canary_[0-9a-f]{32}', permit['event_id']),
            'INVALID_EVENT_ID')
    for name in ('not_before', 'not_after'):
        paid_beta.instant(permit[name])
    require(0 < permit['not_after'] - permit['not_before'] <= 900, 'INVALID_EXECUTION_WINDOW')
    if permit['action'] == 'activate':
        for name in ('period_start', 'paid_until'):
            paid_beta.instant(permit[name])
        require(0 < permit['paid_until'] - permit['period_start'] <= 31 * 86400, 'INVALID_PERIOD')
    else:
        require(permit['period_start'] is permit['paid_until'] is None, 'UNEXPECTED_PERIOD')


def cohort_guard(database, device):
    require(paid_beta.schema_present(database), 'PAID_SCHEMA_REQUIRED')
    for table in ('paid_beta_subscriptions', 'paid_beta_events'):
        require(database.execute('SELECT 1 FROM ' + table + ' WHERE device!=? LIMIT 1', (device,)).fetchone() is None,
                'OTHER_COHORT_MEMBER')
    require(database.execute('SELECT count(*) FROM paid_beta_events').fetchone()[0] <= 4, 'CANARY_EVENT_LIMIT')


def resolve_bound(database, key, envelope):
    validate_envelope(envelope)
    matches = [row['device'] for row in database.execute('SELECT device FROM devices')
               if hmac.compare_digest(token_for(key, row['device']), envelope['device_token'])]
    require(len(matches) == 1, 'BOUND_DEVICE_NOT_FOUND')
    device = matches[0]
    rows = database.execute('SELECT support_id FROM device_support WHERE device=?', (device,)).fetchall()
    require(len(rows) == 1, 'UNIQUE_EXISTING_DEVICE_REQUIRED')
    selector = rows[0]['support_id']
    require(paid_beta.resolve_device(database, selector)['device'] == device, 'BINDING_CHANGED')
    cohort_guard(database, device)
    return device, selector


def sanitized_status(database, selector, envelope, now):
    status = paid_beta.status(database, selector, now)
    subscription = status.get('subscription', {})
    return dict(schema=1, alias=ALIAS, purpose=PURPOSE, amount_minor=0,
                safe_ref=envelope['safe_ref'], device_token=envelope['device_token'], observed_at=now,
                activation_active=status['activation_active'], cohort=status['cohort'],
                effective_state=status.get('effective_state'), paid_allow=status.get('paid_allow'),
                entitlement_until=status.get('entitlement_until'), version=subscription.get('version', 0),
                paid_until=subscription.get('paid_until'), event_count=database.execute(
                    'SELECT count(*) FROM paid_beta_events').fetchone()[0])


def lookup(path, selector, key, now):
    with paid_beta.connection(path) as database:
        device = paid_beta.resolve_device(database, selector)
        require(not device['revoked'] and device['invite_revoked'] == 0, 'ACTIVE_IDENTITY_REQUIRED')
        paid_beta.confirm_android106(database, device['device'])
        cohort_guard(database, device['device'])
        token = token_for(key, device['device'])
        envelope = dict(schema=1, alias=ALIAS, device_token=token, safe_ref='dev_' + token[:12], permit=None)
        return dict(binding=envelope, observation=sanitized_status(database, selector, envelope, now))


def preserved_tables(database):
    names = [row[0] for row in database.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
             if row[0] not in paid_beta.TABLES]
    return {name: hashlib.sha256(repr(sorted((tuple(row) for row in database.execute(
        'SELECT * FROM "' + name.replace('"', '""') + '"')), key=repr)).encode()).hexdigest() for name in names}


def observe(path, key, envelope, now):
    with paid_beta.connection(path) as database:
        _, selector = resolve_bound(database, key, envelope)
        return sanitized_status(database, selector, envelope, now)


def apply(path, key, envelope, now):
    validate_envelope(envelope)
    permit = envelope['permit']
    require(permit is not None, 'PERMIT_REQUIRED')
    with paid_beta.connection(path, write=True) as database:
        device, selector = resolve_bound(database, key, envelope)
        previous = database.execute('SELECT * FROM paid_beta_events WHERE event_id=?', (permit['event_id'],)).fetchone()
        before = sanitized_status(database, selector, envelope, now)
        if previous is None:
            require(permit['not_before'] <= now < permit['not_after'], 'EXECUTION_WINDOW_CLOSED')
            version = permit['expected_version']
            require(before['version'] == before['event_count'] == version, 'STALE_CANARY_PERMIT')
            if version in (1, 3):
                require(before['effective_state'] == 'expired', 'EXPIRY_NOT_OBSERVED')
            if version == 2:
                require(before['paid_allow'] is True, 'ACTIVE_ENTITLEMENT_REQUIRED')
            if version in (2, 3):
                require(database.execute("SELECT 1 FROM sqlite_master WHERE name='restricted_certificates'").fetchone(),
                        'CERTIFICATE_INVENTORY_REQUIRED')
                valid_certificate = database.execute(
                    'SELECT 1 FROM restricted_certificates WHERE device=? AND expires>? LIMIT 1', (device, now)).fetchone()
                require(valid_certificate is not None if version == 2 else valid_certificate is None,
                        'EXPIRE_REQUIRES_VALID_CERTIFICATE' if version == 2 else 'CERTIFICATES_STILL_VALID')
        preserved = preserved_tables(database)
        values = {}
        if permit['action'] == 'activate':
            values = dict(period_start=permit['period_start'], paid_until=permit['paid_until'], apk_sha256=paid_beta.APK_SHA256)
        raw = paid_beta.apply_event(database, selector, 'payment' if permit['action'] == 'activate' else 'expire',
                                    permit['event_id'], 'internal-canary:' + permit['event_id'], now=now, **values)
        require(preserved_tables(database) == preserved, 'NON_PAID_STATE_CHANGED')
        result = sanitized_status(database, selector, envelope, now)
        result.update(event_id=raw['event']['event_id'], event_type=raw['event']['event_type'],
                      payload_hash=raw['event']['payload_hash'], applied_at=raw['event']['applied_at'],
                      result=raw['event']['result'], duplicate=raw['duplicate'])
        return result


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise paid_beta.PaidBetaError('INVALID_ARGUMENTS')


def main(argv=None, *, envelope=None):
    try:
        parser = Parser(description=__doc__)
        parser.add_argument('--db', type=Path, required=True)
        parser.add_argument('action', choices=('lookup', 'status', 'apply'))
        args = parser.parse_args(argv)
        require(args.action == 'lookup' or envelope is not None, 'BOUND_PACKAGE_REQUIRED')
        require(args.action != 'lookup' or envelope is None, 'BOUND_LOOKUP_FORBIDDEN')
        request = strict_json(sys.stdin.buffer.read(MAX_INPUT + 1))
        fields(request, 'hmac_key support_id' if args.action == 'lookup' else 'hmac_key')
        key = request['hmac_key']
        require(type(key) is str and re.fullmatch('[0-9a-f]{64}', key), 'INVALID_HMAC_KEY')
        now = int(time.time())
        if args.action == 'lookup':
            result = lookup(args.db, request['support_id'], bytes.fromhex(key), now)
        else:
            result = (observe if args.action == 'status' else apply)(args.db, bytes.fromhex(key), envelope, now)
        print(json.dumps(result, sort_keys=True, allow_nan=False))
        return 0
    except paid_beta.PaidBetaError as error:
        print(json.dumps(dict(schema=1, result='REJECTED', reason=str(error))))
        return 2
    except Exception:
        print(json.dumps(dict(schema=1, result='REJECTED', reason='CANARY_OPERATION_FAILED')))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
