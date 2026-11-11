import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile

import pytest

from scripts.package_support_chat import ROOT, archive, build


def test_support_ci_review_command_is_owner_only_and_source_bound():
    workflow = (ROOT / '.github/workflows/control-panel.yml').read_text()
    assert 'pull_request_review:\n    types: [submitted]' in workflow
    assert 'pull_request_target' not in workflow
    assert 'permissions:\n  contents: read' in workflow
    for clause in ("github.event.review.state == 'commented'",
                   "github.event.review.body == '/qualify-support-candidate'",
                   'github.event.review.user.login == github.repository_owner',
                   'github.event.pull_request.head.repo.full_name == github.repository'):
        assert workflow.count(clause) == 3
    assert workflow.count('ref: ${{ env.SUPPORT_SOURCE_SHA }}') == 3
    assert "github.event.pull_request.head.sha || github.sha" in workflow
    assert '--source-commit "$SUPPORT_SOURCE_SHA"' in workflow
    assert workflow.count("github.event.review.body == '/qualify-system-messages'") == 1
    assert "github.event.review.body == '/qualify-system-messages'" in workflow.split('\n  panel:\n')[1]


def test_closed_support_kit_imports_outside_checkout_and_is_reproducible(tmp_path):
    output = tmp_path / 'kit'
    hashes = build(output)
    assert hashes['app/provisioning/support_worker.py'] == hashlib.sha256(
        (ROOT / 'provisioning/support_worker.py').read_bytes()).hexdigest()
    assert 'registry/http/friends-http.pyz' in hashes
    assert not any(name.endswith(('.key', '.db', '.env')) or 'state' in Path(name).parts for name in hashes)
    environment = dict(os.environ, PYTHONPATH=str(output / 'app'), PYTHONDONTWRITEBYTECODE='1')
    for module in ('provisioning.support_worker', 'provisioning.support_bindings'):
        result = subprocess.run([sys.executable, '-m', module, '--help'], cwd=tmp_path,
                                env=environment, capture_output=True, timeout=15)
        assert result.returncode == 0, result.stderr.decode()
    first, second = tmp_path / 'first.tar.gz', tmp_path / 'second.tar.gz'
    archive(output, first)
    archive(output, second)
    assert first.read_bytes() == second.read_bytes()
    with tarfile.open(first) as packaged:
        assert set(packaged.getnames()) == set(hashes) | {'sha256.json'}
        assert all(entry.isfile() and entry.mode == 0o644 for entry in packaged.getmembers())


def test_web_overlay_exposes_only_socket_and_preserves_existing_volumes():
    if shutil.which('docker') is None:
        pytest.skip('Compose integration requires Docker CLI, not a running daemon')
    environment = dict(os.environ, FC_SUPPORT_IPC_GID='19001',
                       POSTGRES_PASSWORD='synthetic-compose-test', DJANGO_SECRET_KEY='synthetic-compose-test')
    command = ['docker', 'compose', '-f', str(ROOT / 'control_plane/compose.yaml'), '-f',
               str(ROOT / 'deploy/support-chat/panel.override.yaml'), 'config', '--format', 'json']
    result = subprocess.run(command, env=environment, capture_output=True, check=True, timeout=15)
    overlay = json.loads(result.stdout)
    console = overlay['services']['console']
    assert console['environment']['FC_SUPPORT_SOCKET'] == '/run/family-connect-support/worker.sock'
    assert console['group_add'] == ['19001']
    assert len(console['volumes']) == 2
    assert any(mount['type'] == 'volume' and mount['source'] == 'synthetic_state' for mount in console['volumes'])
    mount, = [mount for mount in console['volumes'] if mount['type'] == 'bind']
    assert mount['source'] == mount['target'] == '/run/family-connect-support'
    assert mount['read_only'] and not mount.get('bind', {}).get('create_host_path', False)
    assert set(overlay['volumes']) == {'postgres_data', 'synthetic_state'}
