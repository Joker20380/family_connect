"""Bounded existing-identity readiness relay; authentication stays at the issuer API."""

import base64
import http.client
import json
import ssl
import threading


PATHS = frozenset('/friends/restricted-readiness' + suffix for suffix in
                  ('', '/challenge', '/ack-challenge', '/ack'))
MAX_REQUEST = 8192
MAX_RESPONSE = 65536


class ReadinessRelay:
    def __init__(self, connection=None):
        self.connection = connection or (lambda: http.client.HTTPSConnection(
            '185.251.89.19', 8443, timeout=10, context=ssl.create_default_context()))
        self.slots = threading.BoundedSemaphore(4)

    @staticmethod
    def result(status, body=b''):
        return json.dumps({'status': status, 'body': base64.b64encode(body).decode('ascii')},
                          separators=(',', ':')).encode()

    def respond(self, path, data, request_id=None, remote_identity=None, requested_at=None):
        if path not in PATHS or type(data) is not bytes or not 0 < len(data) <= MAX_REQUEST:
            return self.result(400)
        if not self.slots.acquire(blocking=False):
            return self.result(503)
        connection = None
        try:
            connection = self.connection()
            connection.request('POST', path, body=data,
                               headers={'Content-Type': 'application/json', 'Cache-Control': 'no-store'})
            response = connection.getresponse()
            if response.status != 200:
                return self.result(response.status)
            if response.getheader('Content-Encoding', 'identity') != 'identity':
                return self.result(502)
            body = response.read(MAX_RESPONSE + 1)
            if not body or len(body) > MAX_RESPONSE:
                return self.result(502)
            return self.result(200, body)
        except (OSError, http.client.HTTPException):
            return self.result(503)
        finally:
            if connection is not None:
                connection.close()
            self.slots.release()
