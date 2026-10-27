from collections import Counter
from datetime import timedelta
from functools import wraps
import json

from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from . import backend, workflow
from .labels import error_label
from .forms import ConfirmForm, LookupForm, OperationForm, PaymentForm
from .models import AuditRecord, CohortMetadata, DeviceProjection, Incident, OperationRequest, PaymentRecord, ReleaseMetadata


def staff(permission):
    def decorate(view):
        @wraps(view)
        def protected(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.path)
            workflow.authorize(request.user, permission)
            return view(request, *args, **kwargs)
        return protected
    return decorate


def analytics_data():
    now = timezone.now()
    devices = list(DeviceProjection.objects.all())
    states = Counter(item.readback['status'].get('effective_state', 'non-cohort') for item in devices)
    versions = Counter(str(item.readback['version_observation']['version_code']) for item in devices)
    since = now.date() - timedelta(days=6)
    rows = OperationRequest.objects.filter(created_at__date__gte=since).annotate(day=TruncDate('created_at')).values('day', 'status').annotate(count=Count('id'))
    daily = {(row['day'], row['status']): row['count'] for row in rows}
    series = []
    for offset in range(7):
        day = since + timedelta(days=offset)
        series.append(dict(day=day.isoformat(), applied=daily.get((day, 'APPLIED'), 0),
            other=sum(count for (row_day, status), count in daily.items() if row_day == day and status != 'APPLIED')))
    return dict(scope='synthetic-only; read-only projections, not current entitlement', observed_at=now.isoformat(),
        devices=len(devices), stale=sum(item.observed_at < now - timedelta(seconds=60) for item in devices),
        states=dict(states), versions=dict(versions), daily=series,
        confirmed_payments=PaymentRecord.objects.filter(confirmed_at__isnull=False,
            purpose=PaymentRecord.Purpose.CUSTOMER_PAYMENT).count(),
        confirmed_internal_canary_records=PaymentRecord.objects.filter(confirmed_at__isnull=False,
            purpose=PaymentRecord.Purpose.INTERNAL_CANARY).count(),
        uncertain_operations=OperationRequest.objects.filter(status__in=['RUNNING', 'UNKNOWN']).count(),
        open_incidents=Incident.objects.exclude(status='resolved').count(),
        live_crash_rate=None, live_mesh_success_rate=None)


@staff('view_deviceprojection')
def dashboard(request):
    data = analytics_data()
    maximum = max([row['applied'] + row['other'] for row in data['daily']] + [1])
    chart = [dict(row, applied_width=round(300 * row['applied'] / maximum), other_width=round(300 * row['other'] / maximum)) for row in data['daily']]
    state_chart = [dict(state=state, count=count, width=round(300 * count / max(data['devices'], 1))) for state, count in data['states'].items()]
    return render(request, 'console/dashboard.html', dict(data=data, chart=chart, state_chart=state_chart,
        operations=OperationRequest.objects.select_related('device')[:6], incidents=Incident.objects.select_related('device').exclude(status='resolved')[:6]))


@staff('view_deviceprojection')
def analytics(request):
    return JsonResponse(analytics_data(), json_dumps_params={'allow_nan': False})


@staff('view_deviceprojection')
def devices(request):
    form = LookupForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        try:
            device = backend.lookup(form.cleaned_data['selector'])
            workflow.refresh(device)
            workflow.audit(request.user, 'device.lookup', device)
            return redirect('console:device', device=device)
        except backend.BackendError:
            form.add_error(None, 'Демо-устройство не найдено. Поиск реальных устройств доступен отдельно в инвентаризации.')
    return render(request, 'console/devices.html', dict(form=form, devices=DeviceProjection.objects.all()))


@staff('view_deviceprojection')
def device_detail(request, device):
    record = get_object_or_404(DeviceProjection, pk=device)
    return render(request, 'console/device.html', dict(device=record,
        readback=json.dumps(record.readback, indent=2, sort_keys=True),
        metadata=CohortMetadata.objects.filter(device=record).first(),
        operations=OperationRequest.objects.filter(device=record), payments=PaymentRecord.objects.filter(device=record)))


@require_POST
@staff('view_deviceprojection')
def refresh(request):
    try:
        workflow.refresh_all(request.user)
        messages.success(request, 'Демо-снимки обновлены. Это наблюдения, не текущие решения о доступе.')
    except backend.BackendError:
        messages.error(request, 'Чтение недоступно. Сохранённые снимки исторические, доступ не подтверждён.')
    return redirect('console:devices')


@staff('view_paymentrecord')
def payments(request):
    return render(request, 'console/payments.html', dict(payments=PaymentRecord.objects.select_related('device').order_by('-created_at')))


@staff('add_paymentrecord')
def payment_new(request):
    form = PaymentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        try:
            payment = workflow.create_payment(request.user, **form.cleaned_data)
            return redirect('console:payment', payment_id=payment.pk)
        except (ValidationError, IntegrityError):
            form.add_error(None, 'Основание некорректно или уже записано. Не дублируйте оплату для повтора операции.')
    return render(request, 'console/form.html', dict(form=form, title='Запись демо-оплаты или служебной canary', subtitle='Без эквайринга и данных плательщика. Canary — не выручка. Запись не означает подтверждение или доступ.'))


@staff('view_paymentrecord')
def payment_detail(request, payment_id):
    payment = get_object_or_404(PaymentRecord, pk=payment_id)
    form = ConfirmForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        workflow.confirm_payment(request.user, payment_id)
        return redirect('console:payment', payment_id=payment_id)
    return render(request, 'console/payment.html', dict(payment=payment, form=form))


@staff('view_operationrequest')
def operations(request):
    return render(request, 'console/operations.html', dict(operations=OperationRequest.objects.select_related('device').all()))


@staff('add_operationrequest')
def operation_new(request):
    form = OperationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        values = {key: value for key, value in form.cleaned_data.items() if key != 'attest_exact_apk'}
        try:
            operation = workflow.create_operation(request.user, values)
            return redirect('console:operation', request_id=operation.pk)
        except (workflow.WorkflowError, ValidationError, IntegrityError):
            form.add_error(None, 'Проверьте согласие, передачу APK и соответствующую подтверждённую неиспользованную оплату. Запрос не создан.')
    return render(request, 'console/form.html', dict(form=form, title='Создать запрос операции', subtitle='Неизменяемый запрос → предпросмотр в настоящем backend → явное подтверждение. Отзыв окончателен; меняются только демо-подписки.'))


@staff('view_operationrequest')
def operation_detail(request, request_id):
    operation = get_object_or_404(OperationRequest.objects.select_related('device', 'payment'), pk=request_id)
    token = workflow.confirmation_token(request.user, operation)
    return render(request, 'console/operation.html', dict(operation=operation,
        preview=json.dumps(operation.preview, indent=2, sort_keys=True),
        receipt=json.dumps(operation.receipt, indent=2, sort_keys=True),
        form=ConfirmForm(initial={'token': token}), token=token))


@require_POST
@staff('preview_operation')
def operation_preview(request, request_id):
    get_object_or_404(OperationRequest, pk=request_id)
    try:
        workflow.prepare(request.user, request_id)
    except (workflow.WorkflowError, backend.BackendError) as error:
        messages.error(request, error_label(error))
    return redirect('console:operation', request_id=request_id)


@require_POST
@staff('execute_operation')
def operation_execute(request, request_id):
    get_object_or_404(OperationRequest, pk=request_id)
    form = ConfirmForm(request.POST)
    if form.is_valid():
        try:
            workflow.execute(request.user, request_id, form.cleaned_data['token'])
        except workflow.WorkflowError as error:
            messages.error(request, error_label(error))
    else:
        messages.error(request, 'Необходимо явное подтверждение. Операция не отправлена.')
    return redirect('console:operation', request_id=request_id)


@require_POST
@staff('execute_operation')
def operation_reconcile(request, request_id):
    get_object_or_404(OperationRequest, pk=request_id)
    try:
        workflow.reconcile(request.user, request_id)
    except (workflow.WorkflowError, backend.BackendError) as error:
        messages.error(request, error_label(error))
    return redirect('console:operation', request_id=request_id)


@staff('view_operationrequest')
def receipt(request, request_id):
    operation = get_object_or_404(OperationRequest, pk=request_id)
    return JsonResponse(dict(scope='synthetic-only administrative receipt; not MESH authorization',
        request=str(operation.pk), status=operation.status,
        payment_purpose=operation.payment.purpose if operation.payment_id else None,
        receipt=operation.receipt), json_dumps_params={'allow_nan': False})


@staff('view_auditrecord')
def audit_log(request):
    return render(request, 'console/audit.html', dict(records=AuditRecord.objects.select_related('actor')[:200]))


@staff('view_releasemetadata')
def releases(request):
    return render(request, 'console/releases.html', dict(releases=ReleaseMetadata.objects.all()))


def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        with backend.registry():
            pass
    except Exception:
        return JsonResponse({'status': 'unready', 'scope': 'synthetic'}, status=503)
    return JsonResponse({'status': 'ok', 'scope': 'synthetic'})


def csrf_failure(request, reason=''):
    return render(request, '403.html', status=403)
