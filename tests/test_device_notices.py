import base64
import pytest
from control.friends.access import Access, Rejected
from control.friends.notices import device_request, NoticeDenied
from device_identity.device import DeviceIdentity
from scripts.service_notices import Notices

@pytest.fixture
def setup(tmp_path):
    access=Access(tmp_path/'access.db');access.initialize()
    device=DeviceIdentity.generate()
    def proof(purpose, invitation=''):
        public=device.public_identity
        if isinstance(public,bytes):public=base64.b64encode(public).decode()
        c=access.challenge(public,device.wireguard_public_key,purpose,invitation)
        return device.prove_transport_key(c['challenge'])
    record=access.complete(proof('activate',access.invite()),'activate')
    registry=tmp_path/'notices.sqlite';store=Notices(registry)
    def request(action, **extra):
        return device_request(access,registry,tmp_path/'feed.json',action,dict(proof=proof('notices-'+action),**extra))
    yield access,store,record['device'],proof,request,tmp_path
    store.db.close()

NOTICE=dict(id='a'*32,kind='information',title='Update',body='New version',platforms=['android'],days=30)

def test_grant_role_publish_retry_and_revoke(setup):
    access,store,device,proof,request,path=setup
    assert request('role')['role']=='member'
    with pytest.raises(NoticeDenied):request('publish',notice=NOTICE)
    store.grant_device(access,device,'Owner')
    assert request('role')==dict(device=device,role='administrator',name='Owner')
    assert request('publish',notice=NOTICE)==dict(id='a'*32,status='published')
    assert request('publish',notice=NOTICE)['id']=='a'*32
    assert len(store.feed()['events'])==1
    store.revoke_device(device)
    assert request('role')['role']=='member'
    with pytest.raises(NoticeDenied):request('publish',notice=NOTICE)

def test_proof_cannot_replay_or_cross_purpose(setup):
    access,store,device,proof,request,path=setup
    store.grant_device(access,device,'Owner')
    p=proof('notices-role')
    with pytest.raises(Rejected):device_request(access,path/'notices.sqlite',path/'feed.json','publish',dict(proof=p,notice=NOTICE))
    device_request(access,path/'notices.sqlite',path/'feed.json','role',dict(proof=p))
    with pytest.raises(Rejected):device_request(access,path/'notices.sqlite',path/'feed.json','role',dict(proof=p))

def test_device_revocation_and_unknown_grant(setup):
    access,store,device,proof,request,path=setup
    with pytest.raises(ValueError):store.grant_device(access,'f'*32,'Owner')
    store.grant_device(access,device,'Owner')
    p=proof('notices-publish')
    with access.db() as db:db.execute('UPDATE devices SET revoked=1 WHERE device=?',(device,))
    with pytest.raises(Rejected):device_request(access,path/'notices.sqlite',path/'feed.json','publish',dict(proof=p,notice=NOTICE))
    with pytest.raises(ValueError):store.grant_device(access,device,'Owner')

def test_role_revoked_after_challenge_denies_publication(setup):
    access,store,device,proof,request,path=setup
    store.grant_device(access,device,'Owner');p=proof('notices-publish');store.revoke_device(device)
    with pytest.raises(NoticeDenied):device_request(access,path/'notices.sqlite',path/'feed.json','publish',dict(proof=p,notice=NOTICE))
    assert store.feed()['events']==[]

def test_edit_list_retry_conflict_and_legacy_feed(setup):
    from control.friends.notices import NoticeConflict
    access,store,device,proof,request,path=setup
    with pytest.raises(NoticeDenied):request('list',offset=0)
    store.grant_device(access,device,'Owner');request('publish',notice=NOTICE)
    page=request('list',offset=0);assert page['next_offset'] is None
    assert page['events'][0]['revision']==1
    edit=dict(id=NOTICE['id'],revision=1,request_id='b'*32,title='Edited',body='Corrected text')
    result=request('edit',notice=edit);assert result['revision']==2
    assert request('edit',notice=edit)==result
    assert store.feed()['events'][0]['title']=='Update'  # Old clients keep immutable v1.
    assert store.feed(version=2)['events'][0]['title']=='Edited'
    assert request('list',offset=0)['events'][0]['revision']==2
    with pytest.raises(NoticeConflict):request('edit',notice=dict(edit,request_id='c'*32))
    store.revoke_device(device)
    with pytest.raises(NoticeDenied):request('edit',notice=dict(edit,revision=2,request_id='d'*32))
    assert store.db.execute('SELECT COUNT(*) FROM edit_operations').fetchone()[0]==1


def test_edit_validation_and_missing_notice(setup):
    access,store,device,proof,request,path=setup
    store.grant_device(access,device,'Owner');request('publish',notice=NOTICE)
    edit=dict(id=NOTICE['id'],revision=1,request_id='b'*32,title='',body='Text')
    with pytest.raises(ValueError):request('edit',notice=edit)
    with pytest.raises(ValueError):request('edit',notice=dict(edit,id='c'*32,title='Valid'))
    assert store.current_event(NOTICE['id'])['revision']==1
