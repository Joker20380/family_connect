"""Consistent private SQLite backup and isolated restore; no live registry writes."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import stat


def readonly(path):
    database = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True, timeout=15)
    database.execute('PRAGMA query_only=ON')
    return database


def inventory(database):
    names = [row[0] for row in database.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    result = {}
    for name in names:
        quoted = '"' + name.replace('"', '""') + '"'
        rows = database.execute('SELECT * FROM ' + quoted).fetchall()
        encoded = sorted(json.dumps(row, separators=(',', ':'), allow_nan=False,
            default=lambda value: {'bytes': value.hex()}) for row in rows)
        result[name] = dict(count=len(rows), sha256=hashlib.sha256('\n'.join(encoded).encode()).hexdigest())
    return result


def backup(source, destination):
    source, destination = Path(source), Path(destination)
    if any(parent.is_symlink() for parent in (source, *source.parents)):
        raise ValueError('Symlink source forbidden')
    source = source.resolve(strict=True)
    if (not stat.S_ISREG(source.stat().st_mode) or destination.exists()
            or any(parent.is_symlink() for parent in (destination, *destination.parents))):
        raise ValueError('Unsafe backup path')
    original = readonly(source)
    try:
        original.execute('BEGIN')
        if original.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
            raise ValueError('Source integrity failed')
        before = inventory(original)
        if any(before.get(name, {}).get('count', 0) for name in ('paid_beta_subscriptions', 'paid_beta_events')):
            raise ValueError('Nonempty paid cohort: this empty-cohort procedure is forbidden')
        destination.mkdir(mode=0o700)
        backup_path = destination / 'registry.sqlite3'
        descriptor = os.open(backup_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.close(descriptor)
        target = sqlite3.connect(backup_path)
        try:
            original.backup(target)
        finally:
            target.close()
    finally:
        original.rollback()
        original.close()
    copied = readonly(backup_path)
    restored_path = destination / 'restore-rehearsal.sqlite3'
    descriptor = os.open(restored_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    os.close(descriptor)
    restored = sqlite3.connect(restored_path)
    try:
        copied.backup(restored)
        after = inventory(restored)
        if before != after or restored.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
            raise ValueError('Restore verification failed; retain private evidence and stop')
        foreign_keys = restored.execute('PRAGMA foreign_key_check').fetchall()
    finally:
        copied.close()
        restored.close()
    if foreign_keys:
        raise ValueError('Restore foreign-key verification failed; stop')
    restored_path.unlink()
    receipt = dict(schema=1, result='BACKUP_AND_ISOLATED_SQLITE_RESTORE_PASS',
        utc=datetime.now(timezone.utc).isoformat(), size=backup_path.stat().st_size,
        sha256=hashlib.sha256(backup_path.read_bytes()).hexdigest(), tables=before,
        live_database_writes=0, service_restarts=0, application_recovery='NOT_RUN')
    descriptor = os.open(destination / 'receipt.json', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'w') as output:
        json.dump(receipt, output, sort_keys=True, indent=2, allow_nan=False)
        output.write('\n')
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    args = parser.parse_args()
    if any(parent.is_symlink() for parent in (args.database, *args.database.parents)):
        parser.error('Symlink source forbidden')
    receipt = backup(args.database, args.destination)
    print(json.dumps({key: value for key, value in receipt.items() if key != 'tables'}, allow_nan=False))


if __name__ == '__main__':
    main()
