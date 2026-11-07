"""Local manual-payment operator. Never an HTTP endpoint or automatic enrollment."""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import time
import zipimport

from . import paid_beta


class OperatorParser(argparse.ArgumentParser):
    def error(self, message):
        raise paid_beta.PaidBetaError('INVALID_ARGUMENTS')


def provenance():
    result = paid_beta.policy()
    result['modules'] = {
        'control/friends/paid_beta.py': hashlib.sha256(paid_beta.__loader__.get_data(paid_beta.__file__)).hexdigest(),
        'control/friends/paid_beta_admin.py': hashlib.sha256(__loader__.get_data(__file__)).hexdigest(),
    }
    if isinstance(__loader__, zipimport.zipimporter):
        result['archive_sha256'] = hashlib.sha256(Path(__loader__.archive).read_bytes()).hexdigest()
    return result


def main(argv=None):
    parser = OperatorParser(description=__doc__, prog='paid-beta')
    parser.add_argument('--db', type=Path)
    commands = parser.add_subparsers(dest='action', required=True)
    commands.add_parser('policy', help='Read release descriptors and executable provenance without opening a registry')
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
        if args.action == 'policy':
            print(json.dumps(provenance(), sort_keys=True, allow_nan=False))
            return 0
        paid_beta.require(args.db is not None, 'INVALID_ARGUMENTS')
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
