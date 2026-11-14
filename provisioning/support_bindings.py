"""Operator-side pinned read only; neither Django nor the sender gets SSH or HMAC keys."""
import argparse
import ipaddress
import json
import os
from pathlib import Path
import resource
import stat
import subprocess
import tempfile
import time


def limit_output():
    resource.setrlimit(resource.RLIMIT_FSIZE, (512 * 1024 + 1, 512 * 1024 + 1))


def collect(host, key, known_hosts, output, *, command='support-bindings'):
    host = str(ipaddress.IPv4Address(host))
    for path in (key, known_hosts):
        if not path.is_absolute() or path.is_symlink() or not path.is_file():
            raise ValueError('Pinned credential files required')
    info = key.stat()
    if info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError('Private restricted SSH credential required')
    if any(path.is_symlink() for path in (output, *output.parents)):
        raise ValueError('Trusted output directory required')
    parent = output.parent.stat()
    if not stat.S_ISDIR(parent.st_mode) or parent.st_uid != os.getuid() or parent.st_mode & 0o022:
        raise ValueError('Trusted output directory required')
    with tempfile.TemporaryFile() as response:
        result = subprocess.run(['/usr/bin/ssh', '-T', '-i', str(key), '-o', 'IdentitiesOnly=yes', '-o',
            'BatchMode=yes', '-o', 'ConnectTimeout=5', '-o', 'StrictHostKeyChecking=yes',
            '-o', 'UserKnownHostsFile='+str(known_hosts), 'root@'+host, command],
            stdin=subprocess.DEVNULL, stdout=response, stderr=subprocess.DEVNULL, timeout=12, preexec_fn=limit_output)
        if result.returncode or response.tell() > 512 * 1024:
            raise ValueError('Binding projection unavailable')
        response.seek(0)
        raw = response.read(512 * 1024 + 1)
    document = json.loads(raw)
    if (type(document) is not dict or type(document.get('expires_at')) is not int
            or not time.time() < document['expires_at'] <= time.time() + 120):
        raise ValueError('Fresh projection required')
    descriptor, temporary = tempfile.mkstemp(prefix='.bindings-', dir=output.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            os.fchown(stream.fileno(), -1, parent.st_gid)
            os.fchmod(stream.fileno(), 0o640)
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, output)
        directory = os.open(output.parent, os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', required=True)
    for name in ('key', 'known-hosts', 'output'):
        parser.add_argument('--'+name, required=True, type=Path)
    args = parser.parse_args()
    try:
        collect(args.host, args.key, args.known_hosts, args.output)
    except Exception:
        parser.exit(1, 'Support binding refresh unavailable; previous lease is not extended.\n')


if __name__ == '__main__':
    main()
