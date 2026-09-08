"""Read-only signed bootstrap for the private Phase 0 laboratory."""
import base64
import json
import os
import time
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from fastapi import FastAPI, HTTPException

DOMAIN = b"family-connect/network-state/v1\x00"
app = FastAPI(title="Family Connect — private Phase 0", docs_url=None, redoc_url=None)


def sign_state(payload, key):
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return {"payload": base64.b64encode(raw).decode(),
            "signature": base64.b64encode(key.sign(DOMAIN + raw)).decode()}


def verify_state(envelope, pinned_key, *, now, minimum_epoch=0):
    raw = base64.b64decode(envelope["payload"], validate=True)
    if len(raw) > 65536:
        raise ValueError("oversized network state")
    signature = base64.b64decode(envelope["signature"], validate=True)
    Ed25519PublicKey.from_public_bytes(pinned_key).verify(signature, DOMAIN + raw)
    state = json.loads(raw)
    if state["version"] != 1 or state["epoch"] < minimum_epoch:
        raise ValueError("unsupported or rolled-back state")
    if not state["issued_at"] <= now < state["expires_at"]:
        raise ValueError("expired or future state")
    if state["expires_at"] - state["issued_at"] > 3600:
        raise ValueError("excessive validity")
    for node in state["nodes"]:
        if node["role"] not in ("relay", "gateway"):
            raise ValueError("unknown role")
        if node["role"] == "relay" and node["internet_exit"]:
            raise ValueError("relay cannot be an exit")
    return state


def state_path():
    return Path(os.environ.get("STATE_DIR", "/state"))


@app.get("/healthz")
def health():
    return {"status": "ok", "phase": "private-lab", "public_vpn": False}


@app.get("/v1/network-state")
def network_state():
    try:
        root = state_path()
        key = Ed25519PrivateKey.from_private_bytes((root / "signing.key").read_bytes())
        payload = json.loads((root / "network.json").read_text())
        now = int(time.time())
        payload.update(issued_at=now, expires_at=now + 900)
        return sign_state(payload, key)
    except (OSError, ValueError, KeyError):
        raise HTTPException(503, "network state unavailable") from None


@app.get("/v1/trust-root")
def trust_root():
    # Bootstrap provisioning aid only: clients MUST pin this out of band.
    try:
        key = Ed25519PrivateKey.from_private_bytes((state_path() / "signing.key").read_bytes())
        public = key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
        return {"public_key": base64.b64encode(public).decode(), "trust_on_first_use": False}
    except OSError:
        raise HTTPException(503, "trust root unavailable") from None
