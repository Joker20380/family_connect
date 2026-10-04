"""Bounded server-only synchronization using a dedicated forced-command SSH key."""
import argparse
import json
import os
import re
from pathlib import Path
import resource
import secrets
import sqlite3
import subprocess
import sys
import tempfile
import time

from cryptography import x509

from provisioning.friends_catalog import fields, parse, require
from .access import Access
from .restricted import MAX_TEST_LIFETIME, DirectoryValidationError, bounded_file, clock_nanoseconds, delegation, directory, from_env, iso, utc
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


def gateway(profile_path, directory_path, request, now=None):
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
    require(incoming.last_update_utc <= utc(time.time() if now is None else now) < incoming.next_update_utc)
    require(incoming.last_update_utc >= previous.last_update_utc)
    require((incoming.next_update_utc - incoming.last_update_utc).total_seconds() <= MAX_TEST_LIFETIME)
    if number == old_number:
        require(value['revocations'] == profile['revocations'])
    profile['revocations'], profile['minimum_crl'] = value['revocations'], number
    atomic(profile_path, json.dumps(profile, separators=(',', ':')).encode())
    raw = bounded_file(directory_path, 8192, True)
    directory(raw, profile['family'], profile['gateway'], now)
    return raw


def sync(access, host, ssh_key, known_hosts, *, crl_lifetime=900):
    require(host == '186.246.45.246')
    root = Path(os.environ['FC_FRIENDS_RESTRICTED_DIR'])
    service = from_env(access)
    publish_crl(service, root / 'revocations.pem', lifetime=crl_lifetime)
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
    directory(raw, trust['family'], trust['gateway'], now_ns=clock_nanoseconds(access.clock))
    atomic(root / 'directory.json', raw)


def check(access, host, ssh_key, known_hosts):
    require(host == '186.246.45.246' and access.path.is_file())
    service = from_env(access)
    _, _, _, _, number = service._trust(int(access.clock()))
    bounded_file(ssh_key, 4096, True)
    bounded_file(known_hosts, 16384)
    database = sqlite3.connect(access.path.resolve().as_uri() + '?mode=ro', uri=True)
    try:
        require(database.execute('SELECT sequence FROM restricted_crl_sequence WHERE singleton=1').fetchone() == (number,))
        require(database.execute('PRAGMA quick_check').fetchone() == ('ok',))
    finally:
        database.close()


def check_directory(profile_path, directory_path, receipt_path, generation, *, now_ns=None):
    require(type(generation) is str and re.fullmatch(r'[A-Za-z0-9_.-]{1,64}', generation))
    require(receipt_path.resolve() not in (profile_path.resolve(), directory_path.resolve()))
    record = dict(timestamp=iso(time.time()), generation=generation, result='failed')
    try:
        try:
            profile = parse(bounded_file(profile_path, 49152, True))
            family, gateway = profile['family'], profile['gateway']
            raw = bounded_file(directory_path, 8192, True)
        except (OSError, ValueError, TypeError, KeyError, RecursionError):
            raise DirectoryValidationError('input', 'unavailable_or_invalid_input', 'directory') from None
        instant = time.time_ns() if now_ns is None else now_ns
        record['observed_at_ns'] = instant
        directory(raw, family, gateway, now_ns=instant)
        record['result'] = 'passed'
    except DirectoryValidationError as error:
        record.update(stage=error.stage, predicate=error.predicate, field=error.field)
        raise
    finally:
        atomic(receipt_path, json.dumps(record, separators=(',', ':')).encode())
    return record


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
    worker.add_argument('--crl-lifetime', type=int, choices=(900, 3600, MAX_TEST_LIFETIME), default=900,
                        help='Signed CRL lifetime; testing policies require compatible clients and gateway')
    worker.add_argument('--check', action='store_true', help='Validate local inputs only; no publisher, SSH or writes')
    validator = commands.add_parser('directory-check', help='Read-only BOOT-1 validation; persist a redacted receipt before exit')
    validator.add_argument('--profile', type=Path, required=True)
    validator.add_argument('--directory', type=Path, required=True)
    validator.add_argument('--receipt', type=Path, required=True)
    validator.add_argument('--generation', required=True)
    args = parser.parse_args()
    try:
        if args.mode == 'directory-check':
            check_directory(args.profile, args.directory, args.receipt, args.generation)
            print('Restricted directory validation passed; receipt persisted')
        elif args.mode == 'gateway':
            import fcntl
            descriptor = os.open(args.profile.with_suffix('.sync-lock'), os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                sys.stdout.buffer.write(gateway(args.profile, args.directory, sys.stdin.buffer.read(20001)))
            finally:
                os.close(descriptor)
        elif args.check:
            check(Access(args.db), args.host, args.ssh_key, args.known_hosts)
            print('Restricted runtime pre-network check passed')
        else:
            sync(Access(args.db), args.host, args.ssh_key, args.known_hosts, crl_lifetime=args.crl_lifetime)
    except DirectoryValidationError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from None
    except Exception:
        print('Restricted synchronization unavailable', file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == '__main__':
    main()
