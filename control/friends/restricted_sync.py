"""Bounded server-only synchronization using a dedicated forced-command SSH key."""
import argparse
import json
import os
from pathlib import Path
import resource
import secrets
import subprocess
import sys
import tempfile
import time

from cryptography import x509

from provisioning.friends_catalog import fields, parse, require
from .access import Access
from .restricted import bounded_file, delegation, directory, from_env, utc
from .restricted_admin import publish_crl


def atomic(path, raw):
    pending = path.with_name(path.name + '.' + secrets.token_hex(8))
    descriptor = os.open(pending, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(descriptor, 'wb') as output:
            output.write(raw)
            output.flush()
            os.fsync(output.fileno())
        os.replace(pending, path)
        folder = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(folder)
        finally:
            os.close(folder)
    finally:
        if pending.exists():
            pending.unlink()


def gateway(profile_path, directory_path, request, now):
    require(len(request) <= 20000)
    value = parse(request)
    fields(value, 'revocations')
    profile = parse(bounded_file(profile_path, 49152, True))
    require(type(value['revocations']) is str and len(value['revocations']) <= 16384)
    ca = x509.load_pem_x509_certificate(profile['authority'].encode())
    incoming = x509.load_pem_x509_crl(value['revocations'].encode())
    from cryptography.hazmat.primitives.serialization import Encoding
    require(value['revocations'] == incoming.public_bytes(Encoding.PEM).decode())
    previous = x509.load_pem_x509_crl(profile['revocations'].encode())
    require(incoming.is_signature_valid(ca.public_key()) and incoming.issuer == ca.subject)
    require(previous.is_signature_valid(ca.public_key()))
    number = incoming.extensions.get_extension_for_class(x509.CRLNumber).value.crl_number
    old_number = previous.extensions.get_extension_for_class(x509.CRLNumber).value.crl_number
    require(number >= max(old_number, profile['minimum_crl']))
    require(incoming.last_update_utc <= utc(now) < incoming.next_update_utc)
    require(incoming.last_update_utc >= previous.last_update_utc)
    require((incoming.next_update_utc - incoming.last_update_utc).total_seconds() <= 3600)
    if number == old_number:
        require(value['revocations'] == profile['revocations'])
    profile['revocations'], profile['minimum_crl'] = value['revocations'], number
    atomic(profile_path, json.dumps(profile, separators=(',', ':')).encode())
    raw = bounded_file(directory_path, 8192, True)
    directory(raw, profile['family'], profile['gateway'], now)
    return raw


def sync(access, host, ssh_key, known_hosts):
    require(host == '186.246.45.246')
    root = Path(os.environ['FC_FRIENDS_RESTRICTED_DIR'])
    service = from_env(access)
    publish_crl(service, root / 'revocations.pem')
    trust, _ = delegation(service.manifest, service.anchor, int(access.clock()))
    command = ['/usr/bin/ssh', '-i', str(ssh_key), '-o', 'IdentitiesOnly=yes', '-o', 'BatchMode=yes',
               '-o', 'StrictHostKeyChecking=yes', '-o', 'UserKnownHostsFile=' + str(known_hosts),
               '-o', 'ConnectTimeout=5', 'family-restricted@' + host, 'restricted-sync']
    request = json.dumps(dict(revocations=service.crl_source().decode())).encode()
    with tempfile.TemporaryFile() as output:
        result = subprocess.run(command, input=request, stdout=output, stderr=subprocess.DEVNULL, timeout=15,
                                preexec_fn=lambda: resource.setrlimit(resource.RLIMIT_FSIZE, (20000, 20000)))
        require(result.returncode == 0)
        output.seek(0)
        raw = output.read(8193)
    directory(raw, trust['family'], trust['gateway'], int(access.clock()))
    atomic(root / 'directory.json', raw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='mode', required=True)
    remote = commands.add_parser('gateway')
    remote.add_argument('--profile', type=Path, required=True)
    remote.add_argument('--directory', type=Path, required=True)
    worker = commands.add_parser('sync')
    worker.add_argument('--db', type=Path, required=True)
    worker.add_argument('--host', required=True)
    worker.add_argument('--ssh-key', type=Path, required=True)
    worker.add_argument('--known-hosts', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.mode == 'gateway':
            import fcntl
            descriptor = os.open(args.profile.with_suffix('.sync-lock'), os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                sys.stdout.buffer.write(gateway(args.profile, args.directory, sys.stdin.buffer.read(20001), int(time.time())))
            finally:
                os.close(descriptor)
        else:
            sync(Access(args.db), args.host, args.ssh_key, args.known_hosts)
    except Exception:
        print('Restricted synchronization unavailable', file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == '__main__':
    main()
