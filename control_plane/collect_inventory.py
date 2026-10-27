"""Operator-only SSH read; no SSH key or production DB is mounted in Django."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import secrets
import subprocess

HOSTS = {'gateway-ru': '185.251.89.19', 'gateway-nl': '186.246.45.246'}
BASE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description='Read-only инвентаризация разрешённых шлюзов; без remote файлов и команд изменения')
    parser.add_argument('source', choices=HOSTS)
    args = parser.parse_args()
    local = BASE / '.local'
    key_path = local / 'inventory-hmac.key'
    if any(parent.is_symlink() for parent in (key_path, *key_path.parents)):
        parser.error('Симлинки запрещены')
    local.mkdir(mode=0o700, exist_ok=True)
    if not key_path.exists():
        descriptor = os.open(key_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, 'wb') as handle:
            handle.write(secrets.token_bytes(32))
    if key_path.stat().st_mode & 0o077 or key_path.stat().st_size != 32:
        parser.error('Ключ HMAC должен содержать 32 байта и иметь права 0600')
    source = (BASE / 'apps/console/collector.py').read_text()
    source += f'\nprint(json.dumps(collect({args.source!r}, bytes.fromhex({key_path.read_bytes().hex()!r})), allow_nan=False))\n'
    try:
        result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=10',
            'root@' + HOSTS[args.source], 'python3 -B -'], input=source.encode(), capture_output=True, timeout=45)
        if result.returncode:
            parser.error('Read-only сбор не выполнен. Проверьте SSH доступ; предыдущие снимки не заменены.')
        data = json.loads(result.stdout)
        raw = json.dumps(data, ensure_ascii=False, allow_nan=False, indent=2).encode()
    except (OSError, ValueError, subprocess.TimeoutExpired):
        parser.error('Снимок не получен; предыдущие данные не изменены.')
    destination = local / (args.source + '-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f') + '.json')
    descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'wb') as handle:
        handle.write(raw + b'\n')
    print(destination)


if __name__ == '__main__':
    main()
