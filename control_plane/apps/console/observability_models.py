import uuid

from django.db import models

SCOPE = [('synthetic', 'Синтетическое демо'), ('production', 'Рабочие серверы · только чтение')]


class InventorySnapshot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scope = models.CharField('Контур', max_length=12, choices=SCOPE)
    source = models.CharField('Источник', max_length=32)
    observed_at = models.DateTimeField('Время наблюдения')
    imported_at = models.DateTimeField('Время импорта', auto_now_add=True)
    digest = models.CharField('SHA256 снимка', max_length=64, unique=True)
    registry_status = models.CharField('Состояние чтения реестра', max_length=16,
        choices=[('ok', 'Прочитан'), ('unavailable', 'Недоступен'), ('not_collected', 'Не собирается')])

    class Meta:
        ordering = ['-observed_at']
        verbose_name = 'снимок инвентаризации'
        verbose_name_plural = 'снимки инвентаризации'


class InventoryDevice(models.Model):
    snapshot = models.ForeignKey(InventorySnapshot, on_delete=models.PROTECT, related_name='devices', verbose_name='Снимок')
    pseudonym = models.CharField('Псевдоним устройства (HMAC)', max_length=64)
    activated = models.BooleanField('Активация наблюдалась', null=True)
    revoked = models.BooleanField('Отзыв наблюдался', null=True)
    version_code = models.PositiveIntegerField('Наблюдаемый код версии', null=True)
    version_source = models.CharField('Источник версии', max_length=24,
        choices=[('support', 'Отчёт поддержки'), ('readiness_ack', 'Подтверждение готовности'), ('unknown', 'Нет данных')])
    last_seen = models.DateTimeField('Последний отчёт устройства', null=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['snapshot', 'pseudonym'], name='unique_inventory_device')]
        verbose_name = 'устройство в снимке'
        verbose_name_plural = 'устройства в снимках'


class ServerObservation(models.Model):
    snapshot = models.OneToOneField(InventorySnapshot, on_delete=models.PROTECT, related_name='server', verbose_name='Снимок')
    load_1m = models.FloatField('Нагрузка за минуту', null=True)
    memory_used_percent = models.FloatField('Использовано памяти, %', null=True)
    disk_used_percent = models.FloatField('Занято диска, %', null=True)
    uptime_seconds = models.PositiveBigIntegerField('Время работы, секунды', null=True)
    services = models.JSONField('Наблюдения systemd', default=dict)

    class Meta:
        verbose_name = 'наблюдение сервера'
        verbose_name_plural = 'наблюдения серверов'


class TechnicalSample(models.Model):
    METRICS = [('activation', 'Успешность активации'), ('mesh_connect', 'Успешность подключения MESH'),
        ('crash', 'Сбой в сессии'), ('api_latency_ms', 'Задержка API, мс')]
    event_id = models.CharField('Идентификатор события', max_length=64, unique=True)
    scope = models.CharField('Контур', max_length=12, choices=SCOPE)
    source = models.CharField('Источник', max_length=32)
    device = models.ForeignKey('console.DeviceProjection', null=True, on_delete=models.PROTECT, verbose_name='Демо-устройство')
    metric = models.CharField('Метрика', max_length=24, choices=METRICS)
    value = models.FloatField('Значение')
    observed_at = models.DateTimeField('Время наблюдения')
    ingested_at = models.DateTimeField('Время приёма', auto_now_add=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(scope='synthetic', device__isnull=False), name='telemetry_synthetic_only'),
            models.CheckConstraint(condition=(models.Q(metric__in=['activation', 'mesh_connect', 'crash'], value__in=[0, 1]) |
                models.Q(metric='api_latency_ms', value__gte=0, value__lte=60000)), name='telemetry_metric_domain')]
        verbose_name = 'техническое измерение'
        verbose_name_plural = 'технические измерения'


class OperationSwitch(models.Model):
    singleton = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    stopped = models.BooleanField('Новые операции остановлены', default=False)

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(singleton=1), name='one_operation_switch')]
        permissions = [('control_operations', 'Останавливать и возобновлять synthetic операции')]
        verbose_name = 'ограничитель операций'
        verbose_name_plural = 'ограничитель операций'
