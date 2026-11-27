"""Unreleased SQLite schema, only for disposable candidate qualification."""
from control.friends import technical_metadata as metadata


def migrate_disposable(path):
    with metadata.store(path) as database:
        database.execute("ALTER TABLE device_metadata ADD COLUMN processing_mode TEXT NOT NULL DEFAULT 'consented_extended'")
        database.execute("ALTER TABLE device_metadata ADD COLUMN policy_version TEXT NOT NULL DEFAULT 'legacy-v1'")
        database.execute('PRAGMA user_version=2')
