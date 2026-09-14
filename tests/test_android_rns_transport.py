import base64,json,os,subprocess,sys
from pathlib import Path
import pytest
import RNS
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from device_identity.device import DeviceIdentity
from provisioning.configuration import ConfigVerifier

@pytest.mark.parametrize('provider',['default','internal'])
def test_android_packaged_transport_real_rns(tmp_path,provider):
    helper=Path(__file__).with_name('android_rns_peer.py')
    result=subprocess.run([sys.executable,str(helper),str(tmp_path),provider],env=os.environ.copy(),capture_output=True,text=True,timeout=90)
    # Never expose temporary fixture files/keys as part of an assertion failure.
    assert result.returncode==0, (result.stdout[-1000:],result.stderr[-2000:])
    assert 'REAL_RNS_PASS '+provider in result.stdout
    data=json.loads((tmp_path/'fixture.json').read_text())
    device=DeviceIdentity(RNS.Identity.from_bytes(bytes.fromhex(data['identity'])),X25519PrivateKey.from_private_bytes(bytes.fromhex(data['wg'])))
    verifier=ConfigVerifier(anchor=bytes.fromhex(data['anchor']),device=device,client_version='0.2.9')
    assert verifier.verify((tmp_path/'envelope1').read_bytes(),now=1000).state.revision==1
    assert verifier.verify((tmp_path/'envelope2').read_bytes(),now=1000).state.revision==2
