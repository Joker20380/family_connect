import argparse
import base64
import json
import os
from pathlib import Path
import resource
import re
import subprocess
import sys
import tempfile
import time

from credential_renewal import MAX_BYTES, Rejected, canonical, digest, evaluate, parse, read_private, require
from node import construct
from production_transport import snapshot_command, ssh_route

GATEWAYS = ('nl-amsterdam-1', 'nl-amsterdam-2')


def gateway_routes(raw, primary_route):
    value = parse(raw)
    require(type(value) is dict and set(value) == {'schema','gateways'}
            and type(value['schema']) is int and value['schema'] == 1
            and type(value['gateways']) is dict and set(value['gateways']) == set(GATEWAYS), 'GATEWAY_ROUTES_SCHEMA')
    routes = value['gateways']
    for entry in routes.values():
        require(type(entry) is dict and set(entry) == {'gateway','ssh'}
                and type(entry['gateway']) is str and re.fullmatch('[0-9a-f]{32}',entry['gateway']),
                'GATEWAY_ROUTES_SCHEMA')
        ssh_route(entry['ssh'],forced=True)
    require(routes[GATEWAYS[0]]['ssh'] == primary_route, 'PRIMARY_ROUTE_CHANGED')
    require(len({entry['gateway'] for entry in routes.values()}) == 2
            and len({entry['ssh']['target'].split('@')[-1] for entry in routes.values()}) == 2,
            'GATEWAY_ROUTES_DUPLICATE')
    return routes


def read_gateway(ssh_key, known_hosts, target):
    command = snapshot_command(dict(key=str(ssh_key),known_hosts=str(known_hosts),target=target))
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


def inspect(node, remote, now, *, authority=None, manifest=None):
    authority = node.public_authority() if authority is None else authority
    profile = remote['profile']
    snapshot = dict(schema=1,authority=authority['authority'] if manifest is None else manifest,crl=authority['crl'],
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


def inspect_gateway(node, remote, authority, manifest, expected_gateway, now, *, now_ns=None):
    from cryptography import x509
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
    from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID
    from control.friends.restricted import PROTOCOL, directory
    profile = remote['profile']
    require(type(profile) is dict and set(profile) == {'authority','certificate','revocations','family',
            'gateway','minimum_revision','minimum_crl'}, 'GATEWAY_PROFILE_SCHEMA')
    require(type(profile['minimum_revision']) is int, 'GATEWAY_PROFILE_SCHEMA')
    result,validated = inspect(node,remote,now,authority=authority,manifest=manifest)
    _,trust,_,crl,leaf = validated
    require(trust['gateway'] == expected_gateway, 'GATEWAY_BINDING')
    sequence = crl.extensions.get_extension_for_class(x509.CRLNumber).value.crl_number
    require(type(profile['minimum_crl']) is int and 0 < profile['minimum_crl'] <= sequence, 'GATEWAY_CRL_FLOOR')
    require(crl.get_revoked_certificate_by_serial_number(leaf.serial_number) is None, 'GATEWAY_REVOKED')
    claims = [attribute.value for attribute in leaf.subject.get_attributes_for_oid(NameOID.ORGANIZATIONAL_UNIT_NAME)]
    revisions = [claim.removeprefix('revision=') for claim in claims if claim.startswith('revision=')]
    require(len(claims) == 4 and len(revisions) == 1 and re.fullmatch('[0-9]{1,19}',revisions[0])
            and trust['minimum_revision'] <= int(revisions[0]) <= 2**63-1
            and set(claims) == {'protocol='+PROTOCOL,'family='+trust['family'],'role=gateway','revision='+revisions[0]}
            and [attribute.value for attribute in leaf.subject.get_attributes_for_oid(NameOID.SERIAL_NUMBER)]
                == [expected_gateway], 'GATEWAY_CERTIFICATE_BINDING')
    require(not leaf.extensions.get_extension_for_class(x509.BasicConstraints).value.ca
            and list(leaf.extensions.get_extension_for_class(x509.ExtendedKeyUsage).value)
                == [ExtendedKeyUsageOID.SERVER_AUTH], 'GATEWAY_CERTIFICATE_ROLE')
    identities = leaf.extensions.get_extension_for_class(x509.SubjectAlternativeName).value.get_values_for_type(
        x509.UniformResourceIdentifier)
    prefix = 'urn:family-connect:identity:'
    require(len(identities) == 1 and re.fullmatch(prefix+'[0-9a-f]{128}',identities[0]), 'GATEWAY_CERTIFICATE_IDENTITY')
    public = bytes.fromhex(identities[0][len(prefix):])
    require(digest(public)[:32] == expected_gateway
            and leaf.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw) == public[32:],
            'GATEWAY_CERTIFICATE_IDENTITY')
    raw = base64.b64decode(remote['directory'],validate=True)
    directory(raw,trust['family'],expected_gateway,now_ns=now*1_000_000_000 if now_ns is None else now_ns)
    return result,raw,trust


def publish_gateway_directory(node, gateway_id, expected_gateway, family, raw, now_ns):
    from credential_renewal import atomic
    from control.friends.restricted import directory, timestamp_ns
    from production_node import pinned
    require(gateway_id in GATEWAYS, 'GATEWAY_BINDING')
    folder = node.live if gateway_id == GATEWAYS[0] else node.live/'gateways'/gateway_id
    path = folder/'directory.json'
    previous,_ = pinned(path,{os.geteuid()})
    incoming = directory(raw,family,expected_gateway,now_ns=now_ns)
    retained = directory(previous,family,expected_gateway,now_ns=timestamp_ns(json.loads(previous)['issued_at']))
    require(timestamp_ns(incoming['issued_at']) >= timestamp_ns(retained['issued_at']), 'DIRECTORY_ROLLBACK')
    require(timestamp_ns(incoming['issued_at']) != timestamp_ns(retained['issued_at']) or incoming == retained,
            'DIRECTORY_CONFLICT')
    if previous != raw:
        temporary = node.state/(gateway_id+'-directory.pending')
        atomic(temporary,raw)
        os.replace(temporary,path)
        for parent in (folder,node.state):
            descriptor = os.open(parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
    return dict(result='DIRECTORY_SYNCED',directory_sha256=digest(raw),files_changed=int(previous != raw))


def inspect_gateways(node, routes, *, directory_only=False):
    from control.friends.restricted import clock_nanoseconds
    from production_node import pinned
    require(node.role == 'RU' and set(routes) == set(GATEWAYS), 'GATEWAY_ROUTES_SCHEMA')
    with node.operation.lock():
        if (node.state/'owner.json').exists():
            return dict(result='MAINTENANCE_IN_PROGRESS',mutations=0)
        authority = node.public_authority()
        primary,_ = node.validator.delegation_parser(authority['authority'],node.validator.anchor,int(node.clock()))
        results = {}
        for gateway_id in GATEWAYS:
            try:
                manifest = authority['authority']
                if gateway_id != GATEWAYS[0]:
                    manifest = json.loads(pinned(node.live/'gateways'/gateway_id/'issuer.json',{os.geteuid()})[0])
                    selected,_ = node.validator.delegation_parser(manifest,node.validator.anchor,int(node.clock()))
                    require(all(selected[name] == primary[name] for name in ('family','authority','minimum_revision'))
                            and selected['gateway'] != primary['gateway'], 'GATEWAY_AUTHORITY_BINDING')
                route = routes[gateway_id]
                remote = read_gateway(**dict(ssh_key=route['ssh']['key'],known_hosts=route['ssh']['known_hosts'],
                                             target=route['ssh']['target']))
                now_ns = clock_nanoseconds(node.clock)
                now = now_ns//1_000_000_000
                node.validator.delegation_parser(authority['authority'],node.validator.anchor,now)
                result,raw,trust = inspect_gateway(node,remote,authority,manifest,route['gateway'],now,now_ns=now_ns)
                if directory_only:
                    credentials = result
                    result = publish_gateway_directory(node,gateway_id,route['gateway'],trust['family'],raw,now_ns)
                    result['credentials'] = credentials
                results[gateway_id] = result
            except Exception as error:
                results[gateway_id] = dict(result='FAIL_CLOSED',cause=str(error) if isinstance(error,Rejected) else 'UNKNOWN')
        healthy = all(value['result'] in ('NOOP','DIRECTORY_SYNCED') for value in results.values())
        return dict(result=('DIRECTORIES_SYNCED' if directory_only else 'NOOP') if healthy else 'GATEWAY_CHECK_REQUIRED',
                    gateways=results,remote_writes=0,restarts=0,crl_publications=0,
                    files_changed=sum(value.get('files_changed',0) for value in results.values()))


def main():
    os.umask(0o077)
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    parser = argparse.ArgumentParser()
    parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--ssh-key',type=Path,required=True)
    parser.add_argument('--known-hosts',type=Path,required=True)
    parser.add_argument('--directory-only',action='store_true')
    parser.add_argument('--gateway-routes',type=Path)
    args = parser.parse_args()
    try:
        node,_ = construct(args.config)
        require(node.role == 'RU', 'NODE_ROLE')
        if args.gateway_routes is not None:
            routes = gateway_routes(read_private(args.gateway_routes),dict(key=str(args.ssh_key),
                known_hosts=str(args.known_hosts),target=node.snapshot_target))
            result = inspect_gateways(node,routes,directory_only=args.directory_only)
            print(canonical(result).decode())
            if result['result'] == 'GATEWAY_CHECK_REQUIRED':
                raise SystemExit(75)
            return
        if (node.state/'owner.json').exists():
            print(canonical(dict(result='MAINTENANCE_IN_PROGRESS',mutations=0)).decode())
            return
        remote = read_gateway(args.ssh_key,args.known_hosts,node.snapshot_target)
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
