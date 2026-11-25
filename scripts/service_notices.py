"""Operator CLI: grant/revoke publisher credentials and export public notices.

Run on the controlled service host. OS access to the private registry is the owner
boundary; administrator credentials only authorize publication, not delegation.
No network requests are performed and no secrets are printed.
"""
import argparse
from contextlib import closing, contextmanager
import hashlib
import hmac
import json
import os
import re
from pathlib import Path
import secrets
import sqlite3
import tempfile
import time
import uuid
from messenger.service_events import validate_feed, KINDS
from control.capture_gate import external_operation


REPOSITORY_PURPOSE = 'family-connect/ha-notices-synthetic/v1/db-only'


def refuse_canonical(path):
    if path is None:
        raise NotImplementedError('Canonical notices cannot use legacy files')
    path = Path(path)
    if path.exists():
        with closing(sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)) as database:
            if database.execute("SELECT 1 FROM sqlite_master WHERE name='ha_notices_schema'").fetchone():
                raise NotImplementedError('Canonical notices require fenced publication')


class NoticeTransaction:
    def __init__(self, database, placeholder='?', order='position'):
        self.db = database
        self.placeholder = placeholder
        self.order = order

    @contextmanager
    def transaction(self):
        yield self

    def execute(self, query, values=()):
        return self.db.execute(query.replace('?', self.placeholder), values)

    def rows(self, query, values=()):
        cursor = self.execute(query, values)
        fields = [description[0] for description in cursor.description]
        return [tuple(row[field] for field in fields) if hasattr(row, 'keys') else tuple(row)
                for row in cursor.fetchall()]

    def one(self, query, values=()):
        rows = self.rows(query, values)
        return rows[0] if rows else None

    def require_schema(self):
        if self.rows('SELECT version,purpose FROM ha_notices_schema') != [(1, REPOSITORY_PURPOSE)]:
            raise RuntimeError('Notices rehearsal schema mismatch')

    def grant_digest(self, name, digest):
        if not name.strip() or len(name) > 80: raise ValueError('Invalid administrator name')
        if type(digest) is not str or re.fullmatch('[a-f0-9]{64}', digest) is None:
            raise ValueError('Invalid credential digest')
        with self.transaction():
            self.execute('INSERT INTO admins VALUES(?,?,1)', (name, digest))
        return name

    def revoke(self, name):
        with self.transaction():
            if not self.execute('UPDATE admins SET active=0 WHERE name=?', (name,)).rowcount: raise ValueError('Unknown administrator')

    def assign_device(self, device, name):
        if not re.fullmatch('[a-f0-9]{32}', device) or not name.strip() or len(name)>80 or any(ord(c)<32 for c in name):
            raise ValueError('Invalid administrator')
        with self.transaction():
            self.execute('INSERT INTO device_admins VALUES(?,?,1) ON CONFLICT(device) DO UPDATE SET name=excluded.name,active=1',(device,name))

    def revoke_device(self, device):
        with self.transaction():
            if not self.execute('UPDATE device_admins SET active=0 WHERE device=?',(device,)).rowcount:
                raise ValueError('Unknown administrator')

    def device_role(self, device):
        row=self.one('SELECT name FROM device_admins WHERE device=? AND active=1',(device,))
        return dict(role='administrator' if row else 'member', name=row[0] if row else '')

    def publish(self, token, *, kind, title, body, platforms, lifetime=30*86400, now=None, ident=None, device=None):
        now = int(time.time()) if now is None else now
        digest = hashlib.sha256(token.strip().encode()).hexdigest()
        with self.transaction():
            names = ([row[0] for row in self.rows('SELECT name FROM device_admins WHERE device=? AND active=1',(device,))] if device is not None else [name for name, saved in self.rows('SELECT name,digest FROM admins WHERE active=1') if hmac.compare_digest(digest, saved)])
            if len(names) != 1: raise ValueError('Publisher access denied')
            event = dict(id=ident or uuid.uuid4().hex, kind=kind, title=title, body=body, platforms=platforms, created=now, expires=now+lifetime, author=names[0])
            if not validate_feed(dict(version=1, events=[event]), now=now): raise ValueError('Invalid expiration')
            old = self.one('SELECT value FROM events WHERE id=?', (event['id'],))
            if old:
                old = json.loads(old[0])
                if any(old[k] != event[k] for k in ('author','kind','title','body','platforms')) or old['expires']-old['created'] != lifetime:
                    raise ValueError('Conflicting notice id')
                return old['id']
            current = self.feed(now=now)['events']
            if len(current) >= 200: raise ValueError('Active notice quota reached')
            validate_feed(dict(version=1,events=current+[event]),now=now)
            validate_feed(dict(version=2,events=self.feed(now=now,version=2)['events']+[dict(event,revision=1,updated=now,editor=event['author'])]),now=now)
            self.save_event(event)
            return event['id']

    def save_event(self, event):
        self.execute('INSERT INTO events(id,value,position) SELECT ?,?,COALESCE(MAX(position),0)+1 FROM events',
                     (event['id'], json.dumps(event, ensure_ascii=False)))

    def current_event(self, ident):
        row=self.one('SELECT value FROM revisions WHERE id=?',(ident,))
        if row:return json.loads(row[0])
        row=self.one('SELECT value FROM events WHERE id=?',(ident,))
        if row is None:raise ValueError('Unknown notice')
        event=json.loads(row[0]);return dict(event,revision=1,updated=event['created'],editor=event['author'])

    def list_device(self, device, offset=0):
        with self.transaction():
            if self.device_role(device)['role']!='administrator':raise ValueError('Publisher access denied')
            if type(offset) is not int or offset<0:raise ValueError('Invalid offset')
            rows=self.rows('SELECT id FROM events ORDER BY ' + self.order + ' DESC LIMIT 51 OFFSET ?',(offset,))
            return dict(events=[self.current_event(row[0]) for row in rows[:50]],next_offset=offset+50 if len(rows)>50 else None)

    def edit_device(self, device, value, now=None):
        if type(value) is not dict or set(value)!={'id','revision','request_id','title','body'} or type(value['revision']) is not int or value['revision']<1:
            raise ValueError('Invalid edit')
        for key in ('id','request_id'):
            if type(value[key]) is not str or re.fullmatch('[a-f0-9]{32}',value[key]) is None:raise ValueError('Invalid edit id')
        now=int(time.time()) if now is None else now
        request=json.dumps(value,sort_keys=True,ensure_ascii=False)
        with self.transaction():
            role=self.device_role(device)
            if role['role']!='administrator':raise ValueError('Publisher access denied')
            prior=self.one('SELECT request,result,device FROM edit_operations WHERE id=?',(value['request_id'],))
            if prior:
                if prior[0]!=request or prior[2]!=device:raise ValueError('Conflicting edit')
                return json.loads(prior[1])
            before=self.current_event(value['id'])
            if before['revision']!=value['revision']:raise ValueError('Stale notice revision')
            after=dict(before,title=value['title'],body=value['body'],revision=before['revision']+1,updated=max(now,before['updated']),editor=role['name'])
            validate_feed(dict(version=2,events=[after]),now=now)
            active=self.feed(now=now,version=2)['events'];active=[after if item['id']==after['id'] else item for item in active]
            validate_feed(dict(version=2,events=active),now=now)
            result=dict(id=after['id'],revision=after['revision'],status='updated')
            self.save_edit(device, value, request, before, after, result)
            return result

    def save_edit(self, device, value, request, before, after, result):
        self.execute('INSERT INTO revisions VALUES(?,?) ON CONFLICT(id) DO UPDATE SET value=excluded.value',
                     (after['id'], json.dumps(after, ensure_ascii=False)))
        self.execute('INSERT INTO edit_operations VALUES(?,?,?,?,?,?)',
                     (value['request_id'], request, json.dumps(result), device,
                      json.dumps(before, ensure_ascii=False), json.dumps(after, ensure_ascii=False)))

    def feed(self, now=None, version=1):
        now = int(time.time()) if now is None else now
        events=[event for row in self.rows('SELECT value FROM events ORDER BY ' + self.order) if (event := json.loads(row[0]))['expires'] > now]
        if version==2:events=[self.current_event(event['id']) for event in events]
        return dict(version=version, events=events)

    def export_all(self, path):
        raise NotImplementedError('Canonical notices require fenced publication')

    def export(self, path, version=1):
        raise NotImplementedError('Canonical notices require fenced publication')


class Notices(NoticeTransaction):
    def __init__(self, path):
        refuse_canonical(path)
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        descriptor = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        os.close(descriptor)
        if path.stat().st_mode & 0o077: raise ValueError('Registry must be private')
        super().__init__(sqlite3.connect(path), order='rowid')
        self.db.executescript('CREATE TABLE IF NOT EXISTS admins(name TEXT PRIMARY KEY, digest TEXT NOT NULL, active INTEGER NOT NULL); CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY, value TEXT NOT NULL); CREATE TABLE IF NOT EXISTS device_admins(device TEXT PRIMARY KEY, name TEXT NOT NULL, active INTEGER NOT NULL); CREATE TABLE IF NOT EXISTS revisions(id TEXT PRIMARY KEY,value TEXT NOT NULL); CREATE TABLE IF NOT EXISTS edit_operations(id TEXT PRIMARY KEY,request TEXT NOT NULL,result TEXT NOT NULL,device TEXT NOT NULL,before_value TEXT NOT NULL,after_value TEXT NOT NULL);')

    @contextmanager
    def transaction(self):
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            yield self

    def save_event(self, event):
        self.execute('INSERT INTO events VALUES(?,?)', (event['id'], json.dumps(event, ensure_ascii=False)))

    def grant(self, name, token_file):
        if not name.strip() or len(name) > 80: raise ValueError('Invalid administrator name')
        token = secrets.token_hex(32)
        descriptor = os.open(token_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(descriptor, 'w') as output: output.write(token)
        try:
            return self.grant_digest(name, hashlib.sha256(token.encode()).hexdigest())
        except Exception:
            Path(token_file).unlink()
            raise

    def grant_device(self, access, device, name):
        refuse_canonical(access.path)
        with access.db() as database:
            row = database.execute('SELECT revoked FROM devices WHERE device=?', (device,)).fetchone()
            if row is None or row['revoked']: raise ValueError('Device not active')
            self.assign_device(device, name)

    def export_all(self, path):
        self._export_versions(((Path(path), 1), (Path(path).with_name('family-connect-events-v2.json'), 2)))

    def export(self, path, version=1):
        self._export_versions(((Path(path), version),))

    def _export_versions(self, targets):
        with external_operation():
            with self.transaction():
                now = int(time.time())
                for path, version in targets:
                    self._write_feed(path, version, now)

    def _write_feed(self, path, version, now):
        data = json.dumps(self.feed(version=version, now=now), ensure_ascii=False, separators=(',', ':')).encode()
        descriptor, temporary = tempfile.mkstemp(prefix='.notices-', dir=path.parent)
        try:
            with os.fdopen(descriptor, 'wb') as output:
                os.fchmod(output.fileno(), 0o644)
                output.write(data);output.flush();os.fsync(output.fileno())
            os.replace(temporary, path)
            directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        finally:
            if os.path.exists(temporary): os.unlink(temporary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registry', required=True)
    commands = parser.add_subparsers(dest='command', required=True)
    grant = commands.add_parser('grant');grant.add_argument('--name', required=True);grant.add_argument('--token-file', required=True)
    device = commands.add_parser('grant-device');device.add_argument('--access-db', required=True);device.add_argument('--device', required=True);device.add_argument('--name', required=True)
    revoke_device = commands.add_parser('revoke-device');revoke_device.add_argument('--device', required=True)
    revoke = commands.add_parser('revoke');revoke.add_argument('--name', required=True)
    send = commands.add_parser('publish');send.add_argument('--token-file', required=True);send.add_argument('--kind', choices=sorted(KINDS), required=True);send.add_argument('--title', required=True);send.add_argument('--body-file', required=True);send.add_argument('--platform', action='append', choices=['android','windows','linux'], required=True);send.add_argument('--days', type=int, default=30)
    export = commands.add_parser('export');export.add_argument('--output', required=True)
    args = parser.parse_args();store = Notices(args.registry)
    try:
        if args.command == 'grant': print('Administrator created:', store.grant(args.name, args.token_file))
        elif args.command == 'grant-device':
            from control.friends.access import Access
            store.grant_device(Access(args.access_db),args.device,args.name);print('Device administrator assigned')
        elif args.command == 'revoke-device': store.revoke_device(args.device);print('Device administrator revoked')
        elif args.command == 'revoke': store.revoke(args.name);print('Administrator revoked')
        elif args.command == 'export': store.export(args.output);print('Public feed exported')
        else: print('Notice created:', store.publish(Path(args.token_file).read_text(), kind=args.kind, title=args.title, body=Path(args.body_file).read_text(), platforms=args.platform, lifetime=args.days*86400))
    finally: store.db.close()


if __name__ == '__main__': main()
