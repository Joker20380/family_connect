import argparse
import base64
import os
from pathlib import Path
import resource
import sys
import time

from credential_renewal import Rejected, Validator, atomic, canonical, digest, parse, read_private, require, evaluate
from maintenance_policy import MaintenanceAuthorization
from production_controller import ProductionController
from production_transport import SshNode


def main():
    os.umask(0o077)
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    parser = argparse.ArgumentParser(description='Operator-host coordinator; uses existing root SSH authorization, never stores SSH keys')
    parser.add_argument('action',choices=('evaluate','authority-request','apply','recover'))
    parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--operation',required=True)
    parser.add_argument('--authority-bundle',type=Path)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--approve-maintenance-outage',action='store_true')
    args = parser.parse_args()
    try:
        from control.friends.restricted import delegation
        config = parse(read_private(args.config))
        require(set(config) - {'admission_mode'} == {'schema','state','anchor','node_sources','ssh_routes'}
                and config['schema'] == 1, 'OPERATOR_CONFIG')
        mode = config.get('admission_mode', 'legacy')
        require(mode in ('legacy', 'all_activated'), 'ADMISSION_MODE')
        anchor = base64.b64decode(config['anchor'],validate=True)
        require(type(config['ssh_routes']) is dict and set(config['ssh_routes']) == {'RU','NL'}, 'OPERATOR_CONFIG')
        nodes = {role:SshNode(role,config['node_sources'][role],route=config['ssh_routes'][role]) for role in ('RU','NL')}
        validator = Validator(anchor,delegation,all_activated=mode == 'all_activated')
        controller = ProductionController(Path(config['state']),nodes,validator)
        if args.action == 'authority-request':
            require(args.output is not None and not args.output.exists(), 'REQUEST_OUTPUT_REQUIRED')
            request = nodes['RU'].call('authority-request',args.operation)
            atomic(args.output,canonical(request))
            result = dict(result='OFFLINE_AUTHORITY_SIGNING_REQUEST_READY',sha256=digest(canonical(request)))
        elif args.action == 'evaluate':
            snapshot,_,_,revocations_changed = controller.read(args.operation)
            result = evaluate(validator.validate(canonical(snapshot),int(time.time()),expired_leaf_predecessor=True),
                              int(time.time()),revocations_changed,all_activated=validator.all_activated)
            if result['result'] != 'NOOP':
                result['result'] = 'MAINTENANCE_REQUIRED'
        elif args.action == 'recover':
            marker = parse(read_private(controller.root/'transaction.json'))
            require(marker['operation_id'] == args.operation, 'OPERATION_ID')
            with controller.operation.lock():
                result = controller.recover(marker)
        else:
            approval = None
            if args.approve_maintenance_outage:
                _,_,current,_ = controller.read(args.operation)
                now = int(time.time())
                approval = MaintenanceAuthorization(args.operation,digest(canonical(current)),now,now+900)
            handoff = read_private(args.authority_bundle) if args.authority_bundle else None
            result = controller.run(args.operation,approval=approval,authority_handoff=handoff)
        print(canonical(result).decode())
        if result['result'] not in ('COMMITTED','NOOP','OFFLINE_AUTHORITY_SIGNING_REQUEST_READY') and not (
                args.action == 'recover' and result['result'] == 'ROLLED_BACK_READERS_STOPPED'):
            raise SystemExit(75)
    except Exception as error:
        print(canonical(dict(result='FAIL_CLOSED',cause=str(error) if isinstance(error,Rejected) else 'UNKNOWN',
                             automatic_retry=False)).decode())
        raise SystemExit(1) from None


if __name__ == '__main__':
    main()
