"""One invite activates one signing identity and its independent WG public key.

Every subsequent configuration request requires a fresh single-use device proof.
No entitlement expiry/payment condition. Operator revocation remains explicit.
"""
import base64,hashlib,json,os,re,secrets,sqlite3,time,uuid
from contextlib import contextmanager,nullcontext
from pathlib import Path
from device_identity.device import _decode,verify_transport_key_proof

# Clients reject expiry more than 120 seconds ahead of their wall clock.
# Leave 20 seconds of clock-skew headroom without extending server validity.
CHALLENGE_TTL = 100

class Rejected(ValueError):pass

class EnrollmentTransaction:
    def __init__(self, database, placeholder):
        self.database = database
        self.placeholder = placeholder

    def device(self, device):
        return self.database.execute(
            f'SELECT * FROM devices WHERE device={self.placeholder}', (device,)).fetchone()

    def invitation(self, invitation):
        return self.database.execute(
            f'SELECT * FROM invites WHERE hash={self.placeholder}', (invitation,)).fetchone()

    def device_invitation(self, device):
        return self.database.execute(
            f'SELECT revoked FROM invites WHERE device={self.placeholder}', (device,)).fetchone()

    def add_invitation(self, invitation):
        self.database.execute(f'INSERT INTO invites(hash) VALUES ({self.placeholder})', (invitation,))

    def revoke_device(self, device):
        return bool(self.database.execute(
            f'UPDATE devices SET revoked=1 WHERE device={self.placeholder} AND revoked=0', (device,)).rowcount)

    def expire_challenges(self, now):
        self.database.execute(f'DELETE FROM challenges WHERE expires<={self.placeholder}', (now,))

    def pending_challenges(self, device):
        return self.database.execute(
            f'SELECT COUNT(*) AS total FROM challenges WHERE device={self.placeholder} AND used=0',
            (device,)).fetchone()['total']

    def add_challenge(self, nonce, device, public, wireguard, purpose, invitation, expires):
        placeholders = ','.join([self.placeholder] * 7)
        self.database.execute(
            f'INSERT INTO challenges(nonce,device,public,wg,purpose,invite,expires,used) VALUES ({placeholders},0)',
            (nonce, device, public, wireguard, purpose, invitation, expires))

    def challenge(self, nonce):
        return self.database.execute(
            f'SELECT * FROM challenges WHERE nonce={self.placeholder}', (nonce,)).fetchone()

    def consume_challenge(self, nonce):
        self.database.execute(f'UPDATE challenges SET used=1 WHERE nonce={self.placeholder}', (nonce,))

    def activate(self, device, public, wireguard, tcp, invitation):
        placeholders = ','.join([self.placeholder] * 4)
        self.database.execute(
            f'INSERT INTO devices(device,public,wg,tcp,revoked) VALUES ({placeholders},0)',
            (device, public, wireguard, tcp))
        self.database.execute(
            f'UPDATE invites SET device={self.placeholder} WHERE hash={self.placeholder}', (device, invitation))


class SQLiteEnrollment(EnrollmentTransaction):
    def __init__(self, database):
        super().__init__(database, '?')

    def registered(self, device):
        from .support_ids import registered
        return registered(self.database, device)

    def paid(self):
        from .paid_beta import SQLitePaidTransaction
        return SQLitePaidTransaction(self.database)

    def referrals(self):
        from .referrals import ReferralTransaction
        return ReferralTransaction(self)

    def support(self):
        from .support_ids import SupportTransaction
        return SupportTransaction(self)

    def restricted_admin(self):
        from .restricted_admin import RestrictedAdminTransaction
        return RestrictedAdminTransaction(self)


class Access:
 def __init__(self,path,clock=time.time,*,enrollment_repository=None):
  if (path is None)!=(enrollment_repository is not None):raise ValueError('Choose exactly one enrollment store')
  self.path=Path(path) if path is not None else None;self.clock=clock;self.enrollment_repository=enrollment_repository
 @contextmanager
 def db(self):
  if self.path is None:raise NotImplementedError('Legacy SQLite writers are not migrated')
  connection=sqlite3.connect(self.path,timeout=15);connection.row_factory=sqlite3.Row
  try:
   connection.execute('PRAGMA synchronous=FULL');connection.execute('BEGIN IMMEDIATE')
   with connection:yield connection
  finally:connection.close()
 @contextmanager
 def enrollment(self):
  if self.enrollment_repository is not None:
   with self.enrollment_repository.transaction() as transaction:yield transaction
  else:
   with self.db() as database:yield SQLiteEnrollment(database)
 def initialize(self):
  if self.path is None:raise NotImplementedError('Repository initialization requires an isolated migration')
  assert self.path.parent.is_dir() and not self.path.exists();fd=os.open(self.path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.close(fd)
  with self.db() as db:
   db.executescript('''CREATE TABLE invites(hash TEXT PRIMARY KEY, device TEXT UNIQUE, revoked INTEGER NOT NULL DEFAULT 0);
CREATE TABLE devices(device TEXT PRIMARY KEY, public TEXT UNIQUE NOT NULL, wg TEXT UNIQUE NOT NULL, tcp TEXT UNIQUE NOT NULL, revoked INTEGER NOT NULL DEFAULT 0);
CREATE TABLE challenges(nonce TEXT PRIMARY KEY, device TEXT NOT NULL, public TEXT NOT NULL,wg TEXT NOT NULL,purpose TEXT NOT NULL,invite TEXT,expires INTEGER NOT NULL,used INTEGER NOT NULL DEFAULT 0);''')
   from .support_ids import create
   create(db)
 @staticmethod
 def code_hash(code):
  if not isinstance(code,str):raise Rejected()
  normalized=code.strip().upper().replace('-','')
  if normalized.startswith('FC'):normalized=normalized[2:]
  if len(normalized)!=32 or any(c not in '0123456789ABCDEF' for c in normalized):raise Rejected()
  return hashlib.sha256(normalized.encode()).hexdigest()
 def invite(self):
  value=secrets.token_hex(16).upper();code='FC-'+'-'.join(value[i:i+4] for i in range(0,32,4))
  with self.enrollment() as transaction:transaction.add_invitation(self.code_hash(code))
  return code
 def revoke_device(self,device):
  if type(device) is not str or re.fullmatch('[0-9a-f]{32}',device) is None or (self.path is not None and not self.path.is_file()):raise Rejected()
  with self.enrollment() as transaction:
   if transaction.device(device) is None:raise Rejected()
   return transaction.revoke_device(device)
 @staticmethod
 def binding(public,wg):
  key=_decode(public,64);_decode(wg,32)
  return hashlib.sha256(key).hexdigest()[:32]
 def challenge(self,public_identity,wireguard_public_key,purpose,invitation=''):
  if purpose not in ('activate','status','subscription','support','ru','nl','gateway:nl-amsterdam-1','gateway:nl-amsterdam-2','refer','notices-role','notices-publish','notices-list','notices-edit') and not (isinstance(purpose,str) and re.fullmatch(r'(diagnostics|technical-metadata-v1):[0-9a-f]{64}',purpose)):raise Rejected()
  device=self.binding(public_identity,wireguard_public_key);now=int(self.clock());invite=None
  with self.enrollment() as transaction:
   row=transaction.device(device)
   if row is not None:
    if row['revoked'] or row['public']!=public_identity or row['wg']!=wireguard_public_key:raise Rejected()
   else:
    if purpose not in ('activate','status'):raise Rejected()
    if purpose=='activate':
     invite=self.code_hash(invitation);grant=transaction.invitation(invite)
     if grant is None or grant['revoked'] or grant['device'] is not None:raise Rejected()
   transaction.expire_challenges(now)
   if transaction.pending_challenges(device)>=8:raise Rejected()
   nonce=base64.b64encode(secrets.token_bytes(32)).decode()
   transaction.add_challenge(hashlib.sha256(nonce.encode()).hexdigest(),device,public_identity,wireguard_public_key,purpose,invite,now+CHALLENGE_TTL)
  return {'challenge':nonce,'expires_at':now+CHALLENGE_TTL,'audience':'family-connect/enrollment/v1'}
 def complete(self,proof,purpose,*,transaction=None):
  device=verify_transport_key_proof(proof,expected_challenge=proof['challenge']);now=int(self.clock());nonce=hashlib.sha256(proof['challenge'].encode()).hexdigest()
  with self.enrollment() if transaction is None else nullcontext(transaction) as transaction:
   challenge=transaction.challenge(nonce)
   if challenge is None or challenge['used'] or challenge['expires']<=now or challenge['purpose']!=purpose or challenge['device']!=device or challenge['public']!=proof['public_identity'] or challenge['wg']!=proof['wireguard_public_key']:raise Rejected()
   row=transaction.device(device)
   if row is None:
    if purpose!='activate':raise Rejected()
    grant=transaction.invitation(challenge['invite'])
    if grant is None or grant['revoked'] or grant['device'] is not None:raise Rejected()
    transaction.activate(device,proof['public_identity'],proof['wireguard_public_key'],str(uuid.uuid4()),challenge['invite'])
    row=transaction.device(device)
   if row['revoked'] or row['public']!=proof['public_identity'] or row['wg']!=proof['wireguard_public_key']:raise Rejected()
   transaction.consume_challenge(nonce)
   if purpose!='support':transaction.registered(device)
   return {'device':device,'public_key':row['wg'],'tcp_id':row['tcp']}
 def status(self,proof):
  """Authenticated read-only recovery query. Never consumes an invitation."""
  device=verify_transport_key_proof(proof,expected_challenge=proof['challenge']);now=int(self.clock());nonce=hashlib.sha256(proof['challenge'].encode()).hexdigest()
  with self.enrollment() as transaction:
   challenge=transaction.challenge(nonce)
   if challenge is None or challenge['used'] or challenge['expires']<=now or challenge['purpose']!='status' or challenge['device']!=device or challenge['public']!=proof['public_identity'] or challenge['wg']!=proof['wireguard_public_key']:raise Rejected()
   transaction.consume_challenge(nonce)
   row=transaction.device(device)
   if row is None:return {'device':device,'registered':False,'revoked':False,'active':False}
   grant=transaction.device_invitation(device)
   revoked=bool(row['revoked'] or (grant is not None and grant['revoked']))
   active=(not revoked and row['public']==proof['public_identity'] and row['wg']==proof['wireguard_public_key'])
   return {'device':device,'registered':True,'revoked':revoked,'active':active}
