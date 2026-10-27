import django.core.validators
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('console', '0003_payment_reference_unique'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='InventorySnapshot',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('scope', models.CharField(choices=[('synthetic', 'Синтетическое демо'), ('production', 'Рабочие серверы · только чтение')], max_length=12, verbose_name='Контур')),
                ('source', models.CharField(max_length=32, verbose_name='Источник')),
                ('observed_at', models.DateTimeField(verbose_name='Время наблюдения')),
                ('imported_at', models.DateTimeField(auto_now_add=True, verbose_name='Время импорта')),
                ('digest', models.CharField(max_length=64, unique=True, verbose_name='SHA256 снимка')),
                ('registry_status', models.CharField(choices=[('ok', 'Прочитан'), ('unavailable', 'Недоступен'), ('not_collected', 'Не собирается')], max_length=16, verbose_name='Состояние чтения реестра')),
            ],
            options={
                'verbose_name': 'снимок инвентаризации',
                'verbose_name_plural': 'снимки инвентаризации',
                'ordering': ['-observed_at'],
            },
        ),
        migrations.AlterModelOptions(
            name='auditrecord',
            options={'ordering': ['-occurred_at'], 'verbose_name': 'событие аудита', 'verbose_name_plural': 'события аудита'},
        ),
        migrations.AlterModelOptions(
            name='cohortmetadata',
            options={'verbose_name': 'метаданные группы', 'verbose_name_plural': 'метаданные группы'},
        ),
        migrations.AlterModelOptions(
            name='deviceprojection',
            options={'ordering': ['label'], 'verbose_name': 'снимок демо-устройства', 'verbose_name_plural': 'снимки демо-устройств'},
        ),
        migrations.AlterModelOptions(
            name='incident',
            options={'verbose_name': 'обращение', 'verbose_name_plural': 'обращения'},
        ),
        migrations.AlterModelOptions(
            name='operationrequest',
            options={'ordering': ['-created_at'], 'permissions': [('preview_operation', 'Предпросмотр в настоящем демо-backend'), ('execute_operation', 'Выполнять или сверять демо-операцию')], 'verbose_name': 'запрос операции', 'verbose_name_plural': 'запросы операций'},
        ),
        migrations.AlterModelOptions(
            name='paymentrecord',
            options={'permissions': [('confirm_payment', 'Подтверждать ручную демо-оплату')], 'verbose_name': 'запись оплаты', 'verbose_name_plural': 'записи оплат'},
        ),
        migrations.AlterModelOptions(
            name='releasemetadata',
            options={'verbose_name': 'метаданные релиза', 'verbose_name_plural': 'метаданные релизов'},
        ),
        migrations.AlterField(
            model_name='auditrecord',
            name='action',
            field=models.CharField(max_length=40, verbose_name='Действие'),
        ),
        migrations.AlterField(
            model_name='auditrecord',
            name='actor',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='Оператор'),
        ),
        migrations.AlterField(
            model_name='auditrecord',
            name='details',
            field=models.JSONField(default=dict, verbose_name='Безопасные сведения'),
        ),
        migrations.AlterField(
            model_name='auditrecord',
            name='occurred_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Время события'),
        ),
        migrations.AlterField(
            model_name='auditrecord',
            name='target',
            field=models.CharField(max_length=64, verbose_name='Объект'),
        ),
        migrations.AlterField(
            model_name='cohortmetadata',
            name='device',
            field=models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, to='console.deviceprojection', verbose_name='Устройство'),
        ),
        migrations.AlterField(
            model_name='cohortmetadata',
            name='handoff_verified',
            field=models.BooleanField(default=False, verbose_name='Передача APK проверена'),
        ),
        migrations.AlterField(
            model_name='cohortmetadata',
            name='opted_in',
            field=models.BooleanField(default=False, verbose_name='Согласие получено'),
        ),
        migrations.AlterField(
            model_name='cohortmetadata',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='Ответственный'),
        ),
        migrations.AlterField(
            model_name='cohortmetadata',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Обновлено'),
        ),
        migrations.AlterField(
            model_name='deviceprojection',
            name='device',
            field=models.CharField(max_length=32, primary_key=True, serialize=False, validators=[django.core.validators.RegexValidator('^[0-9a-f]{32}$')], verbose_name='Устройство'),
        ),
        migrations.AlterField(
            model_name='deviceprojection',
            name='label',
            field=models.CharField(max_length=40, verbose_name='Название'),
        ),
        migrations.AlterField(
            model_name='deviceprojection',
            name='observed_at',
            field=models.DateTimeField(verbose_name='Время наблюдения'),
        ),
        migrations.AlterField(
            model_name='deviceprojection',
            name='readback',
            field=models.JSONField(verbose_name='Снимок ответа backend'),
        ),
        migrations.AlterField(
            model_name='incident',
            name='category',
            field=models.CharField(choices=[('activation', 'Активация'), ('mesh_connect', 'Подключение MESH'), ('crash', 'Сбой приложения'), ('payment', 'Оплата'), ('version', 'Версия'), ('support', 'Поддержка')], max_length=20, verbose_name='Категория'),
        ),
        migrations.AlterField(
            model_name='incident',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Создано'),
        ),
        migrations.AlterField(
            model_name='incident',
            name='device',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='console.deviceprojection', verbose_name='Устройство'),
        ),
        migrations.AlterField(
            model_name='incident',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='Ответственный'),
        ),
        migrations.AlterField(
            model_name='incident',
            name='severity',
            field=models.CharField(choices=[('low', 'Низкая'), ('high', 'Высокая'), ('critical', 'Критическая')], max_length=8, verbose_name='Важность'),
        ),
        migrations.AlterField(
            model_name='incident',
            name='status',
            field=models.CharField(choices=[('open', 'Открыт'), ('triage', 'Разбор'), ('resolved', 'Решён')], default='open', max_length=10, verbose_name='Состояние'),
        ),
        migrations.AlterField(
            model_name='incident',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Обновлено'),
        ),
        migrations.AlterField(
            model_name='operationrequest',
            name='action',
            field=models.CharField(choices=[('activate', 'Активировать / продлить'), ('grace', 'Выдать льготный период'), ('expire', 'Завершить срок'), ('revoke', 'Отозвать навсегда')], max_length=12, verbose_name='Действие'),
        ),
        migrations.AlterField(
            model_name='operationrequest',
            name='completed_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Завершено'),
        ),
        migrations.AlterField(
            model_name='operationrequest',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Создано'),
        ),
        migrations.AlterField(
            model_name='operationrequest',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='Создал'),
        ),
        migrations.AlterField(
            model_name='operationrequest',
            name='device',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='console.deviceprojection', verbose_name='Устройство'),
        ),
        migrations.AlterField(
            model_name='operationrequest',
            name='failure_code',
            field=models.CharField(blank=True, max_length=64, verbose_name='Причина отказа'),
        ),
        migrations.AlterField(
            model_name='operationrequest',
            name='grace_until',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Льготный период до'),
        ),
        migrations.AlterField(
            model_name='operationrequest',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='Идентификатор'),
        ),
        migrations.AlterField(
            model_name='operationrequest',
            name='paid_until',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Оплачено до'),
        ),
        migrations.AlterField(
            model_name='operationrequest',
            name='payment',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='console.paymentrecord', verbose_name='Оплата'),
        ),
        migrations.AlterField(
            model_name='operationrequest',
            name='period_start',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Начало периода'),
        ),
        migrations.AlterField(
            model_name='operationrequest',
            name='preview',
            field=models.JSONField(blank=True, default=dict, verbose_name='Предпросмотр'),
        ),
        migrations.AlterField(
            model_name='operationrequest',
            name='previewed_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Время предпросмотра'),
        ),
        migrations.AlterField(
            model_name='operationrequest',
            name='previewed_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='Предпросмотр выполнил'),
        ),
        migrations.AlterField(
            model_name='operationrequest',
            name='receipt',
            field=models.JSONField(blank=True, default=dict, verbose_name='Квитанция'),
        ),
        migrations.AlterField(
            model_name='operationrequest',
            name='status',
            field=models.CharField(choices=[('DRAFT', 'Черновик'), ('PREVIEWED', 'Предпросмотр готов'), ('RUNNING', 'Выполняется'), ('APPLIED', 'Применено'), ('REJECTED', 'Отклонено'), ('STALE', 'Устарело'), ('UNKNOWN', 'Результат неизвестен')], default='DRAFT', max_length=12, verbose_name='Состояние'),
        ),
        migrations.AlterField(
            model_name='paymentrecord',
            name='amount_minor',
            field=models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)], verbose_name='Сумма в минимальных единицах'),
        ),
        migrations.AlterField(
            model_name='paymentrecord',
            name='confirmed_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Подтверждено'),
        ),
        migrations.AlterField(
            model_name='paymentrecord',
            name='confirmed_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='Подтвердил'),
        ),
        migrations.AlterField(
            model_name='paymentrecord',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Создано'),
        ),
        migrations.AlterField(
            model_name='paymentrecord',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='Создал'),
        ),
        migrations.AlterField(
            model_name='paymentrecord',
            name='currency',
            field=models.CharField(choices=[('EUR', 'EUR'), ('USD', 'USD')], max_length=3, verbose_name='Валюта'),
        ),
        migrations.AlterField(
            model_name='paymentrecord',
            name='device',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='console.deviceprojection', verbose_name='Устройство'),
        ),
        migrations.AlterField(
            model_name='paymentrecord',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='Идентификатор'),
        ),
        migrations.AlterField(
            model_name='paymentrecord',
            name='reference_hash',
            field=models.CharField(max_length=64, unique=True, validators=[django.core.validators.RegexValidator('^[0-9a-f]{64}$')], verbose_name='Хеш основания'),
        ),
        migrations.AlterField(
            model_name='releasemetadata',
            name='channel',
            field=models.CharField(max_length=40, verbose_name='Канал передачи'),
        ),
        migrations.AlterField(
            model_name='releasemetadata',
            name='package_id',
            field=models.CharField(max_length=100, verbose_name='Пакет'),
        ),
        migrations.AlterField(
            model_name='releasemetadata',
            name='sha256',
            field=models.CharField(max_length=64, verbose_name='SHA256'),
        ),
        migrations.AlterField(
            model_name='releasemetadata',
            name='signer_sha256',
            field=models.CharField(max_length=64, verbose_name='SHA256 сертификата'),
        ),
        migrations.AlterField(
            model_name='releasemetadata',
            name='size',
            field=models.PositiveBigIntegerField(verbose_name='Размер в байтах'),
        ),
        migrations.AlterField(
            model_name='releasemetadata',
            name='version_code',
            field=models.PositiveIntegerField(verbose_name='Код версии'),
        ),
        migrations.AlterField(
            model_name='releasemetadata',
            name='version_name',
            field=models.CharField(max_length=64, unique=True, verbose_name='Версия приложения'),
        ),
        migrations.CreateModel(
            name='OperationSwitch',
            fields=[
                ('singleton', models.PositiveSmallIntegerField(default=1, editable=False, primary_key=True, serialize=False)),
                ('stopped', models.BooleanField(default=False, verbose_name='Новые операции остановлены')),
            ],
            options={
                'verbose_name': 'ограничитель операций',
                'verbose_name_plural': 'ограничитель операций',
                'permissions': [('control_operations', 'Останавливать и возобновлять synthetic операции')],
                'constraints': [models.CheckConstraint(condition=models.Q(('singleton', 1)), name='one_operation_switch')],
            },
        ),
        migrations.CreateModel(
            name='ServerObservation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('load_1m', models.FloatField(null=True, verbose_name='Нагрузка за минуту')),
                ('memory_used_percent', models.FloatField(null=True, verbose_name='Использовано памяти, %')),
                ('disk_used_percent', models.FloatField(null=True, verbose_name='Занято диска, %')),
                ('uptime_seconds', models.PositiveBigIntegerField(null=True, verbose_name='Время работы, секунды')),
                ('services', models.JSONField(default=dict, verbose_name='Наблюдения systemd')),
                ('snapshot', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='server', to='console.inventorysnapshot', verbose_name='Снимок')),
            ],
            options={
                'verbose_name': 'наблюдение сервера',
                'verbose_name_plural': 'наблюдения серверов',
            },
        ),
        migrations.CreateModel(
            name='InventoryDevice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pseudonym', models.CharField(max_length=64, verbose_name='Псевдоним устройства (HMAC)')),
                ('activated', models.BooleanField(null=True, verbose_name='Активация наблюдалась')),
                ('revoked', models.BooleanField(null=True, verbose_name='Отзыв наблюдался')),
                ('version_code', models.PositiveIntegerField(null=True, verbose_name='Наблюдаемый код версии')),
                ('version_source', models.CharField(choices=[('support', 'Отчёт поддержки'), ('readiness_ack', 'Подтверждение готовности'), ('unknown', 'Нет данных')], max_length=24, verbose_name='Источник версии')),
                ('last_seen', models.DateTimeField(null=True, verbose_name='Последний отчёт устройства')),
                ('snapshot', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='devices', to='console.inventorysnapshot', verbose_name='Снимок')),
            ],
            options={
                'verbose_name': 'устройство в снимке',
                'verbose_name_plural': 'устройства в снимках',
                'constraints': [models.UniqueConstraint(fields=('snapshot', 'pseudonym'), name='unique_inventory_device')],
            },
        ),
        migrations.CreateModel(
            name='TechnicalSample',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_id', models.CharField(max_length=64, unique=True, verbose_name='Идентификатор события')),
                ('scope', models.CharField(choices=[('synthetic', 'Синтетическое демо'), ('production', 'Рабочие серверы · только чтение')], max_length=12, verbose_name='Контур')),
                ('source', models.CharField(max_length=32, verbose_name='Источник')),
                ('metric', models.CharField(choices=[('activation', 'Успешность активации'), ('mesh_connect', 'Успешность подключения MESH'), ('crash', 'Сбой в сессии'), ('api_latency_ms', 'Задержка API, мс')], max_length=24, verbose_name='Метрика')),
                ('value', models.FloatField(verbose_name='Значение')),
                ('observed_at', models.DateTimeField(verbose_name='Время наблюдения')),
                ('ingested_at', models.DateTimeField(auto_now_add=True, verbose_name='Время приёма')),
                ('device', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='console.deviceprojection', verbose_name='Демо-устройство')),
            ],
            options={
                'verbose_name': 'техническое измерение',
                'verbose_name_plural': 'технические измерения',
                'constraints': [models.CheckConstraint(condition=models.Q(('device__isnull', False), ('scope', 'synthetic')), name='telemetry_synthetic_only'), models.CheckConstraint(condition=models.Q(models.Q(('metric__in', ['activation', 'mesh_connect', 'crash']), ('value__in', [0, 1])), models.Q(('metric', 'api_latency_ms'), ('value__gte', 0), ('value__lte', 60000)), _connector='OR'), name='telemetry_metric_domain')],
            },
        ),
    ]
