import base64
import importlib.util
import json
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('activate_windows_tcp',ROOT/'scripts/activate_windows_tcp.py')
activation=importlib.util.module_from_spec(spec)
spec.loader.exec_module(activation)
DEVICE='FC1-'+bytes(range(1,33)).hex().upper()
PROFILE=dict(type='vless-reality-v1',server='192.0.2.10',port=443,
             id='11111111-2222-4333-8444-555555555555',
             public_key=base64.urlsafe_b64encode(bytes(range(1,33))).decode().rstrip('='),
             server_name='example.com',short_id='0123456789abcdef')


def test_signed_profile_matches_windows_fixture():
    # Public synthetic fixture. This key is ONLY for interoperability tests.
    key=Ed25519PrivateKey.from_private_bytes(bytes(range(32)))
    envelope=activation.issue(DEVICE,json.dumps(PROFILE),7,key,1000)
    key.public_key().verify(base64.b64decode(envelope['signature']),activation.DOMAIN+base64.b64decode(envelope['payload']))
    assert envelope==json.loads((ROOT/'tests/fixtures/windows-tcp-v1.json').read_text())
    assert base64.b64encode(key.public_key().public_bytes_raw()).decode()==(ROOT/'tests/fixtures/windows-tcp-v1.pub').read_text().strip()
    grant=json.loads(base64.b64decode(envelope['payload']))
    assert grant['sequence']==7 and grant['devicePublicKey']==base64.b64encode(bytes(range(1,33))).decode()
    assert grant['expiresAt']==87400


@pytest.mark.parametrize('change',[{'server':'127.0.0.1'},{'server':'224.0.0.1'},
    {'server':'192.0.2.10; x'},{'server':'example.com'},{'port':True},{'port':65536},
    {'server_name':'example.com\npostup=bad'},{'short_id':'a'},
    {'public_key':'A'*43},{'id':'00000000-0000-0000-0000-000000000000'}, {'command':'bad'}])
def test_issuer_rejects_unsafe_credentials(change):
    with pytest.raises(ValueError):
        activation.issue(DEVICE,json.dumps(PROFILE|change),1,Ed25519PrivateKey.generate(),1000)


@pytest.mark.parametrize('sequence',[0,-1,True,1.5,9007199254740992])
def test_issuer_rejects_invalid_sequence(sequence):
    with pytest.raises(ValueError):
        activation.issue(DEVICE,json.dumps(PROFILE),sequence,Ed25519PrivateKey.generate(),1000)


def test_issuer_rejects_duplicate_json():
    with pytest.raises(ValueError):
        activation.issue(DEVICE,json.dumps(PROFILE).replace('"port": 443','"port": 443, "port": 443'),1,Ed25519PrivateKey.generate(),1000)


def test_issuer_rejects_empty_device():
    with pytest.raises(ValueError):
        activation.issue('FC1-'+'0'*64,json.dumps(PROFILE),1,Ed25519PrivateKey.generate(),1000)
