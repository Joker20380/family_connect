"""Proof-gated reservation in the authoritative fleet transaction.

No enrollment, payment ingestion, HTTP endpoint, or Friends DB mirroring. Trusted
operators supply access grants and authenticated telemetry separately.
"""
import base64
import hashlib
import secrets
from typing import Annotated, Literal

from pydantic import Field, model_validator
from control.fleet_store import LeaseRejected
from device_identity.device import _decode, verify_transport_key_proof
from provisioning.envelope import public_identity
from provisioning.models import FrozenModel

AUDIENCE = 'family-connect/fleet-reservation/v1'


class Reservation(FrozenModel):
    request_id: Annotated[str, Field(pattern=r'^[A-Za-z0-9_-]{1,64}$')]
    registry_revision: Annotated[int, Field(strict=True, ge=1, lt=2**63)]
    country: Annotated[str, Field(pattern=r'^[a-z]{2}$')]
    transport: Literal['wireguard', 'amneziawg']
    version: Literal['1', '2.0', '3.1']
    lifetime: Annotated[int, Field(strict=True, ge=1, le=86400)]
    address_families: tuple[Annotated[int, Field(strict=True, ge=4, le=6)], ...] = (4,)

    @model_validator(mode='after')
    def supported(self):
        if (self.version not in ({'2.0', '3.1'} if self.transport == 'amneziawg' else {'1'})
                or self.address_families not in ((4,), (6,), (4, 6))):
            raise ValueError('invalid reservation capability')
        return self


class FleetAccess:
    def __init__(self, store):
        self.store = store

    def challenge(self, *, public, wg, request):
        if isinstance(request, Reservation):
            request = {name: getattr(request, name) for name in Reservation.model_fields}
        request = Reservation.model_validate(request)
        device = public_identity(_decode(public, 64)).hash.hex()
        _decode(wg, 32)
        with self.store._transaction() as (db, now):
            access = self.store._authorized(db, device, now)
            if access['public'] != public or access['wg'] != wg:
                raise LeaseRejected('binding-mismatch')
            db.execute('DELETE FROM challenges WHERE expires_at<=?', (now,))
            if db.execute('SELECT COUNT(*) FROM challenges WHERE device=?', (device,)).fetchone()[0] >= 8:
                raise LeaseRejected('challenge-limit')
            nonce = base64.b64encode(secrets.token_bytes(32)).decode()
            expires = min(now+120, access['expires_at'])
            db.execute('INSERT INTO challenges VALUES(?,?,?,?,?)',
                       (hashlib.sha256(nonce.encode()).hexdigest(), device, access['revision'],
                        request.model_dump_json(), expires))
            return dict(challenge=nonce, audience=AUDIENCE, expires_at=expires,
                        request=request.model_dump(mode='json'))

    def complete(self, proof, *, observations):
        # Verify before acquiring the write lock. Revision, expiry, immutable
        # binding and challenge consumption are rechecked under that lock.
        if type(proof) is not dict:
            raise LeaseRejected('invalid-proof')
        device = verify_transport_key_proof(proof, expected_challenge=proof.get('challenge'), audience=AUDIENCE)
        nonce = hashlib.sha256(proof['challenge'].encode()).hexdigest()
        with self.store._transaction() as (db, now):
            challenge = db.execute('SELECT * FROM challenges WHERE nonce=?', (nonce,)).fetchone()
            access = self.store._authorized(db, device, now)
            if (challenge is None or challenge['device'] != device or challenge['expires_at'] <= now
                    or challenge['revision'] != access['revision']
                    or access['public'] != proof['public_identity'] or access['wg'] != proof['wireguard_public_key']):
                raise LeaseRejected('challenge-denied')
            request = Reservation.model_validate_json(challenge['request'])
            lease = self.store._reserve(db, now, device=device, observations=observations, **request.model_dump())
            db.execute('DELETE FROM challenges WHERE nonce=?', (nonce,))
            return lease
