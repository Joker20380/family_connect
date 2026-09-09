"""Local-only site-link keys; never transfer the private file between hosts."""
import base64
import os
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey


def create(directory):
    os.umask(0o077)
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = root/'private.key'
    if not path.exists():
        key = X25519PrivateKey.generate()
        path.write_bytes(base64.b64encode(key.private_bytes_raw())+b'\n')
    key = X25519PrivateKey.from_private_bytes(base64.b64decode(path.read_bytes(), validate=False))
    path.chmod(0o600)
    (root/'public.pub').write_bytes(base64.b64encode(key.public_key().public_bytes_raw())+b'\n')


if __name__ == '__main__':
    import sys
    create(sys.argv[1])
