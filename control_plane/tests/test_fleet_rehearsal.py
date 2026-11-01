import copy
from unittest.mock import patch

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from django.core.exceptions import ValidationError
from django.db import DatabaseError, transaction

from apps.fleet.models import RehearsalEvidence
from apps.fleet.rehearsal import import_receipt, summary
from fleet.contracts import FleetError, canonical, digest
from fleet.evidence import KINDS, SCOPE, STATES, sign
from fleet.materials import public_hex
from tests.test_fleet_bootstrap import fleet_operator


@pytest.fixture
def evidence():
    key=Ed25519PrivateKey.generate()
    body=dict(schema=1,scope=SCOPE,kind='completion',instance_id='fleet-rehearsal-test',operation_id='operation-one',
        bundle_id='gw-'+'a'*32,previous_bundle=None,actual_bundle='gw-'+'a'*32,state='STAGED',result='PASS',
        provider='synthetic',region='isolated',target_sha256='b'*64,source_receipt_sha256='c'*64,source_commit=None,
        archive_sha256=None,manifest_sha256=None,signature_sha256=None,local_health='NOT_RUN',
        external=dict(awg='NOT_RUN',tcp='NOT_RUN',mesh='NOT_RUN'),duration_ms=12,rollback='NOT_RUN',reboot='NOT_RUN',
        retirement='NOT_RUN',issued_at=1000,signer=digest(bytes.fromhex(public_hex(key.public_key()))))
    return key,body


@pytest.mark.django_db
def test_identical_import_and_changed_receipt(evidence):
    key,body=evidence
    receipt=sign(body,key)
    record,created=import_receipt(receipt,key.public_key())
    assert created
    duplicate,created=import_receipt(receipt,key.public_key())
    assert not created and duplicate.pk==record.pk
    body['duration_ms']=13
    with pytest.raises(ValidationError):
        import_receipt(sign(body,key),key.public_key())
    assert RehearsalEvidence.objects.count()==1


@pytest.mark.django_db
def test_database_triggers(evidence):
    key,body=evidence
    record,created=import_receipt(sign(body,key),key.public_key())
    with pytest.raises(DatabaseError),transaction.atomic():
        RehearsalEvidence.objects.filter(pk=record.pk).update(kind='permit')
    with pytest.raises(DatabaseError),transaction.atomic():
        RehearsalEvidence.objects.filter(pk=record.pk).delete()


@pytest.mark.django_db
@pytest.mark.parametrize('kind',KINDS)
def test_all_import_kinds(evidence,kind):
    key,body=evidence
    body['kind']=kind
    record,created=import_receipt(sign(body,key),key.public_key())
    assert created and record.kind==kind


@pytest.mark.django_db
@pytest.mark.parametrize('state',STATES)
def test_summary_states_no_remote_execution(evidence,state):
    key,body=evidence
    body['state']=state
    import_receipt(sign(body,key),key.public_key())
    with patch('subprocess.run',side_effect=AssertionError('web must not execute')):
        assert summary()[0]['state']==state


@pytest.mark.django_db
@pytest.mark.parametrize('field',['token','private_key','password','packet','client_ip','url'])
def test_raw_private_fields_rejected(evidence,field):
    key,body=evidence
    receipt=sign(body,key)
    receipt['body'][field]='sensitive-value-must-not-be-stored'
    with pytest.raises(FleetError):
        import_receipt(receipt,key.public_key())
    assert RehearsalEvidence.objects.count()==0


def test_web_renders_receipts_without_ssh(client,fleet_operator,evidence,settings):
    settings.STORAGES={'default':{'BACKEND':'django.core.files.storage.FileSystemStorage'},
                       'staticfiles':{'BACKEND':'django.contrib.staticfiles.storage.StaticFilesStorage'}}
    key,body=evidence
    import_receipt(sign(body,key),key.public_key())
    client.force_login(fleet_operator)
    with patch('subprocess.run',side_effect=AssertionError('web must not execute')):
        response=client.get('/fleet/',HTTP_HOST='localhost')
    assert response.status_code==200
    assert b'fleet-rehearsal-test' in response.content
    assert b'NOT_RUN' in response.content
