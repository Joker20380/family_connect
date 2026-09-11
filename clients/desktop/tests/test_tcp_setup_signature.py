import base64,importlib.util,json,sys
from pathlib import Path
import pytest
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('setup_signature',ROOT/'scripts/tcp_setup_signature.py');signature=importlib.util.module_from_spec(spec);spec.loader.exec_module(signature)
@pytest.fixture
def signed(tmp_path):
    key=Ed25519PrivateKey.generate();private=tmp_path/'key';private.write_bytes(key.private_bytes_raw());private.chmod(0o600)
    public=tmp_path/'pub';public.write_bytes(base64.b64encode(key.public_key().public_bytes_raw()))
    archive=tmp_path/'setup';archive.write_bytes(b'bounded test archive');proof=tmp_path/'proof'
    signature.sign(archive,'0.1.0',private,proof)
    return archive,proof,public,private
def test_signature_authenticates_archive_and_explicit_version(signed):
    archive,proof,public,_=signed
    assert signature.verify(archive,proof,public,'0.1.0')['component']=='tcp-setup'
    with pytest.raises(ValueError):signature.verify(archive,proof,public,'0.1.1')
@pytest.mark.parametrize('change',['archive','key','signature','domain','duplicate'])
def test_tampering_and_cross_domain_rejected(signed,change):
    archive,proof,public,private=signed
    if change=='archive':archive.write_bytes(b'tampered')
    elif change=='key':public.write_bytes(base64.b64encode(Ed25519PrivateKey.generate().public_key().public_bytes_raw()))
    elif change=='duplicate':proof.write_text('{"payload":"","payload":"","signature":""}')
    else:
        d=json.loads(proof.read_bytes())
        if change=='domain':d['signature']=base64.b64encode(Ed25519PrivateKey.from_private_bytes(private.read_bytes()).sign(b'family-connect/app-update/v1\0'+base64.b64decode(d['payload']))).decode()
        else:d['signature']=base64.b64encode(bytes(64)).decode()
        proof.write_text(json.dumps(d))
    with pytest.raises((ValueError,InvalidSignature)):signature.verify(archive,proof,public,'0.1.0')
def test_signing_refuses_overwrite_and_unsafe_key(signed):
    archive,proof,_,private=signed
    with pytest.raises(FileExistsError):signature.sign(archive,'0.1.0',private,proof)
    private.chmod(0o644)
    with pytest.raises(ValueError):signature.sign(archive,'0.1.0',private,proof.with_suffix('.new'))
def test_oversized_archive_rejected(signed):
    archive,proof,public,_=signed;archive.write_bytes(bytes(signature.MAX_SIZE+1))
    with pytest.raises(ValueError):signature.verify(archive,proof,public,'0.1.0')
