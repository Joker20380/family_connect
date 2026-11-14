"""Read-only, commit-ordered subscription feed; never a payment writer."""
import hashlib
import hmac
import json
from pathlib import Path
import sqlite3
import time


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def boundary(subscription):
    return subscription['grace_until'] if subscription['state'] == 'grace' else subscription['paid_until']


def read(registry, key, cursor=-1, anchor=None, *, now=None, limit=128):
    if type(cursor) is not int or cursor < -1 or not 1 <= limit <= 128 or len(key) != 32:
        raise ValueError('invalid_cursor')
    path = Path(registry)
    if path.is_symlink() or not path.is_file():
        raise ValueError('registry_unavailable')
    database = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True, timeout=5)
    database.row_factory = sqlite3.Row
    try:
        database.execute('PRAGMA query_only=ON')
        database.execute('BEGIN')
        highwater = database.execute('SELECT coalesce(max(rowid),0) FROM paid_beta_events').fetchone()[0]
        def at(position):
            row = database.execute('SELECT rowid AS position,* FROM paid_beta_events WHERE rowid=?', (position,)).fetchone()
            return digest(dict(row)) if row else digest(None)
        if cursor >= 0 and (cursor > highwater or anchor != at(cursor)):
            raise ValueError('source_position_changed')
        observed = int(time.time()) if now is None else now
        subscriptions = []
        for row in database.execute('SELECT s.*,c.public,c.support_sender,d.revoked AS device_revoked, '
                'EXISTS(SELECT 1 FROM invites i WHERE i.device=s.device AND i.revoked=0) AS invited '
                'FROM paid_beta_subscriptions s JOIN devices d ON d.device=s.device '
                'LEFT JOIN chat_bindings c ON c.device=s.device ORDER BY s.device'):
            item = dict(row)
            item['pseudonym'] = hmac.new(key, item['device'].encode(), hashlib.sha256).hexdigest()
            subscriptions.append(item)
        events = []
        if cursor >= 0:
            for row in database.execute('SELECT rowid AS position,* FROM paid_beta_events '
                    'WHERE rowid>? ORDER BY rowid LIMIT ?', (cursor, limit)):
                item = dict(row)
                if item['result'] != 'APPLIED':
                    raise ValueError('noncanonical_event')
                item['version'] = database.execute('SELECT count(*) FROM paid_beta_events '
                    'WHERE device=? AND rowid<=?', (item['device'], item['position'])).fetchone()[0]
                prior = database.execute('SELECT rowid AS position,* FROM paid_beta_events '
                    "WHERE device=? AND rowid<? AND event_type IN ('payment','grace') ORDER BY rowid DESC LIMIT 1",
                    (item['device'], item['position'])).fetchone()
                item['prior'] = dict(prior) if prior else None
                if prior:
                    item['prior']['version'] = database.execute('SELECT count(*) FROM paid_beta_events '
                        'WHERE device=? AND rowid<=?', (item['device'], prior['position'])).fetchone()[0]
                events.append(item)
        position = highwater if cursor == -1 else events[-1]['position'] if events else cursor
        return dict(schema=1, cursor=cursor, anchor=anchor, position=position, position_hash=at(position),
            highwater=highwater, baseline_count=database.execute('SELECT count(*) FROM paid_beta_events').fetchone()[0],
            observed_at=observed, expires_at=observed + 90, events=events, subscriptions=subscriptions)
    finally:
        database.close()
