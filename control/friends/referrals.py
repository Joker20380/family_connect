"""Bounded referral campaign; claims and one-use invites commit atomically."""
import hashlib
import hmac
import re
from .access import Rejected


class Exhausted(Rejected): pass
class RateLimited(Rejected): pass


class Referrals:
    LIMIT = 500
    DAILY = 20
    def __init__(self, access, secret):
        if type(secret) is not bytes or len(secret)!=32:raise ValueError('Referral secret required')
        self.access,self.secret=access,secret

    def initialize(self):
        with self.access.db() as db:
            db.execute('CREATE TABLE IF NOT EXISTS referral_links (token TEXT PRIMARY KEY, sponsor TEXT UNIQUE NOT NULL)')
            db.execute('''CREATE TABLE IF NOT EXISTS referral_claims (
                request TEXT PRIMARY KEY, sponsor TEXT NOT NULL, invite TEXT UNIQUE NOT NULL,
                created INTEGER NOT NULL)''')
            db.execute('CREATE INDEX IF NOT EXISTS referral_daily ON referral_claims(sponsor,created)')

    def digest(self, value):return hmac.new(self.secret,value.encode(),hashlib.sha256).hexdigest()

    @staticmethod
    def active(db, device):
        row=db.execute('''SELECT d.revoked AS device_revoked,i.revoked AS invite_revoked
            FROM devices d JOIN invites i ON i.device=d.device WHERE d.device=?''',(device,)).fetchone()
        if row is None or row['device_revoked'] or row['invite_revoked']:raise Rejected()

    def issue(self, proof):
        device=self.access.complete(proof,'refer')['device']
        token=self.digest('referral-v1:'+device)
        token_hash=hashlib.sha256(token.encode()).hexdigest()
        with self.access.db() as db:
            self.active(db,device)
            db.execute('INSERT OR IGNORE INTO referral_links VALUES (?,?)',(token_hash,device))
            remaining=self.LIMIT-db.execute('SELECT COUNT(*) FROM referral_claims').fetchone()[0]
        return dict(url='https://185.251.89.19:8443/invite/#'+token,pool_limit=self.LIMIT,remaining=max(0,remaining))

    def claim(self, token, request_id):
        if type(token) is not str or not re.fullmatch('[0-9a-f]{64}',token):raise Rejected()
        if type(request_id) is not str or not re.fullmatch('[0-9a-f]{32}',request_id):raise Rejected()
        token_hash=hashlib.sha256(token.encode()).hexdigest()
        request=self.digest('request-v1:'+request_id)
        # Reconstruct only this claim's code; no plaintext invitation archive in DB.
        raw=self.digest('invite-v1:'+request)[:32].upper()
        code='FC-'+'-'.join(raw[i:i+4] for i in range(0,32,4))
        now=int(self.access.clock())
        with self.access.db() as db:
            link=db.execute('SELECT sponsor FROM referral_links WHERE token=?',(token_hash,)).fetchone()
            if link is None:raise Rejected()
            prior=db.execute('SELECT invite FROM referral_claims WHERE request=?',(request,)).fetchone()
            if prior is not None:
                grant=db.execute('SELECT device,revoked FROM invites WHERE hash=?',(prior['invite'],)).fetchone()
                if grant is None or grant['revoked']:raise Rejected()
                return dict(invitation=code,status='activated' if grant['device'] else 'issued')
            self.active(db,link['sponsor'])
            if db.execute('SELECT COUNT(*) FROM referral_claims').fetchone()[0]>=self.LIMIT:raise Exhausted()
            if db.execute('SELECT COUNT(*) FROM referral_claims WHERE sponsor=? AND created>?',
                          (link['sponsor'],now-86400)).fetchone()[0]>=self.DAILY:raise RateLimited()
            db.execute('INSERT INTO invites(hash) VALUES (?)',(self.access.code_hash(code),))
            db.execute('INSERT INTO referral_claims VALUES (?,?,?,?)',
                       (request,link['sponsor'],self.access.code_hash(code),now))
        return dict(invitation=code,status='issued')
