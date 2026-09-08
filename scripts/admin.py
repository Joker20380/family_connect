"""RU: Локальное управление членством. EN: Operator-local membership management."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.x509.oid import ExtendedKeyUsageOID


def update(root, action, certificate, ca_file):
    root = Path(root)
    cert_bytes = Path(certificate).read_bytes()
    cert = x509.load_der_x509_certificate(cert_bytes)
    cert.verify_directly_issued_by(x509.load_der_x509_certificate(Path(ca_file).read_bytes()))
    if ExtendedKeyUsageOID.CLIENT_AUTH not in cert.extensions.get_extension_for_class(x509.ExtendedKeyUsage).value:
        raise ValueError('certificate is not a device credential')
    pin = hashlib.sha256(cert_bytes).hexdigest()
    identity = hashlib.sha256(cert.public_key().public_bytes(serialization.Encoding.DER,
                              serialization.PublicFormat.SubjectPublicKeyInfo)).hexdigest()
    with (root / 'membership.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        path = root / 'network.json'
        state = json.loads(path.read_text())
        present = any(d['identity'] == identity for d in state['devices'])
        if action == 'enroll' and present:
            raise ValueError('device already enrolled')
        if action == 'revoke' and not present:
            raise ValueError('device not enrolled')
        state['devices'] = [d for d in state['devices'] if d['identity'] != identity]
        if action == 'enroll':
            state['devices'].append({'identity': identity, 'cert_sha256': pin})
        state['epoch'] += 1
        temp = path.with_suffix('.tmp')
        with temp.open('w') as stream:
            json.dump(state, stream, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        temp.replace(path)
        directory_fd = os.open(root, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
        return state['epoch']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='RU: членство / EN: membership')
    parser.add_argument('action', choices=('enroll', 'revoke'))
    parser.add_argument('--state', default='/state')
    parser.add_argument('--certificate', required=True)
    parser.add_argument('--ca', required=True)
    args = parser.parse_args()
    print(json.dumps({'epoch': update(args.state, args.action, args.certificate, args.ca)}))
