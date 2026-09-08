"""RU: запускать на клиентском компьютере. EN: run on the client computer only."""
import argparse
import base64
import os
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey


def generate(output, server_public, endpoint):
    root = Path(output)
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    for name, number in [('android', 2), ('linux', 3)]:
        key_path = root / (name + '.key')
        if key_path.exists():
            key = X25519PrivateKey.from_private_bytes(base64.b64decode(key_path.read_bytes()))
        else:
            key = X25519PrivateKey.generate()
            key_path.write_text(base64.b64encode(key.private_bytes_raw()).decode()+'\n')
            key_path.chmod(0o600)
        public = base64.b64encode(key.public_key().public_bytes_raw()).decode()
        (root / (name+'.pub')).write_text(public+'\n')
        if server_public:
            if len(base64.b64decode(server_public, validate=True)) != 32:
                raise ValueError('invalid server public key')
            config = (f'[Interface]\nPrivateKey = {key_path.read_text().strip()}\n'
                      f'Address = 10.77.0.{number}/32, fd77:92::{number}/128\n'
                      'DNS = 1.1.1.1\nMTU = 1380\n\n[Peer]\n'
                      f'PublicKey = {server_public}\nEndpoint = {endpoint}\n'
                      'AllowedIPs = 0.0.0.0/0, ::/0\nPersistentKeepalive = 25\n')
            path = root / f'fc-ru-{name}.conf'
            path.write_text(config)
            path.chmod(0o600)
    print('Client keys/configs saved locally; private keys were not printed.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='RU/EN: локальные ключи / local keys')
    parser.add_argument('--output', required=True)
    parser.add_argument('--server-public', default='')
    parser.add_argument('--endpoint', default='185.251.89.19:51820')
    args = parser.parse_args()
    os.umask(0o077)
    generate(args.output, args.server_public, args.endpoint)
