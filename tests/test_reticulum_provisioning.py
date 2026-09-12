import threading

import pytest
import RNS

from provisioning import reticulum as module
from provisioning.envelope import ProvisioningRejected
from test_control_channel import environment


@pytest.mark.parametrize('data', [b'{}', b'[]', b'{', b'\xff', b'{"x":1,"x":2}', b'x'*4097, 'string', None])
def test_invalid_request_before_service(data):
    server = module.ReticulumControlProvider.__new__(module.ReticulumControlProvider)
    server.service = None
    assert server.respond(module.CONTROL_CHALLENGE, data, None, None, 0) == module.REJECTED


@pytest.mark.parametrize('timeout', [True, 0, -1, 301, float('inf'), float('nan')])
def test_invalid_timeout(environment, timeout):
    with pytest.raises(ValueError):
        module.ReticulumAdapter(provider_public=RNS.Identity().get_public_key(), device=environment.device,
            clock=lambda: 1000, timeout=timeout)


def test_path_timeout_and_cancel(environment, monkeypatch):
    requests = []
    monkeypatch.setattr(module.RNS.Transport, 'has_path', lambda _: False)
    monkeypatch.setattr(module.RNS.Transport, 'request_path', lambda value: requests.append(value))
    class Destination:
        OUT, SINGLE = 1, 0
        def __init__(self, *args): self.hash = b'pinned'
    monkeypatch.setattr(module.RNS, 'Destination', Destination)
    cancel = threading.Event()
    carrier = module.ReticulumAdapter(provider_public=RNS.Identity().get_public_key(),
        device=environment.device, clock=lambda: 1000, timeout=0.03, cancel=cancel)
    with pytest.raises(ProvisioningRejected, match='timed out'):
        carrier.receive()
    cancel.set()
    with pytest.raises(ProvisioningRejected, match='cancelled'):
        carrier.receive()
    assert requests == [b'pinned'] and not carrier._busy.locked()
