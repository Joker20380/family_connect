import hashlib

from django.core import signing
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone

from . import backend
from .models import AuditRecord, CohortMetadata, DeviceProjection, OperationRequest, PaymentRecord


class WorkflowError(Exception):
    pass


def authorize(actor, permission):
    if not actor.is_active or not actor.is_staff or not actor.has_perm('console.' + permission):
        raise PermissionDenied


def audit(actor, action, target, **details):
    allowed = {'status', 'code', 'operation', 'payment', 'synthetic', 'category', 'severity', 'apk_attested'}
    if not set(details) <= allowed:
        raise ValueError('Unsupported audit field')
    return AuditRecord.objects.create(actor=actor, action=action, target=str(target), details=dict(details, synthetic=True))


def refresh(device):
    readback = backend.readback(device)
    label = next(member['label'] for member in backend.members() if member['device'] == device)
    return DeviceProjection.objects.update_or_create(device=device, defaults={
        'label': label, 'readback': readback, 'observed_at': timezone.now(),
    })[0]


def refresh_all(actor):
    authorize(actor, 'view_deviceprojection')
    for member in backend.members():
        refresh(member['device'])
    audit(actor, 'projection.refresh', 'synthetic-registry')


@transaction.atomic
def create_payment(actor, *, device, amount_minor, currency, reference):
    authorize(actor, 'add_paymentrecord')
    payment = PaymentRecord(device=device, amount_minor=amount_minor, currency=currency,
        reference_hash=hashlib.sha256(reference.encode()).hexdigest(), created_by=actor)
    payment.full_clean()
    payment.save()
    audit(actor, 'payment.create', payment.pk)
    return payment


@transaction.atomic
def confirm_payment(actor, payment_id):
    authorize(actor, 'confirm_payment')
    payment = PaymentRecord.objects.select_for_update().get(pk=payment_id)
    if payment.confirmed_at is None:
        payment.confirmed_at = timezone.now()
        payment.confirmed_by = actor
        payment.save(update_fields=['confirmed_at', 'confirmed_by'])
        audit(actor, 'payment.confirm', payment.pk)
    return payment


def metadata_gate(request):
    if request.action in ('activate', 'grace'):
        metadata = CohortMetadata.objects.filter(device=request.device, opted_in=True, handoff_verified=True).first()
        if metadata is None:
            raise WorkflowError('OPT_IN_AND_HANDOFF_REQUIRED')
    if request.action == 'activate':
        payment = PaymentRecord.objects.get(pk=request.payment_id)
        if payment.confirmed_at is None or payment.device_id != request.device_id:
            raise WorkflowError('CONFIRMED_MATCHING_PAYMENT_REQUIRED')


@transaction.atomic
def create_operation(actor, values):
    authorize(actor, 'add_operationrequest')
    request = OperationRequest(created_by=actor, **values)
    request.full_clean()
    metadata_gate(request)
    request.save()
    audit(actor, 'operation.create', request.pk, apk_attested=request.action == 'activate')
    return request


def intent(request):
    return dict(device=request.device_id, event_id=request.event_id, action=request.action,
        period_start=int(request.period_start.timestamp()) if request.period_start else None,
        paid_until=int(request.paid_until.timestamp()) if request.paid_until else None,
        grace_until=int(request.grace_until.timestamp()) if request.grace_until else None,
        reference='cp0:' + str(request.payment_id or request.id))


@transaction.atomic
def prepare(actor, request_id):
    authorize(actor, 'preview_operation')
    request = OperationRequest.objects.select_for_update().get(pk=request_id)
    if request.status not in ('DRAFT', 'PREVIEWED', 'STALE', 'REJECTED'):
        raise WorkflowError('RECONCILE_OR_READ_RECEIPT')
    metadata_gate(request)
    try:
        request.preview = backend.preview(intent(request))
        request.status, request.failure_code = 'PREVIEWED', ''
        request.previewed_by, request.previewed_at = actor, timezone.now()
    except backend.BackendError as error:
        request.status, request.failure_code, request.preview = 'REJECTED', str(error), {}
    request.save(update_fields=['preview', 'status', 'failure_code', 'previewed_by', 'previewed_at'])
    audit(actor, 'operation.preview', request.pk, status=request.status, code=request.failure_code)
    return request


def confirmation_token(actor, request):
    if request.status != 'PREVIEWED' or request.previewed_by_id != actor.pk:
        return ''
    return signing.dumps({'request': str(request.pk), 'actor': actor.pk, 'preview': backend.digest(request.preview)}, salt='cp0-operation')


def execute(actor, request_id, token):
    authorize(actor, 'execute_operation')
    with transaction.atomic():
        request = OperationRequest.objects.select_for_update().get(pk=request_id)
        if request.status == 'APPLIED':
            return request
        if request.status != 'PREVIEWED' or request.previewed_by_id != actor.pk:
            raise WorkflowError('PREVIEW_REQUIRED_OR_RECONCILE')
        try:
            signed = signing.loads(token, salt='cp0-operation', max_age=300)
        except signing.BadSignature:
            raise WorkflowError('INVALID_OR_EXPIRED_CONFIRMATION') from None
        if signed != {'request': str(request.pk), 'actor': actor.pk, 'preview': backend.digest(request.preview)}:
            raise WorkflowError('CONFIRMATION_MISMATCH')
        metadata_gate(request)
        request.status = 'RUNNING'
        request.save(update_fields=['status'])
        audit(actor, 'operation.dispatch', request.pk)
    try:
        receipt = backend.execute(intent(request), request.preview)
        status, code = 'APPLIED', ''
    except backend.BackendError as error:
        receipt, code = {}, str(error)
        status = 'STALE' if code == 'PREVIEW_STALE' else 'REJECTED'
        if code == 'SYNTHETIC_BACKEND_UNAVAILABLE':
            status = 'UNKNOWN'
    except Exception:
        receipt, status, code = {}, 'UNKNOWN', 'READBACK_REQUIRED'
    return complete(actor, request.pk, receipt, status, code)


@transaction.atomic
def complete(actor, request_id, receipt, status, code):
    request = OperationRequest.objects.select_for_update().get(pk=request_id)
    if request.status == 'APPLIED':
        return request
    request.receipt, request.status, request.failure_code = receipt, status, code
    request.completed_at = timezone.now()
    request.save(update_fields=['receipt', 'status', 'failure_code', 'completed_at'])
    audit(actor, 'operation.result', request.pk, status=status, code=code)
    return request


def reconcile(actor, request_id):
    authorize(actor, 'execute_operation')
    request = OperationRequest.objects.get(pk=request_id)
    if request.status == 'APPLIED':
        return request
    if request.status not in ('RUNNING', 'UNKNOWN'):
        raise WorkflowError('NO_UNCERTAIN_OPERATION')
    receipt = backend.reconcile(request.event_id, request.preview['receipt']['event']['payload_hash'])
    if receipt is None:
        audit(actor, 'operation.readback_absent', request.pk)
        raise WorkflowError('NO_RECEIPT_KEEP_UNCERTAIN_NO_NEW_EVENT')
    return complete(actor, request.pk, receipt, 'APPLIED', '')
