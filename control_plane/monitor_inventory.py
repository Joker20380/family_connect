"""One bounded read-only SSH collection cycle and local PostgreSQL import."""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

if __package__:
    from .apps.console.collector import ACTIVE_SOURCES
else:
    from apps.console.collector import ACTIVE_SOURCES

BASE = Path(__file__).resolve().parent
SOURCES = ACTIVE_SOURCES


def instant():
    return datetime.now(timezone.utc).isoformat()


def cycle(base=BASE, run=subprocess.run, known_hosts=None):
    local = base / '.local'
    local.mkdir(mode=0o700, exist_ok=True)
    if any(parent.is_symlink() for parent in (local, *local.parents)):
        raise ValueError('Unsafe local directory')
    descriptor = os.open(local / 'monitor.lock', os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        results = []
        for source in SOURCES:
            result = dict(source=source, attempted_at=instant(), status='FAILED', error='COLLECTION_FAILED')
            snapshot = None
            try:
                command = [sys.executable, str(base / 'collect_inventory.py')]
                if known_hosts is not None:
                    command += ['--known-hosts', str(known_hosts)]
                collected = run(command + [source],
                    capture_output=True, check=True, timeout=60)
                candidate = Path(collected.stdout.decode().strip())
                if (candidate.parent != local or not candidate.name.startswith(source + '-')
                        or candidate.suffix != '.json' or candidate.is_symlink()):
                    raise ValueError('Unexpected snapshot path')
                snapshot = candidate
                if not snapshot.is_file() or snapshot.stat().st_size > 4 * 1024 * 1024:
                    raise ValueError('Invalid snapshot file')
                raw = snapshot.read_bytes()
                document = json.loads(raw)
                if document.get('source') != source or document.get('scope') != 'production':
                    raise ValueError('Invalid snapshot scope')
                result['error'] = 'IMPORT_FAILED'
                run(['docker', 'compose', '-f', str(base / 'compose.yaml'), '--env-file', str(base / '.env'),
                    'exec', '-T', 'console', 'python', 'manage.py', 'import_inventory'],
                    input=raw, capture_output=True, check=True, timeout=60)
                result.update(status='IMPORTED', error=None, observed_at=document['observed_at'],
                    registry_status=document['registry_status'], sha256=hashlib.sha256(raw).hexdigest())
            except (OSError, ValueError, KeyError, subprocess.SubprocessError):
                pass
            finally:
                if snapshot is not None:
                    snapshot.unlink(missing_ok=True)
            results.append(result)
        receipt = dict(schema=1, completed_at=instant(), production_writes=0, sources=results,
            limitations=['Client telemetry NOT_COLLECTED', 'Local workstation must stay awake',
                'SSH credential is administrative; commands are read-only, credential is not read-only'])
        temporary = local / 'monitor-latest.tmp'
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
        with os.fdopen(descriptor, 'w') as handle:
            json.dump(receipt, handle, ensure_ascii=False, indent=2, allow_nan=False)
            handle.write('\n')
        temporary.replace(local / 'monitor-latest.json')
        return receipt


def main():
    parser = argparse.ArgumentParser(description='Один read-only цикл наблюдения действующих узлов')
    parser.add_argument('--known-hosts', type=Path, help='Существующий файл проверенных SSH host pins для всех узлов')
    args = parser.parse_args()
    try:
        receipt = cycle(known_hosts=args.known_hosts)
    except BlockingIOError:
        print('Наблюдение уже выполняется; повторный запуск пропущен.')
        return 0
    print(json.dumps(receipt, ensure_ascii=False, allow_nan=False))
    return int(any(item['status'] != 'IMPORTED' for item in receipt['sources']))


if __name__ == '__main__':
    raise SystemExit(main())
