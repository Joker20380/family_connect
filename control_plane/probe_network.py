"""Independent local cycle: no SSH credentials, registry or VPN operations."""
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from control.capture_gate import external_operation
from control_plane.collector_admission import cycle_lock, run_cli

if __package__:
    from .apps.console.network_probe import ENDPOINTS, collect
else:
    from apps.console.network_probe import ENDPOINTS, collect

BASE = Path(__file__).resolve().parent


def cycle(base=BASE, probe=collect, run=subprocess.run):
    run = external_operation()(run)
    with cycle_lock(base, 'network-probe.lock'):
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
    raise SystemExit(run_cli(main))
