"""Independent local cycle: no SSH credentials, registry or VPN operations."""
import fcntl
import json
import os
from pathlib import Path
import subprocess

if __package__:
    from .apps.console.network_probe import ENDPOINTS, collect
else:
    from apps.console.network_probe import ENDPOINTS, collect

BASE = Path(__file__).resolve().parent


def cycle(base=BASE, probe=collect, run=subprocess.run):
    local = base / '.local'
    if any(parent.is_symlink() for parent in (local, *local.parents)):
        raise ValueError('Unsafe local directory')
    local.mkdir(mode=0o700, exist_ok=True)
    descriptor = os.open(local / 'network-probe.lock', os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        results = []
        for source in ENDPOINTS:
            sample = probe(source)
            status = 'IMPORTED'
            try:
                run(['docker', 'compose', '-f', str(base / 'compose.yaml'), '--env-file', str(base / '.env'),
                    'exec', '-T', 'console', 'python', 'manage.py', 'import_network_probe'],
                    input=json.dumps(sample, allow_nan=False).encode(), capture_output=True, check=True, timeout=20)
            except (OSError, subprocess.SubprocessError):
                status = 'IMPORT_FAILED'
            results.append(dict(source=source, observed_at=sample['observed_at'], outcome=sample['outcome'], status=status))
        return dict(schema=1, sources=results, automatic_actions=0, vpn_readiness='not_checked')


def main():
    try:
        receipt = cycle()
    except BlockingIOError:
        print('Независимая сетевая проверка уже выполняется.')
        return 0
    print(json.dumps(receipt, allow_nan=False))
    return int(any(item['status'] != 'IMPORTED' for item in receipt['sources']))


if __name__ == '__main__':
    raise SystemExit(main())
