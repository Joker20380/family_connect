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
if sys.argv[1:] == ['up', 'fcawg11111111']:
    import signal
    os.kill(os.getppid(), signal.SIGKILL)
if sys.argv[1:] == ['up', 'fcawg22222222']:
    import time
    time.sleep(10)
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
original_run = backend.subprocess.run
def bounded_run(args, **kwargs):
    if args[-1] == 'fcawg22222222': kwargs['timeout'] = .05
    return original_run(args, **kwargs)
backend.subprocess.run = bounded_run
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


@pytest.mark.parametrize('kind', ['awg', 'tcp'])
def test_reserved_helper_receipt_not_error_text_classifies_prestart(kind):
    from types import SimpleNamespace
    request = dict(kind=kind,action='up',ident='fc'+kind+'12345678',data=None)
    receipt = backend.pre_start_receipt(backend.PreStartRejected('TRANSPORT_BUSY'))
    result = SimpleNamespace(returncode=backend.PRE_START_EXIT,stdout=json.dumps(receipt))
    reply = backend._helper_reply(request,result)
    backend._validate_session_reply(reply)
    assert reply == dict(schema=2,outcome='PRE_START_REJECTED',reason='TRANSPORT_BUSY',value='')
    result.returncode = 1
    assert backend._helper_reply(request,result)['outcome'] == 'OUTCOME_UNKNOWN'


@pytest.mark.parametrize('change', [{'schema':True},{'schema':1},{'outcome':'safe'}, {'reason':'arbitrary'},
                                  {'value':'secret'},{'outcome':[]},{'extra':'field'}])
def test_unknown_or_malformed_receipts_fail_closed(change):
    reply=dict(schema=2,outcome='PRE_START_REJECTED',reason='TRANSPORT_BUSY',value='')
    reply.update(change)
    with pytest.raises(ValueError):backend._validate_session_reply(reply)


def test_non_start_cannot_claim_prestart():
    from types import SimpleNamespace
    receipt=json.dumps(backend.pre_start_receipt(backend.PreStartRejected('TRANSPORT_BUSY')))
    result=SimpleNamespace(returncode=backend.PRE_START_EXIT,stdout=receipt)
    assert backend._helper_reply(dict(kind='awg',action='discard'),result)['outcome']=='OUTCOME_UNKNOWN'


def test_discard_is_fixed_owned_profile_only():
    assert backend._session_request(dict(kind='awg',action='discard',ident='fcawg12345678',data=None))[0] == [backend._SESSION_HELPERS['awg'],'discard','fcawg12345678']
    for kind in ('mesh','auto','chat'):
        with pytest.raises(ValueError):backend._session_request(dict(kind=kind,action='discard',ident='fcawg12345678',data=None))


@pytest.mark.parametrize('kind', ['awg', 'tcp'])
def test_recovery_sends_down_even_when_tun_is_already_absent(monkeypatch, kind):
    driver = backend.LinuxTCP()
    calls = []
    monkeypatch.setattr(driver, '_'+kind, lambda action, ident: calls.append((action, ident)))
    monkeypatch.setattr(driver, 'active', lambda _: False)
    driver.rollback_imported('fc'+kind+'12345678')
    assert calls == [('down', 'fc'+kind+'12345678')]


@pytest.mark.parametrize('kind', ['awg', 'tcp'])
@pytest.mark.parametrize('unsafe', [None, 'owner', 'paired', 'marker', 'malformed', 'link', 'mode', 'hardlink'])
def test_discard_requires_owned_unpaired_inactive_safe_files(tmp_path, monkeypatch, kind, unsafe):
    identifier = 'fc'+kind+'12345678'
    root = tmp_path/'etc/family-connect'/kind
    root.mkdir(parents=True)
    metadata, profile = root/(identifier+'.json'), root/(identifier+'.conf')
    metadata.write_text(json.dumps(dict(id=identifier, owner=1001 if unsafe == 'owner' else 1000,
                                       primary='paired' if unsafe == 'paired' else None)))
    metadata.chmod(0o644)
    profile.write_bytes(b'synthetic')
    profile.chmod(0o644 if unsafe == 'mode' else 0o600)
    if unsafe == 'hardlink':os.link(profile, root/'foreign')
    if unsafe == 'link':
        profile.rename(root/'foreign')
        profile.symlink_to(root/'foreign')
    if unsafe in ('marker', 'malformed'):
        marker = tmp_path/('run/family-connect-'+kind)/('active.json' if kind == 'awg' else 'active')
        marker.parent.mkdir(parents=True)
        marker.write_text(json.dumps(dict(id=identifier) if unsafe == 'marker' else {}))
        marker.chmod(0o600)
    original_stat = os.fstat
    def root_stat(descriptor):
        values = list(original_stat(descriptor));values[4] = 0
        return os.stat_result(values)
    monkeypatch.setattr(backend.os, 'geteuid', lambda: 0)
    monkeypatch.setattr(backend.os, 'fstat', root_stat)
    monkeypatch.setattr(backend, 'Path', lambda *parts: tmp_path/str(Path(*parts)).lstrip('/'))
    monkeypatch.setattr(backend, 'run', lambda *args: 'inactive')
    if unsafe:
        with pytest.raises((ValueError, backend.BackendError, OSError)):
            backend.discard_inactive_profile(kind, identifier, 1000)
        assert metadata.exists() and profile.exists()
    else:
        backend.discard_inactive_profile(kind, identifier, 1000)
        assert not metadata.exists() and not profile.exists()
        backend.discard_inactive_profile(kind, identifier, 1000)


@pytest.mark.parametrize(('ident','reason'), [('fcawg11111111','CHANNEL_LOST'),('fcawg22222222','HELPER_TIMEOUT')])
def test_real_pipe_loss_and_process_timeout_remain_unknown(session_process, ident, reason):
    calls, log = session_process
    with backend.authorization_operation():
        with pytest.raises(backend.RecoveryRequired) as caught:backend.Linux()._awg('up',ident)
        assert caught.value.outcome == 'OUTCOME_UNKNOWN' and caught.value.reason == reason
    assert len(calls) == 1
    assert [json.loads(line)[0] for line in log.read_text().splitlines()] == [['up',ident]]
