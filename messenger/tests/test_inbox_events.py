import os
import time
import pytest
from messenger.local import LocalChat, LocalError, contact_card
from messenger.store import Store
from messenger.service_events import validate_feed
from scripts.service_notices import Notices
import RNS


def event(**changes):
    now=int(time.time())
    return dict(dict(id='ab'*16,kind='information',title='Новости',body='Обновление готовится',author='Администратор',created=now,expires=now+1000,platforms=['android']),**changes)


def test_unread_notification_flags_persist_and_migrate_old_history(tmp_path):
    key=os.urandom(32)
    with_store=Store(tmp_path/'chat',key,create=True)
    old=dict(id='old',peer='ab'*16,text='old',timestamp=1)
    with_store.add(old,b'x'*100,outgoing=False)
    assert with_store.inbox()[0]['read']
    new=dict(old,id='new',text='new')
    assert with_store.add(new,b'y'*100,outgoing=False)
    assert not with_store.inbox()[1]['read']
    with_store.inbox_mark(['new'],'notified')
    assert with_store.inbox()[1]['notified'] and not with_store.inbox()[1]['read']
    with_store.close()
    reopened=Store(tmp_path/'chat',key,create=False)
    assert reopened.inbox()[1]['notified']
    reopened.inbox_mark(['new'],'read')
    assert all(m['read'] for m in reopened.inbox())
    assert not reopened.add(new,b'y'*100,outgoing=False)
    reopened.close()


def test_event_dedupe_read_persistence_and_changed_id_rejected(tmp_path):
    store=Store(tmp_path/'chat',os.urandom(32),create=True)
    item=event();store.service_events([item]);store.service_mark([item['id']],'read')
    assert store.service_events([item])[0]['read']
    with pytest.raises(ValueError,match='Changed'):store.service_events([event(body='changed')])
    assert store.service_events()[0]['body']==item['body']
    store.close()


@pytest.mark.parametrize('changes',[{'id':'bad'},{'kind':'execute'},{'body':''},{'platforms':['android','android']},{'expires':1},{'title':'x'*161}])
def test_invalid_notice_rejected(changes):
    with pytest.raises(ValueError):validate_feed(dict(version=1,events=[event(**changes)]))


def test_notice_platform_expiry_and_duplicates():
    assert validate_feed(dict(version=1,events=[event()]),platform='windows')==[]
    assert validate_feed(dict(version=1,events=[event(created=1,expires=2)]))==[]
    with pytest.raises(ValueError):validate_feed(dict(version=1,events=[event(),event()]))


def test_admin_grant_publish_revoke_and_export(tmp_path):
    registry=Notices(tmp_path/'registry.sqlite');secret=tmp_path/'admin.token'
    registry.grant('Owner',secret)
    assert secret.stat().st_mode&0o777==0o600
    kwargs=dict(kind='server_change',title='Плановые работы',body='Завтра',platforms=['android'])
    with pytest.raises(ValueError,match='denied'):registry.publish('wrong',**kwargs)
    ident=registry.publish(secret.read_text(),**kwargs)
    assert registry.feed()['events'][0]['author']=='Owner'
    assert registry.feed()['events'][0]['id']==ident
    registry.revoke('Owner')
    with pytest.raises(ValueError,match='denied'):registry.publish(secret.read_text(),**kwargs)
    registry.export(tmp_path/'feed.json')
    assert secret.read_text() not in (tmp_path/'feed.json').read_text()
    registry.db.close()


def test_contact_alias_saved_encrypted_and_identity_unchanged(tmp_path,chat_runtime):
    key=os.urandom(32);local=LocalChat(tmp_path/'chat',key,create=True)
    card=contact_card(RNS.Identity().get_public_key().hex())
    local.trust_contact(card['public'],card['fingerprint'])
    renamed=local.rename_contact(card['address'],'  Мама  ')
    assert renamed==dict(card,name='Мама')
    with pytest.raises(LocalError):local.rename_contact(card['address'],'bad\nname')
    local.close();local=LocalChat(tmp_path/'chat',key,create=False)
    assert local.contacts()==[renamed]
    assert 'Мама'.encode() not in (tmp_path/'chat'/'history.sqlite').read_bytes()
    assert local.rename_contact(card['address'],'')==card
    local.close()


def test_http_publisher_denies_revoked_and_retries_without_duplicate(tmp_path):
    from control.friends.notices import publish, NoticeDenied
    path=tmp_path/'registry.sqlite';registry=Notices(path);token=tmp_path/'owner.token'
    registry.grant('Owner',token)
    request=dict(id='cd'*16,kind='update',title='New version',body='Test only',platforms=['android'],days=1)
    output=tmp_path/'feed.json'
    with pytest.raises(NoticeDenied):publish(path,output,'',request)
    with pytest.raises(NoticeDenied):publish(path,output,'Bearer '+'0'*64,request)
    one=publish(path,output,'Bearer '+token.read_text(),request)
    assert publish(path,output,'Bearer '+token.read_text(),request)==one
    assert len(registry.feed()['events'])==1
    with pytest.raises(ValueError):publish(path,output,'Bearer '+token.read_text(),dict(request,body='Changed'))
    registry.revoke('Owner')
    with pytest.raises(NoticeDenied):publish(path,output,'Bearer '+token.read_text(),dict(request,id='ef'*16))
    assert len(registry.feed()['events'])==1
    registry.db.close()


def test_revision_migration_update_replay_and_notification(tmp_path):
    store=Store(tmp_path/'chat',os.urandom(32),create=True)
    original=event();store.service_events([original]);store.service_mark([original['id']],'read')
    first=dict(original,revision=1,updated=original['created'],editor=original['author'])
    store.service_events(validate_feed(dict(version=2,events=[first])))
    assert store.service_events()[0]['read']
    edited=dict(first,revision=2,body='Исправлено')
    result=store.service_events(validate_feed(dict(version=2,events=[edited])))
    assert len(result)==1 and not result[0]['read'] and not result[0]['notified']
    store.service_mark([original['id']],'read')
    assert store.service_events([edited])[0]['read']
    assert store.service_events([first])[0]['body']=='Исправлено'
    with pytest.raises(ValueError):store.service_events([dict(edited,body='Тихая подмена')])
    with pytest.raises(ValueError):store.service_events([dict(edited,revision=3,author='Другой')])
    store.close()
