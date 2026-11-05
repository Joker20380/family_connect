import argparse
import base64
import os
from pathlib import Path
import resource

from credential_renewal import Rejected, Validator, canonical, parse, read_private, require
from online_contract import CONTRACT, window
from online_runtime import load_api, package_manifest, runtime_binding, verify_participants
from production_controller import ProductionController
from production_transport import SshNode


def main():
    os.umask(0o077)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    parser = argparse.ArgumentParser(description='Explicit online renewal; no timer or implicit outage approval')
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--mode', choices=('inspect', 'online', 'resume', 'abort', 'emergency'), default='inspect')
    parser.add_argument('--operation', required=True)
    parser.add_argument('--outage-approval', type=Path)
    args = parser.parse_args()
    try:
        require(os.geteuid() == 0, 'ROOT_REQUIRED')
        require(args.outage_approval is None or args.mode == 'emergency', 'MAINTENANCE_APPROVAL_INVALID')
        config = parse(read_private(args.config))
        require(type(config) is dict and set(config) - {'isolated_runtime'} == {'schema', 'online', 'state', 'anchor', 'gateway_ids',
                'schedule_seconds', 'ssh_routes'} and type(config['schema']) is int and config['schema'] == 1,
                'ONLINE_CONTROLLER_CONFIG')
        require(config['online'] == CONTRACT, 'ONLINE_OPT_IN_REQUIRED')
        window(120, config['schedule_seconds'])
        from gateway_set import membership
        members = membership(config['gateway_ids'])
        source = Path(__file__).resolve().parent
        manifest = package_manifest(source)
        load_api(source.parent/'api.pyz', manifest['api_sha256'])
        from control.friends.restricted import delegation
        require(type(config['ssh_routes']) is dict and set(config['ssh_routes']) == {'RU', 'NL', 'NL2'},
                'ONLINE_MEMBERSHIP_REQUIRED')
        nodes = {slot: SshNode('RU' if slot == 'RU' else 'NL', manifest['source_sha256'], route=route)
                 for slot, route in config['ssh_routes'].items()}
        binding = runtime_binding(manifest, config.get('isolated_runtime'))
        verify_participants(nodes, args.operation, manifest, members, running=args.mode in ('inspect', 'online'), binding=binding)
        if args.mode == 'inspect':
            result = dict(result='ONLINE_CAPABILITIES_READY', mutations=0)
        else:
            validator = Validator(base64.b64decode(config['anchor'], validate=True), delegation, all_activated=True)
            controller = ProductionController(Path(config['state']), nodes, validator)
            if args.mode == 'emergency':
                from maintenance_policy import MaintenanceAuthorization
                approval = None
                if args.outage_approval is not None:
                    value = parse(read_private(args.outage_approval))
                    require(type(value) is dict and set(value) == {'operation_id', 'expected_state_sha256',
                            'approved_at', 'expires_at', 'approval'} and
                            all(type(value[name]) is int for name in ('approved_at', 'expires_at')),
                            'MAINTENANCE_APPROVAL_INVALID')
                    approval = MaintenanceAuthorization(**value)
                result = controller.recover_online_emergency(args.operation, approval=approval)
            elif args.mode == 'abort':
                result = controller.abort_online(args.operation)
            else:
                result = controller.run_online(args.operation, schedule_seconds=config['schedule_seconds'],
                                               resume=args.mode == 'resume')
        print(canonical(result).decode())
        return 0 if result['result'] in ('ONLINE_CAPABILITIES_READY', 'COMMITTED', 'ABORTED', 'EMERGENCY_RECOVERED') else 75
    except Exception as error:
        print(canonical(dict(result='FAIL_CLOSED', cause=str(error) if isinstance(error, Rejected) else 'UNKNOWN',
                             automatic_retry=False)).decode())
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
