import base64
import json
from pathlib import Path
import sys
import threading
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import RNS
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from device_identity.device import DeviceIdentity
from messenger.admission import message
from provisioning.chat_bridge import ChatBridge
from provisioning import chat_bridge_protocol as wire


def main():
    config = json.loads(sys.stdin.readline())
    identity = RNS.Identity(create_keys=False)
    assert identity.load_private_key(base64.b64decode(config['identity']))
    device = DeviceIdentity(identity, X25519PrivateKey.from_private_bytes(base64.b64decode(config['wireguard_private'])))
    chat = RNS.Identity()
    public = chat.get_public_key().hex()
    bridge = ChatBridge(device.reference, _paths=[Path(config['vpn'])], _root_uid=0)
    bridge.service_path = Path(config['service'])
    bridge.configure(lambda: dict(identity=config['identity'], wireguard_public=device.wireguard_public_key))
    channel = None
    try:
        for raw in sys.stdin:
            command = json.loads(raw)
            try:
                if command['action'] == 'exchange':
                    body = dict(public_identity=device.public_identity, wireguard_public_key=device.wireguard_public_key, chat_public=public)
                    status, reply = bridge.request(wire.PATHS[0], json.dumps(body).encode(), 12)
                    assert status == 200
                    challenge = json.loads(reply)['challenge']
                    registration = dict(proof=device.prove_transport_key(challenge), chat_public=public,
                        chat_signature=chat.sign(message(public, device.reference, challenge)).hex())
                    assert bridge.request(wire.PATHS[1], json.dumps(registration).encode(), 12)[0] == 200
                    assert bridge.route == command['route']
                    mailbox = bridge.open_mailbox if bridge.route == 'EXISTING_EXIT' else bridge.open_service_mailbox
                    with mailbox(time.monotonic() + 12, threading.Event()) as stream:
                        stream.settimeout(3)
                        assert stream.recv(9) == b'from-peer'
                        stream.sendall(b'to-peer')
                        assert stream.recv(7) == b'to-peer'
                elif command['action'] == 'open':
                    mailbox = bridge.open_mailbox if bridge.route == 'EXISTING_EXIT' else bridge.open_service_mailbox
                    channel = mailbox(time.monotonic() + 12, threading.Event())
                    channel.settimeout(3)
                    assert channel.recv(9) == b'from-peer'
                elif command['action'] == 'eof':
                    assert channel.recv(1) == b''
                    channel.close()
                    channel = None
                elif command['action'] == 'drain':
                    deadline = time.monotonic() + 16
                    while True:
                        assert time.monotonic() < deadline
                        try:
                            channel.sendall(b'k')
                            if channel.recv(1) == b'':
                                break
                        except BrokenPipeError:
                            break
                        time.sleep(.1)
                    channel.close()
                    channel = None
                elif command['action'] == 'denied':
                    body = dict(public_identity=device.public_identity, wireguard_public_key=device.wireguard_public_key,
                                chat_public=RNS.Identity().get_public_key().hex())
                    bridge.request(wire.PATHS[0], json.dumps(body).encode(), 12)
                    raise AssertionError('native HTTP denial must remain typed DENIED')
                else:
                    raise AssertionError(command['action'])
                result = dict(ok=True, route=bridge.route)
            except wire.BridgeError as error:
                result = dict(ok=False, error=error.code)
            print(json.dumps(result), flush=True)
    finally:
        if channel is not None:
            channel.close()
        bridge.close()


if __name__ == '__main__':
    main()
