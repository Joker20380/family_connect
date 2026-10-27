import uuid

from django.conf import settings
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from .labels import LABELS, label
from .observability_models import InventorySnapshot, InventoryDevice, ServerObservation, TechnicalSample, OperationSwitch


class DeviceProjection(models.Model):
    device = models.CharField(verbose_name=LABELS.get('device', 'device'), primary_key=True, max_length=32, validators=[RegexValidator(r'^[0-9a-f]{32}$')])
    label = models.CharField(verbose_name=LABELS.get('label', 'label'), max_length=40)
    observed_at = models.DateTimeField(verbose_name=LABELS.get('observed_at', 'observed_at'))
    readback = models.JSONField(verbose_name=LABELS.get('readback', 'readback'))

    class Meta:
        ordering = ['label']
        verbose_name = 'снимок демо-устройства'
        verbose_name_plural = 'снимки демо-устройств'

    def __str__(self):
        return self.label


class CohortMetadata(models.Model):
    device = models.OneToOneField(DeviceProjection, verbose_name='Устройство', on_delete=models.PROTECT)
    opted_in = models.BooleanField(verbose_name=LABELS.get('opted_in', 'opted_in'), default=False)
    handoff_verified = models.BooleanField(verbose_name=LABELS.get('handoff_verified', 'handoff_verified'), default=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=LABELS.get('owner', 'owner'), on_delete=models.PROTECT)
    updated_at = models.DateTimeField(verbose_name=LABELS.get('updated_at', 'updated_at'), auto_now=True)

    def __str__(self):
        return str(self.device)

    class Meta:
        verbose_name = 'метаданные группы'
        verbose_name_plural = 'метаданные группы'


class PaymentRecord(models.Model):
    id = models.UUIDField(verbose_name=LABELS.get('id', 'id'), primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(DeviceProjection, verbose_name=LABELS.get('device', 'device'), on_delete=models.PROTECT)
    amount_minor = models.PositiveIntegerField(verbose_name=LABELS.get('amount_minor', 'amount_minor'), validators=[MinValueValidator(1)])
    currency = models.CharField(verbose_name=LABELS.get('currency', 'currency'), max_length=3, choices=[('EUR', 'EUR'), ('USD', 'USD')])
    reference_hash = models.CharField(verbose_name=LABELS.get('reference_hash', 'reference_hash'), max_length=64, unique=True, validators=[RegexValidator(r'^[0-9a-f]{64}$')])
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=LABELS.get('created_by', 'created_by'), on_delete=models.PROTECT, related_name='+')
    created_at = models.DateTimeField(verbose_name=LABELS.get('created_at', 'created_at'), auto_now_add=True)
    confirmed_by = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=LABELS.get('confirmed_by', 'confirmed_by'), on_delete=models.PROTECT, null=True, blank=True, related_name='+')
    confirmed_at = models.DateTimeField(verbose_name=LABELS.get('confirmed_at', 'confirmed_at'), null=True, blank=True)

    class Meta:
        verbose_name = 'запись оплаты'
        verbose_name_plural = 'записи оплат'
        permissions = [('confirm_payment', 'Подтверждать ручную демо-оплату')]
        constraints = [models.CheckConstraint(condition=models.Q(amount_minor__gt=0), name='positive_payment_amount'),
                       models.CheckConstraint(condition=(models.Q(confirmed_at__isnull=True, confirmed_by__isnull=True) |
                           models.Q(confirmed_at__isnull=False, confirmed_by__isnull=False)), name='complete_payment_confirmation')]

    def __str__(self):
        return f'{self.id} · {self.currency} {self.amount_minor} мин. единиц'


class OperationRequest(models.Model):
    ACTIONS = [('activate', 'Активировать / продлить'), ('grace', 'Выдать льготный период'), ('expire', 'Завершить срок'), ('revoke', 'Отозвать навсегда')]
    STATUSES = [(value, label(value)) for value in ('DRAFT', 'PREVIEWED', 'RUNNING', 'APPLIED', 'REJECTED', 'STALE', 'UNKNOWN')]
    id = models.UUIDField(verbose_name=LABELS.get('id', 'id'), primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(DeviceProjection, verbose_name=LABELS.get('device', 'device'), on_delete=models.PROTECT)
    action = models.CharField(verbose_name=LABELS.get('action', 'action'), max_length=12, choices=ACTIONS)
    payment = models.OneToOneField(PaymentRecord, verbose_name='Оплата', on_delete=models.PROTECT, null=True, blank=True)
    period_start = models.DateTimeField(verbose_name=LABELS.get('period_start', 'period_start'), null=True, blank=True)
    paid_until = models.DateTimeField(verbose_name=LABELS.get('paid_until', 'paid_until'), null=True, blank=True)
    grace_until = models.DateTimeField(verbose_name=LABELS.get('grace_until', 'grace_until'), null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=LABELS.get('created_by', 'created_by'), on_delete=models.PROTECT, related_name='+')
    created_at = models.DateTimeField(verbose_name=LABELS.get('created_at', 'created_at'), auto_now_add=True)
    status = models.CharField(verbose_name=LABELS.get('status', 'status'), max_length=12, choices=STATUSES, default='DRAFT')
    preview = models.JSONField(verbose_name=LABELS.get('preview', 'preview'), default=dict, blank=True)
    previewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=LABELS.get('previewed_by', 'previewed_by'), on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    previewed_at = models.DateTimeField(verbose_name=LABELS.get('previewed_at', 'previewed_at'), null=True, blank=True)
    receipt = models.JSONField(verbose_name=LABELS.get('receipt', 'receipt'), default=dict, blank=True)
    failure_code = models.CharField(verbose_name=LABELS.get('failure_code', 'failure_code'), max_length=64, blank=True)
    completed_at = models.DateTimeField(verbose_name=LABELS.get('completed_at', 'completed_at'), null=True, blank=True)

    class Meta:
        verbose_name = 'запрос операции'
        verbose_name_plural = 'запросы операций'
        ordering = ['-created_at']
        permissions = [('preview_operation', 'Предпросмотр в настоящем демо-backend'),
                       ('execute_operation', 'Выполнять или сверять демо-операцию')]
        constraints = [models.CheckConstraint(condition=(models.Q(action='activate', payment__isnull=False,
            period_start__isnull=False, paid_until__isnull=False, grace_until__isnull=True) |
            models.Q(action='grace', payment__isnull=True, period_start__isnull=True, paid_until__isnull=True, grace_until__isnull=False) |
            models.Q(action__in=['expire', 'revoke'], payment__isnull=True, period_start__isnull=True,
                     paid_until__isnull=True, grace_until__isnull=True)), name='operation_input_shape')]

    @property
    def event_id(self):
        return 'cp0-' + self.id.hex

    def __str__(self):
        return f'{self.get_action_display()} · {self.device} · {self.get_status_display()}'


class Incident(models.Model):
    device = models.ForeignKey(DeviceProjection, verbose_name=LABELS.get('device', 'device'), on_delete=models.PROTECT)
    category = models.CharField(verbose_name=LABELS.get('category', 'category'), max_length=20, choices=[(value, label(value)) for value in
        ('activation', 'mesh_connect', 'crash', 'payment', 'version', 'support')])
    severity = models.CharField(verbose_name=LABELS.get('severity', 'severity'), max_length=8, choices=[(value, label(value)) for value in ('low', 'high', 'critical')])
    status = models.CharField(verbose_name=LABELS.get('status', 'status'), max_length=10, choices=[(value, label(value)) for value in ('open', 'triage', 'resolved')], default='open')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=LABELS.get('owner', 'owner'), on_delete=models.PROTECT)
    created_at = models.DateTimeField(verbose_name=LABELS.get('created_at', 'created_at'), auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name=LABELS.get('updated_at', 'updated_at'), auto_now=True)

    def __str__(self):
        return f'{self.get_category_display()} · {self.device} · {self.get_status_display()}'

    class Meta:
        verbose_name = 'обращение'
        verbose_name_plural = 'обращения'


class AuditRecord(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=LABELS.get('actor', 'actor'), on_delete=models.PROTECT, null=True)
    action = models.CharField(verbose_name=LABELS.get('action', 'action'), max_length=40)
    target = models.CharField(verbose_name=LABELS.get('target', 'target'), max_length=64)
    occurred_at = models.DateTimeField(verbose_name=LABELS.get('occurred_at', 'occurred_at'), auto_now_add=True)
    details = models.JSONField(verbose_name=LABELS.get('details', 'details'), default=dict)

    class Meta:
        verbose_name = 'событие аудита'
        verbose_name_plural = 'события аудита'
        ordering = ['-occurred_at']


class ReleaseMetadata(models.Model):
    version_name = models.CharField(verbose_name=LABELS.get('version_name', 'version_name'), max_length=64, unique=True)
    version_code = models.PositiveIntegerField(verbose_name=LABELS.get('version_code', 'version_code'))
    package_id = models.CharField(verbose_name=LABELS.get('package_id', 'package_id'), max_length=100)
    size = models.PositiveBigIntegerField(verbose_name=LABELS.get('size', 'size'))
    sha256 = models.CharField(verbose_name=LABELS.get('sha256', 'sha256'), max_length=64)
    signer_sha256 = models.CharField(verbose_name=LABELS.get('signer_sha256', 'signer_sha256'), max_length=64)
    channel = models.CharField(verbose_name=LABELS.get('channel', 'channel'), max_length=40)

    def __str__(self):
        return self.version_name

    class Meta:
        verbose_name = 'метаданные релиза'
        verbose_name_plural = 'метаданные релизов'
