import uuid

from django.conf import settings
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models


class DeviceProjection(models.Model):
    device = models.CharField(primary_key=True, max_length=32, validators=[RegexValidator(r'^[0-9a-f]{32}$')])
    label = models.CharField(max_length=40)
    observed_at = models.DateTimeField()
    readback = models.JSONField()

    class Meta:
        ordering = ['label']
        verbose_name = 'read-only backend projection'

    def __str__(self):
        return self.label


class CohortMetadata(models.Model):
    device = models.OneToOneField(DeviceProjection, on_delete=models.PROTECT)
    opted_in = models.BooleanField(default=False)
    handoff_verified = models.BooleanField(default=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.device)


class PaymentRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(DeviceProjection, on_delete=models.PROTECT)
    amount_minor = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    currency = models.CharField(max_length=3, choices=[('EUR', 'EUR'), ('USD', 'USD')])
    reference_hash = models.CharField(max_length=64, unique=True, validators=[RegexValidator(r'^[0-9a-f]{64}$')])
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name='+')
    confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        permissions = [('confirm_payment', 'Confirm a synthetic manual payment')]
        constraints = [models.CheckConstraint(condition=models.Q(amount_minor__gt=0), name='positive_payment_amount'),
                       models.CheckConstraint(condition=(models.Q(confirmed_at__isnull=True, confirmed_by__isnull=True) |
                           models.Q(confirmed_at__isnull=False, confirmed_by__isnull=False)), name='complete_payment_confirmation')]

    def __str__(self):
        return f'{self.id} · {self.currency} {self.amount_minor} minor units'


class OperationRequest(models.Model):
    ACTIONS = [('activate', 'Activate / renew'), ('grace', 'Explicit grace'), ('expire', 'Expire now'), ('revoke', 'Revoke permanently')]
    STATUSES = [(value, value) for value in ('DRAFT', 'PREVIEWED', 'RUNNING', 'APPLIED', 'REJECTED', 'STALE', 'UNKNOWN')]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(DeviceProjection, on_delete=models.PROTECT)
    action = models.CharField(max_length=12, choices=ACTIONS)
    payment = models.OneToOneField(PaymentRecord, on_delete=models.PROTECT, null=True, blank=True)
    period_start = models.DateTimeField(null=True, blank=True)
    paid_until = models.DateTimeField(null=True, blank=True)
    grace_until = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=12, choices=STATUSES, default='DRAFT')
    preview = models.JSONField(default=dict, blank=True)
    previewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    previewed_at = models.DateTimeField(null=True, blank=True)
    receipt = models.JSONField(default=dict, blank=True)
    failure_code = models.CharField(max_length=64, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        permissions = [('preview_operation', 'Preview using the real synthetic backend'),
                       ('execute_operation', 'Execute or reconcile a previewed synthetic operation')]
        constraints = [models.CheckConstraint(condition=(models.Q(action='activate', payment__isnull=False,
            period_start__isnull=False, paid_until__isnull=False, grace_until__isnull=True) |
            models.Q(action='grace', payment__isnull=True, period_start__isnull=True, paid_until__isnull=True, grace_until__isnull=False) |
            models.Q(action__in=['expire', 'revoke'], payment__isnull=True, period_start__isnull=True,
                     paid_until__isnull=True, grace_until__isnull=True)), name='operation_input_shape')]

    @property
    def event_id(self):
        return 'cp0-' + self.id.hex

    def __str__(self):
        return f'{self.action} · {self.device} · {self.status}'


class Incident(models.Model):
    device = models.ForeignKey(DeviceProjection, on_delete=models.PROTECT)
    category = models.CharField(max_length=20, choices=[(value, value) for value in
        ('activation', 'mesh_connect', 'crash', 'payment', 'version', 'support')])
    severity = models.CharField(max_length=8, choices=[(value, value) for value in ('low', 'high', 'critical')])
    status = models.CharField(max_length=10, choices=[(value, value) for value in ('open', 'triage', 'resolved')], default='open')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.category} · {self.device} · {self.status}'


class AuditRecord(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True)
    action = models.CharField(max_length=40)
    target = models.CharField(max_length=64)
    occurred_at = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(default=dict)

    class Meta:
        ordering = ['-occurred_at']


class ReleaseMetadata(models.Model):
    version_name = models.CharField(max_length=64, unique=True)
    version_code = models.PositiveIntegerField()
    package_id = models.CharField(max_length=100)
    size = models.PositiveBigIntegerField()
    sha256 = models.CharField(max_length=64)
    signer_sha256 = models.CharField(max_length=64)
    channel = models.CharField(max_length=40)

    def __str__(self):
        return self.version_name
