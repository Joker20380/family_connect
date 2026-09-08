"""RU: Изолированный PKI-стенд; выпуск по CSR. EN: Lab PKI, CSR-only issuance."""
import hashlib
import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

root = Path(os.environ.get('PROVISION_ROOT', '/provision'))
authority = root / 'authority'
control = root / 'control'
trust = root / 'trust'
for directory in (authority, control, trust):
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
now = datetime.now(UTC)
if not (authority / 'ca.key').exists():
    key = ec.generate_private_key(ec.SECP256R1())
    (authority / 'ca.key').write_bytes(key.private_bytes(serialization.Encoding.DER,
        serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    (authority / 'ca.key').chmod(0o600)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'Family Connect Lab CA')])
    certificate = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
        .public_key(key.public_key()).serial_number(x509.random_serial_number())
        .not_valid_before(now-timedelta(minutes=1)).not_valid_after(now+timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=True,path_length=0),critical=True)
        .add_extension(x509.KeyUsage(False,False,False,False,False,True,True,None,None),critical=True)
        .sign(key,hashes.SHA256()))
    (trust / 'ca.der').write_bytes(certificate.public_bytes(serialization.Encoding.DER))
ca_key = serialization.load_der_private_key((authority / 'ca.key').read_bytes(), password=None)
ca = x509.load_der_x509_certificate((trust / 'ca.der').read_bytes())
if not (control / 'signing.key').exists():
    key = ed25519.Ed25519PrivateKey.generate()
    (control / 'signing.key').write_bytes(key.private_bytes_raw())
    (control / 'signing.key').chmod(0o600)
root_key = ed25519.Ed25519PrivateKey.from_private_bytes((control / 'signing.key').read_bytes())
(trust / 'root.pub').write_bytes(root_key.public_key().public_bytes_raw())
nodes, devices = [], []
for name, role, endpoint in [('gateway-lab','gateway','172.29.92.10:4433'),
                             ('relay-a','relay','172.29.92.11:4444'),
                             ('relay-b','relay','172.29.92.12:4444'),
                             ('client','device',None),('outsider','device',None)]:
    directory = root / name
    # Issuer consumes a public CSR, never the device private key.
    csr = x509.load_pem_x509_csr((directory / 'request.pem').read_bytes())
    if not csr.is_signature_valid:
        raise ValueError('invalid CSR signature')
    public = csr.public_key().public_bytes(serialization.Encoding.DER,
                                          serialization.PublicFormat.SubjectPublicKeyInfo)
    identity = hashlib.sha256(public).hexdigest()
    cert_path = directory / 'cert.der'
    if not cert_path.exists():
        usage = ExtendedKeyUsageOID.CLIENT_AUTH if role=='device' else ExtendedKeyUsageOID.SERVER_AUTH
        certificate = (x509.CertificateBuilder().subject_name(csr.subject).issuer_name(ca.subject)
            .public_key(csr.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(now-timedelta(minutes=1)).not_valid_after(now+timedelta(days=30))
            .add_extension(x509.BasicConstraints(ca=False,path_length=None),critical=True)
            .add_extension(x509.ExtendedKeyUsage([usage]),critical=False)
            .add_extension(x509.SubjectAlternativeName([x509.DNSName(name+'.test')]),critical=False)
            .sign(ca_key,hashes.SHA256()))
        cert_path.write_bytes(certificate.public_bytes(serialization.Encoding.DER))
    certificate = x509.load_der_x509_certificate(cert_path.read_bytes())
    if certificate.public_key().public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo) != public:
        raise ValueError('certificate/key mismatch')
    pin = hashlib.sha256(cert_path.read_bytes()).hexdigest()
    if role=='device':
        if name!='outsider': devices.append({'identity':identity,'cert_sha256':pin})
    else:
        nodes.append({'identity':identity,'name':name,'endpoint':endpoint,'role':role,
                      'internet_exit':role=='gateway','cert_sha256':pin,'server_name':name+'.test'})
network = control / 'network.json'
# Repeat provisioning must NOT silently re-enroll a revoked device.
if not network.exists():
    network.write_text(json.dumps({'version':2,'epoch':1,'nodes':nodes,'devices':devices},indent=2)+'\n')
