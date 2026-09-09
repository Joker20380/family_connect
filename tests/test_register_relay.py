from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import json
import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID
from scripts.identity import create
from scripts.register_relay import register


def setup(tmp_path):
    key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'test CA')])
    now = datetime.now(timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
        .serial_number(x509.random_serial_number()).not_valid_before(now-timedelta(days=1))
        .not_valid_after(now+timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=True,path_length=0),critical=True).sign(key,hashes.SHA256()))
    (tmp_path/'ca.der').write_bytes(cert.public_bytes(serialization.Encoding.DER))
    (tmp_path/'ca.key').write_bytes(key.private_bytes(serialization.Encoding.DER,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
    create(tmp_path/'device','relay-remote')
    state={'version':2,'epoch':4,'nodes':[],'devices':[]}
    (tmp_path/'network.json').write_text(json.dumps(state))
    return SimpleNamespace(csr=str(tmp_path/'device/request.pem'),ca_cert=str(tmp_path/'ca.der'),
        ca_key=str(tmp_path/'ca.key'),certificate=str(tmp_path/'cert.der'),network=str(tmp_path/'network.json'),
        name='relay-remote',endpoint='172.29.94.11:4444',replace=None)


def test_register_non_exit_and_idempotency(tmp_path):
    args=setup(tmp_path)
    register(args)
    first=(tmp_path/'network.json').read_bytes()
    state=json.loads(first)
    assert state['epoch']==5 and state['nodes'][0]['internet_exit'] is False
    register(args)
    assert (tmp_path/'network.json').read_bytes()==first


def test_invalid_endpoint_does_not_publish(tmp_path):
    args=setup(tmp_path)
    args.endpoint='0.0.0.0:0'
    first=(tmp_path/'network.json').read_bytes()
    with pytest.raises(ValueError): register(args)
    assert (tmp_path/'network.json').read_bytes()==first


def test_cannot_replace_gateway(tmp_path):
    args=setup(tmp_path)
    (tmp_path/'network.json').write_text(json.dumps({'version':2,'epoch':4,'nodes':[{'name':'gateway','role':'gateway'}],'devices':[]}))
    args.replace='gateway'
    first=(tmp_path/'network.json').read_bytes()
    with pytest.raises(ValueError): register(args)
    assert (tmp_path/'network.json').read_bytes()==first
