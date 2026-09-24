import json
import pytest
from clients.desktop.tests.test_xhttp import PROFILE

def test_managed_reality_cannot_smuggle_xhttp():
    from provisioning.configuration import TransportProfile
    with pytest.raises(ValueError):
        TransportProfile(profile_id='test', gateway_id='test', transport='vless-reality',
                         transport_version='1', config=json.dumps(PROFILE))
