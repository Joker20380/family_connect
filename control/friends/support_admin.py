"""Local operator Support ID lookup and explicit, capped FIELD admission."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import re
import secrets

from .access import Access
from . import support_ids
from .restricted import from_env
from .restricted_admin import grant, publish_crl


def admission(path):
    raw = path.read_bytes()
    if len(raw) > 16384:
        raise ValueError('Admission bound')
    value = json.loads(raw)
    if (type(value) is not dict or set(value) != {'devices'} or type(value['devices']) is not list
            or len(value['devices']) > 3 or len(set(value['devices'])) != len(value['devices'])
            or any(type(device) is not str or not re.fullmatch('[0-9a-f]{32}', device) for device in value['devices'])):
        raise ValueError('Explicit FIELD cohort of at most three required')
    return value['devices']


def write_admission(path, previous, devices):
    if admission(path) != previous:
        raise ValueError('Admission changed concurrently')
    temporary = path.with_name(path.name + '.' + secrets.token_hex(8))
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(descriptor, 'wb') as output:
            output.write((json.dumps(dict(devices=devices)) + '\n').encode())
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        temporary.unlink(missing_ok=True)


def change(access, path, support, enabled, expires=None):
    support = support_ids.normalize(support)
    descriptor = os.open(path.with_name('field-operator.lock'), os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'r+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        previous = admission(path)
        safe = support_ids.lookup(access, support, previous)
        if enabled and not safe['active']:
            raise ValueError('Inactive registration')
        with access.db() as database:
            device = database.execute('SELECT device FROM device_support WHERE support_id=?', (support,)).fetchone()['device']
        old = device in previous
        if old == enabled and (enabled and safe['family_state'] == 'ACTIVE' or not enabled and safe['family_state'] != 'ACTIVE'):
            return safe
        if enabled and old:
            raise ValueError('Existing admission needs explicit grant renewal with the restricted operator')
        if enabled and not old and len(previous) >= 3:
            raise ValueError('FIELD cohort limit')
        if not enabled and old and len(previous) == 1:
            raise ValueError('Retain the existing owner admission')
        service = from_env(access)
        if enabled:
            trust, _, _, _, _ = service._trust(int(access.clock()))
            if type(expires) is not int or not access.clock() < expires <= trust['expires_at']:
                raise ValueError('Explicit grant expiry required')
        with access.db() as database:
            cursor = database.execute('INSERT INTO field_support_audit(timestamp,support_id,previous_state,new_state,outcome) VALUES (?,?,?,?,?)',
                                      (int(access.clock()), support, int(old), int(enabled), 'PENDING'))
            audit_id = cursor.lastrowid
            if not enabled:
                database.execute('UPDATE restricted_grants SET revoked=1,revision=revision+1 WHERE device=? AND revoked=0', (device,))
        try:
            if enabled:
                grant(access, device, trust['family'], expires, trust['minimum_revision'])
            publish_crl(service, path.parent / 'revocations.pem')
            devices = sorted(set(previous) | {device}) if enabled else [value for value in previous if value != device]
            write_admission(path, previous, devices)
            with access.db() as database:
                database.execute('UPDATE field_support_audit SET outcome=? WHERE id=?', ('APPLIED', audit_id))
        except Exception:
            with access.db() as database:
                if enabled:
                    database.execute('UPDATE restricted_grants SET revoked=1,revision=revision+1 WHERE device=? AND revoked=0', (device,))
                database.execute('UPDATE field_support_audit SET outcome=? WHERE id=?', ('INCOMPLETE', audit_id))
            raise RuntimeError('FIELD operation incomplete; inspect the safe audit') from None
        return support_ids.lookup(access, support, devices)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', type=Path, required=True)
    parser.add_argument('--admission', type=Path)
    parser.add_argument('--support-id')
    parser.add_argument('--expires', type=int)
    parser.add_argument('action', choices=('backfill', 'inventory', 'lookup', 'enable-field', 'disable-field', 'audit'))
    args = parser.parse_args()
    try:
        if not args.db.is_file():
            raise ValueError('Existing registration DB required')
        access = Access(args.db)
        if args.action == 'backfill':
            result = support_ids.backfill(access)
        elif args.action == 'inventory':
            result = support_ids.inventory(access)
        elif args.action == 'audit':
            with access.db() as database:
                result = [dict(row) for row in database.execute('SELECT timestamp,support_id,previous_state,new_state,outcome FROM field_support_audit ORDER BY id DESC LIMIT 100')]
        else:
            if args.admission is None or args.support_id is None:
                raise ValueError('Admission file and Support ID required')
            if args.action == 'lookup':
                result = support_ids.lookup(access, args.support_id, admission(args.admission))
            else:
                expected = Path(os.environ['FC_FRIENDS_RESTRICTED_DIR']) / 'admission.json'
                if args.admission.resolve() != expected.resolve():
                    raise ValueError('Admission authority mismatch')
                result = change(access, args.admission, args.support_id, args.action == 'enable-field', args.expires)
        print(json.dumps(result, sort_keys=True))
    except Exception:
        print(json.dumps(dict(error='SUPPORT_OPERATION_FAILED', hint='No credentials are printed; inspect configuration and safe audit.')))
        raise SystemExit(1) from None


if __name__ == '__main__':
    main()
