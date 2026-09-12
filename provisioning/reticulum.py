"""RNS carrier only: no config verification, cache or VPN implementation."""
import json
import math
import sqlite3
import threading
import time

import RNS

from .auth import AUDIENCE, prove
from .envelope import MAX_ENVELOPE_BYTES, ProvisioningRejected, _unique_fields, public_identity

APP = 'family_connect'
MAX_REQUEST_BYTES = 4096
REJECTED = b'{"code":"PROVISIONING_REJECTED"}'
UNAVAILABLE = b'{"code":"PROVISIONING_UNAVAILABLE"}'


def _encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


# Stage 5 carrier API. Envelope verification and application live in the core.
CONTROL_CHALLENGE = '/control/v1/challenge'
CONTROL_FETCH = '/control/v1/fetch'
CONTROL_ACK = '/control/v1/ack'


class ReticulumControlProvider:
    def __init__(self, service, identity):
        self.service = service
        self.destination = RNS.Destination(identity, RNS.Destination.IN,
            RNS.Destination.SINGLE, APP, 'control', 'v1')
        for path in (CONTROL_CHALLENGE, CONTROL_FETCH, CONTROL_ACK):
            self.destination.register_request_handler(path, self.respond,
                allow=RNS.Destination.ALLOW_ALL, auto_compress=False)

    def respond(self, path, data, request_id, remote_identity, requested_at):
        try:
            if type(data) is not bytes or len(data) > MAX_REQUEST_BYTES:
                raise ValueError()
            if path == CONTROL_ACK:
                self.service.acknowledge(data)
                return b'ACK_STORED'
            body = json.loads(data, object_pairs_hook=_unique_fields)
            if type(body) is not dict:
                raise ValueError()
            if path == CONTROL_CHALLENGE:
                if set(body) != {'public_identity', 'wireguard_public_key'}:
                    raise ValueError()
                return _encode(self.service.challenge(**body))
            if path == CONTROL_FETCH:
                return self.service.fetch(body)
            raise ValueError()
        except (ValueError, TypeError, KeyError, UnicodeError, RecursionError):
            return REJECTED
        except (sqlite3.Error, OSError):
            return UNAVAILABLE


class ReticulumAdapter:
    """Finite synchronous carrier; caller owns RNS independently of VPN lifecycle."""
    @staticmethod
    def _wait(predicate, deadline, cancel):
        while True:
            if cancel.is_set():
                raise ProvisioningRejected('Reticulum operation cancelled')
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ProvisioningRejected('Reticulum operation timed out')
            if predicate():
                return
            cancel.wait(min(0.02, remaining))

    def _request(self, link, path, body, deadline, cancel):
        done = threading.Event()
        result = []
        def received(receipt):
            result.append(receipt.response)
            done.set()
        receipt = link.request(path, data=_encode(body), response_callback=received,
            failed_callback=lambda _: done.set(), timeout=max(0.001, deadline-time.monotonic()),
            max_response_size=MAX_ENVELOPE_BYTES + 1024)
        if receipt is False or receipt is None:
            raise ProvisioningRejected('Reticulum request failed')
        self._wait(lambda: done.is_set() or link.status == RNS.Link.CLOSED, deadline, cancel)
        if not result or type(result[0]) is not bytes or len(result[0]) > MAX_ENVELOPE_BYTES:
            raise ProvisioningRejected('invalid Reticulum response')
        if result[0] in (REJECTED, UNAVAILABLE):
            raise ProvisioningRejected('Reticulum provisioning rejected or unavailable')
        return result[0]


    def __init__(self, *, provider_public, device, clock, timeout=30, cancel=None):
        if (type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 < timeout <= 300):
            raise ValueError('invalid Reticulum timeout')
        self.provider = public_identity(provider_public)
        self.device, self.clock, self.timeout = device, clock, timeout
        self.cancel = cancel if cancel is not None else threading.Event()
        self._busy = threading.Lock()

    def _exchange(self, operation):
        if not self._busy.acquire(blocking=False):
            raise ProvisioningRejected('Reticulum operation already running')
        link = None
        deadline = time.monotonic() + self.timeout
        try:
            self._wait(lambda: True, deadline, self.cancel)
            destination = RNS.Destination(self.provider, RNS.Destination.OUT,
                RNS.Destination.SINGLE, APP, 'control', 'v1')
            if not RNS.Transport.has_path(destination.hash):
                RNS.Transport.request_path(destination.hash)
            self._wait(lambda: RNS.Transport.has_path(destination.hash), deadline, self.cancel)
            link = RNS.Link(destination)
            self._wait(lambda: link.status in (RNS.Link.ACTIVE, RNS.Link.CLOSED), deadline, self.cancel)
            if link.status != RNS.Link.ACTIVE:
                raise ProvisioningRejected('Reticulum link failed')
            return operation(link, deadline)
        finally:
            try:
                if link is not None:
                    link.teardown()
            finally:
                self._busy.release()

    def receive(self):
        def operation(link, deadline):
            raw = self._request(link, CONTROL_CHALLENGE, dict(public_identity=self.device.public_identity,
                wireguard_public_key=self.device.wireguard_public_key), deadline, self.cancel)
            try:
                challenge = json.loads(raw, object_pairs_hook=_unique_fields)
                now = self.clock()
                if (type(now) is not int or type(challenge) is not dict or
                        set(challenge) != {'challenge', 'audience', 'expires_at'} or
                        challenge['audience'] != AUDIENCE or type(challenge['expires_at']) is not int or
                        not now < challenge['expires_at'] <= now + 120):
                    raise ValueError()
                proof = prove(self.device, challenge['challenge'])
            except (ValueError, TypeError, UnicodeError, RecursionError):
                raise ProvisioningRejected('invalid provisioning challenge') from None
            return self._request(link, CONTROL_FETCH, proof, deadline, self.cancel)
        return self._exchange(operation)

    def send_ack(self, raw):
        # _request JSON encodes once; provider passes the identical canonical ACK
        # bytes to its verifier. No profile material or signing key on this path.
        from .ack import verify
        verify(raw)
        body = json.loads(raw)
        return self._exchange(lambda link, deadline: self._request(
            link, CONTROL_ACK, body, deadline, self.cancel)) == b'ACK_STORED'
