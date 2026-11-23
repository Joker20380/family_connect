from contextlib import contextmanager
import secrets

import pytest

from control.friends.access import Rejected
from control.friends.referrals import Exhausted, RateLimited, Referrals, ReferralTransaction
from control.friends.referrals_postgres import initialize_synthetic_referrals
from device_identity.device import DeviceIdentity
from tests.test_enrollment_repository import access, parallel, peer, postgres_access
from tests.test_friends_access import proof
from tests.test_referrals import sponsor, test_referral_chain_one_use_and_idempotent_claim


@pytest.fixture
def referrals(access):
    access.clock = lambda: 100000
    service = Referrals(access, b'x' * 32)
    if access.path is not None:
        service.initialize()
    else:
        initialize_synthetic_referrals(access.enrollment_repository)
    return service


@pytest.fixture
def postgres_referrals(postgres_access):
    postgres_access.clock = lambda: 100000
    initialize_synthetic_referrals(postgres_access.enrollment_repository)
    return Referrals(postgres_access, b'x' * 32)


def client(service):
    return Referrals(peer(service.access), service.secret)


def state(service):
    with service.access.enrollment() as transaction:
        return {table: [dict(row) for row in transaction.database.execute(
            'SELECT * FROM ' + table + ' ORDER BY 1').fetchall()] for table in (
                'invites', 'devices', 'challenges', 'device_support', 'referral_links', 'referral_claims')}


def test_actual_500_slot_pool_across_independent_connections(referrals):
    referrals.DAILY = 600
    _, first = sponsor(referrals)
    _, second = sponsor(referrals)
    for index in range(499):
        referrals.claim(first, f'{index:032x}')
    results = parallel(lambda index: client(referrals).claim(second, f'{index + 500:032x}'), 8)
    assert sum(result is not None for result in results) == 1
    with pytest.raises(Exhausted):
        client(referrals).claim(second, secrets.token_hex(16))
    assert len(state(referrals)['referral_claims']) == 500


def test_concurrent_exact_replay_and_daily_boundary(referrals):
    _, token = sponsor(referrals)
    nonce = secrets.token_hex(16)
    results = parallel(lambda index: client(referrals).claim(token, nonce), 8)
    assert all(result == results[0] for result in results)
    for index in range(18):
        referrals.claim(token, secrets.token_hex(16))
    results = parallel(lambda index: client(referrals).claim(token, secrets.token_hex(16)), 8)
    assert sum(result is not None for result in results) == 1
    with pytest.raises(RateLimited):
        referrals.claim(token, secrets.token_hex(16))
    referrals.access.clock = lambda: 186399
    with pytest.raises(RateLimited):
        referrals.claim(token, secrets.token_hex(16))
    referrals.access.clock = lambda: 186400
    referrals.claim(token, secrets.token_hex(16))
    assert len(state(referrals)['referral_claims']) == 21


@pytest.mark.parametrize('point', ['invitation', 'claim'])
def test_failure_rolls_back_both_writes_and_allows_exact_retry(referrals, monkeypatch, point):
    _, token = sponsor(referrals)
    nonce = secrets.token_hex(16)
    before = state(referrals)
    with referrals.access.enrollment() as transaction:
        target = type(transaction) if point == 'invitation' else ReferralTransaction
    name = 'add_invitation' if point == 'invitation' else 'add_claim'
    original = getattr(target, name)

    def fail_after(self, *args):
        original(self, *args)
        raise RuntimeError('synthetic interrupted claim')

    with monkeypatch.context() as patch:
        patch.setattr(target, name, fail_after)
        with pytest.raises(RuntimeError, match='synthetic interrupted claim'):
            referrals.claim(token, nonce)
    assert state(referrals) == before
    first = client(referrals).claim(token, nonce)
    assert referrals.claim(token, nonce) == first
    assert len(state(referrals)['referral_claims']) == 1


def test_issue_proof_link_and_support_assignment_are_atomic(referrals, monkeypatch):
    device = DeviceIdentity.generate()
    referrals.access.complete(proof(referrals.access, device, referrals.access.invite()), 'activate')
    with referrals.access.enrollment() as transaction:
        transaction.database.execute('DELETE FROM device_support')
    pending = proof(referrals.access, device, purpose='refer')
    before = state(referrals)
    original = ReferralTransaction.add_link

    def fail_after(self, *args):
        original(self, *args)
        raise RuntimeError('synthetic interrupted issue')

    with monkeypatch.context() as patch:
        patch.setattr(ReferralTransaction, 'add_link', fail_after)
        with pytest.raises(RuntimeError, match='synthetic interrupted issue'):
            referrals.issue(pending)
    assert state(referrals) == before
    results = parallel(lambda index: client(referrals).issue(pending), 8)
    assert sum(result is not None for result in results) == 1
    with pytest.raises(Rejected):
        referrals.issue(pending)
    assert len(state(referrals)['referral_links']) == 1


@pytest.mark.parametrize('operation', ['issue', 'claim'])
def test_lost_response_after_commit_uses_existing_identity(referrals, monkeypatch, operation):
    device, token = sponsor(referrals)
    pending = proof(referrals.access, device, purpose='refer')
    nonce = secrets.token_hex(16)
    original = referrals.access.enrollment

    @contextmanager
    def lose_response():
        with original() as transaction:
            yield transaction
        raise RuntimeError('synthetic committed response lost')

    with monkeypatch.context() as patch:
        patch.setattr(referrals.access, 'enrollment', lose_response)
        with pytest.raises(RuntimeError, match='synthetic committed response lost'):
            if operation == 'issue':
                referrals.issue(pending)
            else:
                referrals.claim(token, nonce)
    if operation == 'issue':
        with pytest.raises(Rejected):
            client(referrals).issue(pending)
        assert client(referrals).issue(proof(referrals.access, device, purpose='refer'))['url'].endswith(token)
    else:
        assert client(referrals).claim(token, nonce) == referrals.claim(token, nonce)
        assert len(state(referrals)['referral_claims']) == 1
    assert len(state(referrals)['referral_links']) == 1


def test_request_is_bound_to_sponsor_and_reconstructed_invitation(referrals):
    _, first = sponsor(referrals)
    _, second = sponsor(referrals)
    nonce = secrets.token_hex(16)
    result = referrals.claim(first, nonce)
    before = state(referrals)
    with pytest.raises(Rejected):
        referrals.claim(second, nonce)
    assert state(referrals) == before
    assert referrals.claim(first, nonce) == result
    other_code = referrals.access.invite()
    with referrals.access.enrollment() as transaction:
        transaction.database.execute('UPDATE referral_claims SET invite=' + transaction.placeholder,
                                     (referrals.access.code_hash(other_code),))
    before = state(referrals)
    with pytest.raises(Rejected):
        referrals.claim(first, nonce)
    assert state(referrals) == before


@pytest.mark.parametrize('revoked', ['device', 'sponsor-invite', 'child-invite'])
def test_revocation_and_independent_previously_issued_grants(referrals, revoked):
    device, token = sponsor(referrals)
    nonce = secrets.token_hex(16)
    issued = referrals.claim(token, nonce)
    pending = proof(referrals.access, device, purpose='refer')
    with referrals.access.enrollment() as transaction:
        if revoked == 'device':
            transaction.revoke_device(device.reference)
        elif revoked == 'sponsor-invite':
            transaction.database.execute('UPDATE invites SET revoked=1 WHERE device=' + transaction.placeholder,
                                         (device.reference,))
        else:
            transaction.database.execute('UPDATE invites SET revoked=1 WHERE hash=' + transaction.placeholder,
                                         (referrals.access.code_hash(issued['invitation']),))
    before = state(referrals)
    if revoked == 'child-invite':
        with pytest.raises(Rejected):
            referrals.claim(token, nonce)
    else:
        with pytest.raises(Rejected):
            referrals.claim(token, secrets.token_hex(16))
        with pytest.raises(Rejected):
            referrals.issue(pending)
        assert referrals.claim(token, nonce) == issued
    assert state(referrals) == before


def test_revoke_racing_claim_has_a_serial_order(referrals):
    device, token = sponsor(referrals)
    nonce = secrets.token_hex(16)
    results = parallel(lambda index: client(referrals).claim(token, nonce) if index == 0
                       else peer(referrals.access).revoke_device(device.reference), 2)
    with pytest.raises(Rejected):
        referrals.claim(token, secrets.token_hex(16))
    if results[0] is None:
        assert state(referrals)['referral_claims'] == []
    else:
        assert referrals.claim(token, nonce) == results[0]
        assert len(state(referrals)['referral_claims']) == 1


@pytest.mark.parametrize('bad', ['', 'z' * 64, '0' * 64, None, True])
def test_invalid_or_unknown_token_never_writes(referrals, bad):
    before = state(referrals)
    with pytest.raises(Rejected):
        referrals.claim(bad, secrets.token_hex(16))
    assert state(referrals) == before


@pytest.mark.parametrize('bad', ['', 'z' * 32, '0' * 31, None, True])
def test_invalid_request_never_writes(referrals, bad):
    _, token = sponsor(referrals)
    before = state(referrals)
    with pytest.raises(Rejected):
        referrals.claim(token, bad)
    assert state(referrals) == before


def test_wrong_or_expired_proof_never_issues(referrals):
    device, token = sponsor(referrals)
    wrong = proof(referrals.access, device, purpose='ru')
    before = state(referrals)
    with pytest.raises(Rejected):
        referrals.issue(wrong)
    assert state(referrals) == before
    pending = proof(referrals.access, device, purpose='refer')
    referrals.access.clock = lambda: 100100
    before = state(referrals)
    with pytest.raises(Rejected):
        referrals.issue(pending)
    assert state(referrals) == before


def test_repository_does_not_fall_back_to_sqlite(postgres_referrals):
    referrals = postgres_referrals
    device, token = sponsor(referrals)
    pending = proof(referrals.access, device, purpose='refer')
    before = state(referrals)
    with pytest.raises(NotImplementedError, match='Legacy SQLite writers'):
        referrals.initialize()
    with referrals.access.enrollment() as transaction:
        transaction.database.execute('UPDATE ha_referrals_schema SET purpose=%s', ('wrong-purpose',))
    for attempt in (lambda: referrals.issue(pending), lambda: referrals.claim(token, secrets.token_hex(16))):
        with pytest.raises(RuntimeError, match='Referral rehearsal schema mismatch'):
            attempt()
    assert state(referrals) == before


def test_postgres_backend_loss_rolls_back_claim(postgres_referrals, monkeypatch):
    referrals = postgres_referrals
    import psycopg
    _, token = sponsor(referrals)
    nonce = secrets.token_hex(16)
    before = state(referrals)
    original = ReferralTransaction.add_claim
    repository = referrals.access.enrollment_repository

    def terminate_after(self, *args):
        original(self, *args)
        pid = self.database.execute('SELECT pg_backend_pid() AS pid').fetchone()['pid']
        with repository.connect() as killer:
            assert killer.execute('SELECT pg_terminate_backend(%s,1000) AS terminated', (pid,)).fetchone()['terminated']
        self.database.execute('SELECT 1')

    with monkeypatch.context() as patch:
        patch.setattr(ReferralTransaction, 'add_claim', terminate_after)
        with pytest.raises(psycopg.OperationalError):
            referrals.claim(token, nonce)
    assert state(referrals) == before
    assert client(referrals).claim(token, nonce) == referrals.claim(token, nonce)
