from datetime import timedelta
import base64
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import DatabaseError, transaction
from django.utils import timezone
import pytest

from apps.fleet.models import GatewayArtifact, LogicalGateway, GatewayInstance, DeploymentOperation, EnrollmentToken, InstanceHealthCheck
from apps.fleet.workflow import create_intent, record_completion, accept_enrollment
from apps.console.observability_models import InventorySnapshot, ServerObservation
from fleet.health import required
from fleet.contracts import canonical


@pytest.fixture
def fleet_node(db):
    artifact=GatewayArtifact.objects.create(bundle_id='test-v1',source_commit='a'*40,manifest_sha256='b'*64,
        archive_sha256='c'*64,signature='A'*86+'==',signature_verified=True,supported_os=['ubuntu-24.04'],architectures=['x86_64'],roles=['awg'])
    gateway=LogicalGateway.objects.create(id='nl',country='NL',transports=['awg'])
    return GatewayInstance.objects.create(instance_id='nl-test-001',logical_gateway=gateway,provider='synthetic',region='test',
        ipv4='192.0.2.10',desired_bundle=artifact,roles=['awg'])


@pytest.fixture
def fleet_operator(db):
    return get_user_model().objects.create_superuser('fleet-synthetic-operator',password='synthetic-test-only')


def receipt(intent,state):
    return dict(operation_id=str(intent.pk),request=dict(instance=intent.instance_id,target=intent.target_bundle_id,action=intent.action),
        state='SUCCEEDED',first_failure=None,scope='synthetic',previous_bundle=intent.previous_bundle_id,result=dict(state=state))


def test_create_intent_without_execution(fleet_node,fleet_operator):
    intent=create_intent(fleet_operator,fleet_node.pk,'preflight')
    fleet_node.refresh_from_db()
    assert intent.state=='INTENT' and intent.requested_by==fleet_operator and fleet_node.state=='DISCOVERED'
    assert intent.safe_receipt['scope']=='synthetic'


def test_readonly_console_and_intent(client,fleet_node,fleet_operator,settings):
    settings.STORAGES = {'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
                        'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'}}
    client.force_login(fleet_operator)
    response=client.get('/fleet/',HTTP_HOST='localhost')
    assert response.status_code==200 and 'Серверы'.encode() in response.content
    assert client.post('/fleet/',dict(instance=fleet_node.pk,action='preflight'),HTTP_HOST='localhost').status_code==302
    assert DeploymentOperation.objects.count()==1
    for model,identifier in [('gatewayinstance',fleet_node.pk),('gatewayartifact','test-v1')]:
        assert client.post('/admin/fleet_console/'+model+'/'+identifier+'/change/',{},HTTP_HOST='localhost').status_code==403


def test_no_permission_or_direct_activation(fleet_node,fleet_operator):
    actor=get_user_model().objects.create_user('fleet-readonly')
    with pytest.raises(PermissionDenied):create_intent(actor,fleet_node.pk,'plan')
    with pytest.raises(ValidationError):create_intent(fleet_operator,fleet_node.pk,'activate')
    fleet_node.state='ACTIVE'
    with pytest.raises(ValidationError):fleet_node.save()


def test_immutable_intent_model_and_database(fleet_node,fleet_operator):
    intent=create_intent(fleet_operator,fleet_node.pk,'plan')
    with pytest.raises(ValidationError):intent.save()
    with pytest.raises(ValidationError):intent.delete()
    with pytest.raises(DatabaseError), transaction.atomic():
        DeploymentOperation.objects.filter(pk=intent.pk).update(state='FAILED')
    with pytest.raises(DatabaseError), transaction.atomic():
        DeploymentOperation.objects.filter(pk=intent.pk).delete()


def test_completion_sequence_and_idempotency(fleet_node,fleet_operator):
    for action,state in [('preflight','PREFLIGHTED'),('stage','STAGED')]:
        intent=create_intent(fleet_operator,fleet_node.pk,action)
        completed=record_completion(fleet_operator,intent.pk,receipt(intent,state))
        assert record_completion(fleet_operator,intent.pk,receipt(intent,state)).pk==completed.pk
        fleet_node.refresh_from_db();assert fleet_node.state==state
    with pytest.raises(ValidationError):create_intent(fleet_operator,fleet_node.pk,'activate')
    intent=create_intent(fleet_operator,fleet_node.pk,'verify')
    report=dict(schema=1,scope='synthetic',instance_id=fleet_node.pk,bundle_id='test-v1',observed_at=int(timezone.now().timestamp()),checks={name:True for name in required(['awg'])})
    record_completion(fleet_operator,intent.pk,receipt(intent,'VERIFIED'),report)
    fleet_node.refresh_from_db();assert fleet_node.state=='VERIFIED' and fleet_node.health_state=='PASS'
    authority=Ed25519PrivateKey.generate()
    body=dict(schema=1,scope='synthetic',binding=dict(instance_id=fleet_node.pk,logical_gateway='nl',bundle_id='test-v1',provider='synthetic',region='test',ipv4='192.0.2.10',roles=['awg']),
        public_key='d'*64,enrolled_at=int(timezone.now().timestamp()),transport_issuance=False)
    signed=dict(body=body,signature=base64.b64encode(authority.sign(canonical(body))).decode())
    accept_enrollment(fleet_operator,fleet_node.pk,signed,authority.public_key())
    intent=create_intent(fleet_operator,fleet_node.pk,'activate')
    record_completion(fleet_operator,intent.pk,receipt(intent,'ACTIVE'))
    fleet_node.refresh_from_db();fleet_node.logical_gateway.refresh_from_db()
    assert fleet_node.actual_bundle_id=='test-v1' and fleet_node.logical_gateway.active_instance_id==fleet_node.pk


def test_completion_wrong_binding(fleet_node,fleet_operator):
    intent=create_intent(fleet_operator,fleet_node.pk,'preflight')
    evidence=receipt(intent,'PREFLIGHTED');evidence['request']['instance']='different'
    with pytest.raises(ValidationError):record_completion(fleet_operator,intent.pk,evidence)
    assert DeploymentOperation.objects.count()==1


def test_observability_link_retains_snapshot(fleet_node):
    snapshot=InventorySnapshot.objects.create(scope='production',source='gateway-nl',observed_at=timezone.now(),digest='e'*64,registry_status='not_collected')
    observation=ServerObservation.objects.create(snapshot=snapshot,load_1m=0.1,memory_used_percent=20,disk_used_percent=30,uptime_seconds=500,services={})
    link=InstanceHealthCheck.objects.create(instance=fleet_node,bundle=fleet_node.desired_bundle,observation=observation,
        scope='production-readonly',ram=20,disk=30)
    assert link.observation_id==observation.pk and ServerObservation.objects.count()==1
    assert InventorySnapshot.objects.count()==1


def test_enrollment_metadata_no_raw_token(fleet_node):
    now=timezone.now()
    binding=dict(instance_id=fleet_node.pk,logical_gateway='nl',bundle_id='test-v1',provider='synthetic',region='test',ipv4='192.0.2.10',roles=['awg'])
    token=EnrollmentToken.objects.create(token_hash='f'*64,instance=fleet_node,binding=binding,created_at=now,expires_at=now+timedelta(seconds=600))
    assert not hasattr(token,'token')
    with pytest.raises(ValidationError):
        EnrollmentToken.objects.create(token_hash='d'*64,instance=fleet_node,binding=binding,created_at=now,expires_at=now+timedelta(seconds=601))


def test_unknown_metrics_and_receipts_rejected(fleet_node,fleet_operator):
    with pytest.raises(ValidationError):InstanceHealthCheck.objects.create(instance=fleet_node,bundle=fleet_node.desired_bundle,scope='synthetic',checks=dict(secret=True))
    with pytest.raises(ValidationError):InstanceHealthCheck.objects.create(instance=fleet_node,bundle=fleet_node.desired_bundle,scope='synthetic',cpu=float('nan'))
    with pytest.raises(ValidationError):DeploymentOperation.objects.create(instance=fleet_node,target_bundle=fleet_node.desired_bundle,requested_by=fleet_operator,action='plan',safe_receipt=dict(token='redacted'))


def test_duplicate_deployment_identity(fleet_node):
    fleet_node.deployment_identity='d'*64;fleet_node.save()
    with pytest.raises(ValidationError):GatewayInstance.objects.create(instance_id='nl-test-002',logical_gateway=fleet_node.logical_gateway,provider='other',region='test',ipv4='192.0.2.11',desired_bundle=fleet_node.desired_bundle,roles=['awg'],deployment_identity='d'*64)
