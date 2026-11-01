from django.core.exceptions import ValidationError
from django.db import transaction

from fleet.contracts import canonical, digest
from fleet.evidence import verify
from .models import RehearsalEvidence


@transaction.atomic
def import_receipt(receipt, public_key):
    body = verify(receipt, public_key)
    key = dict(instance_id=body['instance_id'], kind=body['kind'], operation_id=body['operation_id'])
    expected = digest(canonical(receipt))
    record, created = RehearsalEvidence.objects.get_or_create(**key,
        defaults=dict(receipt_sha256=expected, receipt=receipt))
    if record.receipt_sha256 != expected or record.receipt != receipt:
        raise ValidationError('Операция уже импортирована с другим receipt.')
    return record, created


def summary():
    instances = {}
    records = sorted(RehearsalEvidence.objects.all(), key=lambda record:(record.receipt['body']['issued_at'],record.pk))
    for record in records:
        body = record.receipt['body']
        node = instances.setdefault(record.instance_id, dict(instance_id=record.instance_id,
            local_health='NOT_RUN',external=dict(awg='NOT_RUN',tcp='NOT_RUN',mesh='NOT_RUN'),
            rollback='NOT_RUN',reboot='NOT_RUN',retirement='NOT_RUN'))
        if body['actual_bundle'] != node.get('actual_bundle') or body['state']=='AWAITING_EXTERNAL_ACCEPTANCE':
            node.update(local_health='NOT_RUN',external=dict(awg='NOT_RUN',tcp='NOT_RUN',mesh='NOT_RUN'))
        for name in ('operation_id','provider','region','target_sha256','bundle_id','actual_bundle','state','duration_ms'):
            node[name] = body[name]
        for name in ('local_health','rollback','reboot','retirement'):
            if body[name] != 'NOT_RUN':
                node[name] = body[name]
        for role, result in body['external'].items():
            if result != 'NOT_RUN':
                node['external'][role] = result
    return list(instances.values())
