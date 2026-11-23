"""Loopback-only mTLS etcd rehearsal; deliberately not a production authority."""
import base64
import http.client
import json
import socket
import ssl
import time
from urllib.parse import urlsplit

from .control_shadow import MAX_BYTES, encode, validate

KEY = b'/family-connect/rehearsal/control-ha/shadow-v1'


class QuorumUnavailable(RuntimeError):
    pass


class ShadowConflict(RuntimeError):
    pass


def encoded(raw):
    return base64.b64encode(raw).decode()


def tls_context(ca, certificate, key):
    context = ssl.create_default_context(cafile=ca)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(certificate, key)
    return context


class ShadowQuorum:
    def __init__(self, endpoints, context, *, timeout=5):
        if (len(endpoints) != 3 or len(set(endpoints)) != 3 or not 0 < timeout <= 10
                or context.verify_mode != ssl.CERT_REQUIRED or not context.check_hostname):
            raise ValueError('THREE_VERIFIED_REHEARSAL_ENDPOINTS_REQUIRED')
        self.endpoints = []
        for endpoint in endpoints:
            parsed = urlsplit(endpoint)
            if (parsed.scheme != 'https' or parsed.hostname != '127.0.0.1'
                    or not parsed.port or parsed.username or parsed.password
                    or parsed.path or parsed.query or parsed.fragment):
                raise ValueError('LOOPBACK_MTLS_REHEARSAL_ONLY')
            self.endpoints.append(parsed)
        self.context, self.timeout = context, timeout

    def request(self, route, payload, *, first_only=False):
        if route not in ('/v3/kv/range', '/v3/kv/txn', '/v3/maintenance/status'):
            raise ValueError('SHADOW_ROUTE_FORBIDDEN')
        deadline = time.monotonic() + self.timeout
        raw = encode(payload)
        for endpoint in self.endpoints[:1] if first_only else self.endpoints:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            connection = http.client.HTTPSConnection(endpoint.hostname, endpoint.port,
                context=self.context, timeout=min(remaining, self.timeout / 3))
            try:
                connection.request('POST', route, raw, {'Content-Type': 'application/json'})
                response = connection.getresponse()
                body = response.read(MAX_BYTES * 2 + 1)
                if response.status != 200 or len(body) > MAX_BYTES * 2:
                    continue
                value = json.loads(body)
                header = value.get('header', {}) if type(value) is dict else {}
                if (type(value) is dict and 'error' not in value and type(header) is dict
                        and all(str(header.get(field, '')).isdigit() and int(header[field]) > 0
                                for field in ('cluster_id', 'member_id', 'revision'))):
                    return value
            except (OSError, socket.timeout, http.client.HTTPException, ValueError):
                continue
            finally:
                connection.close()
        raise QuorumUnavailable('SHADOW_QUORUM_UNAVAILABLE')

    def read(self, *, first_only=False):
        result = self.request('/v3/kv/range', dict(key=encoded(KEY), serializable=False), first_only=first_only)
        records = result.get('kvs', [])
        if not records:
            if int(result.get('count', 0)) != 0:
                raise ValueError('INVALID_QUORUM_REPLY')
            return None, 0
        if len(records) != 1 or records[0]['key'] != encoded(KEY):
            raise ValueError('INVALID_QUORUM_REPLY')
        raw = base64.b64decode(records[0]['value'], validate=True)
        revision = int(records[0]['mod_revision'])
        if len(raw) > MAX_BYTES or revision <= 0:
            raise ValueError('INVALID_QUORUM_REPLY')
        return json.loads(raw), revision

    def replace(self, manifest, revision):
        if type(revision) is not int or revision < 0 or len(encode(manifest)) > MAX_BYTES:
            raise ValueError('INVALID_SHADOW_REPLACEMENT')
        guard = dict(key=encoded(KEY), target='MOD' if revision else 'VERSION', result='EQUAL')
        guard['mod_revision' if revision else 'version'] = str(revision)
        result = self.request('/v3/kv/txn', dict(compare=[guard], success=[dict(
            request_put=dict(key=encoded(KEY), value=encoded(encode(manifest))))], failure=[]))
        return result.get('succeeded', False) is True

    def publish(self, manifest, key, *, now=None):
        payload = validate(manifest, key, now=now)
        current, revision = self.read()
        if current == manifest:
            return 'unchanged'
        if current is not None:
            previous = validate(current, key, now=current.get('payload', {}).get('observed_at'))
            if payload['observed_at'] <= previous['observed_at']:
                raise ShadowConflict('SHADOW_ORDER_CONFLICT')
        try:
            if self.replace(manifest, revision):
                return 'published'
        except QuorumUnavailable:
            pass
        current, _ = self.read()
        if current == manifest:
            return 'confirmed-by-readback'
        raise ShadowConflict('SHADOW_WRITE_CONFLICT_OR_UNKNOWN')
