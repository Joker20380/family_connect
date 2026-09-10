"""Synchronous reference HTTP provider with explicit offline cache access."""
import json

from .auth import AUDIENCE, prove
from .envelope import MAX_ENVELOPE_BYTES, ProvisioningRejected, _unique_fields


class ProvisioningClient:
    def __init__(self, http_client, device, cache):
        # Inject a configured HTTPS client, including bounded timeout and pinned
        # service URL. Test transports can implement this same client interface.
        if http_client.base_url.scheme != 'https':
            raise ValueError('provisioning requires HTTPS')
        self.http = http_client
        self.device = device
        self.cache = cache

    def _post(self, path, body):
        with self.http.stream('POST', path, json=body, follow_redirects=False) as response:
            response.raise_for_status()
            raw = bytearray()
            for chunk in response.iter_bytes():
                if len(raw) + len(chunk) > MAX_ENVELOPE_BYTES:
                    raise ProvisioningRejected('oversized provisioning response')
                raw.extend(chunk)
            return bytes(raw)

    def refresh(self, *, now):
        raw = self._post('/v2/provisioning/challenge', dict(
            public_identity=self.device.public_identity,
            wireguard_public_key=self.device.wireguard_public_key))
        try:
            challenge = json.loads(raw, object_pairs_hook=_unique_fields)
            if (type(challenge) is not dict or
                    set(challenge) != {'challenge', 'audience', 'expires_at'} or
                    challenge['audience'] != AUDIENCE or type(challenge['expires_at']) is not int or
                    not now < challenge['expires_at'] <= now + 120):
                raise ValueError()
            proof = prove(self.device, challenge['challenge'])
        except (ValueError, TypeError, UnicodeError, RecursionError):
            raise ProvisioningRejected('invalid provisioning challenge') from None
        envelope = self._post('/v2/provisioning/fetch', proof)
        return self.cache.accept(envelope, now=now)

    def cached(self, *, now):
        # No automatic fallback on a rejected authentication or failed refresh.
        return self.cache.load(now=now)
