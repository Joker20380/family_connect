from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from fleet.contracts import transition, canonical, digest, typed
from fleet.health import accept
from fleet.enrollment import verify_receipt
from .models import DeploymentOperation, GatewayInstance, InstanceHealthCheck, LogicalGateway


@transaction.atomic
def accept_enrollment(actor, instance_id, receipt, authority):
    if not actor.is_active or not actor.has_perm('fleet_console.change_gatewayinstance'):
        raise PermissionDenied
    instance=GatewayInstance.objects.select_for_update().get(pk=instance_id)
    binding=dict(instance_id=instance.pk,logical_gateway=instance.logical_gateway_id,bundle_id=instance.desired_bundle_id,
        provider=instance.provider,region=instance.region,ipv4=instance.ipv4,roles=instance.roles)
    try:
        identity=verify_receipt(receipt,authority,binding)
    except ValueError as error:
        raise ValidationError('Подписанная регистрация не принята.') from error
    receipt_hash=digest(canonical(receipt))
    if instance.enrollment_state=='ENROLLED':
        if instance.enrollment_receipt_sha256!=receipt_hash:
            raise ValidationError('Экземпляр уже зарегистрирован иначе.')
        return instance
    if instance.enrollment_state!='NEW':
        raise ValidationError('Регистрация отменена.')
    GatewayInstance.objects.filter(pk=instance.pk).update(enrollment_state='ENROLLED',deployment_identity=identity,enrollment_receipt_sha256=receipt_hash)
    from apps.console.models import AuditRecord
    AuditRecord.objects.create(actor=actor,action='fleet_enrollment_accepted',target=receipt_hash,details=dict(scope='synthetic'))
    instance.refresh_from_db()
    return instance


@transaction.atomic
def create_intent(actor, instance_id, action):
    if not actor.is_active or not actor.has_perm('fleet_console.add_deploymentoperation'):
        raise PermissionDenied
    instance = GatewayInstance.objects.select_for_update().get(pk=instance_id)
    if not instance.desired_bundle.signature_verified:
        raise ValidationError('Артефакт не проверен оператором.')
    targets = dict(preflight='PREFLIGHTED',stage='STAGED',verify='VERIFIED',activate='ACTIVE',drain='DRAINING',quarantine='QUARANTINED')
    if action not in dict(DeploymentOperation._meta.get_field('action').choices):
        raise ValidationError('Неизвестная операция.')
    if action in targets:
        try:
            transition(instance.state,targets[action],health_pass=action=='verify' or instance.health_state=='PASS')
            if action=='activate':
                if instance.enrollment_state!='ENROLLED' or not instance.enrollment_receipt_sha256:
                    raise ValueError('enrollment_missing')
                check=instance.health_checks.filter(scope='synthetic',bundle=instance.desired_bundle).first()
                if not check:
                    raise ValueError('missing_health')
                accept(dict(schema=1,scope='synthetic',instance_id=instance.pk,bundle_id=check.bundle_id,
                    observed_at=int(check.observed_at.timestamp()),checks=check.checks),instance.pk,check.bundle_id,instance.roles)
        except ValueError as error:
            raise ValidationError('Предусловия состояния/здоровья не выполнены.') from error
    previous=instance.actual_bundle
    if action=='rollback':
        accepted=DeploymentOperation.objects.filter(instance=instance,action='activate',state='SUCCEEDED').first()
        if not accepted or instance.actual_bundle_id!=accepted.target_bundle_id:
            raise ValidationError('Нет сохранённой activation receipt для отката.')
        if instance.state in ('PREFLIGHTED','STAGED','VERIFIED') and instance.desired_bundle_id!=instance.actual_bundle_id:
            previous=instance.actual_bundle
        elif instance.state in ('ACTIVE','DRAINING','QUARANTINED','FAILED'):
            previous=accepted.previous_bundle
        else:
            raise ValidationError('Откат уже выполнен или переход не разрешён.')
    return DeploymentOperation.objects.create(requested_by=actor,instance=instance,action=action,previous_bundle=previous,
        target_bundle=instance.desired_bundle,safe_receipt=dict(scope='synthetic',result='operator_intent'))


@transaction.atomic
def record_completion(actor, intent_id, receipt, health_report=None):
    if not actor.is_active or not actor.has_perm('fleet_console.add_deploymentoperation'):
        raise PermissionDenied
    intent=DeploymentOperation.objects.select_for_update().get(pk=intent_id,state='INTENT')
    instance=GatewayInstance.objects.select_for_update().get(pk=intent.instance_id)
    if DeploymentOperation.objects.filter(intent=intent).exists():
        existing=DeploymentOperation.objects.get(intent=intent)
        if existing.safe_receipt.get('evidence_sha256') != digest(canonical(receipt)):
            raise ValidationError('Повторный receipt конфликтует с сохранённым.')
        return existing
    try:
        if (set(receipt) - {'operation_id','request','state','first_failure','previous_bundle','scope','result','rollback_pointer','rollback_failed'}
                or receipt['operation_id'] != str(intent.operation_id) or receipt['scope'] != 'synthetic'
                or receipt['request']['instance'] != instance.pk or receipt['request']['target'] != intent.target_bundle_id
                or receipt['request']['action'] != intent.action or receipt['state'] not in ('SUCCEEDED','FAILED')
                or instance.desired_bundle_id != intent.target_bundle_id):
            raise ValueError('receipt_binding')
        failure=receipt.get('first_failure') or ''
        if failure and not typed(failure,'id'):
            raise ValueError('failure_code')
        updates={}
        if receipt['state']=='SUCCEEDED':
            targets=dict(preflight='PREFLIGHTED',stage='STAGED',verify='VERIFIED',activate='ACTIVE',drain='DRAINING',quarantine='QUARANTINED')
            if intent.action in targets:
                target=targets[intent.action]
                if receipt['result']['state'] != target:
                    raise ValueError('receipt_state')
                if intent.action=='verify':
                    accept(health_report,instance.pk,intent.target_bundle_id,instance.roles)
                    InstanceHealthCheck.objects.create(instance=instance,bundle=intent.target_bundle,scope='synthetic',
                        observed_at=timezone.datetime.fromtimestamp(health_report['observed_at'],tz=timezone.get_current_timezone()),checks=health_report['checks'])
                if intent.action=='activate':
                    check=instance.health_checks.filter(scope='synthetic',bundle=intent.target_bundle).first()
                    if not check or instance.enrollment_state!='ENROLLED' or not instance.deployment_identity or not instance.enrollment_receipt_sha256:
                        raise ValueError('activation_identity')
                    accept(dict(schema=1,scope='synthetic',instance_id=instance.pk,bundle_id=intent.target_bundle_id,
                        observed_at=int(check.observed_at.timestamp()),checks=check.checks),instance.pk,intent.target_bundle_id,instance.roles)
                    updates.update(actual_bundle=intent.target_bundle,activated_at=timezone.now())
                transition(instance.state,target,health_pass=intent.action in ('verify','activate'))
                updates['state']=target
                if intent.action=='verify':updates['health_state']='PASS'
                if intent.action in ('preflight','stage'):updates['health_state']='UNKNOWN'
                if intent.action=='drain':updates['drained_at']=timezone.now()
                if intent.action=='quarantine':updates['quarantined_at']=timezone.now()
            elif intent.action=='rollback':
                if receipt['result']['actual_bundle'] != intent.previous_bundle_id:
                    raise ValueError('rollback_binding')
                updates.update(actual_bundle=intent.previous_bundle,state='STAGED' if intent.previous_bundle_id else 'DISCOVERED',health_state='UNKNOWN')
            if updates:
                GatewayInstance.objects.filter(pk=instance.pk).update(**updates)
                if updates.get('state')=='ACTIVE':
                    LogicalGateway.objects.filter(pk=instance.logical_gateway_id).update(active_instance=instance)
                elif updates.get('state') in ('DRAINING','QUARANTINED','STAGED','DISCOVERED'):
                    LogicalGateway.objects.filter(active_instance=instance).update(active_instance=None)
    except (ValueError,KeyError,TypeError) as error:
        raise ValidationError('Неверный локальный receipt или health binding.') from error
    return DeploymentOperation.objects.create(requested_by=actor,intent=intent,instance=instance,action=intent.action,
        previous_bundle=intent.previous_bundle,target_bundle=intent.target_bundle,state=receipt['state'],first_failure=failure,
        completed_at=timezone.now(),safe_receipt=dict(scope='synthetic',result=receipt['state'],evidence_sha256=digest(canonical(receipt))))
