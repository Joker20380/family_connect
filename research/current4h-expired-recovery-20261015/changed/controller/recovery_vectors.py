import argparse
import os
from pathlib import Path
import time

from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption

from credential_renewal import atomic, canonical, digest, parse
from test_expired_recovery import RecoveryFixture


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    args.directory.mkdir(mode=0o700)
    fixture = RecoveryFixture(args.directory, now=int(time.time()))
    before = parse((fixture.nodes.nodes['NL'].live/'gateway.json').read_bytes())
    assert fixture.apply(fixture.bundle())['result'] == 'COMMITTED'
    snapshot = fixture.strict()
    issuer = fixture.validator.validate(canonical(snapshot), fixture.nodes.now)[2]
    after = parse((fixture.nodes.nodes['NL'].live/'gateway.json').read_bytes())
    clients = []
    with fixture.nodes.fixture.access.db() as database:
        for device in fixture.nodes.fixture.devices:
            row = fixture.nodes.fixture.service._grant(database, device, fixture.nodes.now)
            certificate = fixture.nodes.fixture.service._issue(row, issuer, fixture.nodes.now,
                                                               min(row['expires']-5, fixture.nodes.now+3600))
            clients.append(dict(after, certificate=certificate.public_bytes(Encoding.PEM).decode(),
                private_key=fixture.nodes.fixture.keys[device].private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()).decode()))
    vectors = canonical(dict(server_before=before, server_after=after, clients_after=clients))
    atomic(args.directory/'vectors.json', vectors)
    print(canonical(dict(result='GENERATED_DISPOSABLE_RECOVERY_ONLY', vector_sha256=digest(vectors),
                         production_inputs=0)).decode())


if __name__ == '__main__':
    main()
