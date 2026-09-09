"""Operator-only CSR issuance and atomic signed-catalog membership update."""
import argparse
import fcntl
import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import ExtendedKeyUsageOID
from control.app import validate_payload


def register(args):
    csr = x509.load_pem_x509_csr(Path(args.csr).read_bytes())
    if not csr.is_signature_valid or not isinstance(csr.public_key(), ec.EllipticCurvePublicKey):
        raise ValueError('invalid EC CSR')
    public = csr.public_key().public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
    identity = hashlib.sha256(public).hexdigest()
    ca = x509.load_der_x509_certificate(Path(args.ca_cert).read_bytes())
    ca_key = serialization.load_der_private_key(Path(args.ca_key).read_bytes(), password=None)
    cert_path = Path(args.certificate)
    now = datetime.now(timezone.utc)
    if cert_path.exists():
        cert = x509.load_der_x509_certificate(cert_path.read_bytes())
        cert.verify_directly_issued_by(ca)
        if cert.public_key().public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo) != public:
            raise ValueError('existing certificate belongs to another key')
        if cert.not_valid_after_utc <= now:
            raise ValueError('expired certificate requires explicit rotation')
    else:
        cert = (x509.CertificateBuilder().subject_name(csr.subject).issuer_name(ca.subject)
            .public_key(csr.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(now-timedelta(minutes=1)).not_valid_after(now+timedelta(days=30))
            .add_extension(x509.BasicConstraints(ca=False,path_length=None),critical=True)
            .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]),critical=False)
            .add_extension(x509.SubjectAlternativeName([x509.DNSName(args.name+'.test')]),critical=False)
            .sign(ca_key,hashes.SHA256()))
        cert_path.write_bytes(cert.public_bytes(serialization.Encoding.DER))
    node = {'identity':identity,'name':args.name,'endpoint':args.endpoint,'role':'relay',
            'internet_exit':False,'cert_sha256':hashlib.sha256(cert_path.read_bytes()).hexdigest(),
            'server_name':args.name+'.test'}
    path = Path(args.network)
    with (path.parent/'membership.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = json.loads(path.read_text())
        for old in state['nodes']:
            if old['name'] == args.name and old['identity'] != identity:
                raise ValueError('node name already belongs to another identity')
            if old['name'] == args.replace and old['role'] != 'relay':
                raise ValueError('only a relay can be replaced')
        nodes = [node]+[n for n in state['nodes'] if n['name'] not in [args.name,args.replace]]
        if state['nodes'] == nodes:
            print('unchanged'); return
        state['nodes'] = nodes
        state['epoch'] += 1
        validate_payload({**state,'issued_at':int(now.timestamp()),'expires_at':int(now.timestamp())+900}, now=int(now.timestamp()))
        temp = path.with_suffix('.tmp')
        with temp.open('w') as out:
            json.dump(state,out,indent=2); out.write('\n'); out.flush(); os.fsync(out.fileno())
        os.replace(temp,path)
        descriptor = os.open(path.parent,os.O_DIRECTORY)
        try: os.fsync(descriptor)
        finally: os.close(descriptor)
        print('registered relay at epoch',state['epoch'])


if __name__ == '__main__':
    p=argparse.ArgumentParser()
    for name in ['csr','ca-key','ca-cert','certificate','network','name','endpoint']:
        p.add_argument('--'+name,required=True)
    p.add_argument('--replace')
    register(p.parse_args())
