import argparse
import json
import os
from pathlib import Path
import resource
import secrets
import sys
import time

from credential_renewal import Rejected, canonical, digest, evaluate, parse, read_private, require
from maintenance_policy import MaintenanceAuthorization
from node import construct, dispatch
from production_controller import ProductionController
from production_transport import SshNode


class LocalNode:
    def __init__(self, node, source):
        self.node, self.source = node, source

    def call(self, action, operation_id, payload=None):
        return dispatch(self.node, dict(schema=1, role='RU', action=action,
            operation_id=operation_id, expected_source_sha256=self.source, payload=payload))


def main():
    os.umask(0o077)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--mode', choices=('evaluate','scheduled','operator','recover'), default='evaluate')
    parser.add_argument('--authority-bundle', type=Path)
    parser.add_argument('--operation')
    parser.add_argument('--approve-maintenance-outage', action='store_true')
    args = parser.parse_args()
    try:
        config = parse(read_private(args.config))
        require(set(config) == {'schema','node_config','coordinator_state','nl_source_sha256',
            'ssh','approved_leaf_crl_schedule'} and config['schema'] == 1
            and type(config['approved_leaf_crl_schedule']) is bool, 'CONTROLLER_CONFIG')
        node, source = construct(Path(config['node_config']))
        require(node.role == 'RU', 'NODE_ROLE')
        nodes = {'RU': LocalNode(node, source),
                 'NL': SshNode('NL', config['nl_source_sha256'], forced=config['ssh'])}
        controller = ProductionController(Path(config['coordinator_state']), nodes, node.validator)
        operation = args.operation or ('scheduled-' + str(int(time.time())) + '-' + secrets.token_hex(8))
        if args.mode == 'evaluate':
            snapshot, _, _, changed = controller.read(operation)
            result = evaluate(node.validator.validate(canonical(snapshot), int(time.time()),
                expired_leaf_predecessor=True), int(time.time()), changed)
            result.update(files_changed=0, remote_writes=0, restarts=0)
        elif args.mode == 'recover':
            record = parse(read_private(controller.root / 'transaction.json'))
            with controller.operation.lock():
                result = controller.recover(record)
        else:
            approval = None
            handoff = None
            if args.mode == 'operator':
                require(args.approve_maintenance_outage, 'MAINTENANCE_APPROVAL_REQUIRED')
                _, _, current, _ = controller.read(operation)
                now = int(time.time())
                approval = MaintenanceAuthorization(operation, digest(canonical(current)), now, now+900)
                handoff = read_private(args.authority_bundle) if args.authority_bundle else None
            else:
                require(not args.authority_bundle and not args.approve_maintenance_outage, 'SCHEDULED_SCOPE')
            result = controller.run(operation, approval=approval, scheduled=args.mode == 'scheduled',
                approved_leaf_crl_schedule=config['approved_leaf_crl_schedule'], authority_handoff=handoff)
        result.update(policy='CURRENT_PRODUCTION_VALIDITY_LIMITS', remote_alert_delivery='UNAVAILABLE')
        print(canonical(result).decode())
        if result['result'] not in ('NOOP','COMMITTED'):
            raise SystemExit(75)
    except Exception as error:
        print(canonical(dict(result='FAIL_CLOSED', cause=str(error) if isinstance(error, Rejected) else 'UNKNOWN',
            automatic_retry=False, remote_alert_delivery='UNAVAILABLE')).decode())
        raise SystemExit(1) from None


if __name__ == '__main__':
    main()
