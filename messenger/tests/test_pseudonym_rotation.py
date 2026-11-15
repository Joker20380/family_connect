from copy import deepcopy
import time
import uuid
import pytest

from control.friends.pseudonyms import ENVIRONMENT, prepare, pseudonym, save, seal, unseal
from control.friends.subscription_events import read
from messenger.tests.test_support import support
from messenger.tests.test_subscription_notifications import route, cycle, pay
from tests.test_paid_beta import registry
from provisioning.support_worker import SupportError


def rotation(route, tmp_path, monkeypatch):
    registry, second, owner, clients, bindings = route
    devices = [registry[1].reference, second[1].reference]
    with registry[0].db() as database:
        events = [row[0] for row in database.execute('SELECT event_id FROM paid_beta_events')]
    aliases = prepare(dict(device=devices,panel_event=events),b'n'*32,legacy_key=b'h'*32)
    path = tmp_path/'aliases.json';save(path,aliases);monkeypatch.setenv(ENVIRONMENT,str(path))
    new = deepcopy(bindings);new['sequence'] += 1
    for item in new['devices']:
        item['pseudonym'] = pseudonym(b'n'*32,'device',item['device'])
    owner.update(unseal(seal(new,'support',b'n'*32,aliases),'support',aliases))
    return aliases, new


def test_support_replay_keeps_original_request_message_and_identity(route,tmp_path,monkeypatch):
    _,_,owner,clients,bindings=route
    old = bindings['devices'][0]['pseudonym']
    request=dict(pseudonym=old,address=clients[0].profile()['address'],request_id=str(uuid.uuid4()),actor='1',text='isolated migration test')
    response=owner.send(**request)
    previous=owner.store._get('support-request:'+request['request_id'])
    threads=deepcopy(owner.store._get('support-threads'))
    aliases,new=rotation(route,tmp_path,monkeypatch)
    assert owner.store._get('support-threads') == threads
    assert owner.send(**dict(request,pseudonym=new['devices'][0]['pseudonym'])) == response
    assert owner.send(**request) == response
    assert owner.store._get('support-request:'+request['request_id']) == previous
    assert len(owner.history(old)['messages']) == 1
    for field,value in [('text','changed'),('actor','2'),('address','f'*32)]:
        with pytest.raises(SupportError,match='request_conflict'):
            owner.send(**dict(request,**{field:value}))


@pytest.mark.parametrize('blocked',['revoked','identity_changed'])
def test_new_pseudonym_cannot_clear_pinned_block(route,tmp_path,monkeypatch,blocked):
    _,_,owner,_,bindings=route
    old=bindings['devices'][0]['pseudonym']
    with owner.store._lock,owner.store._db:
        threads=owner.store._get('support-threads');threads[old]['blocked']=blocked
        owner.store._put('support-threads',threads)
    aliases,new=rotation(route,tmp_path,monkeypatch)
    assert owner.binding(new['devices'][0]['pseudonym'])['state'] == blocked
    assert len(owner.store._get('support-threads')) == 2
    forged=deepcopy(new);forged['sequence']+=1;forged['devices'][0]['pseudonym']='f'*64
    with pytest.raises(SupportError,match='ambiguous_binding'):
        owner.update(unseal(seal(forged,'support',b'n'*32,aliases),'support',aliases))


def test_pending_job_baseline_cursor_event_and_request_survive_rotation(route,tmp_path,monkeypatch):
    registry,_,owner,_,_=route;now=int(time.time())
    cycle(route,now=now);pay(registry,now=now);cycle(route,now=now,dispatch=False)
    keys=['subscription-baseline','subscription-cursor']+[
        row[0] for row in owner.store._db.execute("SELECT id FROM records WHERE id LIKE 'subscription-job:%'")]
    before={key:owner.store._get(key) for key in keys}
    aliases,new=rotation(route,tmp_path,monkeypatch)
    feed=read(registry[0].path,b'n'*32,**owner.notifications.cursor(),now=now)
    owner.notifications.ingest(unseal(seal(feed,'notifications',b'n'*32,aliases),'notifications',aliases),now=now)
    assert {key:owner.store._get(key) for key in keys} == before
    owner.notifications.dispatch(now=now)
    job=owner.notifications.jobs()[0]
    ident=job['message_id'];assert ident is not None
    original=owner.store._get('support-request:'+job['request_id'])
    with pytest.raises(SupportError,match='request_conflict'):
        owner.enqueue(job['pseudonym'],original['request']['address'],job['request_id'],
            original['request']['source'],job['text'],expires_at=job['expires_at']+1)
    assert owner.store._get('subscription-baseline') == before['subscription-baseline']


def test_preexisting_canonical_history_remains_excluded(route,tmp_path,monkeypatch):
    registry,_,owner,_,_=route;now=int(time.time())
    pay(registry,now=now);cycle(route,now=now)
    baseline=owner.store._get('subscription-baseline');cursor=owner.notifications.cursor()
    assert baseline['excluded_events']>0 and not owner.notifications.jobs()
    aliases,new=rotation(route,tmp_path,monkeypatch)
    feed=read(registry[0].path,b'n'*32,**cursor,now=now)
    owner.notifications.ingest(unseal(seal(feed,'notifications',b'n'*32,aliases),'notifications',aliases),now=now)
    owner.notifications.dispatch(now=now)
    assert owner.store._get('subscription-baseline')==baseline and owner.notifications.cursor()==cursor
    assert not owner.notifications.jobs() and not owner.store.visible_messages()
