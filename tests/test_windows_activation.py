import base64
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

root=Path(__file__).resolve().parents[1]
def module(name):
    spec=importlib.util.spec_from_file_location(name,root/'scripts'/f'{name}.py')
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result
activation=module('activate_windows');registration=module('register_pilot_peer')
PUBLIC=base64.b64encode(bytes(range(1,33))).decode()

def test_activation_is_signed_public_data_bound_to_device():
    key=Ed25519PrivateKey.generate()
    envelope,peer=activation.issue('FC1-'+bytes(range(1,33)).hex().upper(),4,PUBLIC,'185.251.89.19:51820',key,100)
    raw=base64.b64decode(envelope['payload'])
    key.public_key().verify(base64.b64decode(envelope['signature']),activation.DOMAIN+raw)
    grant=json.loads(raw)
    assert grant['devicePublicKey']==peer['public_key']==PUBLIC
    assert grant['expiresAt']==86500 and peer['address']=='10.77.0.4'
    assert set(grant)=={'version','devicePublicKey','gatewayPublicKey','endpoint','address','dns','expiresAt'}

def test_registration_rejects_existing_address_without_mutation(tmp_path):
    peer=dict(version=1,public_key=PUBLIC,address='10.77.0.4',ipv6='fd77:92::4')
    responses=[SimpleNamespace(stdout='# family-connect-dynamic-peers-v1'),SimpleNamespace(stdout='another-key\t10.77.0.4/32 fd77:92::4/128\n')]
    with patch.object(registration.subprocess,'run',side_effect=responses) as run:
        with pytest.raises(ValueError,match='already assigned'):registration.register(peer,tmp_path,'gateway')
    assert run.call_count==2 and not list((tmp_path/'peers').glob('*.conf'))

def test_registration_requires_persistent_gateway_support(tmp_path):
    peer=dict(version=1,public_key=PUBLIC,address='10.77.0.4',ipv6='fd77:92::4')
    with patch.object(registration.subprocess,'run',return_value=SimpleNamespace(stdout='old version')) as run:
        with pytest.raises(RuntimeError,match='must be upgraded'):registration.register(peer,tmp_path,'gateway')
    assert run.call_count==1
