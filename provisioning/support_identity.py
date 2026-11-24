"""Explicit one-time support identity initialization; never run by the worker."""
import argparse
import json
import os
from pathlib import Path

from messenger.store import Store


def initialize(directory):
    if not directory.is_absolute() or any(parent.is_symlink() for parent in directory.parents):
        raise ValueError('Absolute private identity directory required')
    directory.mkdir(mode=0o700, parents=False, exist_ok=False)
    key = os.urandom(32)
    with (directory / 'store.key').open('xb') as stream:
        os.fchmod(stream.fileno(), 0o600)
        stream.write(key)
        stream.flush()
        os.fsync(stream.fileno())
    store = Store(directory / 'history', key)
    try:
        identity = store.chat_identity()
        public = identity.get_public_key().hex()
        proof = dict(public=public, signature=identity.sign(
            b'family-connect/chat-service/v1\n' + public.encode('ascii')).hex())
        for name, content in (('registration.json', json.dumps(proof) + '\n'),
                              ('sender.env', 'SUPPORT_SENDER_PUBLIC=' + public + '\n')):
            with (directory / name).open('x') as stream:
                os.fchmod(stream.fileno(), 0o600)
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
    finally:
        store.close()
    descriptor = os.open(directory, os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    initialize(parser.parse_args().directory)
    print('Support identity initialized; private state is not printed.')


if __name__ == '__main__':
    main()
