"""Fixed SSH receiver. Verify the signed permit before any target filesystem write."""

import base64
import ctypes
import hashlib
import io
import ipaddress
import json
import os
from pathlib import Path
import platform
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import time
import zipfile


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode()


def openssl_verify(public, signature, payload):
    descriptors = []
    try:
        for name, value in (('key', bytes.fromhex('302a300506032b6570032100') + public),
                            ('signature', signature), ('payload', payload)):
            descriptor = os.memfd_create('fleet-' + name, os.MFD_CLOEXEC)
            descriptors.append(descriptor)
            os.write(descriptor, value)
            os.lseek(descriptor, 0, os.SEEK_SET)
        result = subprocess.run(['openssl', 'pkeyutl', '-verify', '-pubin', '-keyform', 'DER',
            '-inkey', '/proc/self/fd/'+str(descriptors[0]), '-rawin',
            '-sigfile', '/proc/self/fd/'+str(descriptors[1]), '-in', '/proc/self/fd/'+str(descriptors[2])],
            pass_fds=descriptors, capture_output=True, timeout=10)
        if result.returncode:
            raise ValueError('rehearsal_permit_signature')
    finally:
        for descriptor in descriptors:
            os.close(descriptor)


def check(request):
    permit = request['permit']
    body = permit['body']
    public = bytes.fromhex(request['permit_key'])
    if len(public) != 32:
        raise ValueError('permit_key')
    openssl_verify(public, base64.b64decode(permit['signature'], validate=True), canonical(body))
    now = time.time()
    if (body['schema'] != 1 or body['scope'] != 'DISPOSABLE_FLEET_REHEARSAL'
            or not re.fullmatch(r'fleet-rehearsal-[a-z0-9-]+', body['instance_id'])
            or body['logical_gateway'] != 'fleet-rehearsal'
            or not body['issued_at'] <= now < body['expires_at']
            or not 0 < body['expires_at'] - body['issued_at'] <= 14400
            or any(body[field] is not False for field in ('catalog_publication', 'production_identity_import',
                                                        'user_operations', 'paid_operations'))
            or request['operation']['action'] not in body['allowed_actions']
            or request['operation']['action'] not in ('enroll', 'deliver-materials', 'stage', 'start-verification',
                'complete-verification', 'activate-local', 'status', 'upgrade', 'rollback',
                'reboot-verify', 'drain', 'retire')
            or request['operation']['bundle_id'] not in (body['bundle_a'], body['bundle_b'])):
        raise ValueError('rehearsal_permit_binding')
    address = ipaddress.IPv4Address(body['ipv4'])
    if not address.is_global or str(address) in ('185.251.89.19', '185.10.158.212', '186.246.45.246', '186.246.51.201'):
        raise ValueError('production_or_nonpublic_target')
    if hashlib.sha256(bytes.fromhex(request['bundle_key'])).hexdigest() != body['bundle_signer_sha256']:
        raise ValueError('bundle_key_binding')
    agent = base64.b64decode(request['agent'], validate=True)
    if len(agent) > 2*1024*1024 or hashlib.sha256(agent).hexdigest() != body['agent_sha256']:
        raise ValueError('remote_agent_hash')
    addresses = json.loads(subprocess.check_output(['ip', '-j', 'address', 'show'], timeout=5))
    found = {entry['local'] for interface in addresses for entry in interface.get('addr_info', [])}
    if body['ipv4'] not in found or found & {'185.251.89.19','185.10.158.212','186.246.45.246','186.246.51.201'}:
        raise ValueError('remote_host_binding')
    fingerprints = []
    for path in Path('/etc/ssh').glob('ssh_host_*_key.pub'):
        result = subprocess.run(['ssh-keygen', '-lf', str(path), '-E', 'sha256'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and len(result.stdout.split()) >= 2:
            fingerprints.append(result.stdout.split()[1])
    if body['ssh_fingerprint'] not in fingerprints:
        raise ValueError('ssh_fingerprint_mismatch')
    if os.geteuid() != 0:
        raise ValueError('root_required')
    release = dict(line.split('=',1) for line in Path('/etc/os-release').read_text().splitlines() if '=' in line)
    if release.get('ID','').strip('"') != 'ubuntu' or release.get('VERSION_ID','').strip('"') != '24.04':
        raise ValueError('unsupported_os')
    if platform.machine() != 'x86_64':
        raise ValueError('unsupported_architecture')
    tun = Path('/dev/net/tun')
    if not tun.exists() or not stat.S_ISCHR(tun.stat().st_mode):
        raise ValueError('missing_tun')
    if Path('/opt/apps/family_connect').exists():
        raise ValueError('existing_family_connect_installation')
    existing = Path('/var/lib/family-connect/instance.json')
    if existing.exists() and json.loads(existing.read_bytes()).get('instance_id') != body['instance_id']:
        raise ValueError('private_identity_conflict')
    return agent


def secure_directory(path):
    for parent in [*reversed(path.parents), path]:
        if parent.is_symlink() or parent.exists() and (not parent.is_dir() or parent.stat().st_uid != 0
                                                      or parent.stat().st_mode & 0o022):
            raise ValueError('remote_operation_directory')
    path.mkdir(parents=True, mode=0o700, exist_ok=True)
    if path.stat().st_mode & 0o077:
        raise ValueError('remote_operation_mode')


def verify_bundle_payload(request):
    bundle_id = request['operation']['bundle_id']
    archive_name = 'fc-gateway-'+bundle_id+'.tar.zst'
    files = request['bundle']
    if set(files) != {'manifest.json','manifest.sig','sha256.json',archive_name}:
        raise ValueError('remote_bundle_files')
    decoded = {name:base64.b64decode(value, validate=True) for name,value in files.items()}
    payload = decoded['manifest.json']
    openssl_verify(bytes.fromhex(request['bundle_key']),
                   base64.b64decode(decoded['manifest.sig'], validate=True), payload)
    manifest = json.loads(payload)
    fields = ('schema','source_commit','scope','supported_os','architecture','roles','secret_slots','members')
    if set(manifest) != set(fields) | {'bundle_id','archive_sha256'} or payload != canonical(manifest):
        raise ValueError('remote_manifest_contract')
    core = {name:manifest[name] for name in fields}
    if (manifest['schema'] != 1 or manifest['scope'] != 'rehearsal'
            or manifest['supported_os'] != ['ubuntu-24.04'] or manifest['architecture'] != 'x86_64'
            or manifest['bundle_id'] != bundle_id
            or bundle_id != 'gw-'+hashlib.sha256(canonical(core)).hexdigest()[:32]):
        raise ValueError('remote_manifest_binding')
    archive = decoded[archive_name]
    if len(archive) > 128*1024*1024 or hashlib.sha256(archive).hexdigest() != manifest['archive_sha256']:
        raise ValueError('remote_archive_hash')
    expected_hashes = {name:hashlib.sha256(decoded[name]).hexdigest() for name in (archive_name,'manifest.json','manifest.sig')}
    if json.loads(decoded['sha256.json']) != expected_hashes:
        raise ValueError('remote_hash_inventory')
    library = ctypes.CDLL('libzstd.so.1')
    library.ZSTD_decompress.argtypes = (ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t)
    library.ZSTD_decompress.restype = ctypes.c_size_t
    library.ZSTD_isError.argtypes = (ctypes.c_size_t,)
    library.ZSTD_isError.restype = ctypes.c_uint
    output = ctypes.create_string_buffer(128*1024*1024)
    size = library.ZSTD_decompress(output,len(output),archive,len(archive))
    if library.ZSTD_isError(size) or size > len(output):
        raise ValueError('remote_archive_codec')
    members = manifest['members']
    if not isinstance(members,list) or not 1 <= len(members) <= 1024:
        raise ValueError('remote_member_count')
    expected = {item['path']:item for item in members}
    if len(expected) != len(members) or list(expected) != sorted(expected):
        raise ValueError('remote_member_order')
    seen = []
    verified = {}
    with tarfile.open(fileobj=io.BytesIO(output.raw[:size]),mode='r:') as stream:
        for member in stream:
            name = member.name
            if (not member.isreg() or name not in expected or name in seen or name.startswith('/')
                    or any(part in ('','.','..') for part in name.split('/'))
                    or member.size > 64*1024*1024 or member.uid != 0 or member.gid != 0 or member.mtime != 0):
                raise ValueError('remote_archive_member')
            declared = expected[name]
            if (declared['target'] != 'RELEASE/'+name or member.mode not in (0o444,0o555)
                    or declared['mode'] != member.mode or declared['size'] != member.size
                    or declared['owner'] != 'root' or declared['group'] != 'root'
                    or hashlib.sha256(stream.extractfile(member).read()).hexdigest() != declared['sha256']):
                raise ValueError('remote_member_hash_or_mode')
            seen.append(name)
            verified[name] = stream.extractfile(member).read()
    if seen != list(expected):
        raise ValueError('remote_member_inventory')
    return verified


def python_dependencies(contents, directory):
    metadata = json.loads(contents['metadata/python-dependencies.json'])
    if metadata['python'] != '3.12' or sys.version_info[:2] != (3, 12):
        raise ValueError('remote_python_version')
    destination = directory / ('python-' + hashlib.sha256(canonical(metadata)).hexdigest())
    expected = {}
    for record in metadata['wheels']:
        content = contents[record['path']]
        if hashlib.sha256(content).hexdigest() != record['sha256']:
            raise ValueError('remote_dependency_binding')
        with zipfile.ZipFile(io.BytesIO(content)) as wheel:
            for member in wheel.infolist():
                if member.is_dir():
                    continue
                path = Path(member.filename)
                if (path.is_absolute() or any(part in ('.', '..') for part in path.parts)
                        or str(path) != member.filename or member.file_size > 32*1024*1024
                        or stat.S_ISLNK(member.external_attr >> 16) or member.filename in expected):
                    raise ValueError('remote_dependency_path')
                expected[member.filename] = wheel.read(member)
    if not destination.exists():
        pending = destination.with_name(destination.name + '.pending')
        if pending.exists() or pending.is_symlink():
            raise ValueError('remote_dependency_interrupted')
        pending.mkdir(mode=0o700)
        for name, content in expected.items():
            target = pending/name
            target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            with target.open('xb') as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            target.chmod(0o444)
        for path in sorted((path for path in pending.rglob('*') if path.is_dir()), key=lambda path:len(path.parts), reverse=True)+[pending]:
            descriptor=os.open(path,os.O_RDONLY|os.O_DIRECTORY)
            os.fsync(descriptor)
            os.close(descriptor)
            path.chmod(0o500)
        os.rename(pending,destination)
        descriptor=os.open(directory,os.O_RDONLY|os.O_DIRECTORY)
        os.fsync(descriptor)
        os.close(descriptor)
    if destination.is_symlink() or destination.stat().st_uid != 0 or stat.S_IMODE(destination.stat().st_mode)!=0o500:
        raise ValueError('remote_dependency_root')
    observed = set()
    for path in destination.rglob('*'):
        info=path.lstat()
        if path.is_symlink() or info.st_uid!=0:
            raise ValueError('remote_dependency_ownership')
        if path.is_dir():
            if stat.S_IMODE(info.st_mode)!=0o500:
                raise ValueError('remote_dependency_directory_mode')
            continue
        name=str(path.relative_to(destination))
        if (name not in expected or not stat.S_ISREG(info.st_mode) or info.st_nlink!=1
                or stat.S_IMODE(info.st_mode)!=0o444 or path.read_bytes()!=expected[name]):
            raise ValueError('remote_dependency_tamper')
        observed.add(name)
    if observed!=set(expected):
        raise ValueError('remote_dependency_inventory')
    return destination


def receive(request):
    agent = check(request)
    contents = verify_bundle_payload(request)
    body = request['permit']['body']
    directory = Path('/var/lib/family-connect-rehearsal') / body['instance_id']
    secure_directory(directory)
    target = directory / ('agent-' + body['agent_sha256'] + '.pyz')
    if target.exists() or target.is_symlink():
        if (target.is_symlink() or not target.is_file() or target.stat().st_uid != 0
                or target.stat().st_nlink != 1 or target.stat().st_mode & 0o777 != 0o500
                or target.read_bytes() != agent):
            raise ValueError('remote_agent_tamper')
    else:
        with os.fdopen(os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o500), 'wb') as output:
            output.write(agent)
            output.flush()
            os.fsync(output.fileno())
    if hashlib.sha256(target.read_bytes()).hexdigest() != body['agent_sha256']:
        raise ValueError('remote_agent_readback')
    response = dict(agent_sha256=body['agent_sha256'], mode='0500', scope=body['scope'])
    if request['upload_only'] is True:
        return response
    if any(shutil.which(name) is None for name in ('zstd', 'nft', 'ip', 'curl')):
        if request['operation']['action'] not in ('enroll', 'stage'):
            raise ValueError('remote_runtime_dependency_required')
        environment = dict(PATH='/usr/sbin:/usr/bin:/sbin:/bin', LC_ALL='C', DEBIAN_FRONTEND='noninteractive')
        for argv in (['apt-get', 'update', '-qq'], ['apt-get', 'install', '-y', '--no-install-recommends',
                     'zstd', 'nftables', 'iproute2', 'curl', 'ca-certificates']):
            check(request)
            result = subprocess.run(argv, env=environment, capture_output=True, timeout=180)
            if result.returncode:
                raise ValueError('remote_runtime_package_install_failed')
    payload = dict(request)
    del payload['agent']
    dependencies=python_dependencies(contents,directory)
    launcher="import sys,runpy;sys.path.insert(0,sys.argv.pop(1));runpy.run_path(sys.argv[1],run_name='__main__')"
    check(request)
    result = subprocess.run(['python3', '-I', '-B', '-c', launcher, str(dependencies), str(target)], input=canonical(payload), capture_output=True, timeout=600)
    if result.returncode:
        raise ValueError('remote_agent_failed')
    return json.loads(result.stdout)


if __name__ == '__main__':
    try:
        request = json.loads(sys.stdin.buffer.read(192*1024*1024))
        print(json.dumps(receive(request), sort_keys=True))
    except Exception:
        print('{"error":"remote_bootstrap_rejected"}')
        raise SystemExit(1)
