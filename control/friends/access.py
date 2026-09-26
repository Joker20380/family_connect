"""One invite activates one signing identity and its independent WG public key.

Every subsequent configuration request requires a fresh single-use device proof.
No entitlement expiry/payment condition. Operator revocation remains explicit.
"""
import base64,hashlib,json,os,secrets,sqlite3,time,uuid
from contextlib import contextmanager
from pathlib import Path
from device_identity.device import _decode,verify_transport_key_proof

# Clients reject expiry more than 120 seconds ahead of their wall clock.
# Leave 20 seconds of clock-skew headroom without extending server validity.
CHALLENGE_TTL = 100

class Rejected(ValueError):pass

class Access:
 def __init__(self,path,clock=time.time):self.path=Path(path);self.clock=clock
 @contextmanager
 def db(self):
  connection=sqlite3.connect(self.path,timeout=15);connection.row_factory=sqlite3.Row
  try:
   connection.execute('PRAGMA synchronous=FULL');connection.execute('BEGIN IMMEDIATE')
   with connection:yield connection
  finally:connection.close()
 def initialize(self):
  assert self.path.parent.is_dir() and not self.path.exists();fd=os.open(self.path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.close(fd)
  with self.db() as db:
   db.executescript('''CREATE TABLE invites(hash TEXT PRIMARY KEY, device TEXT UNIQUE, revoked INTEGER NOT NULL DEFAULT 0);
CREATE TABLE devices(device TEXT PRIMARY KEY, public TEXT UNIQUE NOT NULL, wg TEXT UNIQUE NOT NULL, tcp TEXT UNIQUE NOT NULL, revoked INTEGER NOT NULL DEFAULT 0);
CREATE TABLE challenges(nonce TEXT PRIMARY KEY, device TEXT NOT NULL, public TEXT NOT NULL,wg TEXT NOT NULL,purpose TEXT NOT NULL,invite TEXT,expires INTEGER NOT NULL,used INTEGER NOT NULL DEFAULT 0);''')
 @staticmethod
 def code_hash(code):
  if not isinstance(code,str):raise Rejected()
  normalized=code.strip().upper().replace('-','')
  if normalized.startswith('FC'):normalized=normalized[2:]
  if len(normalized)!=32 or any(c not in '0123456789ABCDEF' for c in normalized):raise Rejected()
  return hashlib.sha256(normalized.encode()).hexdigest()
 def invite(self):
  value=secrets.token_hex(16).upper();code='FC-'+'-'.join(value[i:i+4] for i in range(0,32,4))
  with self.db() as db:db.execute('INSERT INTO invites(hash) VALUES (?)',(self.code_hash(code),))
  return code
 @staticmethod
 def binding(public,wg):
  key=_decode(public,64);_decode(wg,32)
  return hashlib.sha256(key).hexdigest()[:32]
 def challenge(self,public_identity,wireguard_public_key,purpose,invitation=''):
  if purpose not in ('activate','status','ru','nl','refer','notices-role','notices-publish','notices-list','notices-edit'):raise Rejected()
  device=self.binding(public_identity,wireguard_public_key);now=int(self.clock());invite=None
  with self.db() as db:
   row=db.execute('SELECT * FROM devices WHERE device=?',(device,)).fetchone()
   if row is not None:
    if row['revoked'] or row['public']!=public_identity or row['wg']!=wireguard_public_key:raise Rejected()
   else:
    if purpose not in ('activate','status'):raise Rejected()
    if purpose=='activate':
     invite=self.code_hash(invitation);grant=db.execute('SELECT * FROM invites WHERE hash=?',(invite,)).fetchone()
     if grant is None or grant['revoked'] or grant['device'] is not None:raise Rejected()
   db.execute('DELETE FROM challenges WHERE expires<=?',(now,))
   if db.execute('SELECT COUNT(*) FROM challenges WHERE device=? AND used=0',(device,)).fetchone()[0]>=8:raise Rejected()
   nonce=base64.b64encode(secrets.token_bytes(32)).decode()
   db.execute('INSERT INTO challenges VALUES (?,?,?,?,?,?,?,0)',(hashlib.sha256(nonce.encode()).hexdigest(),device,public_identity,wireguard_public_key,purpose,invite,now+CHALLENGE_TTL))
  return {'challenge':nonce,'expires_at':now+CHALLENGE_TTL,'audience':'family-connect/enrollment/v1'}
 def complete(self,proof,purpose):
  device=verify_transport_key_proof(proof,expected_challenge=proof['challenge']);now=int(self.clock());nonce=hashlib.sha256(proof['challenge'].encode()).hexdigest()
  with self.db() as db:
   challenge=db.execute('SELECT * FROM challenges WHERE nonce=?',(nonce,)).fetchone()
   if challenge is None or challenge['used'] or challenge['expires']<=now or challenge['purpose']!=purpose or challenge['device']!=device or challenge['public']!=proof['public_identity'] or challenge['wg']!=proof['wireguard_public_key']:raise Rejected()
   row=db.execute('SELECT * FROM devices WHERE device=?',(device,)).fetchone()
   if row is None:
    if purpose!='activate':raise Rejected()
    grant=db.execute('SELECT * FROM invites WHERE hash=?',(challenge['invite'],)).fetchone()
    if grant is None or grant['revoked'] or grant['device'] is not None:raise Rejected()
    db.execute('INSERT INTO devices VALUES (?,?,?,?,0)',(device,proof['public_identity'],proof['wireguard_public_key'],str(uuid.uuid4())))
    db.execute('UPDATE invites SET device=? WHERE hash=?',(device,challenge['invite']))
    row=db.execute('SELECT * FROM devices WHERE device=?',(device,)).fetchone()
   if row['revoked'] or row['public']!=proof['public_identity'] or row['wg']!=proof['wireguard_public_key']:raise Rejected()
   db.execute('UPDATE challenges SET used=1 WHERE nonce=?',(nonce,))
   return {'device':device,'public_key':row['wg'],'tcp_id':row['tcp']}
 def status(self,proof):
  """Authenticated read-only recovery query. Never consumes an invitation."""
  device=verify_transport_key_proof(proof,expected_challenge=proof['challenge']);now=int(self.clock());nonce=hashlib.sha256(proof['challenge'].encode()).hexdigest()
  with self.db() as db:
   challenge=db.execute('SELECT * FROM challenges WHERE nonce=?',(nonce,)).fetchone()
   if challenge is None or challenge['used'] or challenge['expires']<=now or challenge['purpose']!='status' or challenge['device']!=device or challenge['public']!=proof['public_identity'] or challenge['wg']!=proof['wireguard_public_key']:raise Rejected()
   db.execute('UPDATE challenges SET used=1 WHERE nonce=?',(nonce,))
   row=db.execute('SELECT * FROM devices WHERE device=?',(device,)).fetchone()
   if row is None:return {'device':device,'registered':False,'revoked':False,'active':False}
   grant=db.execute('SELECT revoked FROM invites WHERE device=?',(device,)).fetchone()
   revoked=bool(row['revoked'] or (grant is not None and grant['revoked']))
   active=(not revoked and row['public']==proof['public_identity'] and row['wg']==proof['wireguard_public_key'])
   return {'device':device,'registered':True,'revoked':revoked,'active':active}
