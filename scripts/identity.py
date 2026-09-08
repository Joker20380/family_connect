"""RU: Локальный ключ и публичный CSR. EN: Local key and public CSR."""
import argparse
import hashlib
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID


def create(directory, name):
    directory = Path(directory)
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    path = directory / 'key.der'
    if not path.exists():
        key = ec.generate_private_key(ec.SECP256R1())
        path.write_bytes(key.private_bytes(serialization.Encoding.DER,
                         serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
        path.chmod(0o600)
    key = serialization.load_der_private_key(path.read_bytes(), password=None)
    public = key.public_key().public_bytes(serialization.Encoding.DER,
                                          serialization.PublicFormat.SubjectPublicKeyInfo)
    identity = hashlib.sha256(public).hexdigest()
    csr = (x509.CertificateSigningRequestBuilder()
           .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, name)]))
           .sign(key, hashes.SHA256()))
    (directory / 'request.pem').write_bytes(csr.public_bytes(serialization.Encoding.PEM))
    (directory / 'identity.txt').write_text(identity + '\n')
    return identity


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--directory', required=True)
    parser.add_argument('--name', required=True)
    args = parser.parse_args()
    print(create(args.directory, args.name))
