"""Bounded referral campaign; claims and one-use invites commit atomically."""
import hashlib
import hmac
import re
from .access import Rejected


class Exhausted(Rejected): pass
class RateLimited(Rejected): pass


class ReferralTransaction:
    def __init__(self, enrollment):
        self.enrollment = enrollment
        self.database = enrollment.database
        self.placeholder = enrollment.placeholder

    def active(self, device):
        row = self.enrollment.device(device)
        invitation = self.enrollment.device_invitation(device)
        if row is None or row['revoked'] or invitation is None or invitation['revoked']:
            raise Rejected()

    def link(self, token):
        return self.database.execute(
            f'SELECT sponsor FROM referral_links WHERE token={self.placeholder}', (token,)).fetchone()

    def add_link(self, token, sponsor):
        self.database.execute(f'INSERT INTO referral_links(token,sponsor) VALUES ({self.placeholder},{self.placeholder}) '
                              'ON CONFLICT DO NOTHING', (token, sponsor))
        row = self.link(token)
        if row is None or row['sponsor'] != sponsor:
            raise Rejected()

    def claim(self, request):
        return self.database.execute(
            f'SELECT sponsor,invite FROM referral_claims WHERE request={self.placeholder}', (request,)).fetchone()

    def total(self):
        return self.database.execute('SELECT COUNT(*) AS total FROM referral_claims').fetchone()['total']

    def daily(self, sponsor, since):
        return self.database.execute('SELECT COUNT(*) AS total FROM referral_claims '
            f'WHERE sponsor={self.placeholder} AND created>{self.placeholder}', (sponsor, since)).fetchone()['total']

    def add_claim(self, request, sponsor, invitation, created):
        self.database.execute('INSERT INTO referral_claims(request,sponsor,invite,created) VALUES (' +
                              ','.join([self.placeholder] * 4) + ')', (request, sponsor, invitation, created))


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

    def issue(self, proof):
        with self.access.enrollment() as transaction:
            database=transaction.referrals()
            device=self.access.complete(proof,'refer',transaction=transaction)['device']
            token=self.digest('referral-v1:'+device)
            token_hash=hashlib.sha256(token.encode()).hexdigest()
            database.active(device)
            database.add_link(token_hash,device)
            remaining=self.LIMIT-database.total()
        return dict(url='https://185.251.89.19:8443/i/#'+token,pool_limit=self.LIMIT,remaining=max(0,remaining))

    def claim(self, token, request_id):
        if type(token) is not str or not re.fullmatch('[0-9a-f]{64}',token):raise Rejected()
        if type(request_id) is not str or not re.fullmatch('[0-9a-f]{32}',request_id):raise Rejected()
        token_hash=hashlib.sha256(token.encode()).hexdigest()
        request=self.digest('request-v1:'+request_id)
        # Reconstruct only this claim's code; no plaintext invitation archive in DB.
        raw=self.digest('invite-v1:'+request)[:32].upper()
        code='FC-'+'-'.join(raw[i:i+4] for i in range(0,32,4))
        now=int(self.access.clock())
        with self.access.enrollment() as transaction:
            database=transaction.referrals()
            link=database.link(token_hash)
            if link is None:raise Rejected()
            prior=database.claim(request)
            if prior is not None:
                if prior['sponsor']!=link['sponsor'] or prior['invite']!=self.access.code_hash(code):raise Rejected()
                grant=transaction.invitation(prior['invite'])
                if grant is None or grant['revoked']:raise Rejected()
                return dict(invitation=code,status='activated' if grant['device'] else 'issued')
            database.active(link['sponsor'])
            if database.total()>=self.LIMIT:raise Exhausted()
            if database.daily(link['sponsor'],now-86400)>=self.DAILY:raise RateLimited()
            transaction.add_invitation(self.access.code_hash(code))
            database.add_claim(request,link['sponsor'],self.access.code_hash(code),now)
        return dict(invitation=code,status='issued')
