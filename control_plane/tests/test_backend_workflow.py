from concurrent.futures import ThreadPoolExecutor
import json
import sqlite3
import time

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.db import DatabaseError, close_old_connections, connection, transaction
import pytest

from apps.console import backend, workflow
from apps.console.models import AuditRecord, DeviceProjection, OperationRequest, PaymentRecord
from control.friends import paid_beta


def apply_request(actor, request):
    prepared = workflow.prepare(actor, request.pk)
    return workflow.execute(actor, request.pk, workflow.confirmation_token(actor, prepared))


def counts():
    with backend.registry() as database:
        return tuple(database.execute('SELECT count(*) FROM ' + table).fetchone()[0]
                     for table in ('paid_beta_subscriptions', 'paid_beta_events'))


def test_real_postgresql_and_no_subscription_models(console):
    assert connection.vendor == 'postgresql'
    names = connection.introspection.table_names()
    assert not any('subscription' in name or name == 'paid_beta_events' for name in names)
    assert len(backend.members()) == DeviceProjection.objects.count() == 12
    assert counts() == (0, 0)


def test_preview_uses_real_backend_without_registry_mutation(console, operation, monkeypatch):
    request = operation()
    before = backend.checked_path().read_bytes()
    original = paid_beta.apply_event
    calls = []
    def observed(*args, **kwargs):
        calls.append(args[2])
        return original(*args, **kwargs)
    monkeypatch.setattr(paid_beta, 'apply_event', observed)
    prepared = workflow.prepare(console, request.pk)
    assert prepared.status == 'PREVIEWED' and calls == ['payment']
    assert prepared.preview['after']['status']['effective_state'] == 'active'
    assert backend.checked_path().read_bytes() == before and counts() == (0, 0)
    applied = workflow.execute(console, request.pk, workflow.confirmation_token(console, prepared))
    assert applied.status == 'APPLIED' and counts() == (1, 1) and calls == ['payment', 'payment']
    assert workflow.execute(console, request.pk, 'not-used-after-durable-application').status == 'APPLIED'
    assert counts() == (1, 1)
    assert applied.receipt['event']['event_id'] == request.event_id


@pytest.mark.parametrize('action', ['grace', 'expire', 'revoke'])
def test_management_actions_delegate_to_existing_state_machine(console, operation, action):
    initial = operation()
    assert apply_request(console, initial).status == 'APPLIED'
    changed = apply_request(console, operation(action=action))
    assert changed.status == 'APPLIED'
    state = backend.readback(initial.device_id)['status']
    assert state['effective_state'] == {'grace': 'grace', 'expire': 'expired', 'revoke': 'revoked'}[action]
    assert state['paid_allow'] == (action == 'grace')
    if action == 'revoke':
        rejected = workflow.prepare(console, operation().pk)
        assert rejected.status == 'REJECTED' and rejected.failure_code == 'REVOCATION_TERMINAL'
    assert counts() == (1, 2)


def test_changed_backend_requires_new_preview(console, operation):
    request = operation()
    prepared = workflow.prepare(console, request.pk)
    with backend.registry(write=True) as database:
        database.execute('UPDATE device_support SET version_code=84 WHERE device=?', (request.device_id,))
    result = workflow.execute(console, request.pk, workflow.confirmation_token(console, prepared))
    assert result.status == 'STALE' and result.failure_code == 'PREVIEW_STALE'
    assert counts() == (0, 0)


def test_expired_preview_cannot_dispatch(console, operation):
    request = workflow.prepare(console, operation().pk)
    request.preview['expires_at'] = int(time.time()) - 1
    request.save(update_fields=['preview'])
    result = workflow.execute(console, request.pk, workflow.confirmation_token(console, request))
    assert result.status == 'STALE' and counts() == (0, 0)


def test_tampered_token_and_different_operator_fail(console, operation):
    request = workflow.prepare(console, operation().pk)
    other = get_user_model().objects.create_superuser(username='other-synthetic', password=None)
    for actor, token in ((console, 'tampered'), (other, workflow.confirmation_token(console, request))):
        with pytest.raises(workflow.WorkflowError):
            workflow.execute(actor, request.pk, token)
    assert counts() == (0, 0)


def test_committed_backend_lost_receipt_is_reconciled_once(console, operation, monkeypatch):
    request = workflow.prepare(console, operation().pk)
    original = backend.execute
    def lost_receipt(*args):
        original(*args)
        raise ConnectionError('private-exception-not-for-audit')
    monkeypatch.setattr(backend, 'execute', lost_receipt)
    unknown = workflow.execute(console, request.pk, workflow.confirmation_token(console, request))
    assert unknown.status == 'UNKNOWN' and counts() == (1, 1)
    assert 'private-exception' not in json.dumps(list(AuditRecord.objects.values('details')))
    result = workflow.reconcile(console, request.pk)
    assert result.status == 'APPLIED' and result.receipt['duplicate'] and counts() == (1, 1)
    assert workflow.reconcile(console, request.pk).status == 'APPLIED'


def test_uncertain_without_receipt_never_automatically_retries(console, operation, monkeypatch):
    request = workflow.prepare(console, operation().pk)
    def unavailable(*args):
        raise OSError('offline')
    monkeypatch.setattr(backend, 'execute', unavailable)
    unknown = workflow.execute(console, request.pk, workflow.confirmation_token(console, request))
    with pytest.raises(workflow.WorkflowError, match='NO_RECEIPT_KEEP_UNCERTAIN'):
        workflow.reconcile(console, request.pk)
    with pytest.raises(workflow.WorkflowError):
        workflow.execute(console, unknown.pk, '')
    unknown.refresh_from_db()
    assert unknown.status == 'UNKNOWN' and counts() == (0, 0)


def test_projection_cannot_grant_entitlement_or_override_version(console, operation):
    device = DeviceProjection.objects.get(label='Synthetic 12')
    fake = dict(device.readback)
    fake['status'] = dict(cohort=True, effective_state='active', paid_allow=True)
    fake['version_observation']['version_code'] = 106
    DeviceProjection.objects.filter(pk=device.pk).update(readback=fake)
    result = workflow.prepare(console, operation(device=device).pk)
    assert result.status == 'REJECTED' and result.failure_code == 'ANDROID106_REQUIRED'
    assert counts() == (0, 0)
    restored = workflow.refresh(device.pk)
    assert not restored.readback['status']['cohort']


def test_cap_is_enforced_by_real_backend(console, operation):
    for number, device in enumerate(DeviceProjection.objects.exclude(label='Synthetic 12')):
        request = workflow.prepare(console, operation(device=device).pk)
        if number < 10:
            assert workflow.execute(console, request.pk, workflow.confirmation_token(console, request)).status == 'APPLIED'
        else:
            assert request.status == 'REJECTED' and request.failure_code == 'COHORT_LIMIT'
    assert counts() == (10, 10)


@pytest.mark.parametrize('target', ['audit_update', 'audit_delete', 'intent_update', 'intent_delete', 'payment_update', 'payment_delete'])
def test_postgresql_immutability_triggers(console, operation, target):
    request = operation()
    audit = AuditRecord.objects.first()
    with pytest.raises(DatabaseError), transaction.atomic():
        if target == 'audit_update':
            AuditRecord.objects.filter(pk=audit.pk).update(action='forged')
        elif target == 'audit_delete':
            AuditRecord.objects.filter(pk=audit.pk).delete()
        elif target == 'intent_update':
            OperationRequest.objects.filter(pk=request.pk).update(action='revoke')
        elif target == 'intent_delete':
            OperationRequest.objects.filter(pk=request.pk).delete()
        elif target == 'payment_update':
            PaymentRecord.objects.filter(pk=request.payment_id).update(amount_minor=1)
        else:
            with connection.cursor() as cursor:
                cursor.execute('DELETE FROM console_paymentrecord WHERE id=%s', [request.payment_id])
    assert OperationRequest.objects.get(pk=request.pk).action == 'activate'


def test_safe_receipts_and_audit_never_persist_support_id(console, operation):
    request = operation()
    with backend.registry() as database:
        alias = backend.selector(database, request.device_id)
    assert backend.lookup(alias) == request.device_id
    applied = apply_request(console, request)
    raw = json.dumps(dict(receipt=applied.receipt, audit=list(AuditRecord.objects.values('details'))))
    assert alias not in raw and 'synthetic-reference' not in raw
    assert len(applied.receipt['event']['reference_hash']) == 64


def test_empty_cohort_refresh_and_payment_metadata_preserve_registry(console, operation):
    before = backend.checked_path().read_bytes()
    workflow.refresh_all(console)
    operation()
    assert backend.checked_path().read_bytes() == before and counts() == (0, 0)


def test_duplicate_payment_reference_and_reconfirmation_cannot_double_apply(console):
    from django.core.exceptions import ValidationError
    values = dict(device=DeviceProjection.objects.first(), amount_minor=500, currency='EUR', reference='duplicate-synthetic-ref')
    payment = workflow.create_payment(console, **values)
    with pytest.raises(ValidationError):
        workflow.create_payment(console, **values)
    workflow.confirm_payment(console, payment.pk)
    workflow.confirm_payment(console, payment.pk)
    assert PaymentRecord.objects.count() == 1
    assert AuditRecord.objects.filter(action='payment.confirm').count() == 1
    assert counts() == (0, 0)


def test_backend_event_conflict_does_not_reconcile_as_applied(console, operation):
    request = workflow.prepare(console, operation().pk)
    with backend.registry(write=True) as database:
        other = workflow.intent(request) | {'reference': 'conflicting-opaque-reference'}
        backend.apply(database, other, int(time.time()))
    OperationRequest.objects.filter(pk=request.pk).update(status='UNKNOWN')
    with pytest.raises(backend.BackendError, match='EVENT_ID_CONFLICT'):
        workflow.reconcile(console, request.pk)
    request.refresh_from_db()
    assert request.status == 'UNKNOWN' and counts() == (1, 1)


def test_seed_is_idempotent_without_paid_or_identity_mutation(console, operation):
    from django.core.management import call_command
    apply_request(console, operation())
    before = backend.checked_path().read_bytes()
    call_command('seed_demo', verbosity=0)
    assert backend.checked_path().read_bytes() == before and counts() == (1, 1)


def test_viewer_cannot_prepare_execute_or_confirm(console, operation):
    request = operation()
    viewer = get_user_model().objects.create_user(username='viewer', is_staff=True)
    viewer.groups.add(Group.objects.get(name='Control-plane viewers'))
    for callback in (lambda: workflow.prepare(viewer, request.pk), lambda: workflow.execute(viewer, request.pk, ''),
                     lambda: workflow.confirm_payment(viewer, request.payment_id)):
        with pytest.raises(PermissionDenied):
            callback()
    assert counts() == (0, 0)


def test_missing_marker_and_symlink_rejected_without_paid_writes(console, monkeypatch, tmp_path):
    original = backend.ROOT
    fake = tmp_path / 'untrusted'
    fake.mkdir()
    with sqlite3.connect(fake / 'registry.sqlite3') as database:
        database.execute('CREATE TABLE devices(device TEXT)')
    monkeypatch.setattr(backend, 'ROOT', fake)
    with pytest.raises(backend.BackendError, match='SYNTHETIC_FIXTURE_REQUIRED'):
        backend.members()
    (fake / 'registry.sqlite3').unlink()
    (fake / 'registry.sqlite3').symlink_to(original / 'registry.sqlite3')
    with pytest.raises(backend.BackendError, match='SYNTHETIC_FIXTURE_REQUIRED'):
        backend.members()


@pytest.mark.django_db(transaction=True)
def test_concurrent_execute_keeps_one_backend_event(console, operation):
    request = workflow.prepare(console, operation().pk)
    token = workflow.confirmation_token(console, request)
    def run():
        close_old_connections()
        try:
            return workflow.execute(console, request.pk, token).status
        except workflow.WorkflowError:
            return 'IN_FLIGHT'
        finally:
            close_old_connections()
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: run(), range(2)))
    assert 'APPLIED' in results and set(results) <= {'APPLIED', 'IN_FLIGHT'}
    assert counts() == (1, 1)
