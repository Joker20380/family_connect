from datetime import timedelta
import shutil
import uuid

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone
import pytest

from apps.console import backend, workflow
from apps.console.models import CohortMetadata, DeviceProjection


@pytest.fixture(scope='session')
def template_registry(tmp_path_factory):
    original = backend.ROOT
    backend.ROOT = tmp_path_factory.mktemp('synthetic-template')
    try:
        backend.seed_fixture()
        return backend.ROOT / 'registry.sqlite3'
    finally:
        backend.ROOT = original


@pytest.fixture
def fixture_registry(tmp_path, monkeypatch, template_registry):
    root = tmp_path / 'synthetic'
    root.mkdir()
    shutil.copyfile(template_registry, root / 'registry.sqlite3')
    monkeypatch.setattr(backend, 'ROOT', root)
    return root


@pytest.fixture
def console(db, fixture_registry, settings):
    settings.ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1']
    settings.PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
    settings.STORAGES = {'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
                        'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'}}
    call_command('seed_demo', verbosity=0)
    actor = get_user_model().objects.create_superuser(username='synthetic-operator', password='synthetic-test-password-only')
    return actor


@pytest.fixture
def operation(console):
    def create(action='activate', device=None):
        device = device or DeviceProjection.objects.order_by('label').first()
        CohortMetadata.objects.get_or_create(device=device, defaults=dict(owner=console, opted_in=True, handoff_verified=True))
        now = timezone.now().replace(microsecond=0)
        values = dict(device=device, action=action, payment=None, period_start=None, paid_until=None, grace_until=None)
        if action == 'activate':
            payment = workflow.create_payment(console, device=device, amount_minor=500, currency='EUR', reference='synthetic-' + uuid.uuid4().hex)
            workflow.confirm_payment(console, payment.pk)
            values.update(payment=payment, period_start=now - timedelta(seconds=60), paid_until=now + timedelta(hours=1))
        elif action == 'grace':
            values['grace_until'] = now + timedelta(hours=2)
        return workflow.create_operation(console, values)
    return create
