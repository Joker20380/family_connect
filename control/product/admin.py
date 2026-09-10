"""Local operator-only pilot administration. Never supply invitation tokens as CLI arguments."""
import argparse
import json
import os
import time
from pathlib import Path

from .store import ProductStore
from .provisioning import ProvisioningService
from device_identity.device import _private_directory, _read_key, _create_key
import RNS


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
    signer = sub.add_parser('init-provisioning-signer')
    signer.add_argument('--key-directory', type=Path, required=True)
    publish = sub.add_parser('publish-provisioning')
    publish.add_argument('identifier')
    publish.add_argument('--network', type=Path, required=True)
    publish.add_argument('--key-directory', type=Path, required=True)
    publish.add_argument('--lease-seconds', type=int, default=3600)
    stage = sub.add_parser('stage-peers')
    stage.add_argument('identifier')
    stage.add_argument('--network', type=Path, required=True)
    stage.add_argument('--lease-seconds', type=int, default=3600)
    reconcile = sub.add_parser('reconcile-peers')
    reconcile.add_argument('--gateways', type=Path, required=True)
    sub.add_parser('peer-status')
    sub.add_parser('provisioning-versions').add_argument('identifier')
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
    elif args.command == 'init-provisioning-signer':
        # Dedicated signing identity, never a consumer/group secret.
        with _private_directory(args.key_directory) as directory:
            signer = RNS.Identity()
            _create_key(directory, 'signer.key', signer.get_private_key())
            import base64
            print(json.dumps({'public_identity': base64.b64encode(signer.get_public_key()).decode()}))
    elif args.command == 'publish-provisioning':
        with _private_directory(args.key_directory) as directory:
            signer = RNS.Identity(create_keys=False)
            if not signer.load_private_key(_read_key(directory, 'signer.key', 64)):
                raise ValueError('invalid signing identity')
        from provisioning.envelope import _unique_fields
        raw = args.network.read_bytes()
        if len(raw) > 65536:
            raise ValueError('network file too large')
        network = json.loads(raw, object_pairs_hook=_unique_fields)
        print(json.dumps(ProvisioningService(store).publish(args.identifier, network,
            signing_identity=signer, lease_seconds=args.lease_seconds)))
    elif args.command == 'stage-peers':
        from .gateways import GatewayReconciler
        from provisioning.envelope import _unique_fields
        raw = args.network.read_bytes()
        if len(raw)>65536:raise ValueError('network file too large')
        print(json.dumps(GatewayReconciler(store, {}).stage(args.identifier,
            json.loads(raw, object_pairs_hook=_unique_fields), lease_seconds=args.lease_seconds)))
    elif args.command == 'reconcile-peers':
        from .gateways import GatewayReconciler
        from .gateway_adapter import DockerGateway
        from provisioning.envelope import _unique_fields
        raw = args.gateways.read_bytes()
        if len(raw)>65536:raise ValueError('gateway file too large')
        config = json.loads(raw, object_pairs_hook=_unique_fields)
        if type(config) is not dict or not 1<=len(config)<=8:raise ValueError('invalid gateways')
        adapters = {key:DockerGateway(**value) for key,value in config.items()}
        worker = GatewayReconciler(store, adapters)
        print(json.dumps(worker.run_once()))
        if any(row['desired'] != row['applied'] or row['error'] for row in worker.status()):
            raise SystemExit(1)
    elif args.command == 'peer-status':
        from .gateways import GatewayReconciler
        print(json.dumps(GatewayReconciler(store, {}).status()))
    elif args.command == 'provisioning-versions':
        print(json.dumps(ProvisioningService(store).versions(args.identifier)))
    elif args.command == 'prune-challenges':
        store.prune_challenges()


if __name__ == '__main__':
    main()
