"""Read-only native OWNER probe, streamed into an isolated pinned console image."""
import hashlib
import ctypes.util
import json
import os
from pathlib import Path
import sqlite3
import sys

ROOT = Path('/app/control_plane/.local')


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def require(condition, code):
    if not condition:
        raise ValueError(code)


def probe():
    require(os.getuid() != 0, 'NONROOT_REQUIRED')
    attempted = []

    def audit(event, args):
        if event.startswith(('socket.', 'subprocess.', 'os.exec', 'os.spawn')) or event == 'os.system':
            attempted.append(event)
            raise RuntimeError('OFFLINE_ONLY')

    sys.addaudithook(audit)
    original_find_library = ctypes.util.find_library

    def offline_library(name):
        require(name == 'c', 'UNEXPECTED_NATIVE_LIBRARY')
        return 'libc.so.6'

    ctypes.util.find_library = offline_library
    configuration = json.loads((ROOT / 'probe.json').read_bytes())
    os.environ.update(configuration['environment'])
    os.environ.update(DJANGO_SETTINGS_MODULE='fc_control_plane.settings', POSTGRES_HOST='127.0.0.1',
                      POSTGRES_PORT='65535', FC_SUPPORT_SOCKET='',
                      FC_PSEUDONYM_ALIASES=str(ROOT / 'panel-aliases.json'))
    import django
    from django.db.backends.base.base import BaseDatabaseWrapper

    def deny_database(*args, **kwargs):
        attempted.append('postgres')
        raise RuntimeError('OFFLINE_ONLY')

    BaseDatabaseWrapper.ensure_connection = deny_database
    django.setup()
    from apps.console import backend, system_publisher
    from control.friends import paid_beta, pseudonyms, subscription
    ctypes.util.find_library = original_find_library

    database_path = ROOT / 'synthetic' / 'registry.sqlite3'
    before = digest(database_path.read_bytes())
    tables = {}
    with backend.registry() as database:
        for row in database.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
            name = row[0]
            rows = database.execute('SELECT * FROM "' + name.replace('"', '""') + '"').fetchall()
            values = sorted(json.dumps(tuple(entry), separators=(',', ':'), allow_nan=False,
                            default=lambda value: {'bytes': value.hex()}) for entry in rows)
            tables[name] = dict(count=len(rows), sha256=digest('\n'.join(values).encode()))
        require(tables == configuration['tables'], 'NATIVE_TABLE_READBACK')
        paid = database.execute('SELECT device,paid_until,grace_until FROM paid_beta_subscriptions ORDER BY device').fetchall()
        projection = [subscription.snapshot(database, row['device'], configuration['observed']) for row in paid]
        require(digest(encoded(projection)) == configuration['paid_projection_sha256'], 'NATIVE_PAID_READBACK')
        future = max([configuration['observed']] + [max(row['paid_until'], row['grace_until'] or 0) for row in paid]) + 1
        require(all(not paid_beta.effective_subscription_state(database, row['device'], future).allowed for row in paid),
                'NATIVE_EXPIRY_DENIAL')
    aliases = pseudonyms.load(ROOT / 'panel-aliases.json')
    aliases.check_key((ROOT / 'inventory-hmac.key').read_bytes())
    checked = 0
    for domain, entities in aliases.document['entities'].items():
        for entity in entities:
            for value in entity['aliases'].values():
                require(aliases.resolve(domain, value) == entity['handle'], 'NATIVE_ALIAS_READBACK')
                checked += 1
    system_publisher.Publisher(configuration['publisher_origin'], ROOT / 'publisher.token')
    require(not attempted and before == digest(database_path.read_bytes()), 'NATIVE_PROBE_SIDE_EFFECT')
    pins = {module.__name__: digest(Path(module.__file__).read_bytes())
            for module in (backend, system_publisher, paid_beta, pseudonyms, subscription)}
    return dict(result='NATIVE_OWNER_OFFLINE_PASS', tables=len(tables), rows=sum(row['count'] for row in tables.values()),
                paid_expiry_denials=len(paid), aliases_checked=checked, source_sha256=pins, sqlite_sha256=before,
                activation=False, pg_pair_fence=False, dispatch_calls=0, database_unchanged=True)


if __name__ == '__main__':
    try:
        print(json.dumps(probe(), sort_keys=True))
    except Exception as error:
        trace = error.__traceback__
        frames = []
        while trace is not None:
            frames.append((Path(trace.tb_frame.f_code.co_filename).name, trace.tb_lineno))
            trace = trace.tb_next
        print(json.dumps(dict(result='OWNER_NATIVE_PROBE_REFUSED', error=type(error).__name__, frames=frames)), file=sys.stderr)
        raise SystemExit(1) from None
