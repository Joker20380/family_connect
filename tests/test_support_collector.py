import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import time

import pytest

from provisioning.support_bindings import collect


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
