import base64,json,importlib.util
from pathlib import Path
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('awg_issuer',ROOT/'scripts/activate_windows_awg.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
PROFILE={'gatewayPublicKey': 'ICEiIyQlJicoKSorLC0uLzAxMjM0NTY3ODk6Ozw9Pj8=', 'server': '192.0.2.10', 'port': 51821, 'number': 4, 'parameters': {'Jc': '3', 'Jmin': '40', 'Jmax': '80', 'S1': '17', 'S2': '29', 'S3': '3', 'S4': '9', 'H1': '1001-1010', 'H2': '2001-2010', 'H3': '3001-3010', 'H4': '4001-4010', 'I1': '<b 0x11223344><r 16>'}}
DEVICE='FC1-'+bytes(range(1,33)).hex().upper()
def test_awg_fixture():
 key=Ed25519PrivateKey.from_private_bytes(bytes(range(32)));e=m.issue(DEVICE,json.dumps(PROFILE),7,key,1000)
 assert e==json.loads((ROOT/'tests/fixtures/windows-awg-v1.json').read_text())
 key.public_key().verify(base64.b64decode(e['signature']),m.DOMAIN+base64.b64decode(e['payload']))
@pytest.mark.parametrize('change',[{'number':3},{'number':255},{'number':True},{'server':'127.0.0.1'},{'server':'224.0.0.1'},{'port':0},{'port':True},{'gatewayPublicKey':'A'*44},{'hook':'bad'}])
def test_reject_profile(change):
 with pytest.raises((ValueError,TypeError)):m.issue(DEVICE,json.dumps(PROFILE|change),1,Ed25519PrivateKey.generate(),1000)
@pytest.mark.parametrize('change',[{'Jc':'0'},{'Jmin':'0'},{'Jmax':'10'},{'H1':'2005'},{'H1':'4294967296'},{'S1':'257'},{'I1':'<b 0x1>'},{'I1':'<r 1281>'},{'I1':'\nprivate_key=bad'},{'PostUp':'bad'}])
def test_reject_parameters(change):
 with pytest.raises(ValueError):m.issue(DEVICE,json.dumps(PROFILE|{'parameters':PROFILE['parameters']|change}),1,Ed25519PrivateKey.generate(),1000)
@pytest.mark.parametrize('sequence',[0,True,-1,9007199254740992])
def test_reject_sequence(sequence):
 with pytest.raises(ValueError):m.issue(DEVICE,json.dumps(PROFILE),sequence,Ed25519PrivateKey.generate(),1000)
def test_duplicate():
 with pytest.raises(ValueError):m.issue(DEVICE,json.dumps(PROFILE).replace('"number": 4','"number": 4, "number": 4'),1,Ed25519PrivateKey.generate(),1000)
