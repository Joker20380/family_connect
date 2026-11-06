import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from scripts import ci_android_fixture as android
from scripts import ci_pytest_context as contexts


@pytest.mark.parametrize('nodeid,expected', [
    ('tests/test_profile_store.py::test_owner[one]', 'root'),
    ('tests/test_profile_snapshot.py::test_snapshot', 'root'),
    ('tests/test_restricted_maintenance.py::test_owner', 'root'),
    ('tests/test_gateway_credential_publication.py::IsolatedRootTests::test_owner', 'root'),
    ('tests/test_gateway_credential_publication.py::PublicationTests::test_owner', 'standard'),
    ('tests/test_profile_snapshot_launcher.py::test_executable', 'snapshot314'),
    ('tests/test_device_identity.py::test_private', 'standard'),
])
def test_explicit_context_partition(nodeid, expected):
    assert contexts.context(nodeid) == expected


def test_umask_changes_are_isolated_without_changing_test_permissions(tmp_path):
    (tmp_path / 'test_masks.py').write_text('import os\n'
        'def test_first():\n    os.umask(0o077)\n'
        'def test_second():\n    assert os.umask(0o022) == 0o022\n')
    subprocess.run([sys.executable, '-m', 'pytest', '-q', '-p', 'scripts.ci_pytest_context',
                    str(tmp_path / 'test_masks.py')], cwd=android.ROOT,
                   env=dict(os.environ), check=True, capture_output=True,
                   umask=0o022, timeout=20)


def test_android_historical_snapshot_matches_the_committed_transition(tmp_path):
    relative = 'clients/android/app/src/main/python/fc_rns_transport.py'
    target = tmp_path / relative
    target.parent.mkdir(parents=True)
    shutil.copyfile(android.source('bridge95'), target)
    subprocess.run(['git', 'apply', '--include=' + relative,
                    str(android.ROOT / 'tests/fixtures/mobile_bootstrap/beta95-to-beta96.patch')],
                   cwd=tmp_path, check=True, capture_output=True)
    assert target.read_bytes() == android.source('bridge96').read_bytes()
    assert hashlib.sha256(android.source('bridge103').read_bytes()).hexdigest() == android.SOURCES['bridge103'][1]


def test_android_fixture_rejects_substitution(tmp_path, monkeypatch):
    monkeypatch.setattr(android, 'ROOT', tmp_path)
    relative, expected = android.SOURCES['bridge95']
    path = tmp_path / relative
    path.parent.mkdir(parents=True)
    path.write_bytes(b'substituted source')
    with pytest.raises(ValueError, match='fixture mismatch'):
        android.source('bridge95')
