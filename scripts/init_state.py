import hashlib
import json
import os
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption

root = Path(os.environ.get("STATE_DIR", "/state"))
root.mkdir(mode=0o700, parents=True, exist_ok=True)
key_path = root / "signing.key"
if not key_path.exists():
    key_path.write_bytes(Ed25519PrivateKey.generate().private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption()))
    key_path.chmod(0o600)
network = root / "network.json"
if not network.exists():
    nodes = []
    for name, address, role in [("gateway-lab", "172.29.91.10:4433", "gateway"),
                               ("relay-a", "172.29.91.11:4444", "relay"),
                               ("relay-b", "172.29.91.12:4444", "relay")]:
        # Stable local node identities provisioned once; not yet wired into QUIC peer auth.
        key = Ed25519PrivateKey.generate()
        path = root / f"{name}.identity"
        path.write_bytes(key.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption()))
        path.chmod(0o600)
        nodes.append({"identity": hashlib.sha256(key.public_key().public_bytes_raw()).hexdigest(),
                      "name": name, "endpoint": address, "role": role,
                      "internet_exit": role == "gateway", "transports": ["quic-udp-lab"]})
    network.write_text(json.dumps({"version": 1, "epoch": 1, "nodes": nodes}, indent=2))
