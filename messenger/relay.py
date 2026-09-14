"""Closed pilot relay: authenticated RNS request ingress, bounded ciphertext DB.

GET is compatible with the LXMF 1.1.1 mailbox request shape. Native anonymous
LXMF packet/resource uploads and peering are not registered. This is an optional
Family Connect ingress extension, not a replacement for the RNS wire protocol.
"""
import fcntl
import os
from pathlib import Path
import sqlite3
import stat
import threading
import time

import RNS
from LXMF.LXMPeer import LXMPeer
from .codec import address, identity, MAX_PACKED

PUT_PATH='/family_connect/chat/v1/put'
MAX_BLOB=MAX_PACKED+256


class SpoolFull(Exception):
    pass


class Spool:
    def __init__(self, path, *, max_bytes=262144, max_messages=128,
                 sender_bytes=65536, sender_messages=32, retention=86400, clock=time.time):
        for value in (max_bytes,max_messages,sender_bytes,sender_messages,retention):
            if type(value) is not int or value<=0:raise ValueError('Positive integer limits required')
        if max_bytes>1048576 or max_messages>1000 or retention>30*86400:
            raise ValueError('Pilot limits exceeded')
        self.limits=max_bytes,max_messages,sender_bytes,sender_messages
        self.retention,self.clock=retention,clock
        self.lock=threading.RLock();self.owner=None;self.db=None
        path=Path(path);path.mkdir(mode=0o700,exist_ok=True)
        info=path.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid!=os.getuid() or stat.S_IMODE(info.st_mode)!=0o700:
            raise ValueError('Unsafe spool directory')
        try:
            self.owner=self._open(path/'.lock')
            fcntl.flock(self.owner,fcntl.LOCK_EX|fcntl.LOCK_NB)
            fd=self._open(path/'spool.sqlite');os.close(fd)
            self.db=sqlite3.connect(path/'spool.sqlite',check_same_thread=False)
            self.db.execute('PRAGMA journal_mode=DELETE')
            self.db.execute('PRAGMA synchronous=FULL')
            self.db.execute('PRAGMA temp_store=MEMORY')
            self.db.execute('PRAGMA page_size=4096')
            self.page_size=self.db.execute('PRAGMA page_size').fetchone()[0]
            if self.page_size!=4096:raise ValueError('Unexpected database page size')
            # Hard database-file ceiling, including indexes/free pages. Journal,
            # directory and RNS runtime files need a separate filesystem quota.
            self.max_pages=(2*max_bytes+262144+4095)//4096
            actual=self.db.execute(f'PRAGMA max_page_count={self.max_pages}').fetchone()[0]
            if actual!=self.max_pages:raise ValueError('Existing database exceeds ceiling')
            with self.db:
                self.db.execute('CREATE TABLE IF NOT EXISTS messages (id BLOB PRIMARY KEY,sender BLOB NOT NULL,recipient BLOB NOT NULL,received REAL NOT NULL,body BLOB NOT NULL)')
            self.expire()
            if self.stats()['bytes']>max_bytes or self.stats()['count']>max_messages:
                raise ValueError('Existing spool exceeds configured limits')
        except BaseException:self.close();raise

    @staticmethod
    def _open(path):
        fd=os.open(path,os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW|os.O_NONBLOCK,0o600)
        st=os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_uid!=os.getuid() or st.st_nlink!=1 or stat.S_IMODE(st.st_mode)!=0o600:
            os.close(fd);raise ValueError('Unsafe spool file')
        return fd

    def expire(self):
        with self.lock,self.db:
            self.db.execute('DELETE FROM messages WHERE received<=?',(self.clock()-self.retention,))

    def stats(self):
        with self.lock:
            count,size=self.db.execute('SELECT count(*),coalesce(sum(length(body)),0) FROM messages').fetchone()
            return dict(count=count,bytes=size)

    def put(self,sender,blob):
        if type(sender) is not bytes or len(sender)!=16 or type(blob) is not bytes or not 112<=len(blob)<=MAX_BLOB:
            raise ValueError('Invalid ciphertext envelope')
        ident=RNS.Identity.full_hash(blob)
        with self.lock,self.db:
            self.db.execute('DELETE FROM messages WHERE received<=?',(self.clock()-self.retention,))
            duplicate=self.db.execute('SELECT sender FROM messages WHERE id=?',(ident,)).fetchone()
            if duplicate:
                if duplicate[0]!=sender:raise ValueError('Ciphertext owned by another sender')
                return ident
            total=self.stats()
            count,size=self.db.execute('SELECT count(*),coalesce(sum(length(body)),0) FROM messages WHERE sender=?',(sender,)).fetchone()
            mb,mc,sb,sc=self.limits
            if total['count']>=mc or total['bytes']+len(blob)>mb or count>=sc or size+len(blob)>sb:
                raise SpoolFull()
            try:self.db.execute('INSERT INTO messages VALUES (?,?,?,?,?)',(ident,sender,blob[:16],self.clock(),blob))
            except sqlite3.OperationalError as error:
                if getattr(error,'sqlite_errorcode',None)==sqlite3.SQLITE_FULL:raise SpoolFull() from None
                raise
        return ident # SQLite FULL commit completed before successful response.

    def get(self,recipient,data):
        if type(data) is not list or len(data) not in (2,3):raise ValueError('Invalid mailbox request')
        wants,haves=data[:2]
        for values in (wants,haves):
            if values is not None and (type(values) is not list or len(values)>10 or any(type(x) is not bytes or len(x)!=32 for x in values)):
                raise ValueError('Invalid message IDs')
        with self.lock,self.db:
            self.db.execute('DELETE FROM messages WHERE received<=?',(self.clock()-self.retention,))
            if wants is None and haves is None:
                return [row[0] for row in self.db.execute('SELECT id FROM messages WHERE recipient=? ORDER BY received,id',(recipient,))]
            for ident in haves or []:
                self.db.execute('DELETE FROM messages WHERE id=? AND recipient=?',(ident,recipient))
            result=[];size=0
            for ident in dict.fromkeys(wants or []):
                row=self.db.execute('SELECT body FROM messages WHERE id=? AND recipient=?',(ident,recipient)).fetchone()
                if row and size+len(row[0])<=48000:result.append(row[0]);size+=len(row[0])
            return result

    def close(self):
        with self.lock:
            if self.db is not None:self.db.close();self.db=None
            if self.owner is not None:os.close(self.owner);self.owner=None


class ClosedRelay:
    def __init__(self,relay_identity,spool,*,allowed_public):
        if not 1<=len(allowed_public)<=100:raise ValueError('Closed pilot requires 1..100 identities')
        self.spool=spool
        self.allowed={identity(public).hash:address(public) for public in allowed_public}
        self.rate={};self.rate_lock=threading.Lock()
        self.destination=RNS.Destination(relay_identity,RNS.Destination.IN,RNS.Destination.SINGLE,'lxmf','propagation')
        for path in (PUT_PATH,LXMPeer.MESSAGE_GET_PATH):
            self.destination.register_request_handler(path,self.respond,allow=RNS.Destination.ALLOW_ALL,auto_compress=False)
        # No native upload callbacks or peer offer handlers: requests only.

    def respond(self,path,data,request_id,remote_identity,requested_at):
        if remote_identity is None or remote_identity.hash not in self.allowed:
            return LXMPeer.ERROR_NO_ACCESS
        if path==PUT_PATH:
            if type(data) is not bytes or not 112<=len(data)<=MAX_BLOB or data[:16] not in self.allowed.values():
                return ['rejected']
            with self.rate_lock:
                now=time.monotonic();last,tokens=self.rate.get(remote_identity.hash,(now,4.0))
                tokens=min(4.0,tokens+max(0,now-last))
                if tokens<1:
                    self.rate[remote_identity.hash]=(now,tokens)
                    return ['rate_limited']
                self.rate[remote_identity.hash]=(now,tokens-1)
            try:return ['stored',self.spool.put(remote_identity.hash,data)]
            except SpoolFull:return ['full']
            except ValueError:return ['rejected']
            except (OSError,sqlite3.Error):return ['unavailable']
        if path==LXMPeer.MESSAGE_GET_PATH:
            try:return self.spool.get(self.allowed[remote_identity.hash],data)
            except (ValueError,OSError,sqlite3.Error):return LXMPeer.ERROR_NO_ACCESS
        return LXMPeer.ERROR_NO_ACCESS
