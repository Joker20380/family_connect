import json
from types import SimpleNamespace

import pytest

from scripts import owner_android_support as support


def test_no_injection_and_exact_routing(monkeypatch):
    calls=[]
    def run(args,**kwargs):
        calls.append((args,kwargs))
        return SimpleNamespace(returncode=0,stdout=b'Result: Bundle[{result=NEXT_SESSION_P0}]',stderr=b'')
    monkeypatch.setattr(support.subprocess,'run',run)
    assert support.command('owner','profile','P0')=='NEXT_SESSION_P0'
    assert calls[0][0]==['adb','-s','owner','shell','content','call','--uri',support.URI,'--method','profile','--arg','P0']
    assert calls[0][1]['timeout']==12


@pytest.mark.parametrize('stdout,stderr',[(b'SecurityException: denied',b''),(b'',b'Exception: no provider')])
def test_denied_not_bypassed_or_retried(monkeypatch,stdout,stderr):
    calls=[]
    def run(*args,**kwargs):
        calls.append(args)
        return SimpleNamespace(returncode=0,stdout=stdout,stderr=stderr)
    monkeypatch.setattr(support.subprocess,'run',run)
    with pytest.raises(RuntimeError):support.command('owner','connect')
    assert len(calls)==1


def test_unknown_command_receipt_requires_readback(monkeypatch):
    monkeypatch.setattr(support,'adb',lambda *args:b'provider unavailable')
    with pytest.raises(RuntimeError,match='Unknown command receipt'):support.command('owner','connect')


def test_snapshot_is_whole_and_private_exclusive_file(monkeypatch,tmp_path):
    value=dict(schema=1,restricted_session=dict(protocol_errors=17))
    monkeypatch.setattr(support,'adb',lambda *args:json.dumps(value).encode())
    assert support.snapshot('owner')==value
    path=tmp_path/'capture.json';support.save(path,value)
    assert path.stat().st_mode & 0o777==0o600
    with pytest.raises(FileExistsError):support.save(path,value)
