"""Actual RNS Stage 5 lifecycle fixture. No production keys or interfaces."""
import json
import os
from pathlib import Path
import sys
import time

import RNS
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey

from device_identity.device import DeviceIdentity
from provisioning.configuration import ConfigVerifier
from provisioning.transaction import ControlJournal, ProvisioningCore
from provisioning.reticulum import ReticulumAdapter, ReticulumControlProvider
from provisioning import ack
from test_control_channel import environment, signed, Application

mode, directory, port = sys.argv[1:]
root = Path(directory)
config = root / mode
config.mkdir()
interface = (f'type = TCPServerInterface\nlisten_ip = 127.0.0.1\nlisten_port = {port}'
    if mode == 'server' else f'type = TCPClientInterface\ntarget_host = 127.0.0.1\ntarget_port = {port}')
(config / 'config').write_text('[reticulum]\nshare_instance = No\nenable_transport = No\n'
    '[logging]\nloglevel = 0\n[interfaces]\n[[loopback]]\nenabled = Yes\n' + interface + '\n')
RNS.Reticulum(configdir=str(config), loglevel=0)
if mode == 'server':
    e = environment.__wrapped__(root)
    import hashlib
    second = signed(e, dict(config_id='config-2', revision=2, previous_config_hash=hashlib.sha256(e.raw).hexdigest()))
    original_ack = e.relay.acknowledge
    published = [False]
    def acknowledged(raw):
        original_ack(raw)
        body = ack.verify(raw)
        if body['status'] == 'COMMITTED' and not published[0]:
            e.relay.publish(public=e.device.public_identity, wg=e.device.wireguard_public_key,
                sequence=2, envelope=second)
            published[0] = True
        return True
    e.relay.acknowledge = acknowledged
    transport = RNS.Identity()
    provider = ReticulumControlProvider(e.relay, transport)
    with os.fdopen(os.open(root / 'fixture.json', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w') as f:
        json.dump(dict(provider=transport.get_public_key().hex(), anchor=e.anchor.hex(),
            identity=e.device._identity.get_private_key().hex(),
            wg=e.device._wireguard_key.private_bytes_raw().hex()), f)
    print('ready', flush=True)
    while True:
        provider.destination.announce()
        time.sleep(1)
else:
    data = json.loads((root / 'fixture.json').read_text())
    device = DeviceIdentity(RNS.Identity.from_bytes(bytes.fromhex(data['identity'])),
        X25519PrivateKey.from_private_bytes(bytes.fromhex(data['wg'])))
    verifier = ConfigVerifier(anchor=bytes.fromhex(data['anchor']), device=device, client_version='0.2.9')
    journal = ControlJournal(root / 'receiver-journal', verifier)
    journal.initialize()
    application = Application()
    core = ProvisioningCore(journal=journal, application=application, device=device, clock=lambda: 1000)
    carrier = ReticulumAdapter(provider_public=bytes.fromhex(data['provider']), device=device,
        clock=lambda: 1000, timeout=15)
    assert core.refresh(carrier) == 'COMMITTED'
    good = application.active
    application.health = False
    assert core.refresh(carrier) == 'ROLLED_BACK'
    assert application.active == good
    assert core.refresh(carrier) == 'ROLLED_BACK'
    assert len(application.applied) == 2
    with journal._locked() as directory:
        state = journal.read(directory)
        assert not state['outbox'] and state['committed']['digest'] == good and state['floor'] == 2
    print('RNS: commit, ACK, rollback, ACK, duplicate safe, last-good preserved', flush=True)
