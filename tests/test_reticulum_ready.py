"""Deterministic RNS ACTIVE-before-LRRTT scheduling regression."""
import threading
from types import SimpleNamespace
import pytest
import RNS
from provisioning.reticulum import ReticulumAdapter
from provisioning.envelope import ProvisioningRejected


@pytest.mark.parametrize('complete', [True, False])
def test_request_waits_for_establishment_callback(monkeypatch,complete):
    adapter=ReticulumAdapter(provider_public=RNS.Identity().get_public_key(),device=None,clock=lambda:0,timeout=2)
    early=threading.Event();release=threading.Event();requests=[];closed=[];outcome=[]
    def link(destination, established_callback=None):
        value=SimpleNamespace(status=RNS.Link.ACTIVE,teardown=lambda:closed.append(True))
        def finish():
            release.wait(2)
            if not complete:value.status=RNS.Link.CLOSED
            elif established_callback is not None:established_callback(value)
        threading.Thread(target=finish,daemon=True).start()
        early.set()
        return value
    # A callable class keeps the constants accessed by the adapter.
    class FakeLink:
        ACTIVE=2;CLOSED=4
        def __new__(cls,destination,established_callback=None):return link(destination,established_callback)
    monkeypatch.setattr(RNS,'Link',FakeLink)
    monkeypatch.setattr(RNS.Transport,'has_path',lambda _:True)
    monkeypatch.setattr(RNS,'Destination',lambda *a:SimpleNamespace(hash=b'x'))
    RNS.Destination.OUT=1;RNS.Destination.SINGLE=0
    def exchange():
        try:outcome.append(adapter._exchange(lambda *_:requests.append(True)))
        except ProvisioningRejected:outcome.append('rejected')
    worker=threading.Thread(target=exchange)
    worker.start()
    try:
        assert early.wait(1)
        assert not requests
        # ACTIVE is already visible; the operation must remain blocked.
        worker.join(.08)
        assert worker.is_alive() and not requests
    finally:
        release.set();worker.join(2)
    assert not worker.is_alive() and closed==[True]
    assert requests==([True] if complete else [])
    assert outcome==([None] if complete else ['rejected'])
