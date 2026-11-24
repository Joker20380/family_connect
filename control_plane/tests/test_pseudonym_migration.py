from copy import deepcopy
import pytest
from django.db import DatabaseError,transaction

from control.friends.pseudonyms import prepare,pseudonym,references,seal,unseal
from apps.console import inventory,subscriptions,technical_metadata
from apps.console.models import AuditRecord,DeviceLabel,InventorySnapshot,SubscriptionEventObservation,SubscriptionSnapshot,TechnicalMetadata
from tests.test_observability import snapshot
from tests.test_subscriptions import observation
from tests.test_device_technical_projection import observation as metadata_observation


def test_same_card_events_labels_and_immutable_digests_across_generation(console,client):
    aliases=prepare(dict(device=['a'*32,'b'*32],panel_event=['event-001']),b'n'*32,legacy_key=b'o'*32)
    old=[pseudonym(b'o'*32,'device',value*32) for value in ('a','b')]
    data=snapshot();data['devices'][0]['pseudonym']=old[0]
    first=inventory.ingest(data)
    DeviceLabel.objects.create(pseudonym=old[0],label='isolated retained name')
    subscription=observation()
    for row,value in zip(subscription['devices'],old):row['pseudonym']=value
    subscription['devices'][0]['event']=dict(event_id=pseudonym(b'o'*32,'panel_event','event-001'),event_type='payment',
        occurred_at=subscription['observed_at'],previous_state=None,new_state='active',result='APPLIED')
    previous=subscriptions.ingest(subscription)
    metadata=metadata_observation();metadata['devices'][0]['pseudonym']=old[0]
    technical_metadata.ingest(metadata)
    count=AuditRecord.objects.count()
    for original,channel,ingest in [(data,'inventory',inventory.ingest),(subscription,'subscriptions',subscriptions.ingest),
                                   (metadata,'technical_metadata',technical_metadata.ingest)]:
        new=deepcopy(original)
        for row,field,domain in references(new,channel):
            row[field]=aliases.index[domain][row[field]]['aliases']['2']
        restored=unseal(seal(new,channel,b'n'*32,aliases),channel,aliases)
        assert restored==original
        ingest(restored)
    assert InventorySnapshot.objects.count()==SubscriptionSnapshot.objects.count()==SubscriptionEventObservation.objects.count()==1
    assert TechnicalMetadata.objects.count()==1 and AuditRecord.objects.count()==count
    assert InventorySnapshot.objects.get(pk=first.pk).digest==first.digest
    assert SubscriptionSnapshot.objects.get(pk=previous.pk).digest==previous.digest
    client.force_login(console)
    page=client.get('/inventory/'+old[0]+'/')
    assert page.status_code==200 and b'isolated retained name' in page.content
    with pytest.raises(DatabaseError),transaction.atomic():
        InventorySnapshot.objects.filter(pk=first.pk).update(digest='f'*64)
