"""Local manual-payment operator. Never an HTTP endpoint or automatic enrollment."""
import argparse
import json
from pathlib import Path
import sqlite3
import time

from . import paid_beta


class OperatorParser(argparse.ArgumentParser):
    def error(self, message):
        raise paid_beta.PaidBetaError('INVALID_ARGUMENTS')


def main(argv=None):
    parser = OperatorParser(description=__doc__, prog='paid-beta')
    parser.add_argument('--db', type=Path, required=True)
    commands = parser.add_subparsers(dest='action', required=True)
    commands.add_parser('migrate')
    status = commands.add_parser('status')
    status.add_argument('--support-id', required=True)
    for action in ('activate', 'grace', 'expire', 'revoke'):
        command = commands.add_parser(action)
        command.add_argument('--support-id', required=True)
        command.add_argument('--event-id', required=True)
        command.add_argument('--reference', required=True, help='Opaque reconciliation reference; only its SHA256 is stored')
        if action == 'activate':
            command.add_argument('--period-start', required=True)
            command.add_argument('--paid-until', required=True)
            command.add_argument('--apk-sha256', required=True, help='Operator attests private handoff of the exact accepted APK')
        if action == 'grace':
            command.add_argument('--grace-until', required=True)
    try:
        args = parser.parse_args(argv)
        with paid_beta.connection(args.db, write=args.action != 'status') as database:
            now = int(time.time())
            if args.action == 'migrate':
                paid_beta.migrate(database)
                result = dict(schema=1, result='MIGRATED', cohort_size=database.execute('SELECT count(*) FROM paid_beta_subscriptions').fetchone()[0])
            elif args.action == 'status':
                result = paid_beta.status(database, args.support_id, now)
            else:
                values = {}
                for name in ('period_start', 'paid_until', 'grace_until'):
                    if hasattr(args, name):
                        values[name] = paid_beta.parse_utc(getattr(args, name))
                if args.action == 'activate':
                    values['apk_sha256'] = args.apk_sha256
                result = paid_beta.apply_event(database, args.support_id,
                    'payment' if args.action == 'activate' else args.action, args.event_id, args.reference, now=now, **values)
        print(json.dumps(result, sort_keys=True, allow_nan=False))
        return 0
    except paid_beta.PaidBetaError as error:
        print(json.dumps(dict(schema=1, result='REJECTED', reason=str(error))))
        return 2
    except (sqlite3.Error, OSError):
        print(json.dumps(dict(schema=1, result='REJECTED', reason='REGISTRY_OPERATION_FAILED')))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
