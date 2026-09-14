"""Offline control-config issuer. Reuses the existing Ed25519 signing key.

No key creation/rotation, network access, component downloads or catalog mutation.
Input is a schema-2 config with LOCAL_DEVICE_KEY placeholders, not device secrets.
"""
import argparse
import base64
import os
from pathlib import Path
import stat

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from provisioning.configuration import ControlConfiguration, issue_config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--key', type=Path, required=True)
    parser.add_argument('--configuration', type=Path, required=True)
    parser.add_argument('--recipient-public', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    fd = os.open(args.key, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or
                info.st_nlink != 1 or stat.S_IMODE(info.st_mode) != 0o600):
            raise ValueError('unsafe signing key')
        key = Ed25519PrivateKey.from_private_bytes(os.read(fd, 33))
    finally:
        os.close(fd)
    with args.configuration.open('rb') as source:
        state = ControlConfiguration.model_validate_json(source.read(65537))
    raw = issue_config(state, recipient_public=base64.b64decode(args.recipient_public, validate=True), signing_key=key)
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as output:
        output.write(raw); output.flush(); os.fsync(output.fileno())


if __name__ == '__main__':
    main()
