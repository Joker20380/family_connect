import base64
import copy
import json
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import pytest
from device_identity.friends import load_friends_identity
from provisioning.friends_store import FriendsConfigurationStore
from provisioning.friends import FriendsError

FIXTURE=json.loads((Path(__file__).parent/'fixtures/desktop-friends-catalog-v2.json').read_text())

@pytest.fixture
def owner(tmp_path):
    path=tmp_path/'identity';device=load_friends_identity(path,create=True)
    store=FriendsConfigurationStore(path,device,base64.b64decode(FIXTURE['anchor']))
    def response(country='nl'):
        r=copy.deepcopy(FIXTURE['vectors'][0]['reply']);r.update(device=device.reference,country=country,address='10.83.0.2/32' if country=='nl' else '10.84.0.2/32');return r
    return path,store,response


def test_resume_and_shared_country_floor(owner):
    path,store,response=owner
    first=store.accept('nl',lambda floor,h:response())
    assert first.sequence==2
    seen=[]
    fresh=FriendsConfigurationStore(path,load_friends_identity(path,create=False),store.anchor)
    def fetch(floor,h):
        seen.append((floor,h));return response('ru')
    fresh.accept('ru',fetch)
    assert seen==[(2,first.catalog_hash)]
    assert (path/'friends.configuration.json').stat().st_mode & 0o777==0o600
    assert set(json.loads((path/'friends.configuration.json').read_bytes()))=={'ru','nl'}


def test_parallel_writers_share_floor(owner):
    path,store,response=owner;seen=[]
    def work(i):
        country='ru' if i%2 else 'nl'
        def fetch(floor,h):seen.append(floor);return response(country)
        return store.accept(country,fetch)
    with ThreadPoolExecutor(max_workers=6) as pool:list(pool.map(work,range(12)))
    assert seen.count(0)==1 and seen.count(2)==11
    assert len(json.loads((path/'friends.configuration.json').read_bytes()))==2


@pytest.mark.parametrize('damage',['missing','corrupt','marker_missing','marker_corrupt','mode','symlink','hardlink','identity_missing'])
def test_corrupt_storage_refused_before_network(owner,damage):
    path,store,response=owner;store.accept('nl',lambda *_:response())
    file=path/'friends.configuration.json';marker=path/'friends.configuration.json.initialized'
    if damage=='missing':file.unlink()
    elif damage=='corrupt':file.write_text('{')
    elif damage=='marker_missing':marker.unlink()
    elif damage=='marker_corrupt':marker.write_bytes(b'x')
    elif damage=='mode':file.chmod(0o644)
    elif damage=='symlink':file.rename(path/'saved');file.symlink_to('saved')
    elif damage=='hardlink':os.link(file,path/'linked')
    elif damage=='identity_missing':(path/'wireguard.key').unlink()
    calls=[]
    with pytest.raises((ValueError,OSError)):
        store.accept('nl',lambda *_:calls.append(1))
    assert not calls


def test_network_denial_preserves_cache_and_does_not_return_offline_profile(owner):
    path,store,response=owner;store.accept('nl',lambda *_:response())
    original=(path/'friends.configuration.json').read_bytes()
    def denied(*_):raise FriendsError('access_rejected')
    with pytest.raises(FriendsError):store.accept('nl',denied)
    assert (path/'friends.configuration.json').read_bytes()==original


@pytest.mark.parametrize('initial',[True,False])
def test_failed_replace_never_returns_uncommitted_profile(owner,monkeypatch,initial):
    path,store,response=owner
    if not initial:store.accept('nl',lambda *_:response())
    def fail(*args,**kwargs):raise OSError('simulated interrupted write')
    with monkeypatch.context() as m:
        m.setattr('provisioning.friends_store.os.replace',fail)
        with pytest.raises(OSError):store.accept('nl',lambda *_:response())
    assert not list(path.glob('.friends-config-*'))
    if initial:
        with pytest.raises(ValueError):store.accept('nl',lambda *_:pytest.fail('must recover first'))
    else:assert store.accept('nl',lambda *_:response()).sequence==2


def test_validly_signed_same_sequence_change_is_rejected(owner):
    path,store,response=owner;store.accept('nl',lambda *_:response())
    # Another legitimately signed payload at sequence 2: valid_flags vector.
    changed=copy.deepcopy(next(v['reply'] for v in FIXTURE['vectors'] if v['name']=='valid_flags'))
    changed['device']=store.device.reference
    original=(path/'friends.configuration.json').read_bytes()
    with pytest.raises(ValueError):store.accept('nl',lambda *_:changed)
    assert (path/'friends.configuration.json').read_bytes()==original
