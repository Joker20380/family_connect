import hashlib
import json
import os
from pathlib import Path

import pytest
from cryptography import x509
from cryptography.hazmat.primitives.serialization import Encoding

from scripts.gateway_credential_publication import Contract, PublicationError, publish
from test_native_authority_compat import fixture, native


def test_python_and_native_credential_validation_survives_publication(tmp_path):
    binary=os.environ.get('FC_TEST_NATIVE_CHECKER')
    if not binary:
        pytest.skip('set FC_TEST_NATIVE_CHECKER to the accepted native checker')
    assert hashlib.sha256(Path(binary).read_bytes()).hexdigest()==os.environ['FC_TEST_NATIVE_CHECKER_SHA256']
    service,owner,now,profile=fixture(tmp_path)
    trust,authority,crl,_,floor=service._trust(now)
    with service.access.db() as database:
        certificate=service._issue(service._grant(database,owner.reference,now),authority,now,now+900)
    certificate=certificate.public_bytes(Encoding.PEM).decode()
    live=tmp_path/'live';live.mkdir(mode=0o700)
    receipts=tmp_path/'receipts';receipts.mkdir(mode=0o700)
    validation=tmp_path/'validation';validation.mkdir(mode=0o700)
    target=live/'gateway.json';target.write_bytes(b'old-credential');target.chmod(0o600)
    contract=Contract(os.geteuid(),os.getegid(),os.geteuid(),os.getegid(),0o700)
    def validate(raw):
        value=json.loads(raw)
        assert value['family']==trust['family'] and value['gateway']==trust['gateway']
        x509.load_pem_x509_certificate(value['certificate'].encode()).verify_directly_issued_by(authority)
        assert crl.is_signature_valid(authority.public_key()) and value['minimum_crl']==floor
        result=native(binary,validation,value,certificate)
        return result.returncode==0 and json.loads(result.stdout)['status']=='PASS'
    raw=json.dumps(profile).encode()
    result=publish(target,raw,contract,receipts/'pass.json',validate=validate)
    assert result['status']=='PASS' and validate(target.read_bytes())
    old=target.read_bytes()
    changed=json.dumps(dict(profile,minimum_revision=3)).encode()
    with pytest.raises(PublicationError):publish(target,changed,contract,receipts/'fail.json',validate=validate)
    assert target.read_bytes()==old
    for receipt in receipts.glob('*.json'):
        assert 'PRIVATE KEY' not in receipt.read_text() and profile['private_key'] not in receipt.read_text()
