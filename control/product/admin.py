"""Local operator-only pilot administration. Never supply invitation tokens as CLI arguments."""
import argparse
import json
import os
import time
from pathlib import Path

from .store import ProductStore


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--database', type=Path, required=True)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('migrate')
    entitlement = sub.add_parser('create-entitlement')
    entitlement.add_argument('--days', type=int, default=7)
    entitlement.add_argument('--devices', type=int, default=5)
    invitation = sub.add_parser('create-invitation')
    invitation.add_argument('--entitlement', required=True)
    invitation.add_argument('--hours', type=int, default=24)
    invitation.add_argument('--uses', type=int, default=1)
    invitation.add_argument('--output', type=Path, required=True)
    for operation in ('revoke-device', 'revoke-entitlement', 'revoke-invitation'):
        sub.add_parser(operation).add_argument('identifier')
    sub.add_parser('prune-challenges')
    args = parser.parse_args()
    store = ProductStore(args.database)
    if args.command == 'migrate':
        store.migrate()
    elif args.command == 'create-entitlement':
        print(json.dumps(store.create_entitlement(expires_at=int(time.time()) + args.days * 86400,
                                                 device_limit=args.devices)))
    elif args.command == 'create-invitation':
        # O_EXCL avoids clobbering or following a pre-created output symlink.
        fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'w') as stream:
            result = store.create_invitation(args.entitlement,
                                             expires_at=int(time.time()) + args.hours * 3600,
                                             max_uses=args.uses)
            json.dump(result, stream)
            stream.flush()
            os.fsync(stream.fileno())
    elif args.command == 'revoke-device':
        store.revoke_device(args.identifier)
    elif args.command == 'revoke-entitlement':
        store.revoke_entitlement(args.identifier)
    elif args.command == 'revoke-invitation':
        store.revoke_invitation(args.identifier)
    elif args.command == 'prune-challenges':
        store.prune_challenges()


if __name__ == '__main__':
    main()
