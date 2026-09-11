"""Issue a device-bound Windows TCP activation offline; existing server peer only.

This does not provision a gateway peer. Input and output contain a VPN credential;
use private local paths, never CI or Git. The device private key is not requested.
"""
import argparse
import base64
import json
import os
from pathlib import Path
import re
import sys
import time
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'clients' / 'desktop'))
from profile_config import parse_tcp

DOMAIN = b'family-connect/windows-tcp-activation/v1\0'


def issue(request, profile, sequence, signing_key, now):
    if not isinstance(request, str) or not re.fullmatch(r'FC1-[0-9A-F]{64}', request):
        raise ValueError('Invalid device code')
    device = bytes.fromhex(request[4:])
    if not any(device):
        raise ValueError('Invalid device key')
    if type(sequence) is not int or not 1 <= sequence <= 9007199254740991:
        raise ValueError('Invalid profile sequence')
    if type(now) is not int or not 0 <= now < 253402214399:
        raise ValueError('Invalid clock')
    p = parse_tcp(profile)
    import ipaddress
    address = ipaddress.IPv4Address(p['server'])
    if address.is_loopback or address.packed[0] == 0 or address.packed[0] >= 224:
        raise ValueError('Invalid gateway address')
    if p['id'] == '00000000-0000-0000-0000-000000000000' or not any(base64.urlsafe_b64decode(p['public_key']+'=')):
        raise ValueError('Invalid credential')
    grant = dict(version=1, devicePublicKey=base64.b64encode(device).decode(),
                 sequence=sequence, expiresAt=now+86400, server=p['server'], port=p['port'],
                 id=p['id'], publicKey=p['public_key'], serverName=p['server_name'], shortId=p['short_id'])
    raw = json.dumps(grant, sort_keys=True, separators=(',', ':')).encode()
    return dict(payload=base64.b64encode(raw).decode(),
                signature=base64.b64encode(signing_key.sign(DOMAIN+raw)).decode())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--key', type=Path, required=True)
    parser.add_argument('--profile', type=Path, required=True)
    parser.add_argument('--request', required=True)
    parser.add_argument('--sequence', type=int, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    os.umask(0o077)
    try:
        with args.profile.open('rb') as file:
            raw = file.read(16385)
        if len(raw)>16384:
            raise ValueError('Profile too large')
        key = Ed25519PrivateKey.from_private_bytes(args.key.read_bytes())
        envelope = issue(args.request, raw.decode(), args.sequence, key, int(time.time()))
        with args.output.open('x', encoding='utf-8') as file:
            json.dump(envelope, file, sort_keys=True)
    except (ValueError, OSError, UnicodeError):
        parser.exit(1, 'Cannot issue TCP activation; check inputs and use a new private output path.\n')
    print('TCP activation saved. Deliver privately to its Windows device; gateway unchanged.')


if __name__ == '__main__':
    main()
