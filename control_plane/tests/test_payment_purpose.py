from datetime import timedelta
import uuid

from django.core.exceptions import ValidationError
from django.db import DatabaseError, IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.urls import reverse
from django.utils import timezone
import pytest

from apps.console import backend, workflow
from apps.console.forms import PaymentForm
from apps.console.models import AuditRecord, CohortMetadata, DeviceProjection, PaymentRecord
from apps.console.views import analytics_data


def create_record(actor, *, purpose='internal_canary', amount_minor=0):
    return workflow.create_payment(actor, device=DeviceProjection.objects.order_by('label').first(),
        purpose=purpose, amount_minor=amount_minor, currency='EUR', reference='synthetic-' + uuid.uuid4().hex)


def test_default_preserves_customer_payment_behavior(console):
    record = workflow.create_payment(console, device=DeviceProjection.objects.first(), amount_minor=500,
        currency='EUR', reference='synthetic-default-purpose')
    assert record.purpose == 'customer_payment'
    workflow.confirm_payment(console, record.pk)
    assert analytics_data()['confirmed_payments'] == 1
    assert analytics_data()['confirmed_internal_canary_records'] == 0


@pytest.mark.parametrize('purpose,amount', [('customer_payment', 0), ('customer_payment', -1),
    ('internal_canary', 1), ('internal_canary', -1), ('unrecognized', 0),
    ('customer_payment', None), ('internal_canary', 'invalid')])
def test_invalid_purpose_amount_rejected_by_model(console, purpose, amount):
    with pytest.raises(ValidationError):
        create_record(console, purpose=purpose, amount_minor=amount)
    assert not PaymentRecord.objects.exists()


@pytest.mark.parametrize('purpose,amount', [('customer_payment', 0), ('internal_canary', 500),
    ('unrecognized', 0)])
def test_raw_database_inserts_cannot_bypass_constraint(console, purpose, amount):
    with pytest.raises(IntegrityError), transaction.atomic():
        PaymentRecord.objects.create(device=DeviceProjection.objects.first(), created_by=console,
            purpose=purpose, amount_minor=amount, currency='EUR', reference_hash=uuid.uuid4().hex * 2)


@pytest.mark.parametrize('confirmed', [False, True])
def test_purpose_cannot_be_reclassified_even_before_confirmation(console, confirmed):
    record = create_record(console)
    if confirmed:
        workflow.confirm_payment(console, record.pk)
    with pytest.raises(DatabaseError, match='CONTROL_PLANE_'), transaction.atomic():
        PaymentRecord.objects.filter(pk=record.pk).update(purpose='customer_payment', amount_minor=500)
    record.refresh_from_db()
    assert record.purpose == 'internal_canary' and record.amount_minor == 0


def test_canary_metadata_confirmation_never_enrolls_or_counts_as_customer_payment(console):
    before = backend.checked_path().read_bytes()
    canary = create_record(console)
    pending = create_record(console)
    customer = create_record(console, purpose='customer_payment', amount_minor=500)
    workflow.confirm_payment(console, canary.pk)
    workflow.confirm_payment(console, canary.pk)
    workflow.confirm_payment(console, customer.pk)
    assert backend.checked_path().read_bytes() == before
    metrics = analytics_data()
    assert metrics['confirmed_payments'] == metrics['confirmed_internal_canary_records'] == 1
    assert PaymentRecord.objects.filter(confirmed_at__isnull=False).count() == 2
    assert PaymentRecord.objects.get(pk=pending.pk).confirmed_at is None
    audit = AuditRecord.objects.filter(target=str(canary.pk), action__startswith='payment.')
    assert audit.count() == 2
    assert all(row.details['purpose'] == 'internal_canary' and row.details['synthetic'] for row in audit)
    workflow.confirm_payment(console, pending.pk)
    assert analytics_data()['confirmed_internal_canary_records'] == 2
    assert analytics_data()['confirmed_payments'] == 1
    assert backend.checked_path().read_bytes() == before


@pytest.mark.parametrize('purpose,amount,valid', [('internal_canary', 0, True), ('internal_canary', 1, False),
    ('customer_payment', 500, True), ('customer_payment', 0, False), ('', 500, True), ('unknown', 0, False)])
def test_form_purpose_validation(console, purpose, amount, valid):
    form = PaymentForm(dict(device=DeviceProjection.objects.first().pk, purpose=purpose,
        amount_minor=amount, currency='EUR', reference='synthetic-purpose-form'))
    assert form.is_valid() is valid
    if valid:
        assert form.cleaned_data['purpose'] == (purpose or 'customer_payment')


def test_synthetic_canary_activation_uses_unchanged_backend_event_and_idempotency(console, client):
    record = create_record(console)
    workflow.confirm_payment(console, record.pk)
    CohortMetadata.objects.create(device=record.device, owner=console, opted_in=True, handoff_verified=True)
    now = timezone.now().replace(microsecond=0)
    request = workflow.create_operation(console, dict(device=record.device, action='activate', payment=record,
        period_start=now - timedelta(seconds=60), paid_until=now + timedelta(hours=1)))
    prepared = workflow.prepare(console, request.pk)
    token = workflow.confirmation_token(console, prepared)
    result = workflow.execute(console, request.pk, token)
    assert result.status == 'APPLIED' and result.receipt['event']['event_type'] == 'payment'
    assert 'purpose' not in result.receipt['event']
    workflow.execute(console, request.pk, token)
    with backend.registry() as database:
        assert database.execute('SELECT count(*) FROM paid_beta_subscriptions').fetchone()[0] == 1
        assert database.execute('SELECT count(*) FROM paid_beta_events').fetchone()[0] == 1
    assert analytics_data()['confirmed_payments'] == 0
    assert analytics_data()['confirmed_internal_canary_records'] == 1
    client.force_login(console)
    receipt = client.get(reverse('console:receipt', args=[request.pk])).json()
    assert receipt['payment_purpose'] == 'internal_canary'
    assert receipt['receipt'] == result.receipt
    assert 'не оплата клиента и не выручка' in client.get(reverse('console:operation', args=[request.pk])).content.decode()


def test_canary_form_and_admin_are_explicit_and_synthetic(console, client):
    client.force_login(console)
    response = client.post('/payments/new/', dict(device=DeviceProjection.objects.first().pk,
        purpose='internal_canary', amount_minor=0, currency='EUR', reference='synthetic-ui-purpose'))
    assert response.status_code == 302
    record = PaymentRecord.objects.get()
    detail = client.get(response.url).content.decode()
    assert 'ДЕМО' in detail and 'не оплата клиента и не выручка' in detail
    assert 'Внутренняя проверка (canary)' in client.get('/payments/').content.decode()
    assert client.get('/admin/console/paymentrecord/?purpose=internal_canary').status_code == 200
    assert client.post(f'/admin/console/paymentrecord/{record.pk}/change/',
        {'purpose': 'customer_payment'}).status_code == 403


@pytest.mark.django_db(transaction=True)
def test_migration_preserves_existing_confirmed_payment_rows(console):
    record = create_record(console, purpose='customer_payment', amount_minor=500)
    workflow.confirm_payment(console, record.pk)
    old_target = [('console', '0005_observations_immutable')]
    new_target = [('console', '0006_payment_purpose')]
    executor = MigrationExecutor(connection)
    try:
        executor.migrate(old_target)
        old_model = executor.loader.project_state(old_target).apps.get_model('console', 'PaymentRecord')
        before = old_model.objects.filter(pk=record.pk).values().get()
        executor = MigrationExecutor(connection)
        executor.migrate(new_target)
        new_model = executor.loader.project_state(new_target).apps.get_model('console', 'PaymentRecord')
        after = new_model.objects.filter(pk=record.pk).values().get()
        assert after.pop('purpose') == 'customer_payment'
        assert after == before
        MigrationExecutor(connection).migrate(new_target)
        assert new_model.objects.filter(pk=record.pk).count() == 1
    finally:
        MigrationExecutor(connection).migrate(new_target)
