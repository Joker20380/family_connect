import argparse
import base64
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import tempfile
import time

from credential_renewal import MAX_BYTES, Rejected, canonical, digest, evaluate, parse, read_private, require
from node import construct


def read_gateway(ssh_key, known_hosts):
    for path in (ssh_key,known_hosts):
        require(path.is_absolute() and not path.is_symlink() and path.is_file(), 'SSH_CONFIG')
    command = ['/usr/bin/ssh','-i',str(ssh_key),'-o','IdentitiesOnly=yes','-o','BatchMode=yes',
        '-o','StrictHostKeyChecking=yes','-o','UserKnownHostsFile='+str(known_hosts),'-o','ConnectTimeout=8',
        'family-restricted@186.246.45.246','restricted-sync']
    request = canonical(dict(schema=1,operation='READ_ONLY_SECURITY_SNAPSHOT'))
    with tempfile.TemporaryFile() as output:
        def bounded():
            resource.setrlimit(resource.RLIMIT_FSIZE,(65536,65536))
        try:
            result = subprocess.run(command,input=request,stdout=output,stderr=subprocess.DEVNULL,timeout=20,preexec_fn=bounded)
        except subprocess.TimeoutExpired:
            raise Rejected('GATEWAY_READ_UNAVAILABLE') from None
        require(result.returncode == 0, 'GATEWAY_READ_UNAVAILABLE')
        output.seek(0)
        value = parse(output.read(65537))
    require(set(value) == {'schema','profile','directory'} and value['schema'] == 1, 'GATEWAY_READ_SCHEMA')
    require('private_key' not in value['profile'], 'PRIVATE_MATERIAL_FORBIDDEN')
    return value


def inspect(node, remote, now):
    authority = node.public_authority()
    profile = remote['profile']
    snapshot = dict(schema=1,authority=authority['authority'],crl=authority['crl'],
                    certificate=profile['certificate'],grants=authority['grants'])
    validated = node.validator.validate(canonical(snapshot),now)
    require(profile['authority'] == validated[1]['authority'] and profile['revocations'] == authority['crl'], 'RU_NL_MISMATCH')
    require(all(profile[name] == validated[1][name] for name in ('family','gateway','minimum_revision')), 'GATEWAY_BINDING')
    result = evaluate(validated,now,revocations_changed=authority['pending_revocations'] > 0,
                      all_activated=node.validator.all_activated)
    if result['result'] != 'NOOP':
        result['result'] = 'MAINTENANCE_REQUIRED'
        result['alerts'].extend(['MAINTENANCE_REQUIRED','ACTIVE_SESSION_INVENTORY_UNAVAILABLE'])
        if min(result['headroom'].values()) <= 6*3600:
            result['alerts'].append('EXPIRY_IMMINENT_CRITICAL')
    result.update(mutations=0,remote_writes=0,restarts=0,crl_publications=0,remote_alert_delivery='UNAVAILABLE')
    return result,validated


def main():
    os.umask(0o077)
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    parser = argparse.ArgumentParser()
    parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--ssh-key',type=Path,required=True)
    parser.add_argument('--known-hosts',type=Path,required=True)
    parser.add_argument('--directory-only',action='store_true')
    args = parser.parse_args()
    try:
        node,_ = construct(args.config)
        require(node.role == 'RU', 'NODE_ROLE')
        if (node.state/'owner.json').exists():
            print(canonical(dict(result='MAINTENANCE_IN_PROGRESS',mutations=0)).decode())
            return
        remote = read_gateway(args.ssh_key,args.known_hosts)
        result,validated = inspect(node,remote,int(time.time()))
        if args.directory_only:
            from control.friends.restricted import directory
            from production_node import pinned
            from credential_renewal import atomic
            raw = base64.b64decode(remote['directory'],validate=True)
            directory(raw,validated[1]['family'],validated[1]['gateway'])
            path = node.live/'directory.json'
            previous,metadata = pinned(path,{0})
            if previous != raw:
                temporary = node.state/'directory.pending'
                atomic(temporary,raw)
                os.replace(temporary,path)
                for folder in (node.live,node.state):
                    descriptor = os.open(folder,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
                    try:
                        os.fsync(descriptor)
                    finally:
                        os.close(descriptor)
            result = dict(result='DIRECTORY_SYNCED',crl_publications=0,remote_writes=0,directory_sha256=digest(raw))
        print(canonical(result).decode())
        if result['result'] == 'MAINTENANCE_REQUIRED':
            raise SystemExit(75)
    except Exception as error:
        print(canonical(dict(result='FAIL_CLOSED',cause=str(error) if isinstance(error,Rejected) else 'UNKNOWN',
                             remote_alert_delivery='UNAVAILABLE',automatic_restart=False)).decode())
        raise SystemExit(1) from None


if __name__ == '__main__':
    main()
