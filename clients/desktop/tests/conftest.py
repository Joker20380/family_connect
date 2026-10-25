"""Keep operation-coordination tests off the user's actual client state."""
import sys
from pathlib import Path

import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import backend


@pytest.fixture(params=['awg', 'tcp'])
def normal_owner(request, monkeypatch):
    import threading
    from types import SimpleNamespace

    transport = request.param
    ident = 'fc'+transport+'12345678'
    owner = SimpleNamespace(ident=ident, active=True, downs=[], block_at=None, read_error=False,
                            entered=threading.Event(), release=threading.Event())
    owner.driver = backend.Linux() if transport == 'awg' else backend.LinuxTCP()
    records = {ident: dict(primary=None, endpoint='192.0.2.1')}
    monkeypatch.setattr(owner.driver, '_awg_records', lambda: records if transport == 'awg' else {})
    if transport == 'tcp':
        monkeypatch.setattr(owner.driver, '_tcp_records', lambda: records)
    original_exists = Path.exists

    def barrier(stage):
        if owner.block_at == stage and threading.current_thread().name.startswith('fc-poll'):
            owner.entered.set()
            assert owner.release.wait(5), 'Poll barrier was not released'
            if owner.read_error:
                raise backend.BackendError('Read changed during observation')

    def exists(path):
        if str(path) == '/sys/class/net/'+ident:
            barrier('active')
            return owner.active
        return original_exists(path)

    def run(*arguments, **kwargs):
        if arguments[0] == 'nmcli':
            barrier('profiles')
            return ''
        if arguments[0] == 'curl' or arguments[0] == '/usr/bin/curl':
            barrier('health')
            return '192.0.2.1'
        raise AssertionError('Unexpected external command')

    def helper(action, profile=None, data=None):
        assert action == 'down' and profile == ident and data is None
        owner.downs.append(profile)
        owner.active = False

    monkeypatch.setattr(Path, 'exists', exists)
    monkeypatch.setattr(backend, 'run', run)
    monkeypatch.setattr(owner.driver, '_'+transport, helper)
    yield owner
    owner.release.set()


@pytest.fixture(autouse=True)
def isolated_operations(tmp_path,monkeypatch):
    monkeypatch.setattr(backend,'operation_directory',lambda:tmp_path/'operations')
