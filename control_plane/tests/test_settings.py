import os
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.parametrize('change', [dict(CONTROL_PLANE_MODE='production'), dict(POSTGRES_HOST='unapproved.example'),
                                  dict(DJANGO_SECRET_KEY='short'), dict(POSTGRES_PASSWORD='short')])
def test_unsafe_configuration_is_rejected_before_connections(change):
    environment = dict(os.environ) | change
    result = subprocess.run([sys.executable, '-c', 'import fc_control_plane.settings'], env=environment, capture_output=True)
    assert result.returncode != 0 and b'ImproperlyConfigured' in result.stderr


def test_subtree_has_no_production_registry_or_subscription_orm():
    root = Path(__file__).resolve().parents[1]
    backend = (root / 'apps/console/backend.py').read_text()
    assert 'os.environ' not in backend
    assert "ROOT = settings.BASE_DIR / '.local' / 'synthetic'" in backend
    models = (root / 'apps/console/models.py').read_text()
    assert 'class Subscription' not in models and 'paid_beta_subscriptions' not in models
