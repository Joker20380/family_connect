import importlib.util,subprocess,sys
from pathlib import Path
from types import SimpleNamespace
import pytest
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'clients/desktop'))
import backend

def test_missing_broker_never_requests_root(monkeypatch):
 monkeypatch.setattr(backend,'tcp_updater_available',lambda:False)
 monkeypatch.setattr(backend.subprocess,'run',lambda *a,**k:pytest.fail('unexpected authorization'))
 with pytest.raises(backend.BackendError):backend.install_tcp_component()

@pytest.mark.parametrize('code',[0,1,126,127])
def test_fixed_operation_and_authorization(monkeypatch,code):
 monkeypatch.setattr(backend,'tcp_updater_available',lambda:True)
 def call(args,**kw):
  assert args==['pkexec','/usr/local/lib/family-connect-tcp-updater/broker','install']
  assert kw['stdin']==subprocess.DEVNULL and kw['timeout']==900
  return SimpleNamespace(returncode=code)
 monkeypatch.setattr(backend.subprocess,'run',call)
 if code==0:assert backend.install_tcp_component()
 else:
  with pytest.raises(backend.AuthorizationError if code in (126,127) else backend.BackendError):backend.install_tcp_component()

@pytest.mark.parametrize('args',[[],['install','/tmp/evil'],['--url','https://evil.example'],['serve']])
def test_broker_rejects_caller_paths_and_operations(monkeypatch,args):
 spec=importlib.util.spec_from_file_location('broker',ROOT/'clients/linux/tcp-update-broker.py');broker=importlib.util.module_from_spec(spec);spec.loader.exec_module(broker)
 monkeypatch.setattr(broker.os,'geteuid',lambda:0);monkeypatch.setattr(broker.sys,'argv',['broker']+args)
 monkeypatch.setattr(broker,'trusted',lambda:pytest.fail('accepted caller-controlled operation'))
 with pytest.raises(ValueError):broker.main()

def test_untrusted_broker_not_available(tmp_path,monkeypatch):
 p=tmp_path/'broker';p.write_text('anything');p.chmod(0o777)
 monkeypatch.setattr(backend,'TCP_UPDATER',p)
 assert not backend.tcp_updater_available()
