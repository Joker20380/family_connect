import concurrent.futures
import pytest
from control.friends.access import Access,Rejected
from device_identity.device import DeviceIdentity

@pytest.fixture
def access(tmp_path):
 value=Access(tmp_path/'test.db',clock=lambda:1000);value.initialize();return value

def proof(access,device,code='',purpose='activate'):
 import base64
 public=base64.b64encode(device.public_identity).decode() if isinstance(device.public_identity,bytes) else device.public_identity
 challenge=access.challenge(public,device.wireguard_public_key,purpose,code)
 return device.prove_transport_key(challenge['challenge'])

def test_single_use_invite_and_perpetual_device(access):
 code=access.invite();one=DeviceIdentity.generate();two=DeviceIdentity.generate()
 p=proof(access,one,code);result=access.complete(p,'activate')
 with pytest.raises(Rejected):access.complete(p,'activate')
 with pytest.raises(Rejected):proof(access,two,code)
 access.clock=lambda:1000+10*365*86400
 resumed=access.complete(proof(access,one,purpose='nl'),'nl')
 assert resumed==result

def test_parallel_claims_grant_only_one_device(access):
 code=access.invite();devices=[DeviceIdentity.generate(),DeviceIdentity.generate()];proofs=[proof(access,d,code) for d in devices]
 def claim(p):
  try:access.complete(p,'activate');return True
  except Rejected:return False
 with concurrent.futures.ThreadPoolExecutor(2) as pool:assert sum(pool.map(claim,proofs))==1

def test_signature_purpose_and_revocation(access):
 device=DeviceIdentity.generate();p=proof(access,device,access.invite())
 with pytest.raises(Rejected):access.complete(p,'ru')
 broken=dict(p);broken['signature']='A'*88
 with pytest.raises(ValueError):access.complete(broken,'activate')
 record=access.complete(p,'activate')
 with access.db() as db:db.execute('UPDATE devices SET revoked=1 WHERE device=?',(record['device'],))
 with pytest.raises(Rejected):proof(access,device,purpose='ru')


def test_installation_without_invitation_cannot_enroll(access):
 device=DeviceIdentity.generate()
 for purpose in ('activate','register','nl'):
  with pytest.raises(Rejected):proof(access,device,purpose=purpose)
 with access.db() as db:assert db.execute('SELECT COUNT(*) FROM devices').fetchone()[0]==0


def test_shorter_challenge_expires_at_server_deadline(access):
 device=DeviceIdentity.generate();p=proof(access,device,access.invite())
 access.clock=lambda:1100
 with pytest.raises(Rejected):access.complete(p,'activate')
