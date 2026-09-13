import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location('route_broker', Path(__file__).resolve().parents[1] / 'clients/linux/control-route-helper.py')
h = importlib.util.module_from_spec(spec); spec.loader.exec_module(h)

@pytest.fixture
def pin():
    return dict(schema=1, provider='a'*64, uid=1000, address='186.246.45.246', port=4242, priority=10590)

@pytest.mark.parametrize('field,value', [('uid',1001),('uid',True),('provider','b'*64),('address','127.0.0.1'),('address','10.0.0.1'),('address','::1'),('port',True),('port',0),('priority',32766),('schema',True),('extra','x')])
def test_reject_untrusted_pin(pin, field, value):
    pin[field] = value
    with pytest.raises(ValueError):h.validate(pin, 'a'*64, 1000)

def test_pin_and_exact_rule_ownership(pin):
    assert h.validate(pin, 'a'*64, 1000) == pin
    record=dict(priority=10590,src='all',dst=pin['address'],uid_start=1000,uid_end=1000,ipproto='tcp',dport=4242,table='main',dport_mask='0xffff')
    assert h.matches(record,pin)
    for field,value in [('uid_end',1001),('dport_mask','0xff00'),('table','other'),('iif','lo')]:
        assert not h.matches({**record,field:value},pin)

def test_foreign_priority_not_deleted(pin,tmp_path,monkeypatch):
    marker=tmp_path/'intent.json';marker.write_text('{}')
    monkeypatch.setattr(h,'occupied',lambda _: [dict(priority=10590,src='all',table='main')])
    calls=[];monkeypatch.setattr(h,'command',lambda *a:calls.append(a))
    with pytest.raises(ValueError):h.release(pin,marker)
    assert marker.exists() and not calls

def test_failed_add_cleans_only_owned_intent(pin,tmp_path,monkeypatch):
    marker=tmp_path/'intent.json';monkeypatch.setattr(h,'occupied',lambda _: [])
    def fail(*_):raise OSError('ip unavailable')
    monkeypatch.setattr(h,'command',fail)
    with pytest.raises(OSError):h.acquire(pin,marker)
    assert not marker.exists()
