import concurrent.futures
import pytest
from control.friends.access import Access, Rejected
from control.friends.chat import ChatAccess
from device_identity.device import DeviceIdentity
import RNS
from messenger.admission import message
from tests.test_friends_access import proof


@pytest.fixture
def registry(tmp_path):
    access = Access(tmp_path/'access.db', clock=lambda:1000); access.initialize()
    registry = ChatAccess(access); registry.initialize()
    return registry


def activated(registry):
    device = DeviceIdentity.generate()
    registry.access.complete(proof(registry.access, device, registry.access.invite()), 'activate')
    return device


def request(registry, device, chat):
    public = chat.profile()['public']
    challenge = registry.challenge(device.public_identity, device.wireguard_public_key, public)
    return dict(proof=device.prove_transport_key(challenge['challenge']),
                **chat.enrollment_proof(challenge['device'], challenge['challenge']))


class SigningChat:
    # Server suite must run with control/identity lockfiles, without LXMF.
    def __init__(self): self.identity = RNS.Identity()
    def profile(self): return dict(public=self.identity.get_public_key().hex())
    def enrollment_proof(self, device, challenge):
        public=self.profile()['public']
        return dict(chat_public=public,chat_signature=self.identity.sign(message(public,device,challenge)).hex())
    def close(self): pass


@pytest.fixture
def chat(): return SigningChat()


def test_active_device_two_proofs_replay_and_retry(registry, chat):
    device = activated(registry); enrollment = request(registry, device, chat)
    assert registry.register(**enrollment)['status']=='pending-node'
    with pytest.raises(Rejected): registry.register(**enrollment)
    assert registry.register(**request(registry, device, chat))['chat_public']==chat.profile()['public']
    assert registry.desired_members()==[chat.profile()['public']]
    registry.initialize() # Additive migration is idempotent, preserves membership.
    assert registry.desired_members()==[chat.profile()['public']]


def test_unactivated_device_cannot_request_challenge(registry, chat):
    with pytest.raises(Rejected): request(registry, DeviceIdentity.generate(), chat)


@pytest.mark.parametrize('target', ['devices','invites'])
def test_revocation_between_challenge_and_registration_and_after(registry, chat, target):
    device=activated(registry); first=request(registry,device,chat)
    registry.register(**first); pending=request(registry,device,chat)
    reference=registry.access.binding(device.public_identity,device.wireguard_public_key)
    with registry.access.db() as db: db.execute(f'UPDATE {target} SET revoked=1 WHERE device=?',(reference,))
    with pytest.raises(Rejected): registry.register(**pending)
    with pytest.raises(Rejected): request(registry,device,chat)
    assert registry.desired_members()==[]


def test_challenge_cannot_bind_another_chat_key(registry, chat, tmp_path):
    device=activated(registry); enrollment=request(registry,device,chat)
    other=SigningChat()
    try:
        device_ref=registry.access.binding(device.public_identity,device.wireguard_public_key)
        forged=dict(proof=enrollment['proof'],**other.enrollment_proof(device_ref,enrollment['proof']['challenge']))
        with pytest.raises(Rejected): registry.register(**forged)
        registry.register(**enrollment)
        with pytest.raises(Rejected): request(registry,device,other)
    finally: other.close()


def test_device_proof_and_chat_signature_both_required(registry, chat):
    device=activated(registry); enrollment=request(registry,device,chat)
    bad=dict(enrollment,chat_signature='00'*64)
    with pytest.raises(Rejected): registry.register(**bad)
    other=activated(registry)
    bad=dict(enrollment,proof=other.prove_transport_key(enrollment['proof']['challenge']))
    with pytest.raises(Rejected): registry.register(**bad)
    assert registry.desired_members()==[]
    registry.register(**enrollment)


def test_expiry_and_challenge_cap(registry, chat):
    device=activated(registry); enrollment=request(registry,device,chat)
    for _ in range(7): request(registry,device,chat)
    with pytest.raises(Rejected): request(registry,device,chat)
    registry.access.clock=lambda:1120
    with pytest.raises(Rejected): registry.register(**enrollment)
    registry.register(**request(registry,device,chat))


def test_same_chat_cannot_be_claimed_by_two_invited_devices(registry,chat):
    requests=[request(registry,activated(registry),chat) for _ in range(2)]
    def claim(value):
        try: registry.register(**value); return True
        except Rejected: return False
    with concurrent.futures.ThreadPoolExecutor(2) as pool: assert sum(pool.map(claim,requests))==1
    assert len(registry.desired_members())==1


def test_snapshot_sequence_and_lease_survive_reinitialization(registry,chat):
    device=activated(registry);registry.register(**request(registry,device,chat))
    first=registry.snapshot();registry.initialize();second=registry.snapshot()
    assert second['sequence']==first['sequence']+1
    assert second['expires_at']==1100 and second['public_keys']==[chat.profile()['public']]


def test_busy_sync_fails_before_building_snapshot(tmp_path,monkeypatch):
    import fcntl
    from control.friends import chat_sync
    monkeypatch.setattr(chat_sync,'ROOT',tmp_path)
    with (tmp_path/'chat-sync.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError):chat_sync.synchronize(None)
