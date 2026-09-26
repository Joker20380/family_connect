import concurrent.futures
import secrets
import pytest
from control.friends.access import Access,Rejected
from control.friends.referrals import Referrals,Exhausted,RateLimited
from device_identity.device import DeviceIdentity
from tests.test_friends_access import proof


@pytest.fixture
def referrals(tmp_path):
    access=Access(tmp_path/'access.db',clock=lambda:100000);access.initialize()
    service=Referrals(access,b'x'*32);service.initialize();return service


def sponsor(service):
    d=DeviceIdentity.generate();service.access.complete(proof(service.access,d,service.access.invite()),'activate')
    token=service.issue(proof(service.access,d,purpose='refer'))['url'].split('#')[1]
    return d,token


def test_referral_chain_one_use_and_idempotent_claim(referrals):
    parent,token=sponsor(referrals);nonce=secrets.token_hex(16)
    result=referrals.claim(token,nonce);assert referrals.claim(token,nonce)==result
    child=DeviceIdentity.generate();referrals.access.complete(proof(referrals.access,child,result['invitation']),'activate')
    assert referrals.claim(token,nonce)['status']=='activated'
    with pytest.raises(Rejected):proof(referrals.access,DeviceIdentity.generate(),result['invitation'])
    next_token=referrals.issue(proof(referrals.access,child,purpose='refer'))['url'].split('#')[1]
    assert next_token!=token
    assert referrals.claim(next_token,secrets.token_hex(16))['invitation']!=result['invitation']
    assert referrals.issue(proof(referrals.access,parent,purpose='refer'))['url'].endswith(token)


def test_500_is_one_shared_atomic_pool(referrals):
    referrals.DAILY=600
    _,one=sponsor(referrals);_,two=sponsor(referrals)
    # Exercise all 500 slots, then contend on the last one.
    for _ in range(499):referrals.claim(one,secrets.token_hex(16))
    def claim(token):
        try:return referrals.claim(token,secrets.token_hex(16))
        except Exhausted:return None
    with concurrent.futures.ThreadPoolExecutor(8) as pool:
        assert sum(value is not None for value in pool.map(claim,[one,two]*4))==1
    with referrals.access.db() as db:assert db.execute('SELECT COUNT(*) FROM referral_claims').fetchone()[0]==500
    referrals.initialize()
    with pytest.raises(Exhausted):referrals.claim(two,secrets.token_hex(16))


def test_parallel_repeat_uses_one_slot(referrals):
    _,token=sponsor(referrals);nonce=secrets.token_hex(16)
    with concurrent.futures.ThreadPoolExecutor(8) as pool:
        values=list(pool.map(lambda _:referrals.claim(token,nonce),range(12)))
    assert len({v['invitation'] for v in values})==1
    with referrals.access.db() as db:assert db.execute('SELECT COUNT(*) FROM referral_claims').fetchone()[0]==1


def test_daily_limit_and_parent_revocation(referrals):
    parent,token=sponsor(referrals);nonces=[secrets.token_hex(16) for _ in range(20)]
    for nonce in nonces:referrals.claim(token,nonce)
    with pytest.raises(RateLimited):referrals.claim(token,secrets.token_hex(16))
    assert referrals.claim(token,nonces[0])['status']=='issued'
    referrals.access.clock=lambda:186401
    referrals.claim(token,secrets.token_hex(16))
    with referrals.access.db() as db:db.execute('UPDATE devices SET revoked=1 WHERE device=?',(parent.reference,))
    with pytest.raises(Rejected):referrals.claim(token,secrets.token_hex(16))
    # Earlier issued child grants remain their own independent invitations.
    assert referrals.claim(token,nonces[0])['status']=='issued'


def test_invalid_and_wrong_purpose_never_mint(referrals):
    parent,token=sponsor(referrals)
    with pytest.raises(Rejected):referrals.issue(proof(referrals.access,parent,purpose='ru'))
    for bad in ('','x'*64,'00'*32):
        with pytest.raises(Rejected):referrals.claim(bad,secrets.token_hex(16))
    with referrals.access.db() as db:assert db.execute('SELECT COUNT(*) FROM referral_claims').fetchone()[0]==0
