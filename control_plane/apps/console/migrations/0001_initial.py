import django.core.validators
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DeviceProjection',
            fields=[
                ('device', models.CharField(max_length=32, primary_key=True, serialize=False, validators=[django.core.validators.RegexValidator('^[0-9a-f]{32}$')])),
                ('label', models.CharField(max_length=40)),
                ('observed_at', models.DateTimeField()),
                ('readback', models.JSONField()),
            ],
            options={
                'verbose_name': 'read-only backend projection',
                'ordering': ['label'],
            },
        ),
        migrations.CreateModel(
            name='ReleaseMetadata',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version_name', models.CharField(max_length=64, unique=True)),
                ('version_code', models.PositiveIntegerField()),
                ('package_id', models.CharField(max_length=100)),
                ('size', models.PositiveBigIntegerField()),
                ('sha256', models.CharField(max_length=64)),
                ('signer_sha256', models.CharField(max_length=64)),
                ('channel', models.CharField(max_length=40)),
            ],
        ),
        migrations.CreateModel(
            name='AuditRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(max_length=40)),
                ('target', models.CharField(max_length=64)),
                ('occurred_at', models.DateTimeField(auto_now_add=True)),
                ('details', models.JSONField(default=dict)),
                ('actor', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-occurred_at'],
            },
        ),
        migrations.CreateModel(
            name='CohortMetadata',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('opted_in', models.BooleanField(default=False)),
                ('handoff_verified', models.BooleanField(default=False)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ('device', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, to='console.deviceprojection')),
            ],
        ),
        migrations.CreateModel(
            name='Incident',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(choices=[('activation', 'activation'), ('mesh_connect', 'mesh_connect'), ('crash', 'crash'), ('payment', 'payment'), ('version', 'version'), ('support', 'support')], max_length=20)),
                ('severity', models.CharField(choices=[('low', 'low'), ('high', 'high'), ('critical', 'critical')], max_length=8)),
                ('status', models.CharField(choices=[('open', 'open'), ('triage', 'triage'), ('resolved', 'resolved')], default='open', max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('device', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='console.deviceprojection')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='PaymentRecord',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('amount_minor', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ('currency', models.CharField(choices=[('EUR', 'EUR'), ('USD', 'USD')], max_length=3)),
                ('reference_hash', models.CharField(max_length=64, validators=[django.core.validators.RegexValidator('^[0-9a-f]{64}$')])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('confirmed_at', models.DateTimeField(blank=True, null=True)),
                ('confirmed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('device', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='console.deviceprojection')),
            ],
            options={
                'permissions': [('confirm_payment', 'Confirm a synthetic manual payment')],
            },
        ),
        migrations.CreateModel(
            name='OperationRequest',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('action', models.CharField(choices=[('activate', 'Activate / renew'), ('grace', 'Explicit grace'), ('expire', 'Expire now'), ('revoke', 'Revoke permanently')], max_length=12)),
                ('period_start', models.DateTimeField(blank=True, null=True)),
                ('paid_until', models.DateTimeField(blank=True, null=True)),
                ('grace_until', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('DRAFT', 'DRAFT'), ('PREVIEWED', 'PREVIEWED'), ('RUNNING', 'RUNNING'), ('APPLIED', 'APPLIED'), ('REJECTED', 'REJECTED'), ('STALE', 'STALE'), ('UNKNOWN', 'UNKNOWN')], default='DRAFT', max_length=12)),
                ('preview', models.JSONField(blank=True, default=dict)),
                ('previewed_at', models.DateTimeField(blank=True, null=True)),
                ('receipt', models.JSONField(blank=True, default=dict)),
                ('failure_code', models.CharField(blank=True, max_length=64)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('device', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='console.deviceprojection')),
                ('previewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('payment', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='console.paymentrecord')),
            ],
            options={
                'ordering': ['-created_at'],
                'permissions': [('preview_operation', 'Preview using the real synthetic backend'), ('execute_operation', 'Execute or reconcile a previewed synthetic operation')],
            },
        ),
        migrations.AddConstraint(
            model_name='paymentrecord',
            constraint=models.CheckConstraint(condition=models.Q(('amount_minor__gt', 0)), name='positive_payment_amount'),
        ),
        migrations.AddConstraint(
            model_name='paymentrecord',
            constraint=models.CheckConstraint(condition=models.Q(models.Q(('confirmed_at__isnull', True), ('confirmed_by__isnull', True)), models.Q(('confirmed_at__isnull', False), ('confirmed_by__isnull', False)), _connector='OR'), name='complete_payment_confirmation'),
        ),
        migrations.AddConstraint(
            model_name='operationrequest',
            constraint=models.CheckConstraint(condition=models.Q(models.Q(('action', 'activate'), ('grace_until__isnull', True), ('paid_until__isnull', False), ('payment__isnull', False), ('period_start__isnull', False)), models.Q(('action', 'grace'), ('grace_until__isnull', False), ('paid_until__isnull', True), ('payment__isnull', True), ('period_start__isnull', True)), models.Q(('action__in', ['expire', 'revoke']), ('grace_until__isnull', True), ('paid_until__isnull', True), ('payment__isnull', True), ('period_start__isnull', True)), _connector='OR'), name='operation_input_shape'),
        ),
    ]
