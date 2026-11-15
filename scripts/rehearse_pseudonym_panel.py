"""Verify generation reimport on an isolated restored panel, without historical edits."""
import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import socket
import sys

from control.friends.pseudonyms import load, references, require, seal, unseal, digest
from scripts.prepare_pseudonym_migration import private_bytes


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--aliases',required=True,type=Path)
    parser.add_argument('--new-key',required=True,type=Path)
    args=parser.parse_args()
    require({name for number,name in socket.if_nameindex()} <= {'lo'})
    os.environ.setdefault('DJANGO_SETTINGS_MODULE','fc_control_plane.settings')
    import django
    django.setup()
    from django.conf import settings
    from django.contrib.auth import get_user_model
    from django.db import transaction, DatabaseError
    from django.test import RequestFactory
    from django.urls import resolve
    from apps.console.models import SubscriptionSnapshot,SubscriptionEventObservation,InventoryDevice,InventorySnapshot,AuditRecord,DeviceLabel
    from apps.console.subscriptions import ingest
    aliases=load(args.aliases);key=private_bytes(args.new_key,32)
    saved=SubscriptionSnapshot.objects.filter(status='ok').order_by('-pk').first()
    require(saved is not None)
    before=dict(snapshots=SubscriptionSnapshot.objects.count(),events=SubscriptionEventObservation.objects.count(),
                inventory=InventoryDevice.objects.count(),audit=AuditRecord.objects.count(),labels=DeviceLabel.objects.count())
    original=dict(schema=2 if saved.history is not None else 1,scope='production',source='gateway-ru',
                  observed_at=int(saved.observed_at.timestamp()),status=saved.status,runtime_sha256=saved.runtime_sha256,
                  devices=saved.devices)
    if saved.history is not None:original['history']=saved.history
    require(digest(original)==saved.digest)
    new=deepcopy(original)
    for row,field,domain in references(new,'subscriptions'):
        row[field]=aliases.index[domain][row[field]]['aliases'][str(aliases.generation)]
    envelope=seal(new,'subscriptions',key,aliases)
    blocked=False
    try:
        unseal(envelope,'subscriptions')
    except ValueError:
        blocked=True
    require(blocked)
    require(ingest(unseal(envelope,'subscriptions',aliases)).pk==saved.pk)
    after=dict(snapshots=SubscriptionSnapshot.objects.count(),events=SubscriptionEventObservation.objects.count(),
               inventory=InventoryDevice.objects.count(),audit=AuditRecord.objects.count(),labels=DeviceLabel.objects.count())
    require(before==after)
    protected=False
    try:
        with transaction.atomic():
            InventorySnapshot.objects.filter(pk=InventorySnapshot.objects.first().pk).update(digest='f'*64)
    except DatabaseError:
        protected=True
    require(protected)
    settings.STORAGES={'default':{'BACKEND':'django.core.files.storage.FileSystemStorage'},
                      'staticfiles':{'BACKEND':'django.contrib.staticfiles.storage.StaticFilesStorage'}}
    recipient=original['devices'][0]['pseudonym']
    request=RequestFactory().get('/inventory/'+recipient+'/')
    request.user=get_user_model().objects.filter(is_superuser=True).first()
    require(request.user is not None)
    request.session={}
    match=resolve(request.path)
    response=match.func(request,**match.kwargs)
    require(response.status_code==200)
    print(json.dumps(dict(reimport_same_snapshot=True,event_duplicates=0,partial_activation_refused=blocked,counts_preserved=before,
                          immutable_trigger_enforced=protected,card_render_status=response.status_code)))


if __name__=='__main__':
    try:
        main()
    except Exception:
        sys.exit('Isolated panel rehearsal failed; private inputs withheld.')
