import json

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client
from django.urls import reverse
import pytest

from apps.console import backend, workflow
from apps.console.forms import OperationForm, PaymentForm, UTCInstant
from apps.console.models import CohortMetadata, DeviceProjection, OperationRequest


@pytest.mark.parametrize('path', ['/', '/devices/', '/payments/', '/operations/', '/audit/', '/releases/', '/analytics.json'])
def test_authentication_required(console, client, path):
    result = client.get(path)
    assert result.status_code == 302 and '/admin/login/' in result.url


@pytest.mark.parametrize('path', ['/', '/devices/', '/payments/', '/operations/', '/audit/', '/releases/', '/analytics.json', '/admin/'])
def test_staff_pages_are_local_and_synthetic(console, client, path):
    client.force_login(console)
    result = client.get(path)
    assert result.status_code == 200
    assert result['Cache-Control'] == 'no-store'
    assert "default-src 'self'" in result['Content-Security-Policy']
    if path != '/analytics.json':
        assert b'SYNTHETIC' in result.content


def test_csrf_and_no_get_mutations(console, operation):
    request = operation()
    client = Client(enforce_csrf_checks=True)
    client.force_login(console)
    for name in ('preview', 'execute', 'reconcile'):
        url = reverse('console:' + name, args=[request.pk])
        assert client.get(url).status_code == 405
        assert client.post(url).status_code == 403
    request.refresh_from_db()
    assert request.status == 'DRAFT'


def test_login_keeps_same_origin_csrf_protection(console):
    client = Client(enforce_csrf_checks=True)
    page = client.get('/admin/login/?next=/')
    assert page['Referrer-Policy'] == 'same-origin'
    token = client.cookies['csrftoken'].value
    result = client.post('/admin/login/?next=/', dict(username=console.username,
        password='synthetic-test-password-only', csrfmiddlewaretoken=token, next='/'), HTTP_ORIGIN='http://testserver')
    assert result.status_code == 302 and result.url == '/'
    assert client.get('/').status_code == 200
    assert client.post('/devices/refresh/', {'csrfmiddlewaretoken': token}, HTTP_ORIGIN='null').status_code == 403


def test_operator_ui_lifecycle_and_receipt(console, client, operation):
    client.force_login(console)
    request = operation()
    assert client.get(reverse('console:operation', args=[request.pk])).status_code == 200
    assert client.post(reverse('console:preview', args=[request.pk])).status_code == 302
    request.refresh_from_db()
    token = workflow.confirmation_token(console, request)
    assert client.post(reverse('console:execute', args=[request.pk]), {'token': token, 'confirmed': 'on'}).status_code == 302
    request.refresh_from_db()
    assert request.status == 'APPLIED'
    receipt = client.get(reverse('console:receipt', args=[request.pk])).json()
    assert receipt['receipt']['event']['event_id'] == request.event_id
    with backend.registry() as database:
        alias = backend.selector(database, request.device_id)
    assert alias not in json.dumps(receipt)
    response = client.post('/devices/', {'selector': alias})
    assert response.status_code == 302 and alias not in response.url


def test_admin_cannot_edit_projections_or_authoritative_like_receipts(console, client, operation):
    client.force_login(console)
    request = operation()
    for model, key in [('deviceprojection', request.device_id), ('operationrequest', request.pk), ('paymentrecord', request.payment_id)]:
        assert client.get(f'/admin/console/{model}/add/').status_code == 403
        assert client.post(f'/admin/console/{model}/{key}/change/', {'status': 'APPLIED'}).status_code == 403


def test_nonstaff_and_viewer_permissions(console, client, operation):
    request = operation()
    for is_staff in (False, True):
        user = get_user_model().objects.create_user(username='viewer-' + str(is_staff), is_staff=is_staff)
        user.groups.add(Group.objects.get(name='Control-plane viewers'))
        client.force_login(user)
        assert client.get('/').status_code == (200 if is_staff else 403)
        assert client.post(reverse('console:preview', args=[request.pk])).status_code == 403
        assert client.get('/operations/new/').status_code == 403


def test_analytics_never_fabricates_live_rates_or_recalculates_paid_state(console, client):
    client.force_login(console)
    data = client.get('/analytics.json').json()
    assert data['live_crash_rate'] is None and data['live_mesh_success_rate'] is None
    assert data['states'] == {'non-cohort': 12}
    assert len(data['daily']) == 7 and 'read-only projections' in data['scope']


@pytest.mark.parametrize('value', ['2027-01-01T12:00:00', '2027-01-01T12:00:00+02:00', '2027-01-01T12:00:00.1Z'])
def test_local_time_is_not_accepted(value):
    from django.core.exceptions import ValidationError
    with pytest.raises(ValidationError):
        UTCInstant().clean(value)


def test_payment_form_has_no_raw_financial_fields(console):
    assert set(PaymentForm().fields) == {'device', 'amount_minor', 'currency', 'reference'}
    device = DeviceProjection.objects.first()
    form = PaymentForm(dict(device=device.pk, amount_minor=100, currency='EUR', reference='FC-2222-2222'))
    assert not form.is_valid()
    form = OperationForm(dict(device=device.pk, action='revoke', paid_until='2027-01-01T00:00:00Z'))
    assert not form.is_valid()


def test_metadata_is_required_and_never_itself_enrolls(console, operation):
    request = operation()
    CohortMetadata.objects.filter(device=request.device).update(opted_in=False)
    with pytest.raises(workflow.WorkflowError, match='OPT_IN'):
        workflow.prepare(console, request.pk)
    with backend.registry() as database:
        assert database.execute('SELECT count(*) FROM paid_beta_subscriptions').fetchone()[0] == 0
    assert OperationRequest.objects.get(pk=request.pk).status == 'DRAFT'
