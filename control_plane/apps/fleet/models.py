import uuid
import math

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone

from fleet.contracts import STATES, typed
from fleet.enrollment import binding_check

IDENTIFIER = RegexValidator(r'^[A-Za-z0-9][A-Za-z0-9_.-]{0,95}$')
HASH = RegexValidator(r'^[0-9a-f]{64}$')
CHOICES = [(state, label) for state,label in zip(STATES, (
    'Обнаружен','Предпроверка пройдена','Подготовлен','Проверен','Активен','Выводится',
    'Карантин','Ошибка','Выведен'))]


class Validated(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class Immutable(Validated):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError('Запись аудита неизменяема; создайте новое событие.')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('Удаление аудита запрещено.')


class GatewayArtifact(Immutable):
    bundle_id = models.CharField('Bundle ID', primary_key=True, max_length=96, validators=[IDENTIFIER])
    source_commit = models.CharField('Коммит исходников', max_length=40, validators=[RegexValidator(r'^[0-9a-f]{40}$')])
    manifest_sha256 = models.CharField('SHA256 манифеста', max_length=64, validators=[HASH])
    archive_sha256 = models.CharField('SHA256 архива', max_length=64, validators=[HASH])
    signature = models.CharField('Подпись манифеста', max_length=128)
    signature_verified = models.BooleanField('Подпись проверена локальным оператором', default=False)
    supported_os = models.JSONField('Поддерживаемые ОС')
    architectures = models.JSONField('Архитектуры')
    roles = models.JSONField('Роли')
    created_at = models.DateTimeField('Создан', default=timezone.now)

    def clean(self):
        if not typed(self.signature,'signature') or not typed(self.roles,'roles') or not self.roles:
            raise ValidationError('Неверная подпись или роли артефакта.')
        if self.supported_os != ['ubuntu-24.04'] or self.architectures != ['x86_64']:
            raise ValidationError('Платформа не квалифицирована.')

    def __str__(self):
        return self.bundle_id

    class Meta:
        verbose_name = 'артефакт шлюза'
        verbose_name_plural = 'Артефакты'


class LogicalGateway(Validated):
    id = models.CharField('Логический шлюз', primary_key=True, max_length=96, validators=[IDENTIFIER])
    country = models.CharField('Страна', max_length=2, validators=[RegexValidator(r'^[A-Z]{2}$')])
    transports = models.JSONField('Транспорты')
    desired_state = models.CharField('Желаемое состояние', max_length=16, choices=CHOICES, default='ACTIVE')
    active_instance = models.OneToOneField('GatewayInstance', null=True, blank=True, on_delete=models.PROTECT, related_name='active_for', verbose_name='Активный экземпляр')
    fallback_instances = models.ManyToManyField('GatewayInstance', blank=True, related_name='fallback_for', verbose_name='Резервные экземпляры')
    catalog_generation = models.PositiveIntegerField('Поколение каталога', default=4)

    def clean(self):
        if not typed(self.transports,'transports'):
            raise ValidationError('Неизвестный транспорт.')
        if self.active_instance_id and (self.active_instance.logical_gateway_id != self.pk or self.active_instance.state != 'ACTIVE'):
            raise ValidationError('Активный экземпляр не принадлежит этому шлюзу или не принят.')

    def __str__(self):
        return self.id

    class Meta:
        verbose_name = 'логический шлюз'
        verbose_name_plural = 'Логические шлюзы'


class GatewayInstance(Validated):
    instance_id = models.CharField('Instance ID', primary_key=True, max_length=96, validators=[IDENTIFIER])
    logical_gateway = models.ForeignKey(LogicalGateway, on_delete=models.PROTECT, related_name='instances', verbose_name='Логический шлюз')
    provider = models.CharField('Провайдер', max_length=96, validators=[IDENTIFIER])
    region = models.CharField('Регион', max_length=96, validators=[IDENTIFIER])
    ipv4 = models.GenericIPAddressField('IPv4', protocol='IPv4')
    ipv6 = models.GenericIPAddressField('IPv6', protocol='IPv6', null=True, blank=True)
    os_family = models.CharField('ОС', max_length=16, default='ubuntu')
    os_version = models.CharField('Версия ОС', max_length=16, default='24.04')
    architecture = models.CharField('Архитектура', max_length=16, default='x86_64')
    state = models.CharField('Состояние', max_length=16, choices=CHOICES, default='DISCOVERED')
    desired_bundle = models.ForeignKey(GatewayArtifact, on_delete=models.PROTECT, related_name='+', verbose_name='Желаемый bundle')
    actual_bundle = models.ForeignKey(GatewayArtifact, null=True, blank=True, on_delete=models.PROTECT, related_name='+', verbose_name='Фактический bundle')
    deployment_identity = models.CharField('Публичный digest identity', max_length=64, validators=[HASH], unique=True, null=True, blank=True)
    enrollment_receipt_sha256 = models.CharField('SHA256 подписанной регистрации', max_length=64, validators=[HASH], null=True, blank=True)
    enrollment_state = models.CharField('Регистрация экземпляра', max_length=16, default='NEW', choices=[('NEW','Не зарегистрирован'),('ENROLLED','Зарегистрирован'),('CANCELLED','Отменена')])
    health_state = models.CharField('Здоровье', max_length=8, default='UNKNOWN', choices=[('UNKNOWN','Нет данных'),('PASS','Проверен'),('FAIL','Ошибка')])
    roles = models.JSONField('Роли')
    created_at = models.DateTimeField('Создан', default=timezone.now)
    activated_at = models.DateTimeField('Активирован', null=True, blank=True)
    drained_at = models.DateTimeField('Вывод начат', null=True, blank=True)
    quarantined_at = models.DateTimeField('Карантин', null=True, blank=True)

    def clean(self):
        if not typed(self.roles,'roles') or not self.roles or not set(self.roles) <= set(self.desired_bundle.roles):
            raise ValidationError('Роли не привязаны к артефакту.')
        if self._state.adding and self.state != 'DISCOVERED':
            raise ValidationError('Новый физический экземпляр начинается с DISCOVERED.')
        if self._state.adding and self.enrollment_state!='NEW':
            raise ValidationError('Регистрация требует отдельную проверку подписанного receipt.')
        if not self._state.adding and type(self).objects.filter(pk=self.pk).exclude(state=self.state).exists():
            raise ValidationError('Состояние меняется только через проверенный operator receipt, не через save().')
        if not self._state.adding and type(self).objects.filter(pk=self.pk).exclude(enrollment_state=self.enrollment_state).exists():
            raise ValidationError('Регистрация меняется только через подписанный receipt.')

    def __str__(self):
        return self.instance_id

    class Meta:
        verbose_name = 'физический сервер'
        verbose_name_plural = 'Серверы'
        constraints = [models.UniqueConstraint(fields=['logical_gateway'], condition=models.Q(state='ACTIVE'), name='fleet_one_active_logical'),
            models.CheckConstraint(condition=~models.Q(state='ACTIVE') | models.Q(health_state='PASS',enrollment_state='ENROLLED',deployment_identity__isnull=False,actual_bundle__isnull=False),name='fleet_active_accepted')]


class EnrollmentToken(Immutable):
    token_hash = models.CharField('Хэш одноразового токена', primary_key=True, max_length=64, validators=[HASH])
    instance = models.ForeignKey(GatewayInstance, on_delete=models.PROTECT, verbose_name='Экземпляр')
    binding = models.JSONField('Привязка регистрации · публичные поля')
    created_at = models.DateTimeField('Создан', default=timezone.now)
    expires_at = models.DateTimeField('Истекает')

    def clean(self):
        try:
            binding_check(self.binding)
        except ValueError as error:
            raise ValidationError('Неверная привязка регистрации.') from error
        expected = dict(instance_id=self.instance_id,logical_gateway=self.instance.logical_gateway_id,
            bundle_id=self.instance.desired_bundle_id,provider=self.instance.provider,region=self.instance.region,
            ipv4=self.instance.ipv4,roles=self.instance.roles)
        if self.binding != expected or not 0 < (self.expires_at-self.created_at).total_seconds() <= 600:
            raise ValidationError('Привязка экземпляра или TTL вне контракта.')

    class Meta:
        verbose_name = 'метаданные регистрации'
        verbose_name_plural = 'Регистрация экземпляров · без значений токенов'


class DeploymentOperation(Immutable):
    operation_id = models.UUIDField('Операция', primary_key=True, default=uuid.uuid4, editable=False)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,verbose_name='Оператор')
    intent = models.OneToOneField('self', on_delete=models.PROTECT, null=True, blank=True, related_name='completion', verbose_name='Исходный intent')
    instance = models.ForeignKey(GatewayInstance, on_delete=models.PROTECT, verbose_name='Экземпляр')
    action = models.CharField('Действие', max_length=16, choices=[(name,label) for name,label in (
        ('plan','План'),('preflight','Предпроверка'),('stage','Подготовка'),('verify','Проверка'),('activate','Активация'),
        ('drain','Вывод'),('quarantine','Карантин'),('rollback','Откат'))])
    previous_bundle = models.ForeignKey(GatewayArtifact, null=True, blank=True, on_delete=models.PROTECT, related_name='+', verbose_name='Предыдущий bundle')
    target_bundle = models.ForeignKey(GatewayArtifact, on_delete=models.PROTECT, related_name='+', verbose_name='Целевой bundle')
    state = models.CharField('Результат', max_length=16, default='INTENT', choices=[('INTENT','Ожидает CLI'),('SUCCEEDED','Выполнено локально'),('FAILED','Ошибка')])
    first_failure = models.CharField('Первая ошибка', max_length=96, blank=True, validators=[IDENTIFIER])
    started_at = models.DateTimeField('Создан', default=timezone.now)
    completed_at = models.DateTimeField('Завершён', null=True, blank=True)
    safe_receipt = models.JSONField('Безопасный receipt', default=dict, blank=True)

    def clean(self):
        if not typed(self.safe_receipt,'receipt'):
            raise ValidationError('Произвольный вывод и секреты в receipt запрещены.')
        if self.state=='INTENT' and self.intent_id or self.state!='INTENT' and not self.intent_id:
            raise ValidationError('Completion должен ссылаться на неизменяемый intent.')
        if self.intent_id and (self.intent.instance_id != self.instance_id or self.intent.action != self.action or self.intent.target_bundle_id != self.target_bundle_id):
            raise ValidationError('Completion не соответствует intent.')

    class Meta:
        verbose_name = 'операция развёртывания'
        verbose_name_plural = 'Операции · только intents и локальные receipts'
        ordering = ['-started_at']


class InstanceHealthCheck(Immutable):
    instance = models.ForeignKey(GatewayInstance, on_delete=models.PROTECT, related_name='health_checks', verbose_name='Экземпляр')
    bundle = models.ForeignKey(GatewayArtifact, on_delete=models.PROTECT, verbose_name='Bundle')
    observation = models.OneToOneField('console.ServerObservation', null=True, blank=True, on_delete=models.PROTECT, related_name='fleet_link', verbose_name='Исходный read-only снимок')
    scope = models.CharField('Контур', max_length=24, choices=[('synthetic','Синтетический'),('production-readonly','Production · только чтение')])
    observed_at = models.DateTimeField('Наблюдение', default=timezone.now)
    checks = models.JSONField('Проверки ролей', default=dict, blank=True)
    cpu = models.FloatField('CPU, %', null=True, blank=True, validators=[MinValueValidator(0),MaxValueValidator(100)])
    ram = models.FloatField('RAM, %', null=True, blank=True, validators=[MinValueValidator(0),MaxValueValidator(100)])
    disk = models.FloatField('Диск, %', null=True, blank=True, validators=[MinValueValidator(0),MaxValueValidator(100)])
    active_sessions = models.PositiveIntegerField('Активные сессии · если измерены', null=True, blank=True)
    certificate_expiry = models.DateTimeField('Сертификат истекает', null=True, blank=True)
    directory_expiry = models.DateTimeField('Directory истекает', null=True, blank=True)
    restart_count = models.PositiveIntegerField('Перезапуски', null=True, blank=True)

    def clean(self):
        from fleet.health import required
        if type(self.checks) is not dict or not set(self.checks) <= set(required(self.instance.roles)) or any(type(value) is not bool for value in self.checks.values()):
            raise ValidationError('Неизвестные проверки или значения.')
        if self.scope=='production-readonly' and not self.observation_id:
            raise ValidationError('Production-метаданные требуют неизменяемый исходный снимок.')
        if any(value is not None and not math.isfinite(value) for value in (self.cpu,self.ram,self.disk)):
            raise ValidationError('Метрики должны быть конечными числами.')

    class Meta:
        verbose_name = 'наблюдение экземпляра'
        verbose_name_plural = 'История здоровья экземпляров'
        ordering = ['-observed_at']
