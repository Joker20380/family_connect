"""Explicitly authorized independent test host only; never a production installer."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys

from scripts.prepare_ru_replacement import IMAGE
from scripts.test_paid_transport_systemd import execute


def interrupted(unused_signal, unused_frame):
    raise KeyboardInterrupt('Bounded replacement qualification interrupted')


def verify_distribution(root):
    manifest = json.loads((root/'distribution-inventory.json').read_text())
    for name, expected in manifest['files'].items():
        path = root/name
        if Path(name).is_absolute() or '..' in Path(name).parts or path.is_symlink() or not path.is_file():
            raise ValueError('UNSAFE_DISTRIBUTION_MEMBER')
        with path.open('rb') as handle:
            actual = hashlib.file_digest(handle, 'sha256').hexdigest()
        if actual != expected:
            raise ValueError('DISTRIBUTION_HASH_MISMATCH: '+name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--authorized-machine-id', required=True)
    parser.add_argument('--kit-root', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.authorized_machine_id != Path('/etc/machine-id').read_text().strip():
        raise SystemExit('HOST_AUTHORIZATION_MISMATCH')
    if Path('/opt/apps/family_connect').exists():
        raise SystemExit('EXISTING_PRODUCT_HOST_FORBIDDEN')
    if platform.machine() != 'x86_64' or sys.version_info[:2] != (3, 12):
        raise SystemExit('REQUIRES_X86_64_PYTHON_3_12')
    if not Path('/sys/fs/cgroup/cgroup.controllers').exists() or not Path('/dev/net/tun').exists():
        raise SystemExit('CGROUP_V2_AND_TUN_REQUIRED')
    root = args.kit_root.resolve()
    verify_distribution(root)
    image = subprocess.run(['docker', 'image', 'inspect', IMAGE, '--format', '{{.Id}}'],
        check=True, capture_output=True, timeout=15).stdout.decode().strip()
    if image != IMAGE:
        raise SystemExit('FIXTURE_IMAGE_MISMATCH')
    os.umask(0o077)
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGALRM, interrupted)
    signal.alarm(1500)
    try:
        result = execute(root/'kit', args.report, replacement_qualification=True)
    finally:
        signal.alarm(0)
    print(json.dumps(dict(result=result['result'], cleanup=result.get('cleanup'),
        scope='isolated replacement qualification; no production cutover')))
    return result['result'] != 'PASS'


if __name__ == '__main__':
    raise SystemExit(main())
