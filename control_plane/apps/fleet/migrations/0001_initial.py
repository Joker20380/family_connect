import django.core.validators
import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('console', '0006_payment_purpose'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='GatewayArtifact',
            fields=[
                ('bundle_id', models.CharField(max_length=96, primary_key=True, serialize=False, validators=[django.core.validators.RegexValidator('^[A-Za-z0-9][A-Za-z0-9_.-]{0,95}$')], verbose_name='Bundle ID')),
                ('source_commit', models.CharField(max_length=40, validators=[django.core.validators.RegexValidator('^[0-9a-f]{40}$')], verbose_name='Коммит исходников')),
                ('manifest_sha256', models.CharField(max_length=64, validators=[django.core.validators.RegexValidator('^[0-9a-f]{64}$')], verbose_name='SHA256 манифеста')),
                ('archive_sha256', models.CharField(max_length=64, validators=[django.core.validators.RegexValidator('^[0-9a-f]{64}$')], verbose_name='SHA256 архива')),
                ('signature', models.CharField(max_length=128, verbose_name='Подпись манифеста')),
                ('signature_verified', models.BooleanField(default=False, verbose_name='Подпись проверена локальным оператором')),
                ('supported_os', models.JSONField(verbose_name='Поддерживаемые ОС')),
                ('architectures', models.JSONField(verbose_name='Архитектуры')),
                ('roles', models.JSONField(verbose_name='Роли')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Создан')),
            ],
            options={
                'verbose_name': 'артефакт шлюза',
                'verbose_name_plural': 'Артефакты',
            },
        ),
        migrations.CreateModel(
            name='GatewayInstance',
            fields=[
                ('instance_id', models.CharField(max_length=96, primary_key=True, serialize=False, validators=[django.core.validators.RegexValidator('^[A-Za-z0-9][A-Za-z0-9_.-]{0,95}$')], verbose_name='Instance ID')),
                ('provider', models.CharField(max_length=96, validators=[django.core.validators.RegexValidator('^[A-Za-z0-9][A-Za-z0-9_.-]{0,95}$')], verbose_name='Провайдер')),
                ('region', models.CharField(max_length=96, validators=[django.core.validators.RegexValidator('^[A-Za-z0-9][A-Za-z0-9_.-]{0,95}$')], verbose_name='Регион')),
                ('ipv4', models.GenericIPAddressField(protocol='IPv4', verbose_name='IPv4')),
                ('ipv6', models.GenericIPAddressField(blank=True, null=True, protocol='IPv6', verbose_name='IPv6')),
                ('os_family', models.CharField(default='ubuntu', max_length=16, verbose_name='ОС')),
                ('os_version', models.CharField(default='24.04', max_length=16, verbose_name='Версия ОС')),
                ('architecture', models.CharField(default='x86_64', max_length=16, verbose_name='Архитектура')),
                ('state', models.CharField(choices=[('DISCOVERED', 'Обнаружен'), ('PREFLIGHTED', 'Предпроверка пройдена'), ('STAGED', 'Подготовлен'), ('VERIFIED', 'Проверен'), ('ACTIVE', 'Активен'), ('DRAINING', 'Выводится'), ('QUARANTINED', 'Карантин'), ('FAILED', 'Ошибка'), ('RETIRED', 'Выведен')], default='DISCOVERED', max_length=16, verbose_name='Состояние')),
                ('deployment_identity', models.CharField(blank=True, max_length=64, null=True, unique=True, validators=[django.core.validators.RegexValidator('^[0-9a-f]{64}$')], verbose_name='Публичный digest identity')),
                ('enrollment_receipt_sha256', models.CharField(blank=True, max_length=64, null=True, validators=[django.core.validators.RegexValidator('^[0-9a-f]{64}$')], verbose_name='SHA256 подписанной регистрации')),
                ('enrollment_state', models.CharField(choices=[('NEW', 'Не зарегистрирован'), ('ENROLLED', 'Зарегистрирован'), ('CANCELLED', 'Отменена')], default='NEW', max_length=16, verbose_name='Регистрация экземпляра')),
                ('health_state', models.CharField(choices=[('UNKNOWN', 'Нет данных'), ('PASS', 'Проверен'), ('FAIL', 'Ошибка')], default='UNKNOWN', max_length=8, verbose_name='Здоровье')),
                ('roles', models.JSONField(verbose_name='Роли')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Создан')),
                ('activated_at', models.DateTimeField(blank=True, null=True, verbose_name='Активирован')),
                ('drained_at', models.DateTimeField(blank=True, null=True, verbose_name='Вывод начат')),
                ('quarantined_at', models.DateTimeField(blank=True, null=True, verbose_name='Карантин')),
                ('actual_bundle', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='fleet_console.gatewayartifact', verbose_name='Фактический bundle')),
                ('desired_bundle', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='+', to='fleet_console.gatewayartifact', verbose_name='Желаемый bundle')),
            ],
            options={
                'verbose_name': 'физический сервер',
                'verbose_name_plural': 'Серверы',
            },
        ),
        migrations.CreateModel(
            name='EnrollmentToken',
            fields=[
                ('token_hash', models.CharField(max_length=64, primary_key=True, serialize=False, validators=[django.core.validators.RegexValidator('^[0-9a-f]{64}$')], verbose_name='Хэш одноразового токена')),
                ('binding', models.JSONField(verbose_name='Привязка регистрации · публичные поля')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Создан')),
                ('expires_at', models.DateTimeField(verbose_name='Истекает')),
                ('instance', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='fleet_console.gatewayinstance', verbose_name='Экземпляр')),
            ],
            options={
                'verbose_name': 'метаданные регистрации',
                'verbose_name_plural': 'Регистрация экземпляров · без значений токенов',
            },
        ),
        migrations.CreateModel(
            name='DeploymentOperation',
            fields=[
                ('operation_id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='Операция')),
                ('action', models.CharField(choices=[('plan', 'План'), ('preflight', 'Предпроверка'), ('stage', 'Подготовка'), ('verify', 'Проверка'), ('activate', 'Активация'), ('drain', 'Вывод'), ('quarantine', 'Карантин'), ('rollback', 'Откат')], max_length=16, verbose_name='Действие')),
                ('state', models.CharField(choices=[('INTENT', 'Ожидает CLI'), ('SUCCEEDED', 'Выполнено локально'), ('FAILED', 'Ошибка')], default='INTENT', max_length=16, verbose_name='Результат')),
                ('first_failure', models.CharField(blank=True, max_length=96, validators=[django.core.validators.RegexValidator('^[A-Za-z0-9][A-Za-z0-9_.-]{0,95}$')], verbose_name='Первая ошибка')),
                ('started_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Создан')),
                ('completed_at', models.DateTimeField(blank=True, null=True, verbose_name='Завершён')),
                ('safe_receipt', models.JSONField(blank=True, default=dict, verbose_name='Безопасный receipt')),
                ('intent', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='completion', to='fleet_console.deploymentoperation', verbose_name='Исходный intent')),
                ('requested_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='Оператор')),
                ('previous_bundle', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='fleet_console.gatewayartifact', verbose_name='Предыдущий bundle')),
                ('target_bundle', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='+', to='fleet_console.gatewayartifact', verbose_name='Целевой bundle')),
                ('instance', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='fleet_console.gatewayinstance', verbose_name='Экземпляр')),
            ],
            options={
                'verbose_name': 'операция развёртывания',
                'verbose_name_plural': 'Операции · только intents и локальные receipts',
                'ordering': ['-started_at'],
            },
        ),
        migrations.CreateModel(
            name='InstanceHealthCheck',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('scope', models.CharField(choices=[('synthetic', 'Синтетический'), ('production-readonly', 'Production · только чтение')], max_length=24, verbose_name='Контур')),
                ('observed_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Наблюдение')),
                ('checks', models.JSONField(blank=True, default=dict, verbose_name='Проверки ролей')),
                ('cpu', models.FloatField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)], verbose_name='CPU, %')),
                ('ram', models.FloatField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)], verbose_name='RAM, %')),
                ('disk', models.FloatField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)], verbose_name='Диск, %')),
                ('active_sessions', models.PositiveIntegerField(blank=True, null=True, verbose_name='Активные сессии · если измерены')),
                ('certificate_expiry', models.DateTimeField(blank=True, null=True, verbose_name='Сертификат истекает')),
                ('directory_expiry', models.DateTimeField(blank=True, null=True, verbose_name='Directory истекает')),
                ('restart_count', models.PositiveIntegerField(blank=True, null=True, verbose_name='Перезапуски')),
                ('bundle', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='fleet_console.gatewayartifact', verbose_name='Bundle')),
                ('instance', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='health_checks', to='fleet_console.gatewayinstance', verbose_name='Экземпляр')),
                ('observation', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='fleet_link', to='console.serverobservation', verbose_name='Исходный read-only снимок')),
            ],
            options={
                'verbose_name': 'наблюдение экземпляра',
                'verbose_name_plural': 'История здоровья экземпляров',
                'ordering': ['-observed_at'],
            },
        ),
        migrations.CreateModel(
            name='LogicalGateway',
            fields=[
                ('id', models.CharField(max_length=96, primary_key=True, serialize=False, validators=[django.core.validators.RegexValidator('^[A-Za-z0-9][A-Za-z0-9_.-]{0,95}$')], verbose_name='Логический шлюз')),
                ('country', models.CharField(max_length=2, validators=[django.core.validators.RegexValidator('^[A-Z]{2}$')], verbose_name='Страна')),
                ('transports', models.JSONField(verbose_name='Транспорты')),
                ('desired_state', models.CharField(choices=[('DISCOVERED', 'Обнаружен'), ('PREFLIGHTED', 'Предпроверка пройдена'), ('STAGED', 'Подготовлен'), ('VERIFIED', 'Проверен'), ('ACTIVE', 'Активен'), ('DRAINING', 'Выводится'), ('QUARANTINED', 'Карантин'), ('FAILED', 'Ошибка'), ('RETIRED', 'Выведен')], default='ACTIVE', max_length=16, verbose_name='Желаемое состояние')),
                ('catalog_generation', models.PositiveIntegerField(default=4, verbose_name='Поколение каталога')),
                ('active_instance', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='active_for', to='fleet_console.gatewayinstance', verbose_name='Активный экземпляр')),
                ('fallback_instances', models.ManyToManyField(blank=True, related_name='fallback_for', to='fleet_console.gatewayinstance', verbose_name='Резервные экземпляры')),
            ],
            options={
                'verbose_name': 'логический шлюз',
                'verbose_name_plural': 'Логические шлюзы',
            },
        ),
        migrations.AddField(
            model_name='gatewayinstance',
            name='logical_gateway',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='instances', to='fleet_console.logicalgateway', verbose_name='Логический шлюз'),
        ),
        migrations.AddConstraint(
            model_name='gatewayinstance',
            constraint=models.UniqueConstraint(condition=models.Q(('state', 'ACTIVE')), fields=('logical_gateway',), name='fleet_one_active_logical'),
        ),
        migrations.AddConstraint(
            model_name='gatewayinstance',
            constraint=models.CheckConstraint(condition=models.Q(models.Q(('state', 'ACTIVE'), _negated=True), models.Q(('actual_bundle__isnull', False), ('deployment_identity__isnull', False), ('enrollment_state', 'ENROLLED'), ('health_state', 'PASS')), _connector='OR'), name='fleet_active_accepted'),
        ),
    ]
