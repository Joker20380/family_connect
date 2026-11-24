import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import time
import os
import subprocess
import sys

import pytest

from provisioning.support_bindings import collect
from tests.test_paid_beta import registry, event


def test_pinned_bounded_reader_installs_only_fresh_private_lease(tmp_path, monkeypatch):
    key, hosts, output = [tmp_path / name for name in ('ssh.key', 'known_hosts', 'lease.json')]
    key.write_text('synthetic-not-a-key')
    key.chmod(0o600)
    hosts.write_text('synthetic-pinned-host')
    document = dict(expires_at=int(time.time()) + 100)
    calls = []

    def run(command, **options):
        calls.append(command)
        options['stdout'].write(json.dumps(document).encode())
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr('provisioning.support_bindings.subprocess.run', run)
    collect('127.0.0.1', key, hosts, output)
    assert json.loads(output.read_bytes()) == document
    assert output.stat().st_mode & 0o777 == 0o640
    assert calls[0][-2:] == ['root@127.0.0.1', 'support-bindings']
    assert 'StrictHostKeyChecking=yes' in calls[0]
    assert 'UserKnownHostsFile='+str(hosts) in calls[0]
    before = output.read_bytes()
    document['expires_at'] -= 200
    with pytest.raises(ValueError):
        collect('127.0.0.1', key, hosts, output)
    assert output.read_bytes() == before
    with pytest.raises(ValueError):
        collect('127.0.0.1;anything', key, hosts, output)
    key.chmod(0o644)
    with pytest.raises(ValueError):
        collect('127.0.0.1', key, hosts, output)


def test_forced_reader_rejects_stale_public_and_linked_files(tmp_path):
    path = Path(__file__).resolve().parents[1] / 'deploy/friends/support-bindings-read.py'
    spec = importlib.util.spec_from_file_location('support_reader', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    snapshot = tmp_path / 'snapshot'
    snapshot.write_text(json.dumps(dict(expires_at=int(time.time()) + 100)))
    snapshot.chmod(0o600)
    assert module.read(snapshot) == snapshot.read_bytes()
    snapshot.chmod(0o644)
    with pytest.raises(ValueError):
        module.read(snapshot)
    snapshot.chmod(0o600)
    link = tmp_path / 'link'
    link.symlink_to(snapshot)
    with pytest.raises(OSError):
        module.read(link)
    snapshot.write_text(json.dumps(dict(expires_at=int(time.time()) - 1)))
    with pytest.raises(ValueError):
        module.read(snapshot)


def test_forced_subscription_reader_runs_isolated_without_write_authority(registry):
    from control.friends.chat import ChatAccess
    from control.friends.subscription_events import digest
    root = registry[0].path.parent
    ChatAccess(registry[0]).initialize()
    event(registry)
    source_root = Path(__file__).resolve().parents[1]
    reader = root / 'reader.py'
    reader.write_text((source_root / 'deploy/friends/support-bindings-read.py').read_text().replace(
        '/opt/apps/family_connect/friends-access', str(root)))
    (root / 'subscription_events.py').write_bytes((source_root / 'control/friends/subscription_events.py').read_bytes())
    (root / 'subscription_events.py').chmod(0o644)
    key = root / 'support-inventory-hmac.key'
    key.write_bytes(b'h'*32)
    key.chmod(0o600)
    before = registry[0].path.read_bytes()
    def call(command):
        return subprocess.run([sys.executable, '-I', str(reader)], capture_output=True, timeout=10,
            env=dict(os.environ, SSH_ORIGINAL_COMMAND=command))
    first = call('subscription-notifications -1 none')
    assert first.returncode == 0, first.stderr.decode()
    value = json.loads(first.stdout)
    assert value['baseline_count'] == 1 and value['events'] == []
    page = call('subscription-notifications 0 ' + digest(None))
    assert page.returncode == 0
    assert json.loads(page.stdout)['events'][0]['result'] == 'APPLIED'
    assert call('subscription-notifications -1 none; arbitrary').returncode == 1
    assert call('subscription-notifications 1 ' + '0'*64).returncode == 1
    assert registry[0].path.read_bytes() == before
