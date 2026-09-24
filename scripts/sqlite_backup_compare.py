"""Private bounded SQLite snapshot comparison. Never print rows or digests.

Comparison preserves SQL schema, typed row multisets, user_version/application_id.
It preserves accessible rowids and ignores physical layout, freelist and journal headers.
"""
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import time

from scripts.signing_key import private_file

LIMIT=16*1024*1024


def standalone(raw):
    if not 100<=len(raw)<=LIMIT or raw[:16]!=b'SQLite format 3\x00' or raw[18:20] not in (b'\x01\x01',b'\x02\x02'):
        raise ValueError('invalid database image')
    # Normalize only complete SQLite backup images, never a raw live WAL file.
    return raw[:18]+b'\x01\x01'+raw[20:]


def snapshot(path):
    path=Path(path).absolute();fd=private_file(path)
    try:
        before=os.fstat(fd)
        if before.st_size>LIMIT:raise ValueError('database limit')
        deadline=time.monotonic()+15
        def progress(*_):
            if time.monotonic()>deadline:raise TimeoutError('backup deadline')
        with sqlite3.connect(path.as_uri()+'?mode=ro',uri=True,timeout=5) as source:
            with sqlite3.connect(':memory:') as dest:
                source.backup(dest,pages=128,progress=progress,sleep=.05)
                if dest.execute('PRAGMA quick_check').fetchall()!=[('ok',)]:raise ValueError('integrity')
                raw=standalone(dest.serialize())
        after=path.stat()
        if (after.st_dev,after.st_ino)!=(before.st_dev,before.st_ino):raise ValueError('source replaced')
        return raw
    finally:os.close(fd)


def logical_digest(raw):
    with sqlite3.connect(':memory:') as db:
        db.deserialize(standalone(raw))
        db.execute('PRAGMA trusted_schema=OFF');db.execute('PRAGMA query_only=ON')
        deadline=time.monotonic()+10
        db.set_progress_handler(lambda:int(time.monotonic()>deadline),1000)
        if db.execute('PRAGMA quick_check').fetchall()!=[('ok',)]:raise ValueError('integrity')
        schema=db.execute('SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name').fetchall()
        if any(row[3] and 'CREATE VIRTUAL TABLE' in row[3].upper() for row in schema):raise ValueError('virtual tables unsupported')
        digest=hashlib.sha256();digest.update(json.dumps(schema,ensure_ascii=True).encode())
        for pragma in ('user_version','application_id','encoding'):
            digest.update(json.dumps(db.execute('PRAGMA '+pragma).fetchone()).encode())
        count=total=0
        def scalar(value):
            if value is None:return ['null']
            if isinstance(value,bytes):return ['blob',value.hex()]
            if isinstance(value,float):return ['real',value.hex()]
            if isinstance(value,int):return ['integer',str(value)]
            return ['text',value]
        without_rowid={r[1]:bool(r[4]) for r in db.execute('PRAGMA table_list') if r[0]=='main'}
        for name, in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall():
            rows=[]
            quoted='"'+name.replace('"','""')+'"'
            columns={r[1].lower() for r in db.execute('PRAGMA table_info('+quoted+')')}
            select='*'
            if not without_rowid.get(name,False):
                aliases=[a for a in ('rowid','_rowid_','oid') if a not in columns]
                if not aliases:raise ValueError('shadowed rowid unsupported')
                select=aliases[0]+',*'
            for row in db.execute('SELECT '+select+' FROM '+quoted):
                encoded=json.dumps([scalar(v) for v in row],ensure_ascii=True,separators=(',',':')).encode()
                total+=len(encoded);count+=1
                if total>4*LIMIT or count>100000:raise ValueError('logical comparison limit')
                rows.append(encoded)
            digest.update(json.dumps(name).encode())
            for row in sorted(rows):digest.update(len(row).to_bytes(8,'big'));digest.update(row)
        return digest.digest()


def equivalent(first,second):
    return logical_digest(first)==logical_digest(second)
