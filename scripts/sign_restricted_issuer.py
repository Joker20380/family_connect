"""Offline delegation under the existing control root; never a directory signature."""
import argparse
import base64
import json
import os
import time
from pathlib import Path

from control.friends.restricted import DOMAIN, delegation
from scripts import signing_key


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    signing_key.arguments(parser)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    payload = args.input.read_bytes()
    if not 0 < len(payload) <= 8192:
        raise ValueError('issuer payload bounds')
    signer = signing_key.load(args)
    anchor = base64.b64decode((Path(__file__).resolve().parents[1] / 'clients/android/app/src/main/assets/control-anchor.pub').read_bytes().strip(), validate=True)
    if signer.public_key().public_bytes_raw() != anchor:
        raise ValueError('signer is not the existing Friends control root')
    envelope = dict(payload=base64.b64encode(payload).decode(), signature=base64.b64encode(signer.sign(DOMAIN + payload)).decode())
    delegation(envelope, anchor, int(time.time()))
    descriptor = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'w') as output:
        json.dump(envelope, output, separators=(',', ':'))
        output.flush()
        os.fsync(output.fileno())
    print('Restricted issuer delegation signed offline; no directory or device key included')


if __name__ == '__main__':
    main()
