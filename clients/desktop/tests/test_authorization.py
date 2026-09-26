"""Real pipe/process lifecycle without polkit, root, or host network mutation."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import backend


@pytest.fixture
def session_process(monkeypatch, tmp_path):
    log = tmp_path/'operations.jsonl'
    helper = tmp_path/'helper'
    helper.write_text('#!'+sys.executable+'\n'+f'''
import json, os, sys
with open({str(log)!r}, 'a') as out:
    out.write(json.dumps([sys.argv[1:], os.environ['PKEXEC_UID']])+'\\n')
if sys.argv[1] == 'import':
    sys.stdin.read()
    print('fcawg12345678')
if sys.argv[1:] == ['up', 'fcawg00000000']:
    sys.exit(1)
''')
    helper.chmod(0o700)
    harness = tmp_path/'server.py'
    harness.write_text(f'''
import os, sys
sys.path.insert(0, {str(Path(backend.__file__).parent)!r})
import backend
backend.os.geteuid = lambda: 0
backend._SESSION_HELPERS = {{'awg': {str(helper)!r}, 'tcp': {str(helper)!r}}}
os.environ['PKEXEC_UID'] = '1234'
backend.privileged_session()
''')
    original = subprocess.Popen
    calls = []
    def launch(args, **kwargs):
        assert args[0] == 'pkexec'
        assert args[1] in backend._SESSION_HELPERS.values()
        assert args[2:] == ['session']
        process = original([sys.executable, str(harness)], **kwargs)
        calls.append(process)
        return process
    monkeypatch.setattr(backend, '_authorization_available', lambda helper: True)
    monkeypatch.setattr(backend.subprocess, 'Popen', launch)
    return calls, log


def test_one_prompt_for_import_switch_and_rollback(session_process):
    calls, log = session_process
    driver = backend.LinuxTCP()
    with backend.authorization_operation():
        ident = driver._awg('import', data='synthetic profile')
        with backend.authorization_operation():
            driver._tcp('down', 'fctcp12345678')
            with pytest.raises(backend.BackendError):
                driver._awg('up', 'fcawg00000000')
            driver._awg('down', ident)
            driver._tcp('up', 'fctcp12345678')
    assert len(calls) == 1
    assert calls[0].poll() == 0
    records = [json.loads(line) for line in log.read_text().splitlines()]
    assert len(records) == 5
    assert all(uid == '1234' for _, uid in records)
    # A later user action must authenticate again.
    with backend.authorization_operation():
        driver._tcp('down', 'fctcp12345678')
    assert len(calls) == 2


def test_denial_does_not_reprompt_or_mutate(monkeypatch, tmp_path):
    original = subprocess.Popen
    calls = []
    def denied(args, **kwargs):
        calls.append(args)
        return original([sys.executable, '-c', 'raise SystemExit(126)'], **kwargs)
    monkeypatch.setattr(backend, '_authorization_available', lambda helper: True)
    monkeypatch.setattr(backend.subprocess, 'Popen', denied)
    with backend.authorization_operation():
        for _ in range(3):
            with pytest.raises(backend.AuthorizationError):
                backend.Linux()._awg('import', data='synthetic')
    assert len(calls) == 1


@pytest.mark.parametrize('changes', [
    {'kind': '/tmp/executable'}, {'action': 'serve'}, {'action': 'cleanup'},
    {'action': 'pair'}, {'ident': '../../etc/passwd'}, {'ident': 'fctcp12345678'},
    {'data': 'unexpected'}, {'extra': 'argument'},
])
def test_session_rejects_expanded_privileges(changes):
    request = dict(kind='awg', action='up', ident='fcawg12345678', data=None)
    request.update(changes)
    with pytest.raises(ValueError):
        backend._session_request(request)


def test_eof_and_deadline_are_bounded():
    read, write = os.pipe()
    with os.fdopen(read, 'rb', buffering=0) as source:
        with pytest.raises(backend.BackendError):
            backend._session_line(source, time.monotonic()-.1)
        os.close(write)
        with pytest.raises(EOFError):
            backend._session_line(source, time.monotonic()+1)


def test_no_privilege_when_unused_or_old_helper(monkeypatch):
    monkeypatch.setattr(backend, '_authorization_available', lambda helper: False)
    def unexpected(*args, **kwargs):
        pytest.fail('Must not start pkexec')
    monkeypatch.setattr(backend.subprocess, 'Popen', unexpected)
    with backend.authorization_operation():
        pass
    with backend.authorization_operation():
        with pytest.raises(backend.BackendError, match='Update'):
            backend.Linux()._awg('import', data='synthetic')


def test_exception_closes_privilege(session_process):
    calls, _ = session_process
    with pytest.raises(RuntimeError):
        with backend.authorization_operation():
            backend.Linux()._awg('down', 'fcawg12345678')
            raise RuntimeError('application failed')
    assert calls[0].poll() == 0
    assert backend._operation_local.authorization is None
