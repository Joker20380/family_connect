import argparse
import base64
import json
import os
from pathlib import Path
import resource
import sys

from credential_renewal import MAX_BYTES, Rejected, Validator, canonical, digest, parse, read_private, require
from production_node import ProductionNode, pinned
from production_transport import ACTIONS
from grant_cutover import GrantDatabase

NODE_MODULES = frozenset(('node.py','credential_renewal.py','production_node.py','production_transport.py',
                         'grant_cutover.py','offline_handoff.py','expired_recovery.py'))


def construct(config_path, *, fenced_recovery=False):
    require(os.geteuid() == 0, 'ROOT_REQUIRED')
    config = parse(read_private(config_path))
    require(set(config) - {'admission_mode', 'profile_locator', 'profile_locator_sha256', 'snapshot_target'} == {'schema','role','live','state','database','anchor','anchor_sha256','api_archive','api_sha256','service_units',
                           'source_files','source_sha256'}, 'NODE_CONFIG_SCHEMA')
    require(type(config['schema']) is int and config['schema'] == 1 and config['role'] in ('RU','NL'), 'NODE_CONFIG_SCHEMA')
    source = Path(__file__).resolve().parent
    retained_source = Path(config['api_archive']).parent/'renewal' if fenced_recovery else source
    require(type(config['source_files']) is dict and NODE_MODULES <= set(config['source_files']),
            'SOURCE_MANIFEST_INCOMPLETE')
    hashes = {}
    for name,expected in config['source_files'].items():
        require(type(name) is str and '/' not in name and name.endswith('.py') and not name.startswith('.'), 'SOURCE_PATH')
        hashes[name] = digest(pinned(retained_source/name,{0})[0])
        require(hashes[name] == expected, 'SOURCE_IDENTITY_MISMATCH')
    require(digest(canonical(hashes)) == config['source_sha256'], 'SOURCE_IDENTITY_MISMATCH')
    source_sha256 = config['source_sha256']
    if fenced_recovery:
        require(retained_source.resolve() != source, 'RECOVERY_SOURCE_BOUNDARY')
        manifest = parse(read_private(source.parent/'source-manifest.json'))
        require(manifest['production_configuration'] == 'absent' and manifest['binding'] == 'unbound'
                and manifest['operation_permit'] is None and set(manifest['source_files']) == set(config['source_files']),
                'SOURCE_MANIFEST_INCOMPLETE')
        current = {}
        for name,expected in manifest['source_files'].items():
            require('/' not in name and name.endswith('.py') and not name.startswith('.'), 'SOURCE_PATH')
            current[name] = digest(pinned(source/name,{0})[0])
            require(current[name] == expected, 'SOURCE_IDENTITY_MISMATCH')
        require(digest(canonical(current)) == manifest['source_sha256'], 'SOURCE_IDENTITY_MISMATCH')
        source_sha256 = manifest['source_sha256']
    archive = Path(config['api_archive'])
    descriptor = os.open(archive,os.O_RDONLY|os.O_NOFOLLOW)
    try:
        import hashlib
        with os.fdopen(descriptor,'rb',closefd=False) as stream:
            require(hashlib.file_digest(stream,'sha256').hexdigest() == config['api_sha256'], 'API_IDENTITY_MISMATCH')
        sys.path.insert(0,'/proc/self/fd/'+str(descriptor))
        from control.friends.restricted import RestrictedReadiness, activated_grant, admission_policy, delegation
    except BaseException:
        os.close(descriptor)
        raise
    anchor_raw = read_private(Path(config['anchor']))
    anchor = base64.b64decode(anchor_raw.strip(),validate=True)
    require(digest(anchor) == config['anchor_sha256'], 'TRUST_ROOT_CHANGED')
    mode = config.get('admission_mode', 'legacy')
    require(mode in ('legacy', 'all_activated'), 'ADMISSION_MODE')
    validator = Validator(anchor,delegation,all_activated=mode == 'all_activated')
    live = Path(config['live'])
    database = None
    if config['role'] == 'RU':
        from types import SimpleNamespace
        devices, all_activated = admission_policy(pinned(live/'admission.json',{0})[0])
        require(all_activated == validator.all_activated, 'ADMISSION_MODE_MISMATCH')
        if all_activated:
            envelope = json.loads(pinned(live/'issuer.json',{0})[0])
            issued_at = json.loads(base64.b64decode(envelope['payload'],validate=True))['issued_at']
            trust, _ = delegation(envelope,anchor,issued_at)
            database = GrantDatabase(Path(config['database']),lambda connection,device,now:
                activated_grant(connection,device,trust['family'],trust['minimum_revision']),
                all_activated=True,family=trust['family'],minimum_revision=trust['minimum_revision'])
        else:
            policy = SimpleNamespace(eligible_devices=frozenset(devices))
            database = GrantDatabase(Path(config['database']),lambda connection,device,now:
                RestrictedReadiness._grant(policy,connection,device,now))
    policy_paths = {'anchor':Path(config['anchor'])}
    profile_store = None
    if config['role'] == 'NL':
        require('snapshot_target' not in config, 'NODE_CONFIG_SCHEMA')
        require(type(config.get('profile_locator')) is str and type(config.get('profile_locator_sha256')) is str,
                'CANONICAL_PROFILE_REQUIRED')
        from control.friends.profile_store import Locator, ProfileStore, metadata, read_regular
        locator_path = Path(config['profile_locator'])
        require(digest(read_regular(locator_path, metadata(locator_path.lstat()), 16384)) ==
                config['profile_locator_sha256'], 'PROFILE_LOCATOR_CHANGED')
        locator = Locator.load(locator_path)
        locator.validate()
        profile_store = ProfileStore(locator)
        require(locator.directory_port.path.parent == live, 'DIRECTORY_ROUTE_CHANGED')
    else:
        require(not {'profile_locator', 'profile_locator_sha256'} & set(config), 'PROFILE_STORE_ROLE')
    if validator.all_activated:
        policy_paths['node_config'] = config_path
    if config['role'] == 'RU':
        policy_paths['admission'] = live/'admission.json'
    node = ProductionNode(config['role'],live,Path(config['state']),validator,database=database,
                          policy_paths=policy_paths,profile_store=profile_store,service_units=config['service_units'])
    node.snapshot_target = config.get('snapshot_target')
    node.pinned_archive_descriptor = descriptor
    node.fenced_recovery = fenced_recovery
    return node,source_sha256


def dispatch(node, request):
    require(set(request) == {'schema','role','action','operation_id','expected_source_sha256','payload'}
            and request['schema'] == 1 and request['role'] == node.role and request['action'] in ACTIONS,
            'RPC_SCHEMA')
    action,operation,payload = request['action'],request['operation_id'],request['payload']
    import re
    require(type(operation) is str and re.fullmatch('[a-z0-9-]{16,96}',operation), 'OPERATION_ID')
    if getattr(node,'fenced_recovery',False):
        require(action in {'inspect','stopped','rollback-readback','rollback-registry-overlay','finalize-fenced-rollback','cleanup','fence'},
                'FENCED_RECOVERY_ACTION_FORBIDDEN')
        if (node.state/'owner.json').exists():
            require(node.owner(operation)['state'] in ('ROLLED_BACK','ABORTED_FENCED','CLEANING'), 'TRANSACTION_STATE')
        else:
            ledger = parse(read_private(node.state/'completed.json'))
            require(operation in ledger and ledger[operation]['result'] == 'CLEANED_FENCED_ROLLBACK', 'TRANSACTION_STATE')
    if action == 'inspect':
        require(payload is None, 'RPC_SCHEMA')
        return node.inspect()
    if action == 'public-gateway':
        require(payload is None, 'RPC_SCHEMA')
        return node.public_gateway()
    if action == 'public-authority':
        require(payload is None, 'RPC_SCHEMA')
        return node.public_authority()
    if action == 'authority-request':
        require(payload is None, 'RPC_SCHEMA')
        return node.authority_request(operation)
    if action == 'recovery-evidence':
        return node.recovery_evidence(payload)
    if action == 'recovery-authority-request':
        return node.recovery_authority_request(operation, payload)
    if action == 'prepare-expired':
        require(type(payload) is dict and set(payload) == {'gateway', 'bundle'}, 'RPC_SCHEMA')
        return node.prepare(operation, payload['gateway'], expired_handoff=base64.b64decode(payload['bundle'], validate=True))
    if action == 'acquire':
        return node.acquire(operation,payload)
    if action == 'prepare':
        require(type(payload) is dict and set(payload) == {'gateway','authority_handoff'}, 'RPC_SCHEMA')
        handoff = base64.b64decode(payload['authority_handoff'],validate=True) if payload['authority_handoff'] else None
        return node.prepare(operation,payload['gateway'],authority_handoff=handoff)
    if action == 'stage':
        return node.stage(operation,payload)
    if action == 'publish-directory':
        return node.publish_directory(operation,payload)
    if action == 'commit-decision':
        return node.commit_decision(operation,payload)
    if action == 'restore':
        return node.restore(operation,payload)
    if action == 'finalize-fenced-rollback':
        return node.finalize_fenced_rollback(operation,payload)
    if action == 'rollback-registry-overlay':
        return node.rollback_registry_overlay(operation,payload)
    require(payload is None, 'RPC_SCHEMA')
    if action == 'stopped':
        node.owner(operation)
        return dict(stopped=node.barrier.stopped())
    handlers = {'quiesce':node.quiesce,'fence':node.fence,'cleanup':node.cleanup,'public-directory':node.public_directory,'promote':node.promote,'readback':node.readback,
                'rollback':node.rollback,'rollback-readback':node.previous_readback,'resume':node.resume}
    require(action in handlers, 'RPC_ACTION_NOT_IMPLEMENTED')
    return handlers[action](operation)


def main():
    os.umask(0o077)
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    parser = argparse.ArgumentParser()
    parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--fenced-recovery',action='store_true')
    arguments = parser.parse_args()
    try:
        request = parse(sys.stdin.buffer.read(MAX_BYTES+1))
        node,source_sha256 = construct(arguments.config,**({'fenced_recovery':True} if arguments.fenced_recovery else {}))
        require(request['expected_source_sha256'] == source_sha256, 'SOURCE_IDENTITY_MISMATCH')
        payload = dispatch(node,request)
        response = dict(schema=1,role=node.role,operation_id=request['operation_id'],action=request['action'],
                        source_sha256=source_sha256,result='PASS',payload=payload)
        sys.stdout.buffer.write(canonical(response))
    except Exception as error:
        cause = str(error) if isinstance(error,Rejected) else 'UNKNOWN'
        if 'node' in locals() and 'request' in locals() and type(request) is dict:
            response = dict(schema=1,role=node.role,operation_id=request.get('operation_id'),action=request.get('action'),
                            source_sha256=source_sha256,result='REJECTED',payload=dict(cause=cause))
        else:
            response = dict(result='REJECTED',cause=cause)
        sys.stdout.buffer.write(canonical(response))
        raise SystemExit(1) from None


if __name__ == '__main__':
    main()
