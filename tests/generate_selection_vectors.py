"""PUBLIC TEST ONLY: new immutable selection fixtures, derived from public AWG31 test data."""
import base64, copy, hashlib, json, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import RNS
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from provisioning.configuration import DOMAIN

def generate(out):
    out.mkdir(parents=True,exist_ok=False)
    source=Path(__file__).parent/'vectors/control-awg31-v1'
    manifest=json.loads((source/'manifest.json').read_text())
    identity=json.loads((source/'TEST-ONLY-identity.json').read_text())
    device=RNS.Identity.from_bytes(base64.b64decode(identity['rns_private_b64']))
    signer=Ed25519PrivateKey.from_private_bytes(hashlib.sha256(b'PUBLIC TEST ONLY FC AWG31 issuer').digest())
    state=copy.deepcopy(next(v['payload'] for v in manifest['configurations'] if v['id']=='valid'))
    second=copy.deepcopy(state['transport_profiles'][0]);second.update(profile_id='second',gateway_id='second-node')
    second['config']=second['config'].replace('198.51.100.1:51820','198.51.100.2:51820')
    state['transport_profiles'].append(second)
    state['gateways'].append(dict(gateway_id='second-node',endpoint='198.51.100.2',port=51820))
    files={}
    def put(name,raw):
        (out/name).write_bytes(raw);files[name]=dict(size=len(raw),sha256=hashlib.sha256(raw).hexdigest())
    def sign(value):
        cipher=device.encrypt(json.dumps(value,separators=(',',':')).encode())
        return json.dumps(dict(ciphertext=base64.b64encode(cipher).decode(),signature=base64.b64encode(signer.sign(DOMAIN+cipher)).decode()),separators=(',',':')).encode()
    raw=sign(state);put('two-gateways.envelope',raw)
    state.update(revision=2,config_id='next-config',previous_config_hash=hashlib.sha256(raw).hexdigest())
    state['transport_profiles']=state['transport_profiles'][:1];state['gateways']=state['gateways'][:1]
    put('next.envelope',sign(state))
    put('TEST-ONLY-identity.json',json.dumps(identity).encode())
    (out/'manifest.json').write_text(json.dumps(dict(test_only=True,files=files),sort_keys=True))

if __name__=='__main__':generate(Path(sys.argv[1]))
