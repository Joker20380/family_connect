"""RU: выдача подписанной активации. EN: issue a signed device activation.

Run on the operator's trusted machine. Only public keys leave the Windows device.
Output peer JSON must be registered on the controlled gateway before delivery.
"""
import argparse
import base64
import ipaddress
import json
import os
from pathlib import Path
import re
import time
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

DOMAIN = b'family-connect/device-activation/v1\0'

def key32(value):
    raw = base64.b64decode(value, validate=True)
    if len(raw) != 32 or not any(raw) or base64.b64encode(raw).decode() != value:
        raise ValueError('invalid public key')
    return value

def issue(request, number, gateway_public, endpoint, signing_key, now):
    if not re.fullmatch(r'FC1-[0-9A-F]{64}', request):
        raise ValueError('invalid device code')
    device = key32(base64.b64encode(bytes.fromhex(request[4:])).decode())
    if not 4 <= number <= 254:
        raise ValueError('reserved or invalid device address')
    host, port = endpoint.split(':')
    if str(ipaddress.IPv4Address(host)) != host or not 1 <= int(port) <= 65535:
        raise ValueError('invalid gateway endpoint')
    grant = dict(version=1, devicePublicKey=device, gatewayPublicKey=key32(gateway_public),
                 endpoint=endpoint, address=f'10.77.0.{number}', dns='1.1.1.1', expiresAt=now+86400)
    raw = json.dumps(grant, sort_keys=True, separators=(',', ':')).encode()
    envelope = dict(payload=base64.b64encode(raw).decode(),
                    signature=base64.b64encode(signing_key.sign(DOMAIN+raw)).decode())
    peer = dict(version=1, public_key=device, address=grant['address'], ipv6=f'fd77:92::{number:x}')
    return envelope, peer

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--key', required=True, type=Path)
    parser.add_argument('--init-public', type=Path)
    parser.add_argument('--request')
    parser.add_argument('--number', type=int)
    parser.add_argument('--gateway-public')
    parser.add_argument('--endpoint', default='185.251.89.19:51820')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    os.umask(0o077)
    if args.init_public:
        args.key.parent.mkdir(parents=True, exist_ok=True)
        if not args.key.exists():
            with args.key.open('xb') as file:
                file.write(Ed25519PrivateKey.generate().private_bytes_raw())
        key = Ed25519PrivateKey.from_private_bytes(args.key.read_bytes())
        args.init_public.write_text(base64.b64encode(key.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)).decode()+'\n')
        print('Activation trust root initialized; private key was not printed.')
        return
    if not all([args.request, args.number, args.gateway_public, args.output]):
        parser.error('request, number, gateway-public and output are required')
    key = Ed25519PrivateKey.from_private_bytes(args.key.read_bytes())
    envelope, peer = issue(args.request, args.number, args.gateway_public, args.endpoint, key, int(time.time()))
    args.output.mkdir(parents=True, exist_ok=True)
    # Do not overwrite previous issued devices or quietly reuse an allocated address.
    for filename, data in [('device.fcactivation', envelope), ('peer.json', peer)]:
        with (args.output/filename).open('x') as file:
            json.dump(data,file,sort_keys=True)
    print('Register peer.json on the controlled gateway first, then deliver device.fcactivation. No private device key was transferred.')

if __name__ == '__main__':
    main()
