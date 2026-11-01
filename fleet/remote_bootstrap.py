"""Fixed SSH receiver. Verify the signed permit before any target filesystem write."""

import base64
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time


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
            or request['operation']['action'] not in ('stage', 'verify', 'activate-local', 'upgrade', 'rollback',
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
    if body['ipv4'] not in {entry['local'] for interface in addresses for entry in interface.get('addr_info', [])}:
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
    return agent


def secure_directory(path):
    for parent in [*reversed(path.parents), path]:
        if parent.is_symlink() or parent.exists() and (not parent.is_dir() or parent.stat().st_uid != 0
                                                      or parent.stat().st_mode & 0o022):
            raise ValueError('remote_operation_directory')
    path.mkdir(parents=True, mode=0o700, exist_ok=True)
    if path.stat().st_mode & 0o077:
        raise ValueError('remote_operation_mode')


def receive(request):
    agent = check(request)
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
    probe = subprocess.run(['python3', '-I', '-B', '-c', 'import cryptography'], capture_output=True, timeout=10)
    if probe.returncode or any(shutil.which(name) is None for name in ('zstd', 'nft', 'ip', 'curl')):
        if request['operation']['action'] != 'stage':
            raise ValueError('remote_runtime_dependency_required')
        environment = dict(PATH='/usr/sbin:/usr/bin:/sbin:/bin', LC_ALL='C', DEBIAN_FRONTEND='noninteractive')
        for argv in (['apt-get', 'update', '-qq'], ['apt-get', 'install', '-y', '--no-install-recommends',
                     'python3-cryptography', 'zstd', 'nftables', 'iproute2', 'curl', 'ca-certificates']):
            check(request)
            result = subprocess.run(argv, env=environment, capture_output=True, timeout=180)
            if result.returncode:
                raise ValueError('remote_runtime_package_install_failed')
    payload = dict(request)
    del payload['agent']
    result = subprocess.run(['python3', '-I', '-B', str(target)], input=canonical(payload), capture_output=True, timeout=600)
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
